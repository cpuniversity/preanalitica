# Plan de pruebas

Este documento explica qué se prueba en Preanalítica, cómo se prueba y cuándo
se considera que la aplicación está lista. Los resultados están en
[informe_de_pruebas.md](informe_de_pruebas.md).

## 1. Objetivo

Asegurar que la aplicación entregue a enfermería **la misma respuesta que daría
el tecnólogo médico**: los tubos correctos, en el orden correcto, con las
advertencias que corresponden y con una revisión de estabilidad confiable para
los exámenes derivados. Ante la duda, la aplicación debe advertir; nunca debe
inventar un dato.

## 2. Qué se prueba y qué no

**Se prueba:** los requisitos funcionales RF-1 a RF-7, las reglas clínicas del
tecnólogo médico (agrupación de tubos, excepciones, estabilidad) y los
requisitos no funcionales que se pueden comprobar con un programa (no guardar
datos de pacientes, textos sin punto final, páginas de error en español).

**No se prueba en esta versión:** lo que está fuera del alcance de la versión 1
(volúmenes, sección del laboratorio, pediatría, celular, ficha clínica,
inicio de sesión).

## 3. Tipos de prueba

| Tipo | Qué revisa | Cómo | Quién |
|---|---|---|---|
| Unitarias | Una clase o función por separado: leer un tubo, leer una estabilidad, calcular el día de proceso, agrupar tubos | `pytest`, sin base de datos ni pantallas | Automática |
| De integración | Varias partes juntas: el importador lee un CSV y llena la base; el repositorio entrega los exámenes | `pytest`, con un CSV inventado y una base temporal | Automática |
| Funcionales (de pantalla) | Lo que ve la enfermera: ingreso, buscador, resumen de tubos, auditoría | `pytest` con el cliente de prueba de Flask, que "navega" la app sin abrir el navegador | Automática |
| Integración continua | Que todas las pruebas anteriores pasen en cada cambio subido a GitHub | GitHub Actions (`.github/workflows/pruebas.yml`) | Automática |
| Revisión en el navegador | Tamaños, colores, teclado, impresión y el listado real | Lista de revisión de la sección 7 | Equipo |
| De aceptación | Que los resultados sean correctos con casos reales | Casos del tecnólogo médico (HU-20) | Tecnólogo médico |

## 4. Ambiente y datos de prueba

- **Exámenes inventados.** Las pruebas nunca usan el listado real ni la base de
  `data/`. Cada prueba crea su propia base temporal, que se borra al terminar
  (`tests/conftest.py`).
- **Fechas fijas.** Las pruebas de derivaciones usan fechas de noviembre de
  2026 (lunes 2, jueves 5, viernes 6, sábado 7, domingo 8 y lunes 9), así el
  resultado no cambia según el día en que se corren.
- **Correo en modo prueba.** Ninguna prueba envía un correo real. El envío por
  servidor de correo se prueba con un servidor simulado.
- **Mismo ambiente en todos lados.** Las pruebas se corren en el computador
  (Windows, Python 3.13) y en GitHub Actions (Linux, Python 3.13), sin
  necesitar el archivo `.env` ni la carpeta `data/`.

## 5. Requisitos y sus pruebas

| Requisito | Archivo de pruebas | Ejemplos de casos |
|---|---|---|
| RF-1 Identificación | `test_ingreso.py` | Sin nombre no avanza; nombre con números no avanza; nombres con tilde, guion o apóstrofo sí avanzan; sin identificarse no se entra al paso 2 |
| RF-2 Buscador | `test_buscador.py` | Encuentra sin tildes, con errores de tipeo, con palabras incompletas y por sinónimo entre paréntesis; no autoselecciona; máximo 8 sugerencias; cada sugerencia dice si se procesa en el recinto o se deriva |
| RF-3 Tubos y orden | `test_agrupador.py`, `test_tubos.py` | Ver la tabla de la sección 6 |
| RF-4 Derivaciones y estabilidad | `test_derivaciones.py` | Corte de las 15:00; proceso el mismo día solo antes de las 8:00; feriados; refrigerada antes que ambiente; "según demanda" sin veredicto; "NO alcanza" con sugerencia de días |
| RF-5 Resumen e impresión | `test_interfaz.py`, `test_buscador.py` | Tubos agrupados y ordenados; botones una sola vez al final; etiqueta de estabilidad en el tubo del derivado |
| RF-6 Auditoría | `test_auditoria.py` | Ver los tubos queda registrado; recargar no duplica; la tabla no tiene datos del paciente; si el correo falla no se borra nada; semana de lunes a domingo |
| RF-7 Importación | `test_importador.py` | Encuentra los títulos después del encabezado del documento; limpia los saltos de línea de Windows; avisa campos vacíos y duplicados; excluye "Lab. Derivado" no numérico; usa el código más grande; la consola muestra solo conteos |
| Diseño orientado a objetos | `test_clases.py` | Clases del dominio y patrones Repositorio y Strategy (otro lector de listado, correo de prueba o real) |
| Textos sin punto final | `test_interfaz.py` | Filtro `sin_punto` y textos de la pantalla de tubos |

