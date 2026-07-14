# Portabilidad de proyectos

Al trabajar con los resultados generados, es crucial mantener la integridad de los archivos.

## Qué archivos deben moverse juntos
Nunca muevas los archivos JSON, HTML o las subcarpetas (`objects`, `grouped`) de forma individual. Mueve siempre la **carpeta raíz** completa del proyecto (ej. la carpeta generada por el comando, que incluye `manifest.json` en su primer nivel).

## Por qué no editar rutas
Los archivos manifiesto y `project.json` referencian imágenes mediante rutas relativas. Si editas manualmente una ruta, la vista previa y los scripts de Blender se romperán.

## Ubicación de `source/`
Dependiendo del comando, puede haber una carpeta `source/` que contenga una copia o enlace al atlas original. Esto permite que el proyecto sea autocontenido.

## Qué hacer si el atlas fuente no existe
Si borras la imagen original usada como entrada, el proyecto seguirá funcionando para ver las piezas extraídas (ya que están en la subcarpeta `objects/`), pero no podrás volver a generar nuevos cortes a partir de esa raíz a menos que proporciones el archivo nuevamente. Compatibilidad total garantizada siempre y cuando el manifiesto y objects estén intactos.

## Regenerar reporte
Si se daña el reporte HTML, puedes regenerarlo ejecutando la vista previa:
```text
atlas-splitter preview resultados/atlas
```

## Archivar el resultado
La mejor forma de enviar los resultados a otra persona es comprimir la carpeta entera en un `.zip`. Todos los archivos y rutas relativas se mantendrán intactos.
