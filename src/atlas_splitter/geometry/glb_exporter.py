"""Exportación determinista de resultados guiados por la geometría de un glTF."""

# ruff: noqa: E501
from __future__ import annotations

import hashlib
import logging
from dataclasses import replace
from pathlib import Path
from typing import Any, Literal, cast

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
    slugify,
    stable_element_id,
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
_MAX_UV_ISLANDS_PER_PRIMITIVE = 512


def export_glb(
    loaded: LoadedGltf,
    destination: Path,
    *,
    atlas: Path | None = None,
    texture_index: int | None = None,
    image_index: int | None = None,
    texture_slot: str = "baseColor",
    group_by: GroupBy = "uv-island",
    allow_unbound_atlas: bool = False,
    node_indices: set[int] | None = None,
    flip_v: bool = False,
    uv_set: int | None = None,
    force_external_atlas: bool = False,
    uv_tolerance: float = 1e-6,
) -> UvManifest:
    """Escribe máscaras UV, recortes, manifiestos y el script de reconstrucción."""
    primitives = decode_scene_primitives(loaded)
    destination = destination.resolve()
    elements: list[AtlasElement] = []
    selected_atlas = atlas.resolve() if atlas is not None else None
    for primitive in primitives:
        if node_indices is not None and primitive.reference.node_index not in node_indices:
            continue
        binding = _primary_binding(loaded, primitive.reference.material_index, texture_slot, texture_index, image_index)
        manual_atlas = selected_atlas is not None and (
            force_external_atlas or (binding is None and allow_unbound_atlas)
        )
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
        if uv_set is not None:
            binding = replace(binding, texcoord=uv_set)
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
        groups = _groups(primitive.triangle_indices, group_by, uvs, uv_tolerance)
        if group_by == "uv-island" and len(groups) > _MAX_UV_ISLANDS_PER_PRIMITIVE:
            raise GltfLoadError(
                f"La primitiva {primitive.reference} contiene {len(groups)} islas UV; "
                f"el límite seguro es {_MAX_UV_ISLANDS_PER_PRIMITIVE}. "
                "Use --group-by primitive, mesh o node para evitar un uso excesivo de memoria."
            )
        source_image = override or read_texture_image(loaded, binding.image_index)
        for group_index, triangle_rows in enumerate(groups):
            triangles = primitive.triangle_indices[triangle_rows]
            transformed = _flip_v(binding.transform.apply(uvs)) if flip_v else binding.transform.apply(uvs)
            region = rasterize_uv_triangles(
                transformed, triangles, source_image.width, source_image.height, binding.wrap_s, binding.wrap_t
            )
            key = f"{group_by}-{group_index}"
            element = _element(
                loaded, primitive, binding, key, uvs, transformed, triangles, triangle_rows, region, group_by
            )
            element_dir = destination / "materials" / element.element_id
            material_index = primitive.reference.material_index
            exported = (
                _export_external_crop(element_dir, override, region)
                if manual_atlas and override is not None
                else export_material_crops(
                    element_dir,
                    loaded,
                    material_texture_bindings(loaded, material_index) if material_index is not None else [],
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
    if group_by in {"node", "mesh"}:
        elements = _coalesce_elements(loaded, destination, elements, selected_atlas, group_by)
    if not elements:
        raise GltfLoadError("No se exportó ninguna región: no hay asociaciones material/textura/UV compatibles.")
    first_image = _image_for_dimensions(loaded, elements[0].image_index, selected_atlas)
    manifest = UvManifest(
        source_file=str(loaded.source_path),
        capabilities=AtlasCapabilities.geometry_guided(),
        atlas_width=first_image.width,
        atlas_height=first_image.height,
        elements=elements,
        warnings=[
            "Los recortes preservan la máscara UV; revise materiales con UV repetidas o transformaciones complejas.",
            "El atlas se asoció manualmente porque el GLB no declara materiales." if allow_unbound_atlas else "",
            "La coordenada V se invirtió por la convención confirmada del atlas externo." if flip_v else "",
        ],
    )
    write_versioned_manifest(destination / "uv_manifest.json", manifest)
    write_versioned_manifest(
        destination / "scene_manifest.json",
        SceneManifest(
            source_file=str(loaded.source_path), capabilities=AtlasCapabilities.geometry_guided(), elements=elements
        ),
    )
    write_rebuild_script(
        destination / "blender" / "rebuild_scene.py", loaded.source_path, destination / "uv_manifest.json"
    )
    LOGGER.info("Exportadas %s regiones UV en %s", len(elements), destination)
    return manifest


def _coalesce_elements(
    loaded: LoadedGltf,
    destination: Path,
    elements: list[AtlasElement],
    atlas: Path | None,
    group_by: Literal["node", "mesh"],
) -> list[AtlasElement]:
    """Combina las máscaras de primitivas de un nodo o una malla de forma estable.

    Un elemento UV sólo puede describir un material y una imagen. En vez de elegir
    uno arbitrariamente, los grupos que mezclan materiales se rechazan con una
    instrucción clara para usar ``primitive``/``uv-island`` o seleccionar un slot.
    """
    grouped: dict[int, list[AtlasElement]] = {}
    for element in elements:
        key = element.node_index if group_by == "node" else element.mesh_index
        grouped.setdefault(key, []).append(element)
    result: list[AtlasElement] = []
    for key, members in sorted(grouped.items()):
        if len(members) == 1:
            result.append(members[0].model_copy(update={"source_primitives": [_primitive_record(members[0])]}))
            continue
        first = members[0]
        material_signature = {
            (item.material_index, item.image_index, item.texture_index, item.texcoord) for item in members
        }
        if len(material_signature) != 1:
            # Un elemento UV representa un único material. Mezclarlos produciría
            # una máscara aparentemente válida pero recortes y mapas auxiliares
            # falsos. Conservamos por tanto cada primitiva/material dentro del
            # mismo grupo lógico (node o mesh), con toda su procedencia.
            for item in members:
                result.append(
                    item.model_copy(
                        update={
                            "source_primitives": [_primitive_record(item)],
                            "warnings": [
                                *item.warnings,
                                f"El grupo {group_by}={key} usa varios materiales; esta región se conserva "
                                "por material para no perder mapas auxiliares.",
                            ],
                        }
                    )
                )
            continue
        mask, box = _combined_mask(destination, members)
        image = _external_image(atlas) if atlas is not None else read_texture_image(loaded, first.image_index or 0)
        x, y, width, height = box
        pixels = np.asarray(image.convert("RGBA")).copy()
        pixels[:, :, 3] = np.where(mask, pixels[:, :, 3], 0)
        element_id = stable_element_id(0, first.node_index, first.mesh_index, -1, f"{group_by}-{key}")
        element_dir = destination / "materials" / element_id
        element_dir.mkdir(parents=True, exist_ok=True)
        crop = element_dir / "baseColor.png"
        Image.fromarray(pixels[y : y + height, x : x + width], "RGBA").save(crop)
        mask_path = destination / "masks" / f"{element_id}.png"
        Image.fromarray((mask * 255).astype(np.uint8), "L").save(mask_path)
        files = dict(first.exported_files)
        files["baseColor"] = str(crop.relative_to(destination).as_posix())
        files["uv_mask"] = str(mask_path.relative_to(destination).as_posix())
        source_primitives = [_primitive_record(item) for item in members]
        original_uvs = [uv for item in members for uv in item.original_uvs]
        transformed_uvs = [uv for item in members for uv in item.transformed_uvs]
        triangles = [triangle for item in members for triangle in item.triangle_indices]
        result.append(
            first.model_copy(
                update={
                    "element_id": element_id,
                    "slug": slugify(f"{first.original_name}-{group_by}-{key}"),
                    "original_uvs": original_uvs,
                    "transformed_uvs": transformed_uvs,
                    "triangle_indices": triangles,
                    "bounding_box": BoundingBox(x=x, y=y, width=width, height=height),
                    "uv_islands": [island for item in members for island in item.uv_islands],
                    "group_by": group_by,
                    "exported_files": files,
                    "source_primitives": source_primitives,
                    "warnings": [
                        *first.warnings,
                        f"Máscara combinada de {len(members)} primitivas por {group_by}; los archivos auxiliares "
                        "de materiales secundarios conservan la primera primitiva.",
                    ],
                }
            )
        )
    return result


def _primitive_record(element: AtlasElement) -> dict[str, object]:
    return {
        "node_index": element.node_index,
        "mesh_index": element.mesh_index,
        "primitive_index": element.primitive_index,
        "material_index": element.material_index,
        "node_transform": element.node_transform,
    }


def _combined_mask(destination: Path, members: list[AtlasElement]) -> tuple[np.ndarray, tuple[int, int, int, int]]:
    masks: list[np.ndarray] = []
    for member in members:
        path = destination / member.exported_files["uv_mask"]
        with Image.open(path) as source:
            masks.append(np.asarray(source.convert("L"), dtype=np.uint8) > 0)
    mask = np.logical_or.reduce(masks)
    rows, columns = np.nonzero(mask)
    if not len(rows):
        raise GltfLoadError("No se pudo combinar un grupo UV sin píxeles activos.")
    x, y = int(columns.min()), int(rows.min())
    return mask, (x, y, int(columns.max()) - x + 1, int(rows.max()) - y + 1)


def _primary_binding(
    loaded: LoadedGltf,
    material_index: int | None,
    slot: str,
    texture_index: int | None,
    image_index: int | None,
) -> TextureBinding | None:
    if material_index is None:
        return None
    bindings = [item for item in material_texture_bindings(loaded, material_index) if item.slot == slot]
    if texture_index is not None:
        bindings = [item for item in bindings if item.texture_index == texture_index]
    if image_index is not None:
        bindings = [item for item in bindings if item.image_index == image_index]
    if len(bindings) > 1:
        raise GltfLoadError(
            f"El material {material_index} tiene asociaciones ambiguas para {slot}; use --texture-index."
        )
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
    LOGGER.info(
        "Atlas externo verificado contra imagen material %s (textura %s).", binding.image_index, binding.texture_index
    )
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


def _groups(triangles: np.ndarray, group_by: GroupBy, uvs: np.ndarray, uv_tolerance: float) -> list[np.ndarray]:
    return (
        uv_island_triangle_groups(triangles, uvs, tolerance=uv_tolerance)
        if group_by == "uv-island"
        else [np.arange(len(triangles), dtype=np.int64)]
    )


def _element(
    loaded: Any,
    primitive: Any,
    binding: Any,
    key: str,
    uvs: np.ndarray,
    transformed: np.ndarray,
    triangles: np.ndarray,
    triangle_rows: np.ndarray,
    region: Any,
    group_by: GroupBy,
) -> AtlasElement:
    from atlas_splitter.domain import slugify, stable_element_id

    ref = primitive.reference
    node_name = primitive.node_path[-1] if primitive.node_path else f"node_{ref.node_index}"
    material = loaded.document.materials[ref.material_index] if ref.material_index is not None else None
    islands = [
        UvIsland(
            island_id=key,
            bounding_box=BoundingBox(
                x=region.bounding_box[0],
                y=region.bounding_box[1],
                width=region.bounding_box[2],
                height=region.bounding_box[3],
            ),
            triangle_indices=[int(value) for value in triangle_rows],
        )
    ]
    return AtlasElement(
        element_id=stable_element_id(0, ref.node_index, ref.mesh_index, ref.primitive_index, key),
        original_name=node_name,
        slug=slugify(f"{node_name}-{key}"),
        scene_index=0,
        node_index=ref.node_index,
        node_path=list(primitive.node_path),
        mesh_index=ref.mesh_index,
        primitive_index=ref.primitive_index,
        material_index=ref.material_index,
        material_name=getattr(material, "name", None),
        texture_slot=binding.slot,
        image_index=binding.image_index if binding.image_index >= 0 else None,
        texture_index=binding.texture_index if binding.texture_index >= 0 else None,
        texcoord=binding.texcoord,
        original_uvs=uvs.tolist(),
        transformed_uvs=transformed.tolist(),
        triangle_indices=triangles.tolist(),
        pixel_polygons=[[list(point) for point in polygon] for polygon in region.pixel_polygons],
        bounding_box=BoundingBox(
            x=region.bounding_box[0],
            y=region.bounding_box[1],
            width=region.bounding_box[2],
            height=region.bounding_box[3],
        ),
        uv_islands=islands,
        group_by=group_by,
        node_transform=primitive.node_transform.reshape(-1).tolist(),
        source_primitives=[
            {
                "node_index": ref.node_index,
                "mesh_index": ref.mesh_index,
                "primitive_index": ref.primitive_index,
                "material_index": ref.material_index,
                "node_transform": primitive.node_transform.reshape(-1).tolist(),
            }
        ],
    )


def _image_for_dimensions(loaded: LoadedGltf, image_index: int | None, atlas: Path | None) -> Image.Image:
    if atlas is not None:
        with Image.open(atlas) as image:
            return image.copy()
    if image_index is None:
        raise GltfLoadError("El elemento no declara imagen material.")
    return read_texture_image(loaded, image_index)
