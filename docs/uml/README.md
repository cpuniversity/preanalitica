# Modelado UML y trazabilidad

| Documento | Contenido |
|---|---|
| [casos_de_uso.md](casos_de_uso.md) | Diagrama de casos de uso y casos de uso desarrollados (CU-02, CU-03, CU-06, CU-08) |
| [secuencia.md](secuencia.md) | Diagramas de secuencia SD-1 a SD-4 |
| [clases.md](clases.md) | Diagrama de clases con atributos, métodos, asociaciones y cardinalidades |
| [../arquitectura.md](../arquitectura.md) | Arquitectura, componentes, patrones de diseño y principios SOLID |

Los diagramas están escritos en Mermaid (texto): GitHub los dibuja solos y
quedan versionados junto al código.

## Matriz de trazabilidad

Cada requisito se puede seguir hasta su caso de uso, su diagrama de secuencia,
las clases que lo implementan y las pruebas que lo verifican.

| Requisito | Caso de uso | Secuencia | Clases y métodos | Pruebas |
|---|---|---|---|---|
| RF-1 Identificación | CU-01 | — | `rutas.ingreso()`, `revisar_nombre()` | `test_ingreso.py` (24) |
| RF-2 Buscador | CU-02 | SD-2 | `Buscador.buscar()`, `RepositorioDeExamenes.todos()`, `Examen.etiqueta` | `test_buscador.py` (31) |
| RF-3 Agrupación y orden CLSI | CU-03 | SD-1 | `Agrupador.agrupar()`, `Contenedor`, `ResumenDeTubos`, `TipoDeTubo`, `Examen.opciones_de_tubo()` | `test_agrupador.py` (22), `test_tubos.py` (39) |
| RF-4 Derivaciones y estabilidad | CU-04 | SD-1 | `RevisorDeEstabilidad.revisar()`, `CalendarioDeProceso.dia_de_proceso()`, `Estabilidad.para_decidir()` | `test_derivaciones.py` (57) |
| RF-5 Resumen e impresión | CU-03, CU-05 | SD-1 | `rutas.tubos()`, plantilla `tubos.html` | `test_interfaz.py` (17) |
| RF-6 Auditoría | CU-08, CU-09 | SD-1, SD-4 | `Auditoria.registrar()`, `Auditoria.envio_semanal()`, `EnviadorDeCorreo.enviar()` | `test_auditoria.py` (21) |
| RF-7 Importación del listado | CU-06, CU-07 | SD-3 | `Importador.importar()`, `LectorDeListadoCSV.leer()` | `test_importador.py` (29) |
| Diseño (patrones y SOLID) | — | — | `RepositorioDeExamenes`, `EnviadorDeCorreo`, `LectorDeListado` | `test_clases.py` (10) |

Total: 250 pruebas automáticas (`pytest`).
