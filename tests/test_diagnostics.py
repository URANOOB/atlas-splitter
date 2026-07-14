from atlas_splitter.diagnostics import DiagnosticCheck, collect_diagnostics, has_critical_failures


def test_diagnostics_include_required_categories(tmp_path) -> None:
    checks = collect_diagnostics(tmp_path, module_version=lambda _: None)
    names = {check.name for check in checks}
    assert {"Python", "Sistema operativo", "PyTorch", "CUDA", "ZIP"} <= names


def test_critical_failure_detection() -> None:
    assert has_critical_failures([DiagnosticCheck("CUDA", False, "no", critical=True)])
    assert not has_critical_failures([DiagnosticCheck("Pillow", False, "no")])


def test_diagnostic_statuses_are_user_facing() -> None:
    assert DiagnosticCheck("Pillow", True, "ok").status == "LISTO"
    assert DiagnosticCheck("Blender", False, "missing").status == "OPCIONAL"
    assert DiagnosticCheck("Python", False, "old", critical=True).status == "REQUIERE ATENCIÓN"
