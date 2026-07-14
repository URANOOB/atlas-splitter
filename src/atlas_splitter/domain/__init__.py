"""Modelos de dominio estables, compartidos por los pipelines nuevos."""

from atlas_splitter.domain.element import (
    AtlasCapabilities,
    AtlasElement,
    BoundingBox,
    UvIsland,
    slugify,
    stable_element_id,
)
from atlas_splitter.domain.manifests import (
    SCHEMA_VERSION,
    AtlasAssociationRecord,
    ObjectGroup,
    ObjectManifest,
    ObjectTexturePart,
    SceneManifest,
    UvManifest,
    write_versioned_manifest,
)

__all__ = [
    "SCHEMA_VERSION",
    "AtlasCapabilities",
    "AtlasAssociationRecord",
    "AtlasElement",
    "BoundingBox",
    "ObjectGroup",
    "ObjectManifest",
    "ObjectTexturePart",
    "SceneManifest",
    "UvIsland",
    "UvManifest",
    "slugify",
    "stable_element_id",
    "write_versioned_manifest",
]
