# Blender

Atlas Splitter proporciona un add-on oficial para importar las piezas segmentadas a Blender y reconstruir colecciones basándose en los metadatos generados.

## 1. Exportar el add-on
Genera el archivo `.zip` del add-on para instalarlo en Blender:
```text
atlas-splitter blender-addon export --output Descargas
```
Esto creará el archivo `atlas_splitter_blender.zip` en tu carpeta Descargas.

## 2. Instalarlo en Blender 4.x
1. Abre Blender 4.0 o superior.
2. Ve a `Edit > Preferences > Add-ons`.
3. Haz clic en `Install...` y selecciona el archivo `.zip`.

## 3. Activarlo
Busca "Atlas Splitter" en la lista de add-ons y marca la casilla para activarlo.

## 4. Encontrar el panel
En la Vista 3D (3D Viewport), presiona la tecla `N` para abrir el panel lateral. Busca la pestaña **Atlas Splitter**.

## 5. Cargar proyectos
En el panel, se te pedirá seleccionar un directorio o archivo manifiesto. Puedes cargar:
* `project.json`
* `objects_manifest.json`
* `manifest.json`

Selecciona el manifiesto principal generado en tu carpeta de resultados.

## 6. Crear colecciones
El add-on leerá el manifiesto y te permitirá crear colecciones en Blender correspondientes a los grupos. Selecciona las opciones deseadas en la interfaz del add-on.

## 7. Ejecutar reconstrucción
Haz clic en el botón de **Rebuild Scene**. El add-on aplicará los scripts de reconstrucción y generará los objetos y materiales en tu escena de Blender, asignando las imágenes extraídas a sus UVs correspondientes.

## 8. Recargar un proyecto
Si actualizas la segmentación, puedes presionar "Reload Project" en el panel lateral para refrescar los datos sin reiniciar Blender.

## 9. Desinstalar el add-on
Ve a `Edit > Preferences > Add-ons`, busca "Atlas Splitter", expande los detalles y presiona `Remove`.

## 10. Consultar errores en la consola de Blender
Si algo falla, ve a `Window > Toggle System Console` (en Windows) para ver los registros de error y diagnósticos detallados.
