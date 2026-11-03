# Preanalítica

Aplicación web para personal de enfermería y matronería. A partir de los exámenes indicados por el médico en la ficha clínica, muestra qué tubos usar, cuáles exámenes se procesan en el laboratorio del recinto y cuáles se derivan. Es un prototipo local para un curso (Ingeniería de Software, UDP), pero se construye con criterios profesionales.

Los requisitos completos y el estado del proyecto están en `docs/requisitos.md`.

## Quién usa esto

- Usuaria final: enfermera o matrona, muchas veces en turno de noche, con poco tiempo. La interfaz debe ser clara, ordenada y amigable.
- Dueño del dominio: tecnólogo médico. Las reglas clínicas las define él, no tú. En todo documento o material del proyecto se nombra solo como "tecnólogo médico", sin especialidad.

## Alcance de la versión 1

Dentro:
- La enfermera escribe primero su nombre y apellido, y recién después puede buscar.
- Buscador de exámenes que muestra una lista de sugerencias (no autoselecciona), tolera errores de tipeo y funciona con o sin tildes. Debe reconocer el examen sin escribir el nombre completo.
- Por cada examen informa si se procesa en el laboratorio del recinto o se deriva.
- Agrupación de tubos: comparten tubo los exámenes con el mismo tipo de tubo y el mismo laboratorio (ver "Reglas de tubos").
- Excepciones que van en contenedor aparte o con advertencia: hemocultivos, gases, protegido de la luz, ayuno (ver "Reglas de tubos").
- Resumen final: total de tubos, orden de extracción según CLSI y qué exámenes se derivan.
- Derivaciones: para cada examen derivado, mostrar si la estabilidad de la muestra alcanza hasta el día en que lo procesa el laboratorio externo; si no alcanza, advertir claramente y sugerir cuándo tomarla (ver "Derivaciones y estabilidad").
- Auditoría (ver más abajo).
- Solo adultos. Solo uso desde computador.

Fuera de la versión 1 (no implementar, no anticipar con código a medias):
- Cálculo de volúmenes por tubo.
- Todo lo que sea compartir o fraccionar volumen de una muestra entre exámenes.
- Sección del laboratorio: el listado no la trae; no implementar reglas que dependan de ella.
- Día de envío de las muestras: es tarea del laboratorio, no de enfermería.
- Pacientes pediátricos, uso en celular, integración con la ficha clínica.

Si algo no está en este documento, pregunta antes de implementarlo.

## Reglas clínicas (no negociables)

- Nunca inventes reglas clínicas, tubos, estabilidades ni días de procesamiento. Todo sale del listado técnico del laboratorio. Si falta un dato, muéstralo como "dato no disponible" y avísalo, nunca lo rellenes con una suposición.
- Ante la duda, la app debe advertir, no decidir en silencio.
- Cada regla de agrupación y cada excepción debe tener una prueba automática con un caso que el tecnólogo médico considere correcto.

## Datos

- Fuente: listado técnico de exámenes del laboratorio, en CSV UTF-8 (`data/listado_tecnico.csv`). Es una exportación del documento INSVE 02000: trae filas de encabezado del documento antes de la fila de títulos.
- Separa la importación del resto: el módulo `importador` lee el archivo y carga la base de datos, y el resto de la app solo lee de la base de datos. Así cambiar de formato (Excel, PDF) no rompe nada.
- Después de importar se genera un reporte de revisión (`data/reporte_revision.csv`: campos vacíos, valores raros, duplicados) para que el tecnólogo médico lo valide.
- El listado real del laboratorio no se sube a Git ni se imprime en logs. En la consola solo se muestran conteos.
- El listado nunca se abre ni se guarda con Excel: lo daña (mete cada línea en una sola celda). Para corregirlo se usa el Bloc de notas, con copia de respaldo, y después se verifica que tenga las mismas filas y columnas antes de importar. El importador limpia los saltos de línea de Windows (`\r\n`).

### Decisiones sobre el listado (tecnólogo médico, noviembre 2026)

