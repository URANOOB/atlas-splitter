# ZIP y archivos

**Síntoma:** Permiso denegado al escribir resultados.
**Causa probable:** La carpeta de destino está abierta por otro programa o existe un ZIP bloqueado.
**Comprobación:** Verifica si tienes el Visor de Imágenes o el Explorador de Windows abierto dentro de la carpeta.
**Solución:** Cierra el Explorador o usa otra carpeta con `--output nueva_carpeta`.
**Comando de diagnóstico:** 
```text
atlas-splitter doctor
```
