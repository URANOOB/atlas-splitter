# Seguridad y privacidad

Atlas Splitter procesa todos los archivos de manera **local**. Aunque priorizamos la privacidad, la herramienta no puede garantizar la inmunidad absoluta ante vectores de ataque en formatos complejos.

* **Procesamiento local:** Los comandos `split` y `extract` nunca acceden a la red.
* **Cuándo se usa Internet:** Únicamente al ejecutar `pipx install` y `models download`.
* **Modelos descargados:** Se guardan en el caché seguro de tu usuario local.
* **Manifiestos no confiables:** Si recibes un `.json` o un `.glb` de terceros, inspecciónalo. Aunque el parser valida esquemas, archivos creados con intenciones maliciosas podrían intentar desbordamientos de memoria en bibliotecas subyacentes.
* **Rutas confinadas:** Atlas Splitter busca prevenir escrituras fuera del directorio `--output`.
* **Archivos recibidos de terceros:** Úsalos bajo tu propia responsabilidad.
* **Reporte HTML:** Es estático y autocontenido. No ejecuta código de rastreo.

Para reportar vulnerabilidades, contáctanos a través del correo listado en el repositorio original.
