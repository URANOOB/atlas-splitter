# Draco

**Síntoma:** Error "Draco compression not supported".
**Causa probable:** El GLB fue exportado con Draco compression habilitada.
**Comprobación:** Ver la configuración de exportación original del software 3D.
**Solución:** Re-exporta el archivo desmarcando Draco Compression, o usa la herramienta `gltf-pipeline` para descomprimirlo.
**Comando de diagnóstico:** 
```text
atlas-splitter inspect modelo.glb
```
