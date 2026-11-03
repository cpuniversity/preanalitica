# Product Backlog

Lista priorizada del producto. El detalle y los criterios de aceptación de cada
historia están en [historias.md](historias.md).

- **Prioridad (MoSCoW):** *Must* (imprescindible), *Should* (importante), *Could* (deseable), *Won't* (no en esta versión).
- **Puntos:** estimación del tamaño relativo (1, 2, 3, 5, 8). **Son una propuesta**, hecha según la complejidad real que tuvo cada historia; el equipo debe revisarlos y ajustarlos.
- **Iteración:** en qué iteración se terminó (ver [sprints.md](sprints.md)).

## Versión 1: terminadas

| ID | Historia | Épica | Prioridad | Puntos | Iteración | Estado |
|---|---|---|---|---|---|---|
| HU-01 | Identificarse sin datos del paciente | E1 Identificación | Must | 2 | I0 | ✔ Terminada |
| HU-13 | Cargar el listado técnico con reporte de revisión | E5 Datos | Must | 8 | I1 | ✔ Terminada |
| HU-02 | Encontrar un examen aunque lo escriba mal | E2 Búsqueda | Must | 5 | I2 | ✔ Terminada |
| HU-03 | Saber si el examen se procesa aquí o se deriva | E2 Búsqueda | Must | 2 | I2 | ✔ Terminada |
| HU-04 | Armar la lista de exámenes de la indicación | E2 Búsqueda | Must | 3 | I2 | ✔ Terminada |
| HU-05 | Saber cuántos tubos usar (agrupación) | E3 Tubos | Must | 8 | I3 | ✔ Terminada |
| HU-06 | Extraer en el orden CLSI | E3 Tubos | Must | 3 | I3 | ✔ Terminada |
| HU-07 | Contenedores especiales (hemocultivo, gases) | E3 Tubos | Must | 3 | I3 | ✔ Terminada |
| HU-08 | Avisos de ayuno y luz | E3 Tubos | Should | 2 | I3 | ✔ Terminada |
| HU-09 | Otras muestras aparte | E3 Tubos | Should | 2 | I3 | ✔ Terminada |
| HU-14 | Completar los tubos que la app no reconoce | E5 Datos | Should | 3 | I3 | ✔ Terminada |
| HU-11 | Saber si la muestra derivada alcanza | E4 Derivaciones | Must | 8 | I4 | ✔ Terminada |
| HU-12 | Saber cuándo tomarla si no alcanza | E4 Derivaciones | Should | 3 | I4 | ✔ Terminada |
| HU-15 | Registrar cada consulta | E6 Auditoría | Must | 3 | I5 | ✔ Terminada |
| HU-16 | Recibir el historial semanal | E6 Auditoría | Must | 5 | I5 | ✔ Terminada |
| HU-10 | Imprimir el resumen | E3 Tubos | Should | 2 | I6 | ✔ Terminada |
| HU-17 | Código en clases con UML | E7 Calidad | Must (pauta) | 8 | I7 | ✔ Terminada |

**Total terminado: 70 puntos.**

## Pendientes para la entrega final (EVA4)

| ID | Historia o tarea | Épica | Prioridad | Puntos | Iteración | Estado |
|---|---|---|---|---|---|---|
| HU-18 | Pruebas automáticas en cada cambio (CI) y plan de pruebas | E7 Calidad | Must (pauta) | 2 | I8 | ✔ Terminada |
| HU-19 | Plan de despliegue y operación | E7 Calidad | Must (pauta) | 3 | I8 | ✔ Terminada |
| HU-20 | El tecnólogo médico completa los 47 tubos y valida con casos reales | E5 Datos | Must | 2 | I8 | Por hacer (depende del tecnólogo médico) |
| HU-22 | Configurar el correo real de la auditoría | E6 Auditoría | Should | 1 | I8 | Por hacer |
| HU-23 | Cierre del proyecto y presentación final | E7 Calidad | Must (pauta) | 3 | I8 | En curso (borrador de cierre) |
| HU-21 | Exámenes frecuentes primero en el buscador | E2 Búsqueda | Could | 2 | — | Esperando decisión del tecnólogo médico |

## Fuera de la versión 1 (Won't)

| Idea | Motivo |
|---|---|
| Inicio de sesión con contraseña | Prototipo local; necesario para un uso real en el hospital |
| Instalación en un servidor de producción | Se describe en el plan de despliegue (HU-19), no se implementa |
| Cálculo de volúmenes y fraccionamiento de muestras | Fuera del alcance definido |
| Reglas por sección del laboratorio | El listado no trae sección |
| Día de envío de las muestras | Es tarea del laboratorio, no de enfermería |
| Pacientes pediátricos, uso en celular, integración con la ficha clínica | Fuera del alcance definido |
