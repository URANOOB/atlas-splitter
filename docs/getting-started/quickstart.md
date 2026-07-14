# Inicio rápido

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
    │   └── index.html       
    ├── manifest.json        
    └── objects/
        ├── obj_0000.png     
        ├── obj_0001.png     
        └── ...
```
