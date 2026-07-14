"""Contratos CPU para el adaptador local de Draco."""

from pathlib import Path

import pytest

from atlas_splitter.exceptions import DracoDecoderUnavailableError
from atlas_splitter.geometry.draco_decoder import DracoDecoder, _node_process_path


def test_draco_reports_structured_unavailable_decoder(tmp_path: Path) -> None:
    decoder = DracoDecoder(project_root=tmp_path, node_executable=tmp_path / "node")
    with pytest.raises(DracoDecoderUnavailableError, match="draco_decoder_unavailable"):
        decoder._check_available()
    assert decoder.last_diagnostic is not None
    assert decoder.last_diagnostic.code == "draco_decoder_unavailable"


def test_converts_wsl_decoder_paths_for_windows_node() -> None:
    assert _node_process_path(Path("/mnt/g/atlas-splitter/Draco/gltf/draco_decoder.js"), Path("/mnt/c/node.exe")) == (
        "G:\\atlas-splitter\\Draco\\gltf\\draco_decoder.js"
    )
