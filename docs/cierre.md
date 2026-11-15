# Cierre del proyecto

Síntesis de lo construido, estado final, decisiones, dificultades, mejoras
futuras y conclusiones del equipo (Jared Estrada, Scherezade Huancapaza y
Camila Pastene).

## 1. Síntesis

**El problema.** Para tomar una muestra, la enfermera debe traducir
la indicación médica en tubos, orden de extracción y exámenes que se derivan.
La información está en el listado técnico del laboratorio (documento INSVE
02000): un listado largo, en texto libre y sin cálculo de estabilidad. Un error
puede obligar a repetir la punción o hacer que el laboratorio externo rechace
la muestra.

**La solución.** Preanalítica es una aplicación web local de tres pantallas.
La enfermera se identifica sin ingresar datos del paciente, busca los exámenes
(aunque los escriba mal o sin tildes) y obtiene:

- los tubos agrupados según las reglas del laboratorio y numerados en el orden
  de extracción CLSI;
- los contenedores especiales (hemocultivo, gases) y las otras muestras;
- los avisos de ayuno y protección de la luz, al lado de cada examen y con la
  frase del listado;
- qué exámenes se derivan y si la estabilidad de cada muestra alcanza hasta el
  día en que la procesa el laboratorio externo.

Cada consulta queda en una auditoría que se envía cada semana por correo a la
jefatura.

**El resultado en cifras.**

| | |
|---|---|
| Exámenes del listado cargados | 615 (173 se procesan en el recinto y 442 se derivan) |
| Tubos reconocidos automáticamente | 574 de 615 (93 %); 41 quedan para el tecnólogo médico |
| Historias de usuario | 19 con criterios de aceptación, más 4 tareas de la entrega final (HU-20 a HU-23) |
| Iteraciones | I0 a I7 (31/10 al 02/11) e I8 de entregables finales (hasta el 26/11) |
| Pruebas automáticas | 260, todas pasan, también en GitHub Actions en cada `push` |
| Estilo del código | flake8 sin avisos, con sus reglas por defecto |
| Documentación | Requisitos verificables, arquitectura, UML (casos de uso, secuencia, clases y trazabilidad), gestión ágil, plan e informe de pruebas, plan de despliegue |

## 2. Cumplimiento del objetivo

Objetivo del producto ([producto.md](gestion_agil/producto.md)): que la
enfermera, en pocos segundos y sin ingresar datos del paciente, sepa qué
tubos usar, en qué orden extraerlos y si cada derivado alcanzará a procesarse,
usando solo la información del listado técnico.

| Medida de éxito | Estado | Evidencia |
|---|---|---|
| Obtiene el resumen sin escribir el nombre completo de los exámenes | ✔ Cumplida | RF-2.2 y RF-2.3, `test_buscador.py` |
| Ningún tubo, estabilidad ni día de proceso aparece sin estar en el listado | ✔ Cumplida en las pruebas | RNF-8; si falta un dato se muestra "dato no disponible". Falta la validación con casos reales (HU-20) |
| Toda regla clínica tiene una prueba automática que pasa | ✔ Cumplida | [Plan de pruebas](plan_de_pruebas.md), sección 6 |
| Cada consulta queda en la auditoría, sin datos del paciente | ✔ Cumplida | RF-6.1 y RF-6.3, `test_auditoria.py` |

**Lo que no se puede afirmar todavía:** que los resultados sean correctos con
casos reales. Las reglas se probaron con exámenes inventados que siguen las
decisiones del tecnólogo médico. La validación con casos reales y los 41 tubos
pendientes esperan a que el laboratorio termine de actualizar su listado
técnico (sección 6).

## 3. Decisiones principales

### Del dominio (tecnólogo médico)

Están detalladas en [requisitos.md](requisitos.md), sección 7. Las de mayor
impacto en el diseño fueron:

| Decisión | Por qué importa |
|---|---|
| Comparten tubo solo los exámenes con el mismo tubo **y el mismo laboratorio** | Define cuántos tubos se extraen; es el centro del agrupador |
| Si un examen admite varios tubos, se elige el que permite juntarlo con otro | Evita extraer tubos de más |
| Estabilidad: refrigerada antes que ambiente, según el tipo de muestra del tubo | Hace posible decidir si la muestra alcanza |
| Cortes de las 15:00 en Vespucio y de las 8:00 en el laboratorio externo, y feriados de Chile | Permiten estimar el día de proceso |
| "Según demanda" no tiene veredicto | La app no decide lo que no se puede saber |
| Hielo no se muestra; ayuno y luz como advertencia | La pantalla muestra solo lo que le sirve a enfermería |
| Solo enfermería y pacientes adultos | Matronería y pediatría quedan fuera de la versión 1 |

