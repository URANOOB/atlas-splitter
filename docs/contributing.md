# Contribuir

Abre un issue con pasos para reproducir el problema, la versión y el sistema operativo. No adjuntes datos sensibles sin revisarlos.

Para código, crea una rama, añade pruebas sin GPU para el comportamiento nuevo y ejecuta `python -m pytest`, `python -m ruff check .` y `python -m mypy`.

Las contribuciones de documentación deben usar español claro, comandos existentes y enlaces locales válidos. Ejecuta `mkdocs build --strict`, `python scripts/generate_cli_docs.py --check` y `python scripts/validate_doc_examples.py`.

Consulta [Seguridad](security.md) para vulnerabilidades que no deban publicarse en un issue.
