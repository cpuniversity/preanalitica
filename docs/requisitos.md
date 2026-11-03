# Preanalítica: requisitos y estado del proyecto

Prototipo para el curso Ingeniería de Software (UDP). Noviembre 2026.

## 1. Propósito

Ayudar al personal de enfermería y matronería a preparar la toma de muestras. A partir de los exámenes que indica el médico, la aplicación muestra:

- qué tubos usar y en qué orden extraerlos,
- qué exámenes se procesan en el laboratorio del recinto y cuáles se derivan,
- si la muestra de un examen derivado alcanzará a procesarse antes de que venza su estabilidad.

## 2. Usuarios

| Usuario | Rol |
|---|---|
| Enfermera o matrona | Usa la aplicación, muchas veces en turno de noche y con poco tiempo |
| Tecnólogo médico | Dueño del dominio: define y valida las reglas clínicas |
| Jefatura de laboratorio y de sección | Recibe la auditoría semanal por correo |

## 3. Requisitos funcionales

### RF-1 Identificación
- La enfermera escribe su nombre y apellido antes de buscar. Solo se aceptan letras (con tildes, ñ y ü), espacios, guion y apóstrofo.
- La aplicación nunca pide datos del paciente (nombre, RUT ni ficha).

### RF-2 Buscador de exámenes
- Muestra hasta 8 sugerencias mientras se escribe; nunca elige un examen por sí sola.
- Funciona sin escribir el nombre completo, con o sin tildes y con errores de tipeo.
- Busca también en los sinónimos entre paréntesis, que cuentan como nombre del examen (por ejemplo, "glucosa" encuentra "GLICEMIA (GLUCOSA EN SANGRE)").
- Cada sugerencia indica si el examen se procesa en el recinto o se deriva (y a qué laboratorio).

### RF-3 Agrupación de tubos y orden de extracción
- Comparten tubo los exámenes con el mismo tipo de tubo y el mismo laboratorio.
- Si un examen admite varios tubos, se elige el que permite juntarlo con otro examen.
- Los tubos se numeran según el orden de extracción CLSI: hemocultivo, celeste, amarillo con gel, rojo, verde, jeringa de gases venosos, lila, gris.
- Hemocultivo y gases van en su propio contenedor; los gases arteriales son una punción aparte, fuera del orden.
- Las muestras que no son sangre (orina, deposición, etc.) se muestran en "Otras muestras".
- Advertencias: ayuno y protección de la luz, con la frase original del listado.

### RF-4 Derivaciones y estabilidad
- Para cada examen derivado se muestra: días de proceso del laboratorio externo, el día en que se procesaría si la muestra se toma ahora y cuántos días esperaría guardada.
- Se compara esa espera con la estabilidad del listado y se informa: "la estabilidad lo permite", "al límite, consultar con el laboratorio" o "NO alcanza" (con alerta destacada y sugerencia de días de toma).
- Considera la hora de corte de recepción en Vespucio (15:00), el proceso el mismo día solo antes de las 8:00 y los feriados de Chile en los laboratorios externos.

### RF-5 Resumen e impresión
- Total de tubos, tubos numerados con su laboratorio y sus exámenes, avisos, otras muestras y exámenes derivados.
- Botones "Volver a exámenes", "Imprimir resumen" y "Nueva consulta".

### RF-6 Auditoría
- Se registra cada resumen entregado: fecha y hora, enfermera, exámenes y resultado. Sin datos de pacientes.
- Cada semana la aplicación envía sola por correo un CSV con el historial de la semana anterior y luego lo borra de la base (solo si el envío salió bien).

### RF-7 Importación del listado técnico
- Comando `flask --app app importar data/listado_tecnico.csv`.
- Genera un reporte de revisión (`data/reporte_revision.csv`) y una tabla de tubos por revisar (`data/tubos_por_revisar.csv`) para el tecnólogo médico.

