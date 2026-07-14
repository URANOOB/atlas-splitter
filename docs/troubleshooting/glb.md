# GLB sin UV

**Síntoma:** Error "No TEXCOORD_0 found".
**Causa probable:** El modelo 3D exportado no tiene UVs, o las tiene en un canal personalizado distinto a `TEXCOORD_0`.
**Comprobación:** Inspecciona la estructura del archivo.
**Solución:** Re-exporta desde Blender asegurando marcar "UVs" en la configuración de exportación de glTF.
**Comando de diagnóstico:** 
```text
atlas-splitter inspect modelo.glb
```
