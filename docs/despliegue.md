# Plan de despliegue y operación

Este documento describe qué se necesitaría para pasar Preanalítica del
prototipo local a un uso real en el hospital: ambientes, instalación, entrega
de nuevas versiones, respaldos, monitoreo, mantenimiento e impacto en las
usuarias (HU-19).

**Es un plan, no algo implementado.** La versión 1 es un prototipo que corre en
un computador. La instalación en un servidor del hospital y el inicio de sesión
están fuera de la versión 1 (ver `requisitos.md`, sección 6). Lo marcado como
**[por definir]** lo deben decidir la jefatura de laboratorio, el tecnólogo
médico y el área de informática del hospital.

## 1. Ambientes

| Ambiente | Para qué | Dónde | Datos | Correo de auditoría |
|---|---|---|---|---|
| **Desarrollo** | Programar y probar cada cambio | Computador del equipo, `flask --app app run --debug` | Listado real en `data/` (fuera de Git) | Modo prueba: se guarda como `.eml` en `data/` |
| **Integración continua** | Correr todas las pruebas en cada `push` | GitHub Actions (Linux) | Solo exámenes inventados | Nunca se envía |
| **Validación** | Que el tecnólogo médico revise casos reales antes de cada versión (HU-20) | Un computador del laboratorio, con la misma versión que irá a producción | Listado real vigente | Modo prueba |
| **Producción** (propuesta) | Uso diario de enfermería | Servidor de la red interna del hospital **[por definir]** | Listado real validado | Modo real, con el servidor de correo del hospital |

Producción nunca se usa para probar: todo cambio pasa antes por desarrollo,
integración continua y validación.

## 2. Recursos necesarios

| Recurso | Necesidad | Comentario |
|---|---|---|
| Servidor | Uno pequeño, Windows o Linux, con Python 3.13 | La app es liviana: un listado de unos 290 KB y una base SQLite de unos 370 KB |
| Red | Accesible solo desde la red interna del hospital | Sin inicio de sesión, no debe quedar expuesta a internet |
| Navegador | Cualquier navegador actual de escritorio en los computadores de enfermería | La letra IBM Plex Sans se descarga de Google Fonts; si la red la bloquea, se ve con la letra del sistema |
| Correo | Una cuenta del servidor de correo del hospital para enviar la auditoría | Datos en `.env` (`SMTP_SERVIDOR`, `SMTP_USUARIO`, `SMTP_CLAVE`) |
| Espacio para respaldos | Una carpeta en otro equipo o unidad de red **[por definir]** | Ver sección 5 |
| Personas | Responsable técnico de la app y tecnólogo médico responsable del listado **[por definir]** | Ver sección 8 |

## 3. Requisitos antes de usarla en el hospital

Estos puntos no son necesarios en el prototipo, pero sí para un uso real:

1. **Inicio de sesión.** Hoy cualquier persona con acceso a la red podría
   abrir la app. Para producción se necesita que solo entre personal
   autorizado. Es una funcionalidad nueva, fuera de la versión 1.
2. **Clave de la sesión.** La app usa una clave de desarrollo si no existe la
   variable `SECRET_KEY`. En producción se debe definir una clave larga y
   secreta en el `.env`.
3. **Hora de Chile en el servidor.** La app usa la fecha y hora del equipo
   donde corre para el corte de las 15:00, el de las 8:00 y los feriados. El
   servidor debe tener la zona horaria de Chile continental, con los cambios
   de horario de verano, y la hora sincronizada automáticamente.
4. **Servidor web de producción.** `flask run` es un servidor solo para
   desarrollo. En producción se usaría un servidor web para Python, por
   ejemplo **waitress** (funciona en Windows). Sería una librería nueva y se
   debe aprobar antes de agregarla. Además, hoy el `.env` lo carga el comando
   `flask`; con otro servidor web, la app tendría que cargarlo ella misma al
   iniciar (con `python-dotenv`, que ya está instalada).
