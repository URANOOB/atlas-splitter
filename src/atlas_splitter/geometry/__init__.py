"""Lectura local de escenas glTF para las etapas geométricas."""

from atlas_splitter.geometry.glb_loader import GltfDiagnostic, LoadedGltf, load_gltf
from atlas_splitter.geometry.primitive_decoder import decode_scene_primitives
from atlas_splitter.geometry.texture_resolver import material_texture_bindings, read_texture_image
from atlas_splitter.geometry.uv_islands import uv_island_triangle_groups
from atlas_splitter.geometry.uv_rasterizer import rasterize_uv_triangles, uv_to_pixel_coordinates

__all__ = [
    "GltfDiagnostic",
    "LoadedGltf",
    "decode_scene_primitives",
    "load_gltf",
    "material_texture_bindings",
    "read_texture_image",
    "rasterize_uv_triangles",
    "uv_island_triangle_groups",
    "uv_to_pixel_coordinates",
]
