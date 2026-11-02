# Historias de usuario y criterios de aceptación

Cada historia indica su requisito (`docs/requisitos.md`) y las pruebas
automáticas que verifican sus criterios de aceptación (`tests/`).
Los criterios usan el formato **Dado / Cuando / Entonces**.

---

## Épica E1 · Identificación

### HU-01 Identificarse sin datos del paciente
**Como** enfermera **quiero** identificarme con mi nombre y apellido **para** que la consulta quede registrada a mi nombre, sin ingresar datos del paciente.
**Requisito:** RF-1

| # | Criterio de aceptación | Prueba |
|---|---|---|
| 1 | **Dado** que abro la app, **cuando** veo la primera pantalla, **entonces** me pide nombre y apellido y avisa que no se ingresan datos del paciente | `test_la_pagina_de_inicio_pide_nombre_y_apellido` |
| 2 | **Dado** que escribo números o signos en el nombre, **cuando** presiono Continuar, **entonces** no avanzo y veo el error | `test_nombre_con_numeros_o_signos_no_avanza` |
| 3 | **Dado** un nombre real con tildes, guion o apóstrofo, **cuando** presiono Continuar, **entonces** avanzo al paso 2 | `test_nombres_reales_con_tildes_guion_o_apostrofo_avanzan` |
| 4 | **Dado** que no me identifiqué, **cuando** intento entrar a la búsqueda, **entonces** vuelvo al paso 1 | `test_sin_identificarse_no_se_puede_entrar_al_paso_2` |

---

## Épica E2 · Búsqueda de exámenes

### HU-02 Encontrar un examen aunque lo escriba mal
**Como** enfermera **quiero** encontrar un examen escribiendo parte del nombre, sin tildes o con errores de tipeo, **para** no perder tiempo de noche.
**Requisito:** RF-2

| # | Criterio de aceptación | Prueba |
|---|---|---|
| 1 | **Dado** que escribo "acido urico" sin tildes, **entonces** aparece "ÁCIDO ÚRICO" | `test_encuentra_sin_tildes` |
| 2 | **Dado** que escribo "hemog", **entonces** aparece "HEMOGRAMA COMPLETO" | `test_encuentra_sin_escribir_el_nombre_completo` |
| 3 | **Dado** que escribo "glucoza", **entonces** aparece "GLUCOSA" | `test_tolera_errores_de_tipeo` |
| 4 | **Dado** que escribo un sinónimo, **entonces** aparece el examen que lo tiene entre paréntesis | `test_encuentra_por_sinonimo_entre_parentesis` |
| 5 | **Dado** varias coincidencias, **entonces** veo una lista y la app no elige por mí | `test_no_autoselecciona_entrega_una_lista_de_sugerencias` |
| 6 | **Dado** que escribo algo que no existe, **entonces** no aparece nada dudoso | `test_sin_parecido_no_muestra_nada` |

### HU-03 Saber si el examen se procesa aquí o se deriva
**Como** enfermera **quiero** ver en cada sugerencia si el examen se procesa en el recinto o se deriva, y a qué laboratorio, **para** saberlo antes de tomar la muestra.
**Requisito:** RF-2

| # | Criterio de aceptación | Prueba |
|---|---|---|
| 1 | **Dado** un examen del recinto, **entonces** dice "Se procesa en el recinto" | `test_etiqueta_recinto` |
| 2 | **Dado** un examen derivado, **entonces** dice "Se deriva a" y el laboratorio | `test_etiqueta_deriva_con_nombre_del_laboratorio` |
| 3 | **Dado** un examen sin laboratorio en el listado, **entonces** dice "Laboratorio: dato no disponible" | `test_etiqueta_sin_laboratorio_dice_dato_no_disponible` |

### HU-04 Armar la lista de exámenes de la indicación
**Como** enfermera **quiero** agregar y quitar exámenes de una lista **para** tener todos los de la indicación médica antes de ver los tubos.
**Requisito:** RF-2