## 4. Reglas clínicas no negociables

- La aplicación nunca inventa tubos, estabilidades ni días de proceso: todo sale del listado técnico.
- Si falta un dato, se muestra "dato no disponible" y se pide consultar con el laboratorio.
- Ante la duda, la aplicación advierte; no decide en silencio.
- Cada regla y excepción tiene una prueba automática.

## 5. Requisitos no funcionales

- Interfaz para turnos de noche: letra de al menos 17 px, botones de 56 px, colores con texto (nunca solo color).
- Solo escritorio y solo adultos.
- El listado real, la base de datos y la auditoría no se suben a Git.
- Accesibilidad: navegación con teclado, alertas anunciadas a lectores de pantalla.

## 6. Fuera de la versión 1

- Cálculo de volúmenes y fraccionamiento de muestras.
- Reglas por sección del laboratorio (el listado no trae sección).
- Día de envío de las muestras (es tarea del laboratorio).
- Pacientes pediátricos, uso en celular, integración con la ficha clínica.
- Inicio de sesión con contraseña e instalación en un servidor de producción.

## 7. Decisiones del tecnólogo médico

Todas las decisiones están detalladas en `CLAUDE.md`. Resumen:

| Tema | Decisión |
|---|---|
| Recinto | Laboratorio Clínica Dávila Vespucio, 24/7; los demás son de derivación |
| Sección | No se usa en esta versión |
| Tubo con gel / tapa amarilla | Son el mismo tubo; el rojo es distinto |
| Compartir tubo | Mismo tubo y mismo laboratorio |
| Varios tubos posibles | El que permite juntar; si no, amarillo antes que rojo |
| "2 tubos" en el listado | Son solo de ese examen y se suman al total |
| Hielo | No se muestra a enfermería |
| Estabilidad | Refrigerada; si no hay, ambiente; la del tipo de muestra del tubo |
| "Según demanda" | Sin veredicto; se muestra el tiempo de respuesta |
| Feriados | Los laboratorios externos no reciben; Vespucio sí |
| Códigos repetidos en una celda | Se usa el número más grande |
| "Lab. Derivado" no numérico | El examen no se considera |
| Auditoría | CSV semanal, envío automático, modo prueba por defecto |

## 8. Estado actual

Las seis etapas de la versión 1 están implementadas y con pruebas automáticas (245 pruebas, todas pasan). La lógica está organizada en clases del dominio; ver `docs/arquitectura.md` y los diagramas UML en `docs/uml/`:

| Etapa | Estado |
|---|---|
| Base de datos e importador | Completa |
| Buscador | Completa |
| Agrupador de tubos | Completa |
| Derivaciones y estabilidad | Completa |
| Auditoría | Completa (en modo prueba) |
| Pulido de interfaz | Completa |

GitHub Actions corre las pruebas en cada `push` (`.github/workflows/pruebas.yml`). El plan de pruebas y el informe de resultados están en `docs/plan_de_pruebas.md` y `docs/informe_de_pruebas.md`.

Datos del listado actual: 620 exámenes (173 se procesan en el recinto y 447 se derivan).

## 9. Pendientes

Con el tecnólogo médico:
- Completar los 47 exámenes de `data/tubos_por_revisar.csv` (guía en `docs/tabla_de_tubos.md`). Mientras tanto aparecen como "Tubo: dato no disponible".
- Revisar el reporte de revisión, en especial los derivados sin estabilidad en el listado.
- Probar la aplicación con casos reales y validar los resultados de agrupación, orden y estabilidad.
- Decidir si se quiere una lista de exámenes frecuentes que aparezcan primero en el buscador.

Del equipo:
- Revisar la impresión del resumen.
- Configurar el servidor de correo real en `.env` cuando corresponda.

Para un uso real (fuera de la versión 1): inicio de sesión, instalación en un servidor del hospital, respaldos y un procedimiento para actualizar el listado.
