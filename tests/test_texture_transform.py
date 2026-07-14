"""Pruebas CPU para la transformación UV definida por KHR_texture_transform."""

import math

import numpy as np

from atlas_splitter.geometry.texture_resolver import TextureTransform


def test_texture_transform_scales_rotates_and_offsets_in_specification_order() -> None:
    transform = TextureTransform(offset=(0.25, 0.5), scale=(2.0, 3.0), rotation=math.pi / 2)
    transformed = transform.apply(np.array([[1.0, 0.0], [0.0, 1.0]]))
    assert np.allclose(transformed, [[0.25, 2.5], [-2.75, 0.5]])