| # | Criterio de aceptación | Prueba |
|---|---|---|
| 1 | **Dado** que elijo un examen, **entonces** aparece en la lista de seleccionados | `test_agregar_examen_lo_muestra_en_la_lista` |
| 2 | **Dado** que lo elijo dos veces, **entonces** aparece una sola vez | `test_no_agrega_el_mismo_examen_dos_veces` |
| 3 | **Dado** que presiono "Quitar", **entonces** sale de la lista | `test_quitar_examen` |

---

## Épica E3 · Tubos y orden de extracción

### HU-05 Saber cuántos tubos usar
**Como** enfermera **quiero** que los exámenes que pueden ir juntos compartan tubo **para** no extraer más sangre de la necesaria.
**Requisito:** RF-3

| # | Criterio de aceptación | Prueba |
|---|---|---|
| 1 | **Dado** dos exámenes del mismo tubo y laboratorio, **entonces** van en un solo tubo | `test_mismo_tubo_y_mismo_laboratorio_comparten_tubo` |
| 2 | **Dado** el mismo tubo pero laboratorios distintos, **entonces** van en tubos separados | `test_mismo_tubo_recinto_y_derivado_van_en_tubos_distintos` |
| 3 | **Dado** un examen que admite varios tubos, **entonces** se elige el que permite juntarlo con otro | `test_elige_el_tubo_que_permite_juntarse_con_otro_examen` |
| 4 | **Dado** un examen para el que el laboratorio pide 2 tubos y otro que pide 1, **entonces** el total es 3 | `test_dos_tubos_de_un_examen_mas_uno_de_otro_son_tres` |
| 5 | **Dado** un examen cuyo tubo no se reconoce, **entonces** se avisa "Tubo: dato no disponible" y no se adivina | `test_tubo_no_disponible_se_avisa_y_no_se_adivina` |

### HU-06 Extraer en el orden correcto
**Como** enfermera **quiero** ver los tubos numerados en orden de extracción CLSI **para** evitar contaminar una muestra con el aditivo de otra.
**Requisito:** RF-3

| # | Criterio de aceptación | Prueba |
|---|---|---|
| 1 | **Dado** tubos de todos los tipos, **entonces** el orden es hemocultivo, celeste, amarillo, rojo, verde, jeringa venosa, lila, gris | `test_orden_de_extraccion_clsi` |
| 2 | **Dado** el mismo tipo de tubo para el recinto y un derivado, **entonces** va primero el del recinto | `test_mismo_tubo_primero_el_recinto` |

### HU-07 Contenedores especiales
**Como** enfermera **quiero** que hemocultivos y gases tengan su propio contenedor, y que los gases arteriales aparezcan como punción aparte, **para** no mezclarlos con los tubos.
**Requisito:** RF-3

| # | Criterio de aceptación | Prueba |
|---|---|---|
| 1 | **Dado** dos hemocultivos, **entonces** van en frascos separados | `test_hemocultivo_nunca_se_comparte` |
| 2 | **Dado** gases venosos, **entonces** la jeringa no se comparte | `test_gases_venosos_nunca_se_comparten` |
| 3 | **Dado** gases arteriales, **entonces** aparecen como punción aparte, fuera del orden | `test_gases_arteriales_son_puncion_aparte_fuera_del_orden` |

### HU-08 Avisos de ayuno y luz
**Como** enfermera **quiero** ver los avisos de ayuno y de protección de la luz con la frase original del listado **para** preparar bien al paciente y la muestra.
**Requisito:** RF-3

| # | Criterio de aceptación | Prueba |
|---|---|---|
| 1 | **Dado** un examen con ayuno, **entonces** aparece la frase del listado tal cual | `test_ayuno_es_advertencia_con_la_frase_del_listado` |
| 2 | **Dado** un examen que se protege de la luz, **entonces** se marca el tubo completo, sin tubo aparte | `test_proteccion_de_la_luz_es_advertencia_sobre_el_tubo_completo` |
| 3 | **Dado** un examen que se envía en hielo, **entonces** no se muestra (lo maneja el laboratorio) | `test_hielo_no_se_muestra_a_enfermeria` |

