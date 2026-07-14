"""Pruebas CPU de rasterización UV e islas, incluidas coordenadas fuera del atlas."""

import numpy as np

from atlas_splitter.geometry.uv_islands import uv_island_triangle_groups
from atlas_splitter.geometry.uv_rasterizer import rasterize_uv_triangles, uv_to_pixel_coordinates


def test_v_axis_is_inverted_from_gltf_to_image_pixels() -> None:
    pixels = uv_to_pixel_coordinates(
        np.array([[0.0, 0.0], [0.0, 1.0]]), 9, 7, "CLAMP_TO_EDGE", "CLAMP_TO_EDGE"
    )
    assert pixels.tolist() == [[0, 6], [0, 0]]


def test_triangle_rasterization_is_not_its_bounding_box() -> None:
    region = rasterize_uv_triangles(
        np.array([[0.0, 0.0], [1.0, 0.0], [0.0, 1.0]]), np.array([[0, 1, 2]]), 11, 11
    )
    assert region.bounding_box == (0, 0, 11, 11)
    assert region.mask.sum() < 11 * 11
    assert not region.mask[0, 10]


def test_repeat_mirror_and_clamp_are_applied_before_pixel_conversion() -> None:
    uvs = np.array([[1.25, -0.25]])
    assert uv_to_pixel_coordinates(uvs, 5, 5, "REPEAT", "REPEAT").tolist() == [[1, 1]]
    assert uv_to_pixel_coordinates(uvs, 5, 5, "MIRRORED_REPEAT", "MIRRORED_REPEAT").tolist() == [[3, 3]]
    assert uv_to_pixel_coordinates(uvs, 5, 5, "CLAMP_TO_EDGE", "CLAMP_TO_EDGE").tolist() == [[4, 4]]


def test_keeps_disconnected_uv_islands_separate() -> None:
    triangles = np.array([[0, 1, 2], [2, 1, 3], [4, 5, 6]])
    assert [group.tolist() for group in uv_island_triangle_groups(triangles)] == [[0, 1], [2]]


def test_triangles_touching_only_at_a_vertex_are_different_islands() -> None:
    triangles = np.array([[0, 1, 2], [2, 3, 4]])
    assert [group.tolist() for group in uv_island_triangle_groups(triangles)] == [[0], [1]]


def test_duplicate_uv_coordinates_with_different_indices_share_an_island() -> None:
    triangles = np.array([[0, 1, 2], [3, 4, 5]])
    uvs = np.array([[0, 0], [1, 0], [0, 1], [1, 0], [0, 0], [1, 1]], dtype=float)
    assert [group.tolist() for group in uv_island_triangle_groups(triangles, uvs)] == [[0, 1]]


def test_uv_island_coordinates_support_repeat_ranges() -> None:
    triangles = np.array([[0, 1, 2], [3, 4, 5]])
    uvs = np.array([[1, 0], [2, 0], [1, 1], [2, 0], [1, 0], [2, 1]], dtype=float)
    assert [group.tolist() for group in uv_island_triangle_groups(triangles, uvs)] == [[0, 1]]
