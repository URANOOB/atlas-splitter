"""Exportación determinista de resultados guiados por la geometría de un glTF."""

# ruff: noqa: E501
from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import Literal, cast

import numpy as np
from PIL import Image

from atlas_splitter.blender.script_writer import write_rebuild_script
from atlas_splitter.domain import (
    AtlasCapabilities,
    AtlasElement,
    BoundingBox,
    SceneManifest,
    UvIsland,
    UvManifest,
    write_versioned_manifest,
)
from atlas_splitter.exceptions import GltfLoadError, PrimitiveDecodeError
from atlas_splitter.geometry.glb_loader import LoadedGltf
from atlas_splitter.geometry.primitive_decoder import decode_scene_primitives
from atlas_splitter.geometry.texture_resolver import (
    TextureBinding,
    TextureSlot,
    TextureTransform,
    export_material_crops,
    material_texture_bindings,
    read_texture_image,
)
from atlas_splitter.geometry.uv_islands import uv_island_triangle_groups
from atlas_splitter.geometry.uv_rasterizer import rasterize_uv_triangles

LOGGER = logging.getLogger(__name__)
GroupBy = Literal["node", "mesh", "primitive", "uv-island"]


def export_glb(
    loaded: LoadedGltf,
    destination: Path,
    *,
    atlas: Path | None = None,
    texture_index: int | None = None,
    texture_slot: str = "baseColor",
    group_by: GroupBy = "uv-island",
    allow_unbound_atlas: bool = False,
    node_indices: set[int] | None = None,
    flip_v: bool = False,
) -> UvManifest:
    """Escribe máscaras UV, recortes, manifiestos y el script de reconstrucción."""
    primitives = decode_scene_primitives(loaded)
    destination = destination.resolve()
    elements: list[AtlasElement] = []
    selected_atlas = atlas.resolve() if atlas is not None else None
    for primitive in primitives:
        if node_indices is not None and primitive.reference.node_index not in node_indices:
            continue
        binding = _primary_binding(loaded, primitive.reference.material_index, texture_slot, texture_index)
        manual_atlas = binding is None and selected_atlas is not None and allow_unbound_atlas
        if manual_atlas:
            binding = TextureBinding(
                slot=cast("TextureSlot", texture_slot),
                texture_index=-1,
                image_index=-1,
                texcoord=0,
                transform=TextureTransform(),
                wrap_s="REPEAT",
                wrap_t="REPEAT",
                color_space="sRGB",
            )
        if binding is None:
            LOGGER.warning("Se omite %s: no hay textura %s asociada al material.", primitive.reference, texture_slot)
            continue
        override = (
            _verified_external_atlas(selected_atlas, loaded, binding)
            if selected_atlas and not manual_atlas
            else _external_image(selected_atlas)
            if manual_atlas and selected_atlas
            else None
        )
        if binding.texcoord not in primitive.texcoords:
            raise PrimitiveDecodeError(f"La primitiva {primitive.reference} no contiene TEXCOORD_{binding.texcoord}.")
        uvs = primitive.texcoords[binding.texcoord]
        groups = _groups(primitive.triangle_indices, group_by)
        for group_index, triangle_rows in enumerate(groups):
            triangles = primitive.triangle_indices[triangle_rows]
            transformed = _flip_v(binding.transform.apply(uvs)) if flip_v else binding.transform.apply(uvs)
            source_image = override or read_texture_image(loaded, binding.image_index)
            region = rasterize_uv_triangles(transformed, triangles, source_image.width, source_image.height, binding.wrap_s, binding.wrap_t)
            key = f"{group_by}-{group_index}"
            element = _element(loaded, primitive, binding, key, uvs, transformed, triangles, triangle_rows, region)
            element_dir = destination / "materials" / element.element_id
            material_index = primitive.reference.material_index
            exported = (
                _export_external_crop(element_dir, override, region)
                if manual_atlas and override is not None
                else export_material_crops(
                    element_dir,
                    loaded,
                    material_texture_bindings(loaded, material_index)
                    if material_index is not None
                    else [],
                    uvs,
                    triangles,
                    image_overrides={binding.image_index: override} if override else None,
                )
            )
            mask_path = destination / "masks" / f"{element.element_id}.png"
            mask_path.parent.mkdir(parents=True, exist_ok=True)
            Image.fromarray((region.mask * 255).astype(np.uint8), "L").save(mask_path)
            relative = {slot: str(path.relative_to(destination).as_posix()) for slot, path in exported.items()}
            elements.append(
                element.model_copy(
                    update={
                        "exported_files": relative | {"uv_mask": str(mask_path.relative_to(destination).as_posix())},
                        "warnings": ["Atlas externo asociado manualmente; el GLB no declara este material."]
                        if manual_atlas
                        else [],
                        "compatibility_level": "manual_external_atlas" if manual_atlas else "geometry_guided",
                    }
                )
            )
    if not elements:
        raise GltfLoadError("No se exportó ninguna región: no hay asociaciones material/textura/UV compatibles.")
    first_image = _image_for_dimensions(loaded, elements[0].image_index, selected_atlas)
    manifest = UvManifest(
        source_file=str(loaded.source_path), capabilities=AtlasCapabilities.geometry_guided(),
        atlas_width=first_image.width, atlas_height=first_image.height, elements=elements,
        warnings=[
            "Los recortes preservan la máscara UV; revise materiales con UV repetidas o transformaciones complejas.",
            "El atlas se asoció manualmente porque el GLB no declara materiales."
            if allow_unbound_atlas
            else "",
            "La coordenada V se invirtió por la convención confirmada del atlas externo." if flip_v else "",
        ],
    )
    write_versioned_manifest(destination / "uv_manifest.json", manifest)
    write_versioned_manifest(
        destination / "scene_manifest.json",
        SceneManifest(source_file=str(loaded.source_path), capabilities=AtlasCapabilities.geometry_guided(), elements=elements),
    )
    write_rebuild_script(destination / "blender" / "rebuild_scene.py", loaded.source_path, destination / "uv_manifest.json")
    LOGGER.info("Exportadas %s regiones UV en %s", len(elements), destination)
    return manifest