### HU-09 Otras muestras
**Como** enfermera **quiero** ver aparte las muestras que no son sangre **para** no olvidarlas, aunque no entren en el orden de extracción.
**Requisito:** RF-3

| # | Criterio de aceptación | Prueba |
|---|---|---|
| 1 | **Dado** un examen de orina, **entonces** aparece en "Otras muestras" y no cuenta como tubo | `test_otras_muestras_van_aparte_y_no_cuentan_como_tubo` |

### HU-10 Imprimir el resumen
**Como** enfermera **quiero** imprimir el resumen de tubos **para** tenerlo a mano al tomar la muestra.
**Requisito:** RF-5

| # | Criterio de aceptación | Verificación |
|---|---|---|
| 1 | **Dado** el resumen de tubos, **cuando** presiono "Imprimir resumen", **entonces** se imprime sin botones ni cabecera y con mi nombre y la fecha | Manual en el navegador (vista previa de impresión) |
| 2 | **Dado** el resumen, **entonces** los botones aparecen una sola vez, al final | `test_botones_una_sola_vez_al_final` |

---

## Épica E4 · Derivaciones y estabilidad

### HU-11 Saber si la muestra derivada alcanza
**Como** enfermera **quiero** saber si la estabilidad de una muestra derivada alcanza hasta el día en que la procesa el laboratorio externo **para** no tomar una muestra que será rechazada.
**Requisito:** RF-4

| # | Criterio de aceptación | Prueba |
|---|---|---|
| 1 | **Dado** un laboratorio que procesa solo lunes y una estabilidad de 7 días, **cuando** consulto un jueves, **entonces** dice "La estabilidad lo permite" | `test_jueves_solo_lunes_estabilidad_7_dias_alcanza` |
| 2 | **Dado** una consulta antes o después de las 15:00, **entonces** la espera se cuenta desde ese día o desde el siguiente | `test_viernes_antes_y_despues_de_las_15` |
| 3 | **Dado** un feriado, **entonces** el laboratorio externo no recibe ese día | `test_feriado_el_laboratorio_externo_no_recibe` |
| 4 | **Dado** un examen "según demanda", **entonces** no hay veredicto y se muestra el tiempo de respuesta | `test_segun_demanda_no_da_veredicto_y_muestra_tiempo_de_respuesta` |
| 5 | **Dado** un examen sin estabilidad en el listado, **entonces** dice "dato no disponible" | `test_sin_estabilidad_es_dato_no_disponible` |

### HU-12 Saber cuándo tomarla si no alcanza
**Como** enfermera **quiero** que, si la estabilidad no alcanza, la app me sugiera qué días tomar la muestra **para** coordinarlo con el equipo.
**Requisito:** RF-4

| # | Criterio de aceptación | Prueba |
|---|---|---|
| 1 | **Dado** un laboratorio que procesa solo lunes y una estabilidad de 2 días, **cuando** consulto un jueves, **entonces** dice "NO alcanza" y sugiere el domingo | `test_jueves_solo_lunes_estabilidad_2_dias_no_alcanza_y_sugiere_domingo` |
| 2 | **Dado** que ningún día de la semana alcanza, **entonces** pide consultar con el laboratorio | `test_no_alcanza_ningun_dia_de_la_semana` |

---

## Épica E5 · Datos del laboratorio

### HU-13 Cargar el listado técnico
**Como** tecnólogo médico **quiero** importar el listado técnico y recibir un reporte de revisión **para** validar los datos antes de que los usen las enfermeras.
**Requisito:** RF-7

| # | Criterio de aceptación | Prueba |
|---|---|---|
| 1 | **Dado** el listado con filas de encabezado del documento, **entonces** encuentra la fila de títulos | `test_encuentra_titulos_despues_del_encabezado_del_documento` |
| 2 | **Dado** que falta una columna, **entonces** se detiene con un mensaje claro | `test_falta_una_columna_y_se_detiene_con_mensaje_claro` |
| 3 | **Dado** un examen derivado sin día ni estabilidad, **entonces** aparece en el reporte de revisión | `test_examen_derivado_sin_dia_ni_estabilidad_se_avisa` |
| 4 | **Dado** que importo, **entonces** la consola muestra solo conteos, nunca el contenido | `test_comando_importar_muestra_solo_conteos` |

