# Códigos de error

Los errores de dominio muestran un código, una causa probable y una solución. Los códigos no sustituyen el texto completo del mensaje.

| Código | Significado | Acción inicial |
| --- | --- | --- |
| `AS-CORE-001` | Contrato de entrada no válido | Revisa ruta y opciones. |
| `AS-CLI-004` | Opción o ruta de la CLI inválida | Ejecuta el comando con `--help`. |
| `AS-MODEL-003` | Modelo o dispositivo no disponible | Usa CPU o instala el componente solicitado. |
| `AS-GLB-002` | No se pudo cargar GLB/glTF o asociar atlas | Revisa archivos, texturas y bindings. |
| `AS-UV-001` | La primitiva no tiene UV triangulables compatibles | Exporta UV válidas o prueba otro `--uv-set`. |
| `AS-REVIEW-001` | `review.json` duplica, pierde o inventa piezas | Incluye cada ID exactamente una vez. |

Los códigos de salida del proceso son `0` para éxito, `1` para un error de ejecución y `2` para sintaxis de Click/Typer. Ejecuta `atlas-splitter doctor` antes de instalar extras.
