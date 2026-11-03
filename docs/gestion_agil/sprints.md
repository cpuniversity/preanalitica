# Planificación y seguimiento

El desarrollo se organizó en **iteraciones cortas, una funcionalidad a la vez**,
en el orden definido al inicio del proyecto. Cada iteración siguió el mismo ciclo:

1. **Plan corto** de la funcionalidad.
2. **Preguntas al tecnólogo médico** sobre las reglas clínicas y espera de su confirmación.
3. **Código con pruebas automáticas.**
4. **Revisión en el navegador** con el listado real.
5. **Commit en GitHub.**

Las fechas y commits son los reales del repositorio (`git log`). Las
iteraciones duraron horas y no semanas: el desarrollo se hizo con asistencia
de Claude Code, que aparece como coautor en los commits. Algunas iteraciones
quedaron guardadas en un mismo commit (por ejemplo, I1 e I2).

## Resumen

| Iteración | Fecha | Objetivo | Historias | Puntos | Pruebas al cerrar | Commits |
|---|---|---|---|---|---|---|
| I0 | 31/10 | Estructura del proyecto e identificación | HU-01 | 2 | 24 | `199ba74` |
| I1 | 01/11 | Base de datos e importador del listado | HU-13 | 8 | 75 (junto con I2) | `c8acfd3` |
| I2 | 01/11 | Buscador de exámenes | HU-02, HU-03, HU-04 | 10 | 75 | `c8acfd3` |
| I3 | 01/11 | Agrupador de tubos y pantalla de resumen | HU-05 a HU-09, HU-14 | 21 | 143 | `2b37457`, `ee93d61`, `b00d810` |
| I4 | 01/11 | Derivaciones y estabilidad | HU-11, HU-12 | 11 | 201 | `bb6472c` |
| I5 | 01/11 | Auditoría | HU-15, HU-16 | 8 | 223 | `8125a3c`, `88613ef` |
| I6 | 01/11 | Pulido de interfaz y documentación | HU-10 | 2 | 235 | `07e2b55`, `cf7eea3`, `6288b71` |
| I7 | 02/11 | Diseño orientado a objetos y UML | HU-17 | 8 | 245 | `ab71eeb`, `9761577` |
| **I8** | **por definir** | **Entregables finales y validación** | HU-18 a HU-23 | 11 | — | — |

## Avance (burndown)

Puntos que quedaban por hacer al cerrar cada iteración. El total incluye lo
terminado (70) y lo pendiente para la entrega final (11), sin contar HU-21,
que espera la decisión del tecnólogo médico.

| Al cerrar | I0 | I1 | I2 | I3 | I4 | I5 | I6 | I7 |
|---|---|---|---|---|---|---|---|---|
| Puntos pendientes (de 81) | 79 | 71 | 61 | 40 | 29 | 21 | 19 | 11 |

## Detalle de cada iteración

### I0 · Estructura e identificación (31/10)
- **Hecho:** estructura de carpetas, app Flask mínima y pantalla de identificación.
- **Hallazgo en la revisión:** se podían ingresar números o signos como nombre. Se agregó una validación (solo letras, tildes, guion y apóstrofo) con sus pruebas.

### I1 · Base de datos e importador (01/11)
- **Hecho:** base SQLite, importación del listado CSV y reporte de revisión.
- **Decisiones del tecnólogo médico:** no considerar la vigencia del documento; sin sección en esta versión; el recinto es Dávila Vespucio (24/7); se usa el código más grande cuando hay varios; se excluyen las filas con "Lab. Derivado" no numérico.
- **Hallazgo:** el listado no es una tabla limpia (encabezados de documento, texto libre). El importador ubica cada columna por su título.

### I2 · Buscador (01/11)
- **Hecho:** buscador tolerante a errores y sin tildes, con sugerencias y selección de exámenes.
- **Ajuste posterior (I5):** "glucosa" no mostraba la glicemia; los sinónimos entre paréntesis pasaron a contar como nombre.

### I3 · Agrupador de tubos (01/11)
- **Hecho:** reglas de agrupación, orden CLSI, excepciones, otras muestras y tabla de tubos por revisar.
- **Decisiones del tecnólogo médico:** amarillo con gel y tapa amarilla son el mismo tubo; compartir solo con el mismo laboratorio; elegir el tubo que permite juntar exámenes; los "2 tubos" son del examen; hielo no se muestra; ayuno y luz como advertencia.
- **Hallazgos:** el tubo viene escrito de 145 formas; 47 exámenes quedan para que los complete el tecnólogo médico. Corrección de botones de distinto tamaño y de saltos de línea de Windows en el listado.

### I4 · Derivaciones y estabilidad (01/11)
- **Hecho:** día de proceso estimado, revisión de estabilidad y sugerencia de días de toma.
- **Decisiones del tecnólogo médico:** enfermería no almacena muestras; corte de las 15:00 en Vespucio y de las 8:00 en el laboratorio externo; feriados; refrigerada antes que ambiente; tipo de muestra según el tubo; "según demanda" sin veredicto.
- **Hallazgos:** dos formatos de estabilidad se leían mal (número antes de la temperatura y "sangre completa"); se corrigieron y quedaron como pruebas.

### I5 · Auditoría (01/11)
- **Hecho:** registro de cada consulta y envío semanal automático por correo (modo prueba por defecto).

### I6 · Pulido de interfaz (01/11)
- **Hecho:** textos de 17 px, panel fijo de seleccionados, etiqueta de estabilidad en cada tubo, ícono, títulos y páginas de error en español, impresión compacta.
- **Ajustes pedidos por el equipo:** sin punto final en los textos; botones solo al final; "tecnólogo médico" sin especialidad.

### I7 · Diseño orientado a objetos y UML (02/11)
- **Hecho:** la lógica pasó a clases del dominio con patrones (Repositorio, Strategy) y SOLID; diagramas de casos de uso, secuencia y clases; matriz de trazabilidad.
- **Verificación:** las pruebas anteriores siguen pasando y 40 pantallas comparadas con la versión anterior son idénticas.

## Próxima iteración · I8 (planificada)

**Objetivo:** completar los entregables finales de la pauta y validar la app con el tecnólogo médico.
**Fecha límite:** [fecha de la EVA4]

| Historia o tarea | Responsable | Estado |
|---|---|---|
| HU-18 CI con GitHub Actions y plan de pruebas | [por asignar] | ✔ Hecha (02/11) |
| HU-19 Plan de despliegue y operación | [por asignar] | Por hacer |
| HU-20 Completar los 47 tubos y validar con casos reales | Tecnólogo médico | Por hacer |
| HU-22 Configurar el correo real | [por asignar] | Por hacer |
| HU-23 Cierre del proyecto y presentación final | Todo el equipo | Por hacer |
| Mostrar el avance al ayudante e incorporar su retroalimentación | Todo el equipo | Por hacer |

**Forma de trabajo en I8:** los cambios se hacen directamente en `main`, uno por
commit, con las pruebas automáticas pasando antes de cada commit.
