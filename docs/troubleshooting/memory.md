# Memoria

**Síntoma:** El programa finaliza sin error pero la terminal se cierra repentinamente o dice `Killed`.
**Causa probable:** Out of Memory (OOM). La imagen es demasiado masiva.
**Comprobación:** Observa el Monitor de recursos del sistema mientras procesas.
**Solución:** Divide la imagen previamente en cuartos antes de procesar, o compra más memoria RAM.
**Comando de diagnóstico:** 
```text
atlas-splitter doctor
```