5. **Un solo proceso.** El envío automático de la auditoría se coordina dentro
   de la app. Para no arriesgar envíos repetidos, la app debe correr en un
   solo proceso (waitress funciona así por defecto).

## 4. Instalación y entrega de nuevas versiones

### Primera instalación

```
git clone https://github.com/cpuniversity/preanalitica.git
cd preanalitica
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env          # completar correo real y SECRET_KEY
pytest                          # deben pasar todas
flask --app app importar data/listado_tecnico.csv
```

Después se revisa el reporte de revisión con el tecnólogo médico y se inicia
la app con el servidor web de producción.

### Estrategia de entrega

- **`main` siempre funciona.** Solo se sube a `main` lo que pasa las pruebas,
  y GitHub Actions lo confirma en cada `push`.
- **Versiones con nombre.** Cada versión que va a producción se marca en Git
  con una etiqueta (`v1.0`, `v1.1`, ...), así se sabe exactamente qué código
  está instalado.
- **Validación antes de instalar.** El tecnólogo médico revisa la versión
  nueva en el ambiente de validación con casos reales.
- **Instalación fuera del horario de más uso** **[por definir con
  enfermería]**, avisando antes a las usuarias.

### Pasos para instalar una versión nueva

1. Respaldar la base y la carpeta `data/` (sección 5).
2. `git fetch` y `git checkout v1.1` (la versión aprobada).
3. `pip install -r requirements.txt` (por si cambió alguna librería).
4. `pytest`: si alguna falla, no se instala.
5. Reiniciar la app y abrir la pantalla de ingreso para comprobar que responde.

### Volver atrás

Si la versión nueva tiene un problema: `git checkout` de la versión anterior,
restaurar el respaldo de la base del paso 1 y reiniciar la app.

## 5. Respaldos

| Qué | Por qué importa | Frecuencia |
|---|---|---|
| `data/preanalitica.db` | Exámenes cargados y auditoría de la semana en curso | Diaria |
| `data/tubos_por_revisar.csv` | Trabajo del tecnólogo médico: los tubos que completó a mano | Cada vez que se modifica |
| `data/listado_tecnico.csv` | Listado vigente; permite volver a importarlo | Cada vez que cambia |
| `data/auditoria_<lunes>.csv` | Respaldo local de cada auditoría enviada | Semanal, después del envío |
| `.env` | Configuración del correo y clave de la sesión | Cada vez que cambia, guardado en un lugar seguro: tiene claves |

- El código no necesita respaldo aparte: está en GitHub.
- La base SQLite se debe copiar con la herramienta de respaldo de SQLite (o
  con la app detenida), no copiando el archivo mientras se escribe.
- Los respaldos se guardan en otro equipo o unidad de red **[por definir]** y
  se conservan **[plazo por definir con la jefatura]**.
- Una vez al mes se prueba restaurar un respaldo en el ambiente de validación:
  un respaldo que nunca se probó no se sabe si sirve.

## 6. Monitoreo

| Qué se vigila | Cómo | Quién |
|---|---|---|
| La app responde | Abrir la pantalla de ingreso al inicio de cada turno, o una revisión automática que la consulte cada pocos minutos **[por definir]** | Responsable técnico |
| Llegó la auditoría semanal | La jefatura recibe el correo cada lunes. Si no llega, avisar: la app no borra nada si el envío falla y reintenta cada hora | Jefatura de laboratorio |
| Errores de la app | La app escribe sus avisos (por ejemplo, "No se pudo enviar la auditoría semanal") en su registro. En producción se guardaría en un archivo y se revisaría cada semana | Responsable técnico |
| Espacio en disco | Que los respaldos y los CSV de auditoría no llenen el disco | Responsable técnico |
| Calidad del código | GitHub Actions marca cada `push` con ✔ o ✘ | Equipo de desarrollo |
| Reclamos de enfermería | Un canal simple para avisar si un resultado parece incorrecto **[por definir]** | Tecnólogo médico |

