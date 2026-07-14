# CPU, CUDA y MPS

**Síntoma:** El procesamiento semántico es extremadamente lento, o arroja error de memoria de video.
**Causa probable:** CUDA no instalado o VRAM insuficiente.
**Comprobación:** Ejecuta `nvidia-smi`.
**Solución:** Configura para usar CPU (más lento) o reduce el batch de procesamiento.
**Comando de diagnóstico:** 
```text
atlas-splitter doctor
```
