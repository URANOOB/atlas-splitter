# PATH y Pipx

**Síntoma:** `atlas-splitter: command not found`.
**Causa probable:** `pipx` no añadió la ruta de los scripts al PATH del sistema.
**Comprobación:** Cierra y vuelve a abrir la terminal y escribe `atlas-splitter`.
**Solución:** Ejecuta `pipx ensurepath` y reinicia tu PC.
**Comando de diagnóstico:** 
```text
pipx list
```