- No considerar la fecha de término de vigencia del documento.
- Estabilidad: no hay columna propia. Se guarda el texto tal como lo indica el listado (dentro de las instrucciones); a futuro se creará una columna.
- El recinto es "Laboratorio Clínica Dávila Vespucio" y trabaja 24/7. Los demás laboratorios del listado son laboratorios de derivación.
- Si una celda de código (Vidalab o Medisyn) trae más de un código, se usa el de número más grande.
- Los exámenes cuyo "Lab. Derivado" no es un número (por ejemplo "-" o "NOTA:") no se consideran en la app.
- Si un examen derivado no tiene estabilidad en el listado, se muestra "dato no disponible".

## Reglas de tubos (tecnólogo médico, noviembre 2026)

- "Tubo con gel" y "tapa amarilla" son el mismo tubo: amarillo con gel. El tubo rojo es distinto.
- Comparten tubo solo los exámenes con el mismo tipo de tubo y el mismo laboratorio. Si deben procesarse en más de un laboratorio, van en tubos distintos.
- Un examen puede admitir más de un tipo de tubo: se elige el que permita juntarlo con otro examen; si ninguno lo permite, el primero (amarillo con gel antes que rojo).
- Orden de extracción según CLSI: hemocultivo, celeste, amarillo con gel, rojo, verde, jeringa de gases venosos (junto al verde), lila, gris.
- Gases arteriales: punción aparte, fuera del orden venoso. Hemocultivo y gases van en su propio contenedor (botella o jeringa).
- Si el laboratorio pide 2 o más tubos para un examen, esos tubos son solo de ese examen (ej.: 2 celeste de un examen + 1 celeste de otro = 3 tubos).
- Muestras que no son sangre: sección "Otras muestras", fuera del orden de extracción, sin quitarles importancia.
- Protección de la luz: advertencia sobre el tubo, no tubo aparte. Hielo: no se muestra (lo maneja el laboratorio). Ayuno: advertencia con la frase original del listado.
- Textos con indicación para adultos y pediátricos: se usa la parte de adultos.
- Los tubos que la app no reconoce sola van a `data/tubos_por_revisar.csv` para que el tecnólogo médico los complete (guía en `docs/tabla_de_tubos.md`). Mientras tanto se muestran como "Tubo: dato no disponible".

## Derivaciones y estabilidad (tecnólogo médico, noviembre 2026)

- Enfermería no almacena muestras: las toma y las envía. A la enfermera se le muestra si la estabilidad alcanza hasta el día de proceso del laboratorio externo; si no alcanza, el laboratorio rechazaría la muestra.
- El día de toma es automáticamente la fecha y hora de la consulta.
- Recepción en Vespucio: si la consulta es antes de las 15:00 cuenta ese día; después, el día siguiente. La espera se cuenta en días desde la recepción hasta el día de proceso (es una estimación).
- El laboratorio externo procesa el mismo día solo si la muestra llega antes de las 8:00; si no, en su siguiente día de proceso.
- Los laboratorios externos no reciben en feriados de Chile (librería `holidays`). Vespucio trabaja 24/7, también en feriados.
- Estabilidad: se decide con la refrigerada; si no existe, con la ambiente. La congelada solo se informa. Se usa la del tipo de muestra del tubo del examen (amarillo/rojo: suero; celeste, verde, gris: plasma; lila: sangre total o plasma EDTA, que son lo mismo; si traen valores distintos se usa el más corto). Si no es claro: "consultar con el laboratorio".
- Resultados: "la estabilidad lo permite", "al límite, consultar" (espera igual a la estabilidad, o estabilidad menor a un día) y "NO alcanza" (advertencia destacada, con sugerencia de días de toma en la próxima semana).
- "Según demanda": el laboratorio procesa en tandas; no se sabe el día. No se da veredicto: se muestra el tiempo de respuesta y "consultar con el laboratorio si la estabilidad es corta".
- La estabilidad se muestra tal como la escribe el listado (no desglosada por temperatura).

## Auditoría