### HU-14 Completar los tubos que la app no reconoce
**Como** tecnólogo médico **quiero** escribir en una tabla el tubo correcto de los exámenes que la app no reconoce **para** que las enfermeras no vean "dato no disponible".
**Requisito:** RF-7

| # | Criterio de aceptación | Prueba |
|---|---|---|
| 1 | **Dado** un tubo ambiguo, **entonces** va a la tabla y queda como dato no disponible | `test_tubo_ambiguo_va_a_la_tabla_y_queda_no_disponible` |
| 2 | **Dado** que completo la tabla, **cuando** se vuelve a importar, **entonces** se usa lo que escribí y se conserva | `test_lo_que_completa_el_tecnologo_se_usa_y_se_conserva` |

---

## Épica E6 · Auditoría

### HU-15 Registrar cada consulta
**Como** jefatura de laboratorio **quiero** que cada resumen entregado quede registrado, sin datos del paciente, **para** auditar el uso de la app.
**Requisito:** RF-6

| # | Criterio de aceptación | Prueba |
|---|---|---|
| 1 | **Dado** que una enfermera ve los tubos, **entonces** queda registrada la consulta | `test_ver_los_tubos_queda_registrado` |
| 2 | **Dado** que recarga la pantalla, **entonces** no se duplica | `test_recargar_la_pantalla_no_duplica` |
| 3 | **Dado** el registro, **entonces** no tiene ningún dato del paciente | `test_la_tabla_no_tiene_datos_del_paciente` |

### HU-16 Recibir el historial semanal
**Como** jefatura de laboratorio **quiero** recibir cada semana el historial por correo **para** revisarlo sin entrar a la app.
**Requisito:** RF-6

| # | Criterio de aceptación | Prueba |
|---|---|---|
| 1 | **Dado** que es lunes, **entonces** se envía el historial de la semana anterior y se borra de la base | `test_envio_exitoso_borra_lo_enviado_y_conserva_la_semana_actual` |
| 2 | **Dado** que el correo falla, **entonces** no se borra nada | `test_si_el_correo_falla_no_se_borra_nada` |
| 3 | **Dado** el modo prueba, **entonces** el correo se guarda como archivo y no se envía | `test_modo_prueba_guarda_el_correo_como_archivo` |

---

## Épica E7 · Calidad y entrega (historias técnicas)

### HU-17 Código en clases con UML
**Como** equipo **queremos** el código organizado en clases del dominio, con diagramas UML que coincidan **para** mantenerlo y explicarlo con trazabilidad.

| # | Criterio de aceptación | Verificación |
|---|---|---|
| 1 | El comportamiento no cambia | Las 235 pruebas anteriores pasan y 40 pantallas comparadas son idénticas |
| 2 | Los métodos de los diagramas de secuencia existen en las clases | `docs/uml/` revisado contra `app/` |

### HU-18 Pruebas automáticas en cada cambio (pendiente)
**Como** equipo **queremos** que las pruebas corran solas en cada `push` y Pull Request **para** detectar errores antes de juntar cambios.

| # | Criterio de aceptación |
|---|---|
| 1 | **Dado** un Pull Request, **cuando** se abre, **entonces** GitHub muestra si las pruebas pasan |

### HU-19 Plan de despliegue y operación (pendiente)
**Como** jefatura de laboratorio **quiero** un plan para instalar, respaldar, monitorear y mantener la app **para** saber qué se necesita para usarla en el hospital.

| # | Criterio de aceptación |
|---|---|
| 1 | Existe un documento con ambientes, recursos, estrategia de entrega, monitoreo, mantenimiento e impacto en las usuarias |
