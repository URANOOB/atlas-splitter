# Configuración

`device: auto` es el valor predeterminado. Elige CUDA, luego MPS y finalmente CPU. Una selección explícita de `cuda` o `mps` falla con una explicación si no está disponible.

`output.create_zip: true` crea un ZIP por atlas. `--zip archivo.zip` define otra ruta y `--no-zip` lo desactiva.
