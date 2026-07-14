# Modelos

**Síntoma:** Error "Model not found".
**Causa probable:** Intentar usar `semantic` sin descargar el modelo.
**Comprobación:** Verifica si el modelo está listado como descargado.
**Solución:** Ejecuta `atlas-splitter models download qwen3-vl-2b`.
**Comando de diagnóstico:** 
```text
atlas-splitter models list
```