El registro de la app nunca debe mostrar el contenido del listado ni datos de
pacientes (la app no los tiene).

## 7. Mantenimiento

| Tipo | Ejemplos en Preanalítica | Cuándo |
|---|---|---|
| **Del listado** | El laboratorio actualiza el listado técnico (INSVE 02000) | Cada vez que se publica una versión nueva |
| **Adaptativo** | Actualizar la librería `holidays` para que conozca los feriados nuevos; actualizar Python y Flask | Al menos una vez al año y cada vez que se declare un feriado nuevo |
| **Preventivo** | Actualizaciones de seguridad del servidor y de las librerías; probar los respaldos | Mensual |
| **Correctivo** | Corregir un error informado por enfermería o el tecnólogo médico, siempre con una prueba nueva que lo cubra | Cuando ocurra |
| **Evolutivo** | Funcionalidades nuevas, como los exámenes frecuentes primero (HU-21) o el inicio de sesión | Según el backlog |

### Procedimiento para actualizar el listado técnico

1. Guardar una copia de respaldo del listado anterior.
2. Copiar el listado nuevo en `data/listado_tecnico.csv`. **Nunca abrirlo ni
   guardarlo con Excel:** lo daña. Para corregirlo se usa el Bloc de notas.
3. Verificar que tenga las mismas columnas que el anterior.
4. Importarlo en el ambiente de validación:
   `flask --app app importar data/listado_tecnico.csv`.
5. Revisar con el tecnólogo médico `data/reporte_revision.csv` y los tubos
   nuevos de `data/tubos_por_revisar.csv` (lo ya completado se conserva).
6. Con su aprobación, repetir la importación en producción.

### Feriados

Los feriados de Chile vienen dentro de la librería `holidays` (versión 0.107
en el prototipo). Si se declara un feriado nuevo por ley, la app no lo conoce
hasta actualizar la librería. Mientras tanto, la revisión de estabilidad podría
suponer que un laboratorio externo recibe ese día. Por eso, cada vez que se
anuncie un feriado nuevo, se actualiza `holidays`, se corren las pruebas y se
instala como una versión nueva.

## 8. Responsables

| Rol | Responsabilidad | Persona |
|---|---|---|
| Responsable técnico | Instalación, versiones, respaldos, monitoreo | [por definir] |
| Tecnólogo médico responsable | Reglas clínicas, listado técnico, tabla de tubos, validación de cada versión | [por definir] |
| Jefatura de laboratorio y de sección | Recibir y revisar la auditoría semanal; aprobar el paso a producción | [por definir] |
| Informática del hospital | Servidor, red, correo, zona horaria y acceso | [por definir] |

## 9. Impacto en las usuarias

**Capacitación.** La app tiene tres pantallas y no pide datos del paciente.
Bastaría una demostración corta en cada servicio y una hoja con los tres
pasos (identificarse, buscar los exámenes, ver los tubos).

**Puesta en marcha gradual.** Se propone empezar con un solo servicio
**[por definir]** durante algunas semanas, recoger comentarios y corregir antes
de extenderla al resto.

**Qué cambia para la enfermera.** Deja de buscar en el listado técnico cada
examen: ve los tubos en orden, los avisos de ayuno y luz, y si la muestra
derivada alcanza. Las decisiones clínicas siguen siendo suyas y del
laboratorio: la app informa y advierte; ante la duda indica consultar con el
laboratorio.

**Si la app no está disponible.** Enfermería sigue con el procedimiento
actual (consultar el listado técnico o llamar al laboratorio). La app nunca
debe ser la única forma de saber qué tubo usar.

**Comentarios.** Durante la puesta en marcha, las enfermeras y matronas
pueden informar resultados que les parezcan incorrectos. El tecnólogo médico
los revisa y, si corresponde, se corrige con una prueba nueva.

**Turnos de noche.** La interfaz ya está pensada para ellos: letra grande,
botones grandes y nunca solo el color. Conviene confirmar en la puesta en
marcha que se lee bien con la luz de esos turnos.
