# Seguridad y privacidad

Atlas Splitter procesa imágenes, manifiestos y modelos en la máquina local. `split`, `extract`, `semantic`, reportes y documentación no descargan checkpoints. Las únicas operaciones de red previstas son instalaciones y descargas explícitas de modelos.

Los manifiestos no pueden usar rutas absolutas ni escapar con `..`. Las rutas de piezas se resuelven dentro del directorio de resultado; el ZIP no sigue enlaces simbólicos hacia fuera.

No subas atlas privados, GLB ni manifiestos a issues públicos. Para comunicar una vulnerabilidad, sigue el canal indicado en el archivo `SECURITY.md` del repositorio.
