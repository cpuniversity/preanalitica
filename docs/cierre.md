# Cierre del proyecto

> **Borrador.** Las secciones 1 a 7 reúnen lo que ya está documentado en el
> proyecto, para que el equipo las revise, corrija y complete. **Las
> conclusiones (sección 8) las escribe el equipo.**

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
- los avisos de ayuno y protección de la luz, con la frase del listado;
- qué exámenes se derivan y si la estabilidad de cada muestra alcanza hasta el
  día en que la procesa el laboratorio externo.

Cada consulta queda en una auditoría que se envía cada semana por correo a la
jefatura.

**El resultado en cifras.**

| | |
|---|---|
| Exámenes del listado cargados | 620 (173 se procesan en el recinto y 447 se derivan) |
| Historias de usuario | 19 con criterios de aceptación, más 4 tareas de la entrega final (HU-20 a HU-23); 75 de 81 puntos terminados |
| Iteraciones | I0 a I7 terminadas (31/10 al 02/11); I8 en curso |
| Pruebas automáticas | 257, todas pasan, también en GitHub Actions en cada `push` |
| Commits en `main` | 22, contando el de este borrador |
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
decisiones del tecnólogo médico. La validación con casos reales está pendiente
(sección 6).

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

### Técnicas (equipo)

| Decisión | Por qué |
|---|---|
| Nunca inventar un dato clínico: "dato no disponible" y advertir | Un error silencioso puede causar una punción repetida o una muestra rechazada |
| Importador separado del resto de la app | Si el listado llega en Excel o PDF, solo cambia el lector (patrón Strategy) |
| Reporte de revisión y tabla de tubos por revisar | El tecnólogo médico corrige el listado sin programar |
| Python, Flask y SQLite, sin servidor externo | Prototipo local, fácil de instalar y de explicar |
| Diseño orientado a objetos con patrones Repositorio y Strategy | Lo pide la pauta y separa responsabilidades (ver [arquitectura.md](arquitectura.md)) |
| Una funcionalidad a la vez, con pruebas antes de cada commit | Cada iteración dejó algo que funciona y está probado |
| Trabajo directo en `main`, sin Pull Request, con integración continua | Decisión del equipo; las pruebas en GitHub Actions reemplazan la revisión previa como red de seguridad |
| Desarrollo asistido por Claude Code | Aceleró la programación; las reglas clínicas siempre las definió el tecnólogo médico, y Claude Code aparece como coautor en los commits |

## 4. Dificultades y cómo se resolvieron

| Dificultad | Cómo se resolvió |
|---|---|
| El listado no es una tabla limpia: trae encabezados del documento antes de los títulos y mucho texto libre | El importador busca la fila de títulos y ubica cada columna por su nombre, no por su posición |
| Excel daña el listado (mete cada línea en una sola celda) y aparecen saltos de línea de Windows dentro de las celdas | Regla de nunca abrirlo con Excel; el importador limpia los saltos de línea |
| El tubo viene escrito de 145 formas distintas | La app reconoce las formas claras y las dudosas van a `tubos_por_revisar.csv` para el tecnólogo médico (46 exámenes pendientes; en I8 se corrigió la lectura de "1 frasco con muestra de deposición") |
| La estabilidad no tiene columna propia y se escribe de muchas maneras | Se lee del texto de las instrucciones; dos formatos que se leían mal se corrigieron y quedaron como pruebas |
| "glucosa" no encontraba la glicemia | Los sinónimos entre paréntesis pasaron a contar como nombre del examen |
| "1 frasco con muestra de deposición" se leía como sangre (la regla de "1 frasco" era para hemocultivo) | Si después del frasco viene una muestra que no es sangre, va a "Otras muestras"; se revisaron los 620 exámenes y solo cambió ese |
| Muchas reglas clínicas dependían de decisiones que no estaban escritas | Antes de cada iteración se preguntó al tecnólogo médico y cada respuesta quedó en la documentación |
| Pasar el código ya hecho a clases sin cambiar el comportamiento | Las pruebas anteriores siguieron pasando y 40 pantallas comparadas quedaron idénticas |
| [El equipo puede agregar otras dificultades: de organización, de tiempo, de coordinación] | |

## 5. Lecciones aprendidas

Borrador para que el equipo lo revise:

- **Los datos reales mandan.** La mayor parte del trabajo no fue programar las
  reglas, sino entender un listado que no fue hecho para leerlo con un
  programa.
- **Preguntar antes de programar.** Cada regla confirmada con el tecnólogo
  médico evitó rehacer código.
- **Ante la duda, advertir.** Mostrar "dato no disponible" es más seguro que
  adivinar, y además deja claro qué falta completar.
- **Las pruebas permiten cambiar con confianza.** Gracias a las 245 pruebas se
  pudo reorganizar todo el código en clases sin romper nada.
- [Lecciones del equipo]

## 6. Pendientes al cierre

| Pendiente | Responsable | Historia |
|---|---|---|
| Completar los 46 tubos de `data/tubos_por_revisar.csv` | Tecnólogo médico | HU-20 |
| Validar la app con casos reales | Tecnólogo médico | HU-20 |
| Configurar y probar el correo real de la auditoría | [por asignar] | HU-22 |
| Decidir si se quieren exámenes frecuentes primero en el buscador | Tecnólogo médico | HU-21 |
| Presentación final y conclusiones | Todo el equipo | HU-23 |

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
- Una columna propia para la estabilidad en el listado técnico, como lo
  propuso el tecnólogo médico.
- Cálculo de volúmenes y fraccionamiento de muestras.
- Pacientes pediátricos, uso en celular e integración con la ficha clínica.

## 8. Conclusiones

> **[Las escribe el equipo.]** Preguntas que pueden servir de guía:
>
> - ¿Se cumplió el objetivo del producto? ¿Qué falta para que la app se use de verdad?
> - ¿Qué aprendimos de trabajar con un experto del dominio y con datos reales?
> - ¿Qué haríamos distinto si empezáramos de nuevo?
> - ¿Cómo influyó trabajar en iteraciones cortas y con pruebas automáticas?
> - ¿Qué aporte tuvo y qué límites tuvo el uso de asistencia de IA en el desarrollo?
