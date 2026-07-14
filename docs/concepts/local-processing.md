# Procesamiento local

Atlas Splitter abre atlas, GLB, manifiestos y reportes en el equipo donde ejecutas el comando. Los reportes HTML contienen sus imágenes como datos locales y no necesitan un servidor.

La instalación de paquetes y las descargas solicitadas con `models download` sí pueden usar Internet. `split`, `extract`, `preview` y `review` no descargan modelos durante su ejecución.

Los manifiestos recibidos de otra persona son datos no confiables. Las rutas relativas de proyectos nuevos se confinan al resultado; revisa los proyectos antiguos que aún señalan un atlas externo.

Consulta [Seguridad](../security.md) para el alcance y el reporte de vulnerabilidades.
