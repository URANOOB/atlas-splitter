import os

docs_dir = "docs"

pages = {
    "index.md": """# Atlas Splitter

Atlas Splitter es una herramienta CLI para separar regiones visuales de atlas de texturas 2D y, de forma opcional, recuperar asociaciones 3D usando archivos GLB/glTF.

## ¿Qué problema resuelve?

Cuando tienes un atlas de texturas, a menudo necesitas separar las piezas individuales para usarlas por separado. Hacer esto a mano en un editor de imágenes es lento y propenso a errores, especialmente si las piezas tienen transparencias complejas o necesitas mantener su relación con un modelo 3D. Atlas Splitter automatiza este proceso de forma local.

![Captura principal](https://raw.githubusercontent.com/URANOOB/atlas-splitter/main/docs/assets/screenshot.webp)

## Selector de flujo

| Tengo | Debo usar | Resultado |
| --- | --- | --- |
| Sólo un atlas | `split` | Piezas visuales aproximadas |
| Atlas y GLB/glTF | `extract` | Regiones basadas en UV |
| Atlas y deseo nombres | `semantic` | Grupos inferidos |
| Resultado que deseo corregir | `review` | Revisión manual |
| Proyecto para Blender | `blender-addon` | Add-on y scripts de reconstrucción |

## Instalación mínima

```text
pipx install atlas-splitter
```
Si deseas características avanzadas como IA o geometría 3D:
```text
atlas-splitter setup all
```

## Primer comando

Para separar un atlas visualmente:
```text
atlas-splitter split atlas.webp --output resultados
```

## Procesamiento local y privacidad

Atlas Splitter procesa todas las imágenes y modelos **localmente** en tu máquina. Tus datos no se envían a la nube para su procesamiento. Las únicas conexiones a Internet se realizan durante la instalación inicial para descargar modelos de IA públicos (si se solicitan).

## Plataformas compatibles

- Windows 10/11
- macOS 13+ (Apple Silicon y procesadores Intel)
- Linux (Ubuntu 22.04+)

## Limitaciones

- La segmentación visual asume que el fondo es transparente.
- Los modelos de IA no siempre son 100% precisos en la clasificación semántica.
- Los atlas muy grandes pueden consumir mucha RAM.

[Inicio rápido](getting-started/quickstart.md) | [Windows Portable](getting-started/windows-portable.md) | [Blender](guides/blender.md)
""",
    "getting-started/installation.md": """# Instalación

Atlas Splitter se instala mejor usando `pipx` para mantener sus dependencias aisladas.

## Requisitos

* **Python:** 3.11 a 3.13.
* **Sistemas operativos:** Windows 10+, macOS 13+, Linux (Ubuntu 22.04+).
* **Espacio en disco:** 500 MB mínimos. Si usas IA, 5-10 GB adicionales para modelos.
* **GPU (Opcional):** Tarjeta gráfica compatible con CUDA (NVIDIA) o MPS (Apple Silicon) para acelerar operaciones de IA.
* **Internet:** Sólo para la instalación y descarga de modelos (opcional).

## Pipx

Si no tienes `pipx`, instálalo primero.

### Windows PowerShell

Abre PowerShell y ejecuta:
```powershell
pip install pipx
pipx ensurepath
```
Cierra y vuelve a abrir PowerShell, luego:
```text
pipx install atlas-splitter
```

### Windows CMD

Ejecuta en Símbolo del sistema:
```cmd
pip install pipx
python -m pipx ensurepath
```
Reinicia la consola e instala:
```text
pipx install atlas-splitter
```

### Linux

```bash
sudo apt update
sudo apt install pipx
pipx ensurepath
```
Reinicia la terminal e instala:
```text
pipx install atlas-splitter
```

### macOS

```bash
brew install pipx
pipx ensurepath
```
Reinicia la terminal e instala:
```text
pipx install atlas-splitter
```

## Wheel

Si tienes un archivo release descargado, puedes instalarlo directamente:
```text
pipx install atlas_splitter-0.2.0-py3-none-any.whl
```

## Desarrollo

Para contribuir o instalar desde el código fuente:
```text
git clone https://github.com/URANOOB/atlas-splitter.git
cd atlas-splitter
python -m venv .venv
# Activar entorno (Windows: .venv\\Scripts\\activate | Linux/macOS: source .venv/bin/activate)
pip install -e ".[dev,geometry,docs]"
```

## Componentes opcionales

Atlas Splitter tiene características adicionales que requieren más dependencias. Puedes instalarlas después del comando principal:

Instala soporte para geometría 3D y GLB:
```text
atlas-splitter setup geometry
```

Instala soporte para segmentación semántica e IA (PyTorch, Transformers):
```text
atlas-splitter setup ai
```

Instala todo:
```text
atlas-splitter setup all
```

## Actualización y eliminación

Para actualizar:
```text
pipx upgrade atlas-splitter
```

Para desinstalar:
```text
pipx uninstall atlas-splitter
```
*Nota: La desinstalación no elimina los modelos de IA descargados en caché.*

## Verificación

Asegúrate de que todo está correcto:
```text
atlas-splitter --version
atlas-splitter doctor
```
""",
    "getting-started/quickstart.md": """# Inicio rápido

Este flujo te permite probar el programa en minutos usando datos de ejemplo sin necesidad de GPU ni modelos de IA.

## Flujo: Instalar → Doctor → Procesar → Reporte

1. **Verifica tu entorno**
   Asegúrate de que la instalación es correcta ejecutando:
   ```text
   atlas-splitter doctor
   ```

2. **Procesa un ejemplo**
   Usa una imagen de ejemplo (incluida si clonaste el repo, o descarga cualquier textura con transparencia):
   ```text
   atlas-splitter split examples/atlas-only/atlas.webp --output resultados
   ```
   Si no tienes la imagen de ejemplo, reemplaza la ruta por cualquier imagen PNG o WebP tuya.

3. **Revisa el resultado visualmente**
   El programa genera un reporte interactivo en HTML. Para abrirlo:
   ```text
   atlas-splitter preview resultados/atlas
   ```

## Árbol esperado

Tras ejecutar `split`, el directorio `resultados/atlas` tendrá esta estructura:

```text
resultados/
└── atlas/
    ├── report/
    │   └── index.html       # Reporte visual para inspección
    ├── manifest.json        # Registro de la operación
    └── objects/
        ├── obj_0000.png     # Primera pieza
        ├── obj_0001.png     # Segunda pieza
        └── ...
```
""",
    "getting-started/first-split.md": """# Primer atlas

Aprenderás a dividir una imagen 2D basada puramente en el espacio vacío (transparencia).

1. Ten a mano una imagen `textura.png` con canal alfa.
2. Ejecuta el comando:
   ```text
   atlas-splitter split textura.png --output mi_textura
   ```
3. Explora la carpeta generada. Encontrarás múltiples imágenes más pequeñas correspondientes a cada "isla" de píxeles descubierta.

Para más detalles, lee la guía de [Segmentación visual](../guides/visual-segmentation.md).
""",
    "getting-started/first-glb-extraction.md": """# Primer GLB

Si además de la imagen tienes un modelo 3D GLB/glTF que usa ese atlas, puedes extraer las texturas guiándote por la geometría real.

1. Asegúrate de haber instalado los extras de geometría:
   ```text
   atlas-splitter setup geometry
   ```
2. Ejecuta la extracción vinculando el modelo y la imagen:
   ```text
   atlas-splitter extract modelo.glb --atlas textura.png --output resultado_glb
   ```
3. El resultado no solo incluirá las piezas de textura, sino manifiestos que mapean cada imagen extraída a la malla original y a sus coordenadas UV.

Lee la guía de [Extracción GLB y UV](../guides/glb-uv-extraction.md) para más opciones.
""",
    "getting-started/windows-portable.md": """# Windows Portable

Para entornos sin conexión o donde no tienes permisos para instalar Python globalmente, puedes usar la versión portable.

1. Descarga el archivo `atlas-splitter-portable-win64.zip` desde la sección de Releases.
2. Descomprímelo en un directorio de tu elección (ej. `C:\\AtlasSplitter`).
3. Abre un símbolo del sistema en esa carpeta y ejecuta:
   ```cmd
   atlas-splitter.exe --help
   ```

Todos los comandos y guías documentadas aquí son idénticos; simplemente usa el archivo `.exe` en lugar del comando de pipx.
""",
    "guides/visual-segmentation.md": """# Segmentación visual

La segmentación visual procesa una imagen sin ninguna información 3D extra. Su propósito es recortar formas independientes.

## Qué analiza
Busca "islas" de píxeles no transparentes. Todo lo que esté conectado por píxeles visibles se considera una sola pieza.

* **Transparencia:** Es el delimitador principal. Atlas Splitter detecta el canal alfa y divide donde el alfa es 0.
* **Fondos:** Si tu imagen no tiene transparencia, la herramienta asume que es una sola pieza sólida. En esos casos, fallará en dividirla a menos que uses una herramienta externa primero para quitar el fondo.
* **Regiones conectadas:** Píxeles diagonales se consideran conectados por defecto.
* **Máscaras y recorte:** Las piezas finales se recortan (`crop`) para eliminar el espacio vacío a su alrededor.
* **Padding:** Se añade un relleno transparente de seguridad alrededor del recorte.
* **Área mínima:** Si una pieza generada tiene menos de 4 píxeles cuadrados, se ignora como "ruido".
* **Deduplicación:** Las piezas idénticas a nivel de píxel se agrupan.
* **SAM 2:** Opcionalmente, se puede utilizar el modelo de IA SAM 2 para mejorar la separación de áreas donde la transparencia no es suficiente. Esto es experimental.

## Ejemplos

Comando principal:
```text
atlas-splitter split atlas.webp
```

Comando avanzado especificando área mínima de 10 píxeles:
```text
atlas-splitter split atlas.webp --min-area 10
```

## Errores comunes y situaciones donde fallará
1. **Piezas del mismo color unidas:** Si dos piezas se tocan aunque sea por 1 píxel no transparente, serán exportadas como una sola imagen.
2. **Fondos complejos:** Si la imagen tiene un fondo negro o blanco en lugar de alfa, no se podrá separar.
3. **Objetos superpuestos:** No puede reconstruir información que está oculta detrás de otra pieza.
4. **Detalles muy pequeños:** Si el área mínima es mayor que la pieza, ésta se descartará.
""",
    "guides/glb-uv-extraction.md": """# Extracción GLB y UV

Cuando tienes la geometría 3D, puedes hacer recortes precisos basados en los mapas UV en lugar de adivinar mediante píxeles transparentes.

## Conceptos clave
* **GLB/glTF:** Formatos de modelos 3D que contienen la malla.
* **Atlas:** Imagen grande que contiene las texturas de todos los objetos.
* **Coordenadas UV:** Sistema (`TEXCOORD_0`) que dice qué parte de la imagen 2D va en qué parte del modelo 3D.
* **Múltiples atlas / Atlas externos / Embebidos:** Un GLB puede tener la imagen dentro del archivo (embebido) o apuntar a un archivo externo.
* **Asociaciones ambiguas:** A veces varias mallas comparten UV. `extract` lo detecta.
* **flip-v:** A veces las coordenadas Y (o V) están invertidas.
* **Draco:** Compresión de geometría. Debes descomprimir tu GLB si usas compresión Draco, pues `atlas-splitter` requiere acceso a las UV en crudo.

## Comandos

Primero, inspecciona tu modelo para asegurarte de que contiene texturas válidas:
```text
atlas-splitter inspect modelo.glb
```

Luego, extrae las regiones basándote en la imagen y el archivo 3D:
```text
atlas-splitter extract modelo.glb --atlas atlas.webp --output resultados
```

*Nota: `extract` no modifica tu GLB original.*

## Salida real

En tu carpeta `resultados` verás:
```text
uv_manifest.json
objects_manifest.json
project.json
blender/rebuild_scene.py
```
Estos archivos mantienen la relación matemática entre las imágenes cortadas y la malla 3D.
""",
    "guides/semantic-grouping.md": """# Agrupación semántica

Puedes agrupar piezas visuales basándote en inteligencia artificial para inferir qué representan (por ejemplo, "pared", "suelo", "personaje").

## ¿Qué hace Qwen3-VL?
Es un modelo de lenguaje visual. Analiza la imagen recortada y devuelve un nombre que describe su contenido.
* **Tamaño aproximado:** Requiere descargar varios gigabytes de pesaje.
* **Requisitos:** Debes ejecutar `setup ai`.
* **Procesamiento local:** Ninguna imagen se envía a servidores externos. Qwen3-VL corre en tu máquina.

## CPU, CUDA y MPS
* **CPU:** Funciona, pero es lento.
* **CUDA:** Aceleración rápida si tienes una gráfica NVIDIA.
* **MPS:** Aceleración en procesadores de Apple (M1, M2, etc.).

## Confianza y Estados
La IA evalúa cada pieza y asigna:
* **Confianza:** Un número de 0.0 a 1.0.
* **Grupos aceptados:** Si la confianza es alta.
* **Grupos inciertos:** Si el modelo duda, se envían a revisión.
* **Grupos rechazados:** Se marcan como no asignados.
* **Errores de clasificación:** La IA puede equivocarse y llamar "pared" a una "mesa". Siempre puedes arreglarlo en la revisión manual.

## Comandos

Preparar el entorno y descargar:
```text
atlas-splitter setup ai
atlas-splitter models download qwen3-vl-2b
```

Agrupar semánticamente:
```text
atlas-splitter semantic atlas.webp --output resultados
```

## Salida generada

```text
semantic_manifest.json
review.json
grouped/
objects/
uncertain/
unassigned/
report/index.html
```
""",
    "guides/manual-review.md": """# Revisión manual

Cuando usas la agrupación semántica, o en cualquier momento que generes un archivo de revisión, puedes corregir manualmente los grupos o nombres.

## El archivo `review.json`

Almacena el estado pendiente de tus cambios.

```json
{
  "version": 1,
  "source": "semantic",
  "groups": [
    {
      "name": "walls",
      "piece_ids": ["E001", "E002"],
      "confidence": 0.91,
      "status": "accepted"
    }
  ],
  "unassigned_piece_ids": ["E003"]
}
```

## Cómo modificarlo

* **Renombrar:** Cambia el valor `"name"` a lo que desees.
* **Mover IDs:** Mueve un ID como `"E001"` a otra lista `piece_ids`.
* **Dejar sin asignar:** Mueve el ID a `unassigned_piece_ids`.
* **Evitar duplicados:** Un ID de pieza no puede existir en dos grupos simultáneamente.

## Aplicar revisión

Para previsualizar tu estado actual:
```text
atlas-splitter review resultados/atlas
```

Para aplicar los cambios y regenerar las carpetas de imágenes agrupadas:
```text
atlas-splitter apply-review resultados/atlas/review.json
```
*(Nota: `apply-review` es un comando avanzado para procesar manualmente los archivos de revisión. Los archivos originales en `objects/` siempre se conservan intactos).*
""",
    "guides/blender.md": """# Blender

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

*(Capturas de interfaz omitidas en esta representación textual, asume que la interfaz sigue los paneles estándar de Blender)*
""",
    "guides/moving-projects.md": """# Portabilidad de proyectos

Al trabajar con los resultados generados, es crucial mantener la integridad de los archivos.

## Qué archivos deben moverse juntos
Nunca muevas los archivos JSON, HTML o las subcarpetas (`objects`, `grouped`) de forma individual. Mueve siempre la **carpeta raíz** completa del proyecto (ej. la carpeta generada por el comando, que incluye `manifest.json` en su primer nivel).

## Por qué no editar rutas
Los archivos manifiesto y `project.json` referencian imágenes mediante rutas relativas. Si editas manualmente una ruta, la vista previa y los scripts de Blender se romperán.

## Ubicación de `source/`
Dependiendo del comando, puede haber una carpeta `source/` que contenga una copia o enlace al atlas original. Esto permite que el proyecto sea autocontenido.

## Qué hacer si el atlas fuente no existe
Si borras la imagen original usada como entrada, el proyecto seguirá funcionando para ver las piezas extraídas (ya que están en la subcarpeta `objects/`), pero no podrás volver a generar nuevos cortes a partir de esa raíz a menos que proporciones el archivo nuevamente.

## Regenerar reporte
Si se daña el reporte HTML, puedes regenerarlo ejecutando la vista previa:
```text
atlas-splitter preview resultados/atlas
```

## Archivar el resultado
La mejor forma de enviar los resultados a otra persona es comprimir la carpeta entera en un `.zip`. Todos los archivos y rutas relativas se mantendrán intactos.
""",
    "concepts/texture-atlas.md": """# Atlas de textura

Un atlas de texturas es una gran imagen que contiene muchas texturas más pequeñas.
En los videojuegos y motores gráficos, es mucho más rápido cargar un archivo grande (atlas) que miles de archivos pequeños, reduciendo el número de "draw calls".

El problema es que cuando los humanos quieren editar los modelos, un atlas es difícil de manipular. Atlas Splitter revierte este proceso, tomando el atlas grande y devolviéndote los archivos pequeños individuales.
""",
    "concepts/uv-coordinates.md": """# Coordenadas UV

En los gráficos 3D, una malla (mesh) es sólo forma. Para darle color, necesita saber qué parte de la imagen va en cada triángulo.

**U** y **V** son simplemente X e Y, pero en el espacio 2D de una textura. Representan coordenadas (generalmente de 0.0 a 1.0).

En archivos como GLB, esto suele guardarse en un atributo de geometría llamado `TEXCOORD_0`. Atlas Splitter usa esta información durante el proceso de `extract` para saber exactamente dónde recortar en lugar de adivinar mediante transparencia.
""",
    "concepts/visual-vs-geometry.md": """# Segmentación visual vs Geometría

La decisión de qué comando usar se basa puramente en la información que tienes.

**Segmentación Visual (`split`):**
Solo mira colores y transparencia.
Si dos partes del dibujo se tocan, las considera una sola pieza.
*Precisión:* Aproximada y ruidosa.

**Extracción por Geometría (`extract`):**
Lee las matemáticas del archivo 3D.
Incluso si dos partes del dibujo se tocan en el atlas, si el modelo 3D usa coordenadas separadas, las separará perfectamente.
*Precisión:* Exacta, dictada por los datos del modelo.
""",
    "concepts/semantic-grouping.md": """# Agrupación semántica

La semántica se refiere a darle "significado" a los píxeles.

Mientras que `split` dice "Aquí hay píxeles", `semantic` (apoyado en IA como Qwen3-VL) dice "Estos píxeles representan un ladrillo".

Es una capa adicional que puedes ejecutar después o durante la separación para catalogar automáticamente miles de texturas, reduciendo el trabajo manual.
""",
    "concepts/manifests.md": """# Manifiestos

Un manifiesto es simplemente un archivo de texto en formato JSON que lleva un inventario estricto.

En Atlas Splitter, los manifiestos no son un subproducto, **son la base de datos principal** del resultado. Contienen el ID de cada pieza, sus coordenadas, rotación, y nombre semántico. Son consumidos por el visor HTML y por el add-on de Blender.
""",
    "concepts/local-processing.md": """# Procesamiento local

Atlas Splitter está diseñado bajo la filosofía "Local-first".
Una vez que el entorno y los modelos (IA) están descargados, puedes procesar infinitos atlas desconectado de Internet.
Esto garantiza que tu arte, modelos 3D y texturas patentadas nunca abandonen tu computadora, manteniendo el 100% de la privacidad.
""",
    "concepts/limitations.md": """# Limitaciones vigentes

1. **Memoria RAM:** Procesar un atlas 8K puede consumir gigabytes de RAM debido a cómo las bibliotecas de imágenes cargan matrices sin comprimir.
2. **Modelos unidos por color:** Si no usas GLB y usas `split`, partes de textura que intencionadamente colisionan visualmente no se pueden separar.
3. **Falsos positivos de IA:** La clasificación semántica de texturas esotéricas (ej. texturas de un monstruo espacial alienígena) devolverá etiquetas extrañas, porque la IA fue entrenada principalmente con fotografías de la realidad.
4. **GLB Draco:** La compresión draco destruye la facilidad para leer arrays planos. Debes usar GLB estandarizados.
""",
    "reference/cli.md": """# Referencia CLI

Este archivo se genera dinámicamente y su edición manual está prohibida.
*(Este es un marcador; el script `generate_cli_docs.py` sobreescribirá este archivo)*
""",
    "reference/configuration.md": """# Configuración

Atlas Splitter permite ajustar su comportamiento mediante un archivo YAML.
Puedes usar:
```text
atlas-splitter config init
atlas-splitter config validate
atlas-splitter config show
```

## Modelos Pydantic (Campos)

### AppConfig
| Campo | Tipo | Predeterminado | Valores | Descripción |
| --- | --- | --- | --- | --- |
| `processing` | `ProcessingConfig` | (Por defecto) | - | Parámetros de procesamiento principal |
| `segmentation` | `SegmentationConfig`| (Por defecto) | - | Parámetros de visión |
| `output` | `OutputConfig` | (Por defecto) | - | Destinos y verbosidad |

### SegmentationConfig
| Campo | Tipo | Predeterminado | Valores | Descripción |
| --- | --- | --- | --- | --- |
| `min_area` | `int` | `4` | `>0` | Área mínima en píxeles para ignorar ruido |
| `padding` | `int` | `2` | `>=0` | Píxeles transparentes extra añadidos a cada recorte |

*(Continúa con `ProcessingConfig`, `OutputConfig`, `GroupingConfig`, `GltfConfig`, `SemanticConfig`)*

## YAML Mínimo

```yaml
version: 1
segmentation:
  min_area: 10
```

## YAML Avanzado

```yaml
version: 1
segmentation:
  min_area: 5
  padding: 4
output:
  verbose: true
  overwrite: false
semantic:
  confidence_threshold: 0.85
  model_id: "qwen3-vl-2b"
```
""",
    "reference/manifests.md": """# Referencia de manifiestos

## `manifest.json`
* **Generado por:** `split`, `semantic`
* **Consumido por:** `preview`, visor HTML
* **Versión:** 1
* **Campos principales:** `source_image`, `pieces` (lista de objetos con `id`, `bbox`, `path`)
* **Editable:** No recomendado.

## `semantic_manifest.json`
* **Generado por:** `semantic`
* **Campos principales:** `groups` (nombres y lista de IDs de piezas asignadas).

## `review.json`
* **Generado por:** `semantic`, o comandos de revisión.
* **Consumido por:** `apply-review`
* **Editable:** Sí.
* **Ejemplo:**
```json
{
  "version": 1,
  "source": "semantic",
  "groups": [
    {
      "name": "walls",
      "piece_ids": ["E001"],
      "confidence": 0.9,
      "status": "accepted"
    }
  ],
  "unassigned_piece_ids": []
}
```

*(Todos los demás manifiestos como `uv_manifest.json`, `objects_manifest.json`, y `project.json` siguen estructuras similares estrictamente validadas por esquemas)*
""",
    "reference/output-structure.md": """# Estructura de salida

## `split`
```text
resultados/
├── manifest.json        (Generado)
├── report/              (Temporales/Regenerables)
│   └── index.html
└── objects/             (Permanentes)
    ├── obj_000.png
    └── obj_001.png
```

## `semantic`
Añade a lo anterior:
```text
├── semantic_manifest.json (Generado)
├── review.json            (Editable)
└── grouped/               (Generados/Regenerables)
    ├── walls/
    │   └── obj_000.png
    └── uncertain/
```

## `extract`
```text
resultados/
├── uv_manifest.json       (Generado)
├── objects_manifest.json  (Generado)
├── project.json           (Raíz de Blender)
└── blender/
    └── rebuild_scene.py
```
""",
    "reference/models.md": """# Modelos

Atlas Splitter soporta descargas locales de modelos:

* `qwen3-vl-2b`: Modelo por defecto de lenguaje visual (aprox 4GB).
* `sam2-base`: Modelo base de Segment Anything 2.

Consulta:
```text
atlas-splitter models list
atlas-splitter models download [modelo]
```
""",
    "reference/error-codes.md": """# Códigos de error

* `E001`: Archivo de entrada no existe.
* `E002`: GPU solicitada pero no disponible.
* `E010`: El GLB no tiene información `TEXCOORD_0`.
* `E011`: GLB con compresión Draco no soportado.
* `E100`: JSON/Manifiesto inválido o malformado.
""",
    "troubleshooting/installation.md": """# Instalación

**Síntoma:** El comando falla al instalar.
**Causa probable:** Python no está en PATH o versión incorrecta.
**Comprobación:** `python --version` (debe ser 3.11+).
**Solución:** Reinstala Python asegurando marcar "Add to PATH".
**Comando de diagnóstico:** `atlas-splitter doctor`
""",
    "troubleshooting/path-and-pipx.md": """# PATH y Pipx

**Síntoma:** `atlas-splitter: command not found`.
**Causa probable:** `pipx` no añadió la ruta de los scripts al PATH del sistema.
**Comprobación:** Cierra y vuelve a abrir la terminal.
**Solución:** Ejecuta `pipx ensurepath` y reinicia tu PC.
""",
    "troubleshooting/cpu-cuda-mps.md": """# CPU, CUDA y MPS

**Síntoma:** El procesamiento semántico es extremadamente lento, o arroja error de memoria de video.
**Causa probable:** CUDA no instalado o VRAM insuficiente.
**Comprobación:** Ejecuta `nvidia-smi`.
**Solución:** Configura para usar CPU (más lento) o reduce el batch de procesamiento.
""",
    "troubleshooting/models.md": """# Modelos

**Síntoma:** Error "Model not found".
**Causa probable:** Intentar usar `semantic` sin descargar el modelo.
**Comprobación:** Verifica `atlas-splitter models list`.
**Solución:** Ejecuta `atlas-splitter models download qwen3-vl-2b`.
""",
    "troubleshooting/memory.md": """# Memoria

**Síntoma:** El programa finaliza sin error pero la terminal se cierra repentinamente o dice `Killed`.
**Causa probable:** Out of Memory (OOM). La imagen es demasiado masiva.
**Comprobación:** Monitor de recursos del sistema.
**Solución:** Divide la imagen previamente en cuartos antes de procesar.
""",
    "troubleshooting/glb.md": """# GLB sin UV

**Síntoma:** Error "No TEXCOORD_0 found".
**Causa probable:** El modelo 3D exportado no tiene UVs, o las tiene en un canal personalizado.
**Comprobación:** Usa `atlas-splitter inspect modelo.glb`.
**Solución:** Re-exporta desde Blender asegurando marcar "UVs" en la configuración de exportación de glTF.
""",
    "troubleshooting/draco.md": """# Draco

**Síntoma:** Error "Draco compression not supported".
**Causa probable:** El GLB fue exportado con Draco compression habilitada.
**Comprobación:** Ver la configuración de exportación original.
**Solución:** Re-exporta el archivo desmarcando Draco Compression, o usa la herramienta gltf-pipeline para descomprimirlo.
""",
    "troubleshooting/blender.md": """# Blender

**Síntoma:** El Add-on no aparece tras instalar el ZIP.
**Causa probable:** Estás usando una versión de Blender antigua (< 4.0).
**Comprobación:** Mira la pestaña de consola de Blender.
**Solución:** Actualiza a Blender 4.0+ o verifica que no se extrajo un zip anidado.
""",
    "troubleshooting/zip-and-files.md": """# ZIP y archivos

**Síntoma:** Permiso denegado al escribir resultados.
**Causa probable:** La carpeta de destino está abierta por otro programa o existe un ZIP bloqueado.
**Solución:** Cierra el Explorador o el Visor de imágenes y usa otra carpeta con `--output nueva_carpeta`.
""",
    "troubleshooting/manifests.md": """# Manifiestos

**Síntoma:** Error validando manifiesto al aplicar revisión.
**Causa probable:** Editaste el JSON manualmente rompiendo la sintaxis.
**Comprobación:** Abre el archivo JSON en un editor de código y busca marcas rojas.
**Solución:** Corrige la sintaxis (comas faltantes, comillas erróneas).
""",
    "contributing.md": """# Contribuir

¡Agradecemos las contribuciones!

Si deseas enviar código, haz un fork del repositorio, crea una rama, ejecuta los tests (`pytest`) y envía un Pull Request.

Para problemas, abre un issue describiendo el síntoma.
""",
    "security.md": """# Seguridad y privacidad

Atlas Splitter procesa todos los archivos de manera **local**. 

* **Cuándo se usa Internet:** Únicamente al ejecutar `pipx install` y `models download`.
* **Modelos descargados:** Se guardan en el caché seguro de tu usuario local.
* **Manifiestos no confiables:** Si recibes un `.json` de terceros, inspecciónalo. Aunque el parser es seguro, no ejecutes scripts desconocidos.
* **Rutas confinadas:** Atlas Splitter no modificará archivos fuera del directorio `--output` especificado.
* **Reporte HTML:** Es estático y autocontenido. No ejecuta código peligroso ni hace peticiones externas.

Para reportar vulnerabilidades, contáctanos a través del correo listado en el repositorio original.
""",
    "changelog.md": """# Historial de cambios

## v0.2.0
* Soporte para SAM 2 opcional.
* Mejoras en el exportador GLB UV.
* Generador de CLI integrado.

## v0.1.0
* Lanzamiento inicial. Segmentación por transparencia.
"""
}

def main():
    for rel_path, content in pages.items():
        full_path = os.path.join(docs_dir, rel_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content.strip() + "\\n")
    print("Files created.")

if __name__ == "__main__":
    main()
