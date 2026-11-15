# Informe de resultados de pruebas

Resultado de las pruebas descritas en el [plan de pruebas](plan_de_pruebas.md).

## 1. Resumen

| | |
|---|---|
| Fecha | 14 de noviembre de 2026 |
| Pruebas automáticas | **260** |
| Pasan | **260 (100 %)** |
| Fallan | 0 |
| Duración | 5 a 7 segundos |
| Estilo del código | flake8 sin avisos (reglas por defecto, líneas de máximo 79 caracteres) |
| Integración continua | GitHub Actions revisa flake8 y corre las pruebas en cada `push` (ver sección 3) |

## 2. Resultados por archivo

| Archivo | Qué prueba | Pruebas | Resultado |
|---|---|---|---|
| `test_ingreso.py` | Identificación de la enfermera (RF-1) | 25 | ✔ Pasan todas |
| `test_buscador.py` | Buscador y selección de exámenes (RF-2) | 31 | ✔ Pasan todas |
| `test_tubos.py` | Lectura del tubo desde el texto del listado (RF-3) | 44 | ✔ Pasan todas |
| `test_agrupador.py` | Agrupación, orden CLSI y excepciones (RF-3) | 22 | ✔ Pasan todas |
| `test_derivaciones.py` | Día de proceso y estabilidad (RF-4) | 57 | ✔ Pasan todas |
| `test_interfaz.py` | Pantallas, textos y resumen (RF-5) | 20 | ✔ Pasan todas |
| `test_auditoria.py` | Registro y envío semanal (RF-6) | 21 | ✔ Pasan todas |
| `test_importador.py` | Importación y reportes de revisión (RF-7) | 30 | ✔ Pasan todas |
| `test_clases.py` | Clases del dominio y patrones de diseño | 10 | ✔ Pasan todas |
| **Total** | | **260** | **✔ 260 de 260** |

Algunas pruebas revisan varios casos parecidos de una vez (por ejemplo, varios
nombres válidos en `test_ingreso.py`); `pytest` cuenta cada caso por separado.

## 3. Ejecuciones

| Ambiente | Sistema | Python | Resultado |
|---|---|---|---|
| Computador del equipo | Windows 11 | 3.13.2 | ✔ 245 pasan |
| Copia limpia del repositorio, sin `data/` ni `.env` (como la ve GitHub) | Windows 11 | 3.13.2 | ✔ 245 pasan, sin dejar archivos |
| GitHub Actions, primera ejecución ([ver en GitHub](https://github.com/cpuniversity/preanalitica/actions/runs/41552922051)), commit `00e7df1` | Ubuntu (Linux) | 3.13 | ✔ 245 pasan, en 17 segundos en total |
| Computador del equipo, después de ordenar la pantalla de tubos (5 pruebas nuevas) | Windows 11 | 3.13.2 | ✔ 250 pasan |
| Computador del equipo, después de corregir la lectura de "1 frasco con muestra de deposición" (5 pruebas nuevas) | Windows 11 | 3.13.2 | ✔ 255 pasan |
| Computador del equipo, después de simplificar la pantalla de tubos (2 pruebas nuevas) | Windows 11 | 3.13.2 | ✔ 257 pasan |
| Computador del equipo, después de excluir la leyenda de laboratorios del listado (1 prueba nueva) | Windows 11 | 3.13.2 | ✔ 258 pasan |
| Computador del equipo, después de la nueva cabecera y la bienvenida del ingreso (2 pruebas nuevas) | Windows 11 | 3.13.2 | ✔ 260 pasan |
| Computador del equipo, después de la estabilidad en una línea y de corregir el estilo con flake8 | Windows 11 | 3.13.2 | ✔ 260 pasan · flake8: 0 avisos |

Desde entonces, cada `push` queda con su propia ejecución en la pestaña
[Actions](https://github.com/cpuniversity/preanalitica/actions/workflows/pruebas.yml)
del repositorio.

La copia limpia confirma que las pruebas no dependen del listado real, de la
base local ni de la configuración del correo.

## 4. Evolución

Número de pruebas al cerrar cada iteración (ver
[sprints.md](gestion_agil/sprints.md)). En todas, las pruebas pasaron antes del
commit.

| I0 | I1 e I2 | I3 | I4 | I5 | I6 | I7 |
|---|---|---|---|---|---|---|
| 24 | 75 | 143 | 201 | 223 | 235 | 245 |

## 5. Errores encontrados y corregidos

Errores que aparecieron durante el desarrollo. Cada uno quedó con una prueba
para que no vuelva a pasar.

| Iteración | Error | Prueba que lo cubre |
|---|---|---|
| I0 | Se podían ingresar números o signos como nombre | `test_nombre_con_numeros_o_signos_no_avanza` |
| I3 | Los saltos de línea de Windows (`\r\n`) del listado no se limpiaban | `test_saltos_de_linea_de_windows_se_limpian` |
| I4 | Dos formatos de estabilidad se leían mal (número antes de la temperatura y "sangre completa") | `test_numero_antes_de_la_temperatura`, `test_sangre_completa_es_un_tipo_de_muestra_aparte_del_plasma` |
| I5 | "glucosa" no mostraba la glicemia | `test_encuentra_por_sinonimo_entre_parentesis`, `test_sinonimo_entre_parentesis_cuenta_como_nombre_principal` |
| I8 | "1 FRASCO CON MUESTRA DE DEPOSICIÓN" se leía como sangre y el examen quedaba sin tubo | `test_frasco_con_muestra_que_no_es_sangre_es_otra_muestra`, `test_frasco_sin_otra_muestra_no_cambia` |
| I8 | Las filas de la leyenda de laboratorios ("DERIVACION 1", "2"…) se cargaban como exámenes | `test_leyenda_de_laboratorios_no_se_carga_como_examen` |
| I8 | Al seleccionar un campo se veía una doble línea (borde más contorno separado) | Revisión en el navegador: ahora un solo borde con halo |
| I8 | Los pasos de la cabecera se movían al pasar de Identificación a Exámenes (negrita, barra de desplazamiento y botón "Cambiar") | `test_cabecera_con_logo_y_franja_de_tapas_en_todas_las_pantallas` y medición en el navegador: misma posición en las tres pantallas |
| I8 | La estabilidad de algunos derivados aparecía dos veces (un recuadro y la línea del listado) | `test_estabilidad_no_revisable_pide_consultar_en_una_sola_linea` |
| I8 | flake8, aplicado al final, marcó 521 avisos de estilo (casi todos líneas largas) | Se corrigieron todos y GitHub Actions corre flake8 en cada `push` |

## 6. Lo que falta

- **Validación con casos reales (HU-20).** Las reglas están probadas con casos
  inventados que siguen las decisiones del tecnólogo médico. Falta que él revise
  casos reales y confirme los resultados.
- **41 tubos sin reconocer.** Mientras el tecnólogo médico no complete
  `data/tubos_por_revisar.csv`, esos exámenes se muestran como "Tubo: dato no
  disponible". La app avisa y no adivina, como lo exige la prueba
  `test_tubo_no_disponible_se_avisa_y_no_se_adivina`.
- **Correo real (HU-22).** El envío por servidor de correo está probado con un
  servidor simulado; falta probarlo con el servidor real cuando se configure.
- **Revisión en el navegador.** Se hizo al cerrar cada iteración; la lista de
  la sección 7 del plan queda para repetirla antes de la entrega final.
