# Objetivo del producto

## Objetivo

> Que una enfermera, en pocos segundos y sin ingresar datos del
> paciente, sepa qué tubos usar, en qué orden extraerlos y si cada examen
> derivado alcanzará a procesarse antes de que venza su estabilidad, usando
> solo la información del listado técnico del laboratorio.

## Visión

| | |
|---|---|
| **Para** | enfermeras que toman muestras a pacientes adultos, muchas veces en turno de noche y con poco tiempo |
| **Que necesitan** | traducir la indicación médica en tubos, orden de extracción y exámenes que se derivan, sin errores que obliguen a repetir la punción |
| **Preanalítica es** | una aplicación web local |
| **Que** | busca los exámenes aunque estén mal escritos, agrupa los tubos según las reglas del laboratorio, los ordena según CLSI y advierte cuando una muestra derivada podría ser rechazada |
| **A diferencia de** | consultar a mano el listado técnico (largo, en texto libre y sin cálculo de estabilidad) |
| **Nuestro producto** | nunca inventa un dato clínico: si falta, lo dice y pide consultar con el laboratorio |

## Roles

| Rol | Quién |
|---|---|
| Dueño del producto (*Product Owner*) | Tecnólogo médico: define y prioriza las reglas clínicas |
| Equipo de desarrollo | Jared Estrada, Scherezade Huancapaza, Camila Pastene |
| Usuarias finales | Enfermeras |
| Interesados (*stakeholders*) | Jefatura de laboratorio y de sección (reciben la auditoría) |

## Medidas de éxito

- La enfermera obtiene el resumen de tubos sin escribir el nombre completo de los exámenes.
- Ningún tubo, estabilidad ni día de proceso aparece sin estar en el listado técnico.
- Toda regla clínica tiene una prueba automática que pasa.
- Cada consulta queda en la auditoría, sin datos del paciente.
