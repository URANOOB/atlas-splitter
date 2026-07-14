# Windows portable

La release Lite para Windows se llama `AtlasSplitter-Lite.zip`. Descárgala desde Releases, extráela en una carpeta local y ejecuta `AtlasSplitter-Lite.exe` desde PowerShell o el Explorador.

```text
AtlasSplitter-Lite.exe --version
AtlasSplitter-Lite.exe doctor --format json
AtlasSplitter-Lite.exe split atlas.webp --output resultados
```

La edición Lite no incluye modelos de IA ni CUDA. No necesita descargar modelos para `split`, `preview`, `review`, `inspect` o la exportación del add-on. Ejecuta `doctor` para ver qué capacidades locales faltan.

No ejecutes el ZIP sin extraerlo. Conserva el ejecutable y sus archivos vecinos juntos; mover sólo el `.exe` rompe la distribución portátil.