## 6. Reglas del tecnólogo médico y sus pruebas

Cada regla de agrupación y cada excepción tiene al menos una prueba con un caso
que el tecnólogo médico considera correcto.

| Regla | Prueba (`tests/test_agrupador.py`, salvo que se indique otro archivo) |
|---|---|
| Mismo tubo y mismo laboratorio comparten tubo | `test_mismo_tubo_y_mismo_laboratorio_comparten_tubo`, `test_dos_derivados_al_mismo_laboratorio_comparten_tubo` |
| Distinto laboratorio, distinto tubo | `test_mismo_tubo_recinto_y_derivado_van_en_tubos_distintos`, `test_mismo_tubo_dos_laboratorios_externos_distintos_van_aparte` |
| Si admite varios tubos, el que permite juntar; si no, amarillo antes que rojo | `test_elige_el_tubo_que_permite_juntarse_con_otro_examen`, `test_sin_con_quien_juntarse_elige_el_primero_amarillo_antes_que_rojo` |
| Amarillo con gel y tapa amarilla son el mismo tubo; el rojo es distinto | `test_tubos.py`: `test_reconoce_el_tubo`, `test_sin_gel_no_es_amarillo` |
| "2 tubos" son solo de ese examen | `test_dos_tubos_de_un_examen_mas_uno_de_otro_son_tres` |
| Orden de extracción CLSI | `test_orden_de_extraccion_clsi` |
| Hemocultivo en su propia botella | `test_hemocultivo_nunca_se_comparte` |
| Gases venosos en su jeringa; arteriales, punción aparte | `test_gases_venosos_nunca_se_comparten`, `test_gases_arteriales_son_puncion_aparte_fuera_del_orden` |
| Otras muestras fuera del orden | `test_otras_muestras_van_aparte_y_no_cuentan_como_tubo` |
| Protección de la luz como advertencia sobre el tubo | `test_proteccion_de_la_luz_es_advertencia_sobre_el_tubo_completo` |
| Ayuno con la frase original del listado | `test_ayuno_es_advertencia_con_la_frase_del_listado` |
| Hielo no se muestra | `test_hielo_no_se_muestra_a_enfermeria` |
| Solo la parte de adultos | `test_tubos.py`: `test_solo_se_considera_la_parte_de_adultos` |
| Tubo no reconocido: "dato no disponible", sin adivinar | `test_tubo_no_disponible_se_avisa_y_no_se_adivina`, `test_tubos.py`: `test_si_no_es_claro_no_adivina` |
| Estabilidad según el tipo de muestra del tubo | `test_derivaciones.py`: `test_se_usa_la_estabilidad_del_tipo_de_muestra_del_tubo`, `test_lila_sangre_total_y_plasma_son_lo_mismo_se_usa_la_mas_corta` |
| Refrigerada; si no hay, ambiente; congelada solo se informa | `test_derivaciones.py`: `test_sin_refrigerada_se_usa_la_ambiente`, `test_solo_congelada_no_se_usa_para_decidir` |
| Sin estabilidad: "dato no disponible" | `test_derivaciones.py`: `test_sin_estabilidad_es_dato_no_disponible` |

## 7. Revisión en el navegador (manual)

Hay cosas que un programa no puede juzgar bien. Después de cada funcionalidad
nueva, una persona del equipo revisa con el listado real:

- [ ] El texto se lee bien (al menos 17 px) y los botones principales miden 56 px
- [ ] Cada tubo y cada etiqueta tienen texto, no solo color
- [ ] Se puede usar toda la app solo con el teclado (Tab y Enter)
- [ ] El resumen impreso cabe y se entiende
- [ ] Al importar el listado real, la consola muestra solo conteos, sin datos de exámenes
- [ ] Un caso con exámenes del recinto, un derivado y una otra muestra da el resultado esperado

## 8. Criterios de aprobación

- **Todas** las pruebas automáticas pasan, en el computador y en GitHub Actions.
  Un solo fallo detiene el cambio hasta corregirlo.
- Toda regla clínica nueva o modificada llega con su prueba.
- Si se corrige un error, se agrega una prueba que lo habría detectado (así
  pasó, por ejemplo, con los formatos de estabilidad de la iteración I4).
- La versión se considera validada cuando el tecnólogo médico revisa casos
  reales y está de acuerdo con los resultados (HU-20).

## 9. Cuándo se corren

| Momento | Qué se corre |
|---|---|
| Antes de cada commit | `pytest` en el computador |
| En cada `push` a GitHub | GitHub Actions corre `pytest` y marca el commit con ✔ o ✘ |
| Después de cada funcionalidad | Revisión en el navegador (sección 7) |
| Antes de la entrega final | Validación con el tecnólogo médico (HU-20) |