def _primary_binding(loaded: LoadedGltf, material_index: int | None, slot: str, texture_index: int | None) -> TextureBinding | None:
    if material_index is None:
        return None
    bindings = [item for item in material_texture_bindings(loaded, material_index) if item.slot == slot]
    if texture_index is not None:
        bindings = [item for item in bindings if item.texture_index == texture_index]
    if len(bindings) > 1:
        raise GltfLoadError(f"El material {material_index} tiene asociaciones ambiguas para {slot}; use --texture-index.")
    return bindings[0] if bindings else None


def _verified_external_atlas(atlas: Path, loaded: LoadedGltf, binding: TextureBinding) -> Image.Image:
    if not atlas.is_file():
        raise GltfLoadError(f"No existe el atlas externo: {atlas}")
    try:
        with Image.open(atlas) as candidate:
            external = candidate.convert("RGBA")
    except (OSError, ValueError) as error:
        raise GltfLoadError(f"No se pudo abrir el atlas externo: {atlas}") from error
    declared = read_texture_image(loaded, binding.image_index)
    if external.size != declared.size or _rgba_digest(external) != _rgba_digest(declared):
        raise GltfLoadError(
            f"El atlas externo no coincide con la imagen {binding.image_index} declarada por el material; no se asoció por nombre."
        )
    LOGGER.info("Atlas externo verificado contra imagen material %s (textura %s).", binding.image_index, binding.texture_index)
    return external


def _external_image(atlas: Path) -> Image.Image:
    try:
        with Image.open(atlas) as image:
            return image.convert("RGBA")
    except (OSError, ValueError) as error:
        raise GltfLoadError(f"No se pudo abrir el atlas externo: {atlas}") from error


def _export_external_crop(destination: Path, image: Image.Image, region) -> dict[str, Path]:  # type: ignore[no-untyped-def]
    destination.mkdir(parents=True, exist_ok=True)
    x, y, width, height = region.bounding_box
    pixels = np.asarray(image).copy()
    pixels[:, :, 3] = np.where(region.mask, pixels[:, :, 3], 0)
    output = destination / "baseColor.png"
    Image.fromarray(pixels[y : y + height, x : x + width], "RGBA").save(output)
    return {"baseColor": output}


def _rgba_digest(image: Image.Image) -> str:
    return hashlib.sha256(np.asarray(image.convert("RGBA")).tobytes()).hexdigest()


def _flip_v(uvs: np.ndarray) -> np.ndarray:
    """Convierte UV de un atlas externo cuya V fue exportada con origen superior."""
    flipped = np.asarray(uvs, dtype=np.float64).copy()
    flipped[:, 1] = 1.0 - flipped[:, 1]
    return flipped


def _groups(triangles: np.ndarray, group_by: GroupBy) -> list[np.ndarray]:
    return uv_island_triangle_groups(triangles) if group_by == "uv-island" else [np.arange(len(triangles), dtype=np.int64)]


def _element(loaded, primitive, binding, key, uvs, transformed, triangles, triangle_rows, region) -> AtlasElement:  # type: ignore[no-untyped-def]
    from atlas_splitter.domain import slugify, stable_element_id

    ref = primitive.reference
    node_name = primitive.node_path[-1] if primitive.node_path else f"node_{ref.node_index}"
    material = loaded.document.materials[ref.material_index] if ref.material_index is not None else None
    islands = [UvIsland(island_id=key, bounding_box=BoundingBox(x=region.bounding_box[0], y=region.bounding_box[1], width=region.bounding_box[2], height=region.bounding_box[3]), triangle_indices=[int(value) for value in triangle_rows])]
    return AtlasElement(
        element_id=stable_element_id(0, ref.node_index, ref.mesh_index, ref.primitive_index, key),
        original_name=node_name, slug=slugify(f"{node_name}-{key}"), scene_index=0, node_index=ref.node_index,
        node_path=list(primitive.node_path), mesh_index=ref.mesh_index, primitive_index=ref.primitive_index,
        material_index=ref.material_index, material_name=getattr(material, "name", None), texture_slot=binding.slot,
        image_index=binding.image_index if binding.image_index >= 0 else None,
        texture_index=binding.texture_index if binding.texture_index >= 0 else None,
        texcoord=binding.texcoord,
        original_uvs=uvs.tolist(), transformed_uvs=transformed.tolist(), triangle_indices=triangles.tolist(),
        pixel_polygons=[[list(point) for point in polygon] for polygon in region.pixel_polygons],
        bounding_box=BoundingBox(x=region.bounding_box[0], y=region.bounding_box[1], width=region.bounding_box[2], height=region.bounding_box[3]),
        uv_islands=islands, node_transform=primitive.node_transform.reshape(-1).tolist(),
    )


def _image_for_dimensions(loaded: LoadedGltf, image_index: int | None, atlas: Path | None) -> Image.Image:
    if atlas is not None:
        with Image.open(atlas) as image:
            return image.copy()
    if image_index is None:
        raise GltfLoadError("El elemento no declara imagen material.")
    return read_texture_image(loaded, image_index)
