# Solución de problemas

Ejecuta `atlas-splitter doctor` primero. El informe separa requisitos listos, opcionales y los que requieren atención.

Si falta UV, vuelve a exportar el modelo incluyendo `TEXCOORD_0` o selecciona el UV set correcto. Si no tienes geometría, usa el flujo 2D: sus recortes son visuales y no recuperan capas originales ni mallas.

Los modelos SAM 2 y Qwen3-VL se descargan únicamente mediante sus comandos explícitos de gestión de modelos; no durante un procesamiento normal.