### Técnicas (equipo)

| Decisión | Por qué |
|---|---|
| Nunca inventar un dato clínico: "dato no disponible" y advertir | Un error silencioso puede causar una punción repetida o una muestra rechazada |
| Importador separado del resto de la app | Si el listado llega en Excel o PDF, solo cambia el lector (patrón Strategy) |
| Reporte de revisión y tabla de tubos por revisar | El tecnólogo médico corrige el listado sin programar |
| Python, Flask y SQLite, sin servidor externo | Prototipo local, fácil de instalar y de explicar |
| Diseño orientado a objetos con patrones Repositorio y Strategy | Lo pide la pauta y separa responsabilidades (ver [arquitectura.md](arquitectura.md)) |
| Una funcionalidad a la vez, con pruebas antes de cada commit | Cada iteración dejó algo que funciona y está probado |
| Integración continua con pytest y flake8 | Cada `push` revisa que las pruebas pasen y que el código no tenga avisos de estilo |
| Trabajo directo en `main`, con un solo Pull Request | Decisión del equipo; las pruebas en GitHub Actions sirvieron como red de seguridad en lugar de la revisión previa |
| Desarrollo asistido por Claude Code | Aceleró la programación; las reglas clínicas siempre las definió el tecnólogo médico, y Claude Code aparece como coautor en los commits |

## 4. Dificultades y cómo se resolvieron

| Dificultad | Cómo se resolvió |
|---|---|
| El listado no es una tabla limpia: trae encabezados del documento antes de los títulos y mucho texto libre | El importador busca la fila de títulos y ubica cada columna por su nombre, no por su posición |
| Excel daña el listado (mete cada línea en una sola celda) y aparecen saltos de línea de Windows dentro de las celdas | Regla de nunca abrirlo con Excel; el importador limpia los saltos de línea |
| El tubo viene escrito de 145 formas distintas | La app reconoce las formas claras y las dudosas van a `tubos_por_revisar.csv` para el tecnólogo médico (41 exámenes pendientes; en I8 se corrigió la lectura de "1 frasco con muestra de deposición" y se dejaron fuera las filas de la leyenda de laboratorios) |
| La estabilidad no tiene columna propia y se escribe de muchas maneras | Se lee del texto de las instrucciones; dos formatos que se leían mal se corrigieron y quedaron como pruebas |
| "glucosa" no encontraba la glicemia | Los sinónimos entre paréntesis pasaron a contar como nombre del examen |
| "1 frasco con muestra de deposición" se leía como sangre (la regla de "1 frasco" era para hemocultivo) | Si después del frasco viene una muestra que no es sangre, va a "Otras muestras"; se revisaron los 620 exámenes de entonces y solo cambió ese |
| La leyenda de laboratorios del final del listado ("DERIVACION 1", "2", "3"…) se cargaba como si fueran exámenes | Las filas cuyo nombre es solo un número y no tienen laboratorio no se cargan y quedan anotadas en el reporte de revisión |
| El listado técnico está en actualización por el laboratorio | Los 41 tubos que la app no reconoce quedan como pendientes; mientras tanto la app los muestra como "Tubo: dato no disponible" y pide consultar |
| Muchas reglas clínicas dependían de decisiones que no estaban escritas | Antes de cada iteración se preguntó al tecnólogo médico y cada respuesta quedó en la documentación |
| Pasar el código ya hecho a clases sin cambiar el comportamiento | Las pruebas anteriores siguieron pasando y 40 pantallas comparadas quedaron idénticas |
| flake8 se aplicó recién al final y marcó 521 avisos | Se corrigieron todos (casi todos eran líneas largas) sin cambiar el comportamiento, y desde entonces GitHub Actions lo revisa en cada `push` |
| Detalles visuales que solo se ven al usar la app (una doble línea al seleccionar un campo, los pasos de la cabecera que se movían, textos repetidos en la pantalla de tubos) | Se corrigieron a partir de la revisión del equipo en el navegador |

## 5. Lecciones aprendidas

- **Los datos reales mandan.** La mayor parte del trabajo no fue programar las
  reglas, sino entender un listado que no fue hecho para leerlo con un
  programa.
- **Preguntar antes de programar.** Cada regla confirmada con el tecnólogo
  médico evitó rehacer código.
- **Ante la duda, advertir.** Mostrar "dato no disponible" es más seguro que
  adivinar, y además deja claro qué falta completar.