- Se registra: fecha y hora, nombre y apellido de la enfermera, exámenes elegidos y resultado entregado (total y tubos en orden, punciones aparte, otras muestras, exámenes sin tubo y veredicto de estabilidad de cada derivado).
- Se registra cuando la enfermera ve el resumen de tubos. Recargar la pantalla con los mismos exámenes no duplica el registro.
- No se guarda ningún dato de pacientes. La app nunca pide nombre, RUT ni ficha del paciente.
- La búsqueda no queda guardada para la enfermera; el registro es solo para auditoría.
- Cada semana (lunes a domingo) se genera un CSV con el historial (`data/auditoria_<lunes>.csv`, separado por punto y coma), se envía por correo a la jefatura de laboratorio y de sección, y luego se elimina ese historial de la base. El CSV se conserva como respaldo local.
- La app envía sola la auditoría: lo revisa en cada consulta y, desde el lunes, la envía en segundo plano. Si el correo falla, no borra nada y reintenta más tarde. También existe el comando `flask --app app auditoria-semanal`.
- El correo se configura en `.env` (no va a Git; ver `.env.example`). Por defecto está en modo prueba: el correo se guarda como `.eml` en `data/` en vez de enviarse. En el prototipo se prueba solo con direcciones de prueba (destinataria: la dueña del proyecto).

## Stack

- Python 3, Flask, SQLite, plantillas Jinja2.
- Importación del CSV con el módulo `csv` de Python. pandas y openpyxl solo si el listado llega en Excel; una librería de extracción de tablas para PDF solo si llega en PDF.
- rapidfuzz para la búsqueda tolerante a errores. Normaliza el texto (minúsculas, sin tildes) antes de comparar.
- holidays para los feriados de Chile.
- python-dotenv para leer la configuración del correo desde `.env`.
- pytest para las pruebas.

## Estructura

```
Preanalitica/
  CLAUDE.md
  README.md            # presentación del repositorio e insignia de las pruebas
  .env.example         # ejemplo de configuración del correo (el .env real no va a Git)
  .github/workflows/
    pruebas.yml        # GitHub Actions: corre pytest en cada push
  docs/
    requisitos.md      # requisitos, decisiones y estado del proyecto
    plan_de_pruebas.md # qué se prueba, cómo y criterios de aprobación
    informe_de_pruebas.md # resultados de las pruebas y ejecuciones en GitHub Actions
    despliegue.md      # plan de despliegue y operación: ambientes, respaldos, monitoreo, mantenimiento
    arquitectura.md    # capas, componentes, patrones de diseño y SOLID
    uml/               # casos de uso, secuencia, clases y matriz de trazabilidad (Mermaid)
    gestion_agil/      # objetivo del producto, backlog, historias de usuario e iteraciones
    tabla_de_tubos.md  # guía para que el tecnólogo médico complete la tabla de tubos
  app/
    __init__.py        # crea la app Flask
    rutas.py           # páginas, endpoints y páginas de error
    modelos.py         # tablas de la base de datos
    repositorio.py     # RepositorioDeExamenes: único acceso a los exámenes en la base
    texto.py           # normalizar texto (minúsculas, sin tildes)
    examen.py          # Examen
    tubos.py           # TipoDeTubo, orden CLSI y lectura del tubo desde el listado
    importador.py      # Importador, LectorDeListado: lee el CSV y genera los reportes de revisión
    buscador.py        # Buscador
    agrupador.py       # Agrupador, Contenedor, ResumenDeTubos
    derivaciones.py    # RevisorDeEstabilidad, CalendarioDeProceso, Estabilidad
    auditoria.py       # Auditoria, EnviadorDeCorreo (CorreoDePrueba, CorreoSMTP)
    templates/         # base, ingreso, examenes, tubos, error
    static/            # estilos.css, buscador.js, icono.svg
  tests/
  data/                # listado técnico, base local, reportes y auditoría (no va a Git)
  requirements.txt
```

## Diseño visual

