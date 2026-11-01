# Preanalítica

Aplicación web para personal de enfermería y matronería. A partir de los exámenes indicados por el médico en la ficha clínica, muestra qué tubos usar, cuáles exámenes se procesan en el laboratorio del recinto y cuáles se derivan. Es un prototipo local para un curso (Ingeniería de Software, UDP), pero se construye con criterios profesionales.

## Quién usa esto

- Usuaria final: enfermera o matrona, muchas veces en turno de noche, con poco tiempo. La interfaz debe ser clara, ordenada y amigable.
- Dueño del dominio: tecnólogo médico de microbiología. Las reglas clínicas las define él, no tú.

## Alcance de la versión 1

Dentro:
- La enfermera escribe primero su nombre y apellido, y recién después puede buscar.
- Buscador de exámenes que muestra una lista de sugerencias (no autoselecciona), tolera errores de tipeo y funciona con o sin tildes. Debe reconocer el examen sin escribir el nombre completo.
- Por cada examen informa si se procesa en el laboratorio del recinto o se deriva.
- Agrupación de tubos: exámenes de una misma sección y del mismo tipo de tubo comparten tubo. Nunca se comparte tubo entre secciones distintas.
- Excepciones que van en tubo aparte o con advertencia: hemocultivos, gases, protegido de la luz, en hielo, ayuno.
- Resumen final: total de tubos, orden de extracción según CLSI y qué exámenes se derivan.
- Derivaciones: algunos laboratorios externos procesan solo ciertos días (ej. solo lunes). Si el día de toma no coincide, sugerir el día de envío (ej. viernes: enviar el domingo para el lunes temprano) y verificar que la estabilidad de la muestra lo permita; si no lo permite, advertir claramente.
- Auditoría (ver más abajo).
- Solo adultos. Solo uso desde computador.

Fuera de la versión 1 (no implementar, no anticipar con código a medias):
- Cálculo de volúmenes por tubo.
- Todo lo que sea compartir o fraccionar volumen de una muestra entre exámenes.
- Pacientes pediátricos, uso en celular, integración con la ficha clínica.

Si algo no está en este documento, pregunta antes de implementarlo.

## Reglas clínicas (no negociables)

- Nunca inventes reglas clínicas, tubos, estabilidades ni días de procesamiento. Todo sale del listado técnico del laboratorio. Si falta un dato, muéstralo como "dato no disponible" y avísalo, nunca lo rellenes con una suposición.
- Ante la duda, la app debe advertir, no decidir en silencio.
- Cada regla de agrupación y cada excepción debe tener una prueba automática con un caso que el tecnólogo médico considere correcto.

## Datos

- Fuente: listado técnico de exámenes del laboratorio. Puede llegar como Excel o como PDF (aún pendiente de recibir; no asumas el formato).
- Separa la importación del resto: un módulo `importador` que lee el archivo y carga la base de datos, y el resto de la app solo lee de la base de datos. Así cambiar de Excel a PDF no rompe nada.
- Los datos importados desde PDF pueden traer errores de extracción. Después de importar, genera un reporte de revisión (filas con campos vacíos, valores raros, duplicados) para que el tecnólogo médico lo valide antes de usar los datos.
- El listado real del laboratorio no se sube a Git ni se imprime en logs.

### Listado recibido y decisiones del dueño del dominio (noviembre 2026)

- El listado llegó como CSV UTF-8 (`data/listado_tecnico.csv`). Es una exportación del documento INSVE 02000: trae filas de encabezado del documento antes de la fila de títulos.
- No considerar la fecha de término de vigencia del documento.
- El listado no trae sección. En esta versión no se usa la sección: no implementar reglas que dependan de ella.
- Estabilidad: no hay columna propia. Se guarda el texto tal como lo indica el listado (dentro de las instrucciones); a futuro se creará una columna.
- El recinto es "Laboratorio Clínica Dávila Vespucio" y trabaja 24/7. Los demás laboratorios del listado son laboratorios de derivación.
- Un examen puede admitir más de un tipo de tubo.
- Si una celda de código (Vidalab o Medisyn) trae más de un código, se usa el de número más grande.
- Los exámenes cuyo "Lab. Derivado" no es un número (por ejemplo "-" o "NOTA:") no se consideran en la app.
- Si un examen derivado no tiene estabilidad en el listado, se muestra "dato no disponible".

