# Solución de problemas

Ejecuta `atlas-splitter doctor` primero. `LISTO` significa que la capacidad está disponible; `OPCIONAL`, que el flujo puede funcionar sin ella; y `REQUIERE ATENCIÓN`, que falta un requisito base o permisos de escritura.

## Errores con código

- `AS-GLB-002`: el GLB/glTF o el enlace atlas-material no es compatible. Revisa buffers y rutas locales; ante ambigüedad usa `--bindings`.
- `AS-UV-001`: falta el UV solicitado o la geometría no es triangulable. Prueba otro `--uv-set` o exporta el modelo con UV.
- `AS-MODEL-003`: el modelo local o CUDA no están disponibles. Usa `--device auto`/`cpu` o instala el modelo explícitamente.

Usa `atlas-splitter --debug <subcomando>` para mostrar un traceback completo.

## Problemas frecuentes

**No se asocia un atlas externo.** Atlas Splitter no adivina asociaciones. Comprueba nombres y hashes o crea un `bindings.yaml` con atlas, nodos, `uv_set` y `flip_v`.

**La salida ya existe.** Las carpetas no se sobrescriben. Elige otro `--output` o mueve la salida validada antes de repetir.

**No aparece un modelo en Blender.** Mantén toda la carpeta de resultados junta y abre `blender/rebuild_scene.py` desde Blender. Revisa el manifiesto antes de mover archivos.

**Falta SAM 2 o Qwen3-VL.** `run`, `glb` y `semantic-3d` no descargan modelos. Comprueba `models list` y `semantic-models list`; descarga sólo mediante el subcomando explícito que autorices.