Hay una maqueta de tres pantallas (Ingreso, Búsqueda de exámenes, Resumen de tubos). Sigue su estructura y estilo. Los exámenes, tubos y el laboratorio externo de la maqueta son solo ejemplos: los datos reales salen del listado técnico.

- Tipografía: IBM Plex Sans (Google Fonts), pesos 400, 500, 600 y 700.
- Colores: fondo `#F4F6F7`, tarjetas `#FFFFFF` con borde `#D5DDE2`, texto `#14212B`, texto secundario `#4A5B68`, acento `#0B6E6E` (botones principales y paso activo), bordes de campos `#8696A3`.
- Etiquetas: neutra `#E9EEF1` con texto `#2B3A46`; "Se procesa en el recinto" `#E3F1F1` con texto `#07504F`; "Se deriva" `#E8EEFB` con texto `#1F3F8F`; advertencias `#FFF4D6` con texto `#6B4200`.
- Tamaños pensados para turnos de noche: texto base de 17 a 18 px (nunca menos de 17 px en pantalla), campos de 54 a 60 px de alto, botones de 56 px, botones secundarios de al menos 44 px. Esquinas redondeadas de 10 a 16 px.
- Nunca usar solo el color para distinguir algo: cada tubo y cada etiqueta lleva también texto.
- Ningún texto que se muestra termina en punto (el filtro `sin_punto` se lo quita a los textos del listado). Los puntos entre dos frases sí se mantienen.
- Cabecera con el nombre "Preanalítica", los tres pasos (Identificación, Exámenes, Tubos) y, desde el paso 2, el nombre de la enfermera con la opción "Cambiar".
- Pantalla 1: nombre y apellido, botón "Continuar" y aviso de que no se ingresan datos del paciente.
- Pantalla 2: buscador grande con sugerencias (cada una con si se procesa en el recinto o se deriva) y, al lado, la lista de exámenes seleccionados con botón para quitar cada uno y el botón "Ver qué tubos usar" siempre visible.
- Pantalla 3: tubos numerados en orden de extracción, con su laboratorio y sus exámenes, el total de tubos, los avisos (ayuno, tubo no disponible, estabilidad que no alcanza), las otras muestras, los exámenes que se derivan con su revisión de estabilidad, y al final los botones "Volver a exámenes", "Imprimir resumen" y "Nueva consulta".
- Solo escritorio: no hace falta diseño para celular en la versión 1.

## Cómo trabajar

- Antes de escribir código para una funcionalidad nueva, propón un plan corto y espera confirmación.
- Una funcionalidad a la vez. Las seis etapas de la versión 1 están completas (base de datos e importador, buscador, agrupador de tubos, derivaciones y estabilidad, auditoría, pulido de interfaz).
- Después de cada funcionalidad: corre las pruebas y explica qué probar a mano en el navegador.
- Las pruebas usan exámenes inventados y una base temporal; nunca el listado real ni la base de `data/`. Nunca se envía un correo real en las pruebas.
- Código simple y legible, con nombres en español y comentarios breves en español sencillo, pensados para alguien que está aprendiendo. Evita abstracciones innecesarias.
- Diseño orientado a objetos (lo pide la pauta del curso): la lógica vive en clases del dominio (ver `docs/arquitectura.md`). Las rutas no escriben SQL: usan `RepositorioDeExamenes`. Si se agrega o cambia una clase o un método, se actualizan los diagramas de `docs/uml/` para que código y diagramas no se contradigan.
- No agregues librerías sin avisar y explicar para qué sirven.
- Explica los cambios con claridad, como a una persona que sabe mucho de laboratorio y está aprendiendo programación.

## Comandos

```
python -m venv venv
venv\Scripts\activate                              # Windows
source venv/bin/activate                           # Mac / Linux
pip install -r requirements.txt
copy .env.example .env                             # configuración del correo (una vez)
flask --app app importar data/listado_tecnico.csv  # carga el listado en la base
flask --app app run --debug                        # abre http://127.0.0.1:5000
flask --app app auditoria-semanal                  # envía la auditoría a mano
pytest
```