- **Las pruebas permiten cambiar con confianza.** Gracias a las pruebas se pudo
  reorganizar todo el código en clases, y después corregir 521 avisos de
  estilo, sin romper nada.
- **Las herramientas de calidad conviene usarlas desde el inicio.** Revisar el
  estilo con flake8 desde la primera iteración habría evitado una corrección
  grande al final.
- **Usar la app es la mejor revisión.** Varios problemas de la interfaz solo
  aparecieron al usarla con datos reales en el navegador, no en las pruebas
  automáticas.

## 6. Pendientes al cierre

| Pendiente | Responsable | Historia |
|---|---|---|
| Completar los 41 tubos de `data/tubos_por_revisar.csv` | Tecnólogo médico | HU-20 · Pendiente: el listado está en actualización por el laboratorio |
| Validar la app con casos reales | Tecnólogo médico | HU-20 · Pendiente, por la misma razón |
| Configurar y probar el correo real de la auditoría | Jared Estrada, Scherezade Huancapaza y Camila Pastene | HU-22 |
| Decidir si se quieren exámenes frecuentes primero en el buscador | Tecnólogo médico | HU-21 |

## 7. Mejoras futuras

Para un uso real en el hospital (detalle en [despliegue.md](despliegue.md)):

- Inicio de sesión, para que solo entre personal autorizado.
- Instalación en un servidor de la red interna, con un servidor web de
  producción, la hora de Chile y respaldos automáticos.
- Un procedimiento formal para actualizar el listado técnico y la librería
  de feriados.

Funcionalidades para versiones siguientes (fuera de la versión 1):

- Exámenes frecuentes primero en el buscador (HU-21, si el tecnólogo médico lo
  aprueba).
- Mostrar en cada sugerencia del buscador el tubo y el tipo de muestra, para
  distinguir exámenes de nombre parecido.
- Una columna propia para la estabilidad en el listado técnico, como lo
  propuso el tecnólogo médico.
- Trabajar con ramas y Pull Requests para cada funcionalidad, con revisión
  entre integrantes.
- Cálculo de volúmenes y fraccionamiento de muestras.
- Matronería, pacientes pediátricos, uso en celular e integración con la ficha
  clínica.

## 8. Conclusiones

**Se cumplió el objetivo del producto para la versión 1.** Preanalítica entrega
a la enfermera, en una sola pantalla y sin datos del paciente, los tubos que
debe usar, el orden de extracción, qué exámenes se derivan y si la muestra
derivada alcanzará a procesarse. Todo sale del listado técnico real del
laboratorio y está cubierto por 260 pruebas automáticas que corren en cada
cambio. Lo que falta para usarla de verdad no es código: es que el laboratorio
termine de actualizar su listado, que el tecnólogo médico complete los 41
tubos pendientes y valide la app con casos reales, y que el hospital decida
dónde instalarla y con qué inicio de sesión.

**Trabajar con un experto del dominio cambió la forma de construir el
software.** Las reglas de agrupación, el orden CLSI y los criterios de
estabilidad no se podían deducir del listado: había que preguntarlas. Cada
respuesta del tecnólogo médico quedó escrita y con su prueba, y eso permitió
avanzar sin rehacer trabajo. Los datos reales, por su parte, mostraron que el
problema no era solo de enfermería: el listado trae ambigüedades, errores y
datos incompletos. La app no los esconde; los marca como "dato no disponible"
y genera un reporte para que el laboratorio los corrija. Eso la convierte
también en una herramienta de control de calidad del listado.

**La regla más importante fue "ante la duda, advertir".** En un contexto
clínico, una respuesta equivocada que parece segura es peor que no responder.
Por eso la app nunca rellena un dato que falta, y cada decisión que podía
afectar a una paciente se discutió antes de programarla.

**Las iteraciones cortas y las pruebas automáticas dieron confianza para
cambiar.** Gracias a ellas se pudo reorganizar el código en clases con patrones
de diseño, corregir los errores que aparecieron con el listado real y ajustar
la interfaz sin romper lo que ya funcionaba. Si empezáramos de nuevo, usaríamos
flake8 y ramas con Pull Requests desde la primera iteración, y mostraríamos la
app en el navegador a sus usuarias más temprano.

**La asistencia de IA aceleró mucho el desarrollo**: permitió construir,
probar y documentar el proyecto en pocas iteraciones. Sus límites también
quedaron claros: no conoce las reglas del laboratorio ni puede validar si un
resultado clínico es correcto. Esas decisiones fueron siempre del tecnólogo
médico y del equipo, y la app solo muestra lo que el listado técnico respalda.