### Reglas de tubos (definidas por el tecnólogo médico, noviembre 2026)

- "Tubo con gel" y "tapa amarilla" son el mismo tubo: amarillo con gel. El tubo rojo es distinto.
- Comparten tubo solo los exámenes con el mismo tipo de tubo y el mismo laboratorio. Si deben procesarse en más de un laboratorio, van en tubos distintos.
- Si un examen admite varios tubos, se elige el que permita juntarlo con otro examen; si ninguno lo permite, el primero (amarillo con gel antes que rojo).
- Orden de extracción según CLSI: hemocultivo, celeste, amarillo con gel, rojo, verde, jeringa de gases venosos (junto al verde), lila, gris.
- Gases arteriales: punción aparte, fuera del orden venoso. Hemocultivo y gases van en su propio contenedor (botella o jeringa).
- Si el laboratorio pide 2 o más tubos para un examen, esos tubos son solo de ese examen (ej.: 2 celeste de un examen + 1 celeste de otro = 3 tubos).
- Muestras que no son sangre: sección "Otras muestras", fuera del orden de extracción, sin quitarles importancia.
- Protección de la luz: advertencia sobre el tubo, no tubo aparte. Hielo: no se muestra (lo maneja el laboratorio). Ayuno: advertencia.
- Textos con indicación para adultos y pediátricos: se usa la parte de adultos.
- Los tubos que la app no reconoce sola van a `data/tubos_por_revisar.csv` para que el tecnólogo médico los complete (guía en `docs/tabla_de_tubos.md`). Mientras tanto se muestran como "Tubo: dato no disponible".

## Auditoría

- Se registra: fecha y hora, nombre y apellido de la enfermera, exámenes buscados y resultado entregado (tubos y orden).
- No se guarda ningún dato de pacientes. La app nunca pide nombre, RUT ni ficha del paciente.
- La búsqueda no queda guardada para la enfermera; el registro es solo para auditoría.
- Cada semana se genera un archivo con el historial para enviarlo por correo a la jefatura de laboratorio y de sección, y luego se elimina ese historial de la base. En el prototipo el envío por correo es configurable y se prueba solo con direcciones de prueba.

## Stack

- Python 3, Flask, SQLite, plantillas Jinja2.
- pandas y openpyxl para importar Excel; una librería de extracción de tablas para PDF solo cuando llegue el listado.
- rapidfuzz para la búsqueda tolerante a errores. Normaliza el texto (minúsculas, sin tildes) antes de comparar.
- pytest para las pruebas.

## Estructura sugerida

```
Preanalitica/
  CLAUDE.md
  docs/requisitos.md
  app/
    __init__.py        # crea la app Flask
    rutas.py           # páginas y endpoints
    modelos.py         # tablas de la base de datos
    buscador.py        # búsqueda y sugerencias
    agrupador.py       # lógica de tubos, orden CLSI, excepciones
    derivaciones.py    # días de envío y estabilidad
    auditoria.py       # registro y exportación semanal
    importador.py      # lee Excel/PDF y carga la base
    templates/
    static/
  tests/
  data/                # listado técnico y base local (no va a Git)
  requirements.txt
```

## Diseño visual

Hay una maqueta de tres pantallas (Ingreso, Búsqueda de exámenes, Resumen de tubos). Sigue su estructura y estilo. Los exámenes, tubos y el laboratorio externo de la maqueta son solo ejemplos: los datos reales salen del listado técnico.

- Tipografía: IBM Plex Sans (Google Fonts), pesos 400, 500, 600 y 700.
- Colores: fondo `#F4F6F7`, tarjetas `#FFFFFF` con borde `#D5DDE2`, texto `#14212B`, texto secundario `#4A5B68`, acento `#0B6E6E` (botones principales y paso activo), bordes de campos `#8696A3`.
- Etiquetas: sección `#E9EEF1` con texto `#2B3A46`; "Se procesa en el recinto" `#E3F1F1` con texto `#07504F`; "Se deriva" `#E8EEFB` con texto `#1F3F8F`; advertencias `#FFF4D6` con texto `#6B4200`.
- Tamaños pensados para turnos de noche: texto base de 17 a 18 px, campos de 54 a 60 px de alto, botones de 56 px, botones secundarios de al menos 44 px. Esquinas redondeadas de 10 a 16 px.
- Nunca usar solo el color para distinguir algo: cada tubo y cada etiqueta lleva también texto.
- Cabecera con el nombre "Preanalítica", los tres pasos (Identificación, Exámenes, Tubos) y, desde el paso 2, el nombre de la enfermera con la opción "Cambiar".
- Pantalla 1: nombre y apellido, botón "Continuar" y aviso de que no se ingresan datos del paciente.
- Pantalla 2: buscador grande con sugerencias (cada una con su sección y si se procesa en el recinto o se deriva) y, al lado, la lista de exámenes seleccionados con botón para quitar cada uno y el botón "Ver qué tubos usar".
- Pantalla 3: tubos numerados en orden de extracción, con su sección y sus exámenes, el total de tubos, el examen que se deriva con el día de envío recomendado y la revisión de estabilidad, y los botones "Nueva consulta" e "Imprimir resumen".
- Solo escritorio: no hace falta diseño para celular en la versión 1.

## Cómo trabajar

- Antes de escribir código para una funcionalidad nueva, propón un plan corto y espera confirmación.
- Una funcionalidad a la vez, en este orden: base de datos e importador, buscador, agrupador de tubos, derivaciones y estabilidad, auditoría, pulido de interfaz.
- Después de cada funcionalidad: corre las pruebas y explica qué probar a mano en el navegador.
- Código simple y legible, con nombres en español y comentarios breves en español sencillo, pensados para alguien que está aprendiendo. Evita abstracciones innecesarias.
- No agregues librerías sin avisar y explicar para qué sirven.
- Explica los cambios con claridad, como a una persona que sabe mucho de laboratorio y está aprendiendo programación.

## Comandos

```
python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # Mac / Linux
pip install -r requirements.txt
flask --app app run --debug    # abre http://127.0.0.1:5000
pytest
```

### Derivaciones y estabilidad (definidas por el tecnólogo médico, noviembre 2026)

- Enfermería no almacena muestras: las toma y las envía. El día de envío es tarea del laboratorio. A la enfermera se le muestra si la estabilidad alcanza hasta el día de proceso del laboratorio externo; si no alcanza, el laboratorio rechazaría la muestra.
- El día de toma es automáticamente la fecha y hora de la consulta.
- Recepción en Vespucio: si la consulta es antes de las 15:00 cuenta ese día; después, el día siguiente. La espera se cuenta en días desde la recepción hasta el día de proceso (es una estimación).
- El laboratorio externo procesa el mismo día solo si la muestra llega antes de las 8:00; si no, en su siguiente día de proceso.
- Los laboratorios externos no reciben en feriados de Chile (librería `holidays`). Vespucio trabaja 24/7, también en feriados.
- Estabilidad: se decide con la refrigerada; si no existe, con la ambiente. La congelada solo se informa. Se usa la del tipo de muestra del tubo del examen (amarillo/rojo: suero; celeste, verde, gris: plasma; lila: sangre total o plasma EDTA, que son lo mismo; si traen valores distintos se usa el más corto). Si no es claro: "consultar con el laboratorio".
- Resultados: "la estabilidad lo permite", "al límite, consultar" (espera igual a la estabilidad, o estabilidad menor a un día) y "NO alcanza" (advertencia destacada, con sugerencia de días de toma en la próxima semana).
- "Según demanda": el laboratorio procesa en tandas; no se sabe el día. No se da veredicto: se muestra el tiempo de respuesta y "consultar con el laboratorio si la estabilidad es corta".

### Auditoría (decisiones, noviembre 2026)

- Se registra una consulta cuando la enfermera ve el resumen de tubos: exámenes elegidos (no lo que escribe en el buscador), total y tubos en orden, punciones aparte, otras muestras, exámenes sin tubo y el veredicto de estabilidad de cada derivado. Recargar la pantalla con los mismos exámenes no duplica el registro.
- Archivo semanal en CSV (`data/auditoria_<lunes>.csv`, separado por punto y coma). Se conserva como respaldo local después de enviarlo.
- La app envía sola la auditoría de la semana anterior (lunes a domingo): lo revisa en cada consulta y, desde el lunes, la envía en segundo plano. Si el correo falla, no borra nada y reintenta más tarde. También existe el comando `flask --app app auditoria-semanal`.
- Correo configurado en `.env` (no va a Git; ver `.env.example`). Por defecto en modo prueba: el correo se guarda como `.eml` en `data/` en vez de enviarse. Destinataria de prueba: la dueña del proyecto.
