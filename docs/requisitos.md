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

Cada requisito tiene un identificador, una **prioridad** y un **criterio de
verificación**: cómo se comprueba que se cumple.

**Prioridad (MoSCoW):** *Must* (imprescindible), *Should* (importante),
*Could* (deseable). Las prioridades siguen las del
[backlog](gestion_agil/backlog.md) y **son una propuesta**: el equipo y el
tecnólogo médico deben revisarlas.

**Métodos de verificación:**

| Método | Qué significa |
|---|---|
| **P** · Prueba automática | Una prueba de `tests/` lo comprueba en cada `push` (ver [plan de pruebas](plan_de_pruebas.md)) |
| **I** · Inspección | Se revisa el código, los estilos o la configuración |
| **D** · Demostración | Una persona lo comprueba usando la app en el navegador |
| **V** · Validación | El tecnólogo médico revisa casos reales y confirma el resultado |

Las pruebas citadas están en el archivo que indica el título de cada tabla y
son las que comprueban directamente el requisito. Las demás pruebas de esos
archivos revisan piezas internas (por ejemplo, cómo se lee cada formato de
estabilidad o de tubo del listado). Todos los
requisitos de reglas clínicas (RF-3 y RF-4) se verifican además con **V**
cuando el tecnólogo médico valide la app con casos reales (HU-20).

### RF-1 Identificación · Archivo: `test_ingreso.py`

| ID | Requisito | Prioridad | Verificación |
|---|---|---|---|
| RF-1.1 | La enfermera ingresa su nombre y apellido antes de buscar; sin identificarse no puede entrar al paso 2 | Must | P: `test_sin_nombre_no_avanza`, `test_sin_identificarse_no_se_puede_entrar_al_paso_2`, `test_con_nombre_y_apellido_avanza_al_paso_2` |
| RF-1.2 | El nombre y el apellido aceptan solo letras (con tildes, ñ y ü), espacios, guion y apóstrofo; los espacios de más se ordenan | Must | P: `test_nombre_con_numeros_o_signos_no_avanza`, `test_apellido_con_numeros_o_signos_no_avanza`, `test_nombres_reales_con_tildes_guion_o_apostrofo_avanzan`, `test_espacios_de_mas_se_ordenan` |
| RF-1.3 | La aplicación nunca pide datos del paciente (nombre, RUT ni ficha) y la primera pantalla lo avisa | Must | P: `test_la_pagina_de_inicio_pide_nombre_y_apellido`; `test_auditoria.py`: `test_la_tabla_no_tiene_datos_del_paciente` |
| RF-1.4 | "Cambiar" borra el nombre de la enfermera y los exámenes elegidos | Should | P: `test_cambiar_borra_el_nombre`; `test_buscador.py`: `test_cambiar_de_enfermera_borra_la_seleccion` |

### RF-2 Buscador de exámenes · Archivo: `test_buscador.py`

| ID | Requisito | Prioridad | Verificación |
|---|---|---|---|
| RF-2.1 | Desde 2 letras muestra como máximo 8 sugerencias y nunca elige un examen por sí sola | Must | P: `test_con_menos_de_2_letras_no_busca`, `test_muestra_como_maximo_8_sugerencias`, `test_no_autoselecciona_entrega_una_lista_de_sugerencias` |
| RF-2.2 | Encuentra el examen sin tildes, con mayúsculas o minúsculas y sin escribir el nombre completo | Must | P: `test_encuentra_sin_tildes`, `test_encuentra_con_minusculas_y_tildes`, `test_encuentra_sin_escribir_el_nombre_completo`, `test_encuentra_con_palabras_incompletas` |
| RF-2.3 | Tolera errores de tipeo (no en palabras cortas), muestra primero lo escrito sin error y no muestra nada si no hay parecido | Must | P: `test_tolera_errores_de_tipeo`, `test_palabras_cortas_no_toleran_errores`, `test_ordena_primero_lo_escrito_sin_error`, `test_sin_parecido_no_muestra_nada`, `test_letra_y_numero_con_o_sin_guion` |
| RF-2.4 | Los sinónimos entre paréntesis cuentan como nombre del examen ("glucosa" encuentra "GLICEMIA (GLUCOSA EN SANGRE)") | Must | P: `test_encuentra_por_sinonimo_entre_parentesis`, `test_sinonimo_entre_parentesis_cuenta_como_nombre_principal` |
| RF-2.5 | Cada sugerencia indica si el examen se procesa en el recinto o se deriva y a qué laboratorio; sin laboratorio dice "dato no disponible" | Must | P: `test_etiqueta_recinto`, `test_etiqueta_deriva_con_nombre_del_laboratorio`, `test_etiqueta_sin_laboratorio_dice_dato_no_disponible`, `test_sugerencias_devuelve_nombre_y_etiqueta` |
| RF-2.6 | La enfermera arma la lista de exámenes: agrega, quita y no repite; solo se agregan exámenes que existen | Must | P: `test_agregar_examen_lo_muestra_en_la_lista`, `test_quitar_examen`, `test_no_agrega_el_mismo_examen_dos_veces`, `test_no_agrega_un_examen_que_no_existe` |
| RF-2.7 | Sin identificarse, el buscador no responde | Must | P: `test_sugerencias_sin_identificarse_no_responde` |
| RF-2.8 | Si no hay listado cargado, la app lo avisa | Should | P: `test_sin_listado_cargado_avisa` |

### RF-3 Agrupación de tubos y orden de extracción · Archivos: `test_agrupador.py`, `test_tubos.py`

| ID | Requisito | Prioridad | Verificación |
|---|---|---|---|
| RF-3.1 | Comparten tubo solo los exámenes con el mismo tipo de tubo y el mismo laboratorio | Must | P: `test_mismo_tubo_y_mismo_laboratorio_comparten_tubo`, `test_dos_derivados_al_mismo_laboratorio_comparten_tubo`, `test_mismo_tubo_recinto_y_derivado_van_en_tubos_distintos`, `test_mismo_tubo_dos_laboratorios_externos_distintos_van_aparte`, `test_tubos_distintos_no_se_comparten`, `test_sin_laboratorio_no_comparte_tubo` |
| RF-3.2 | Si un examen admite varios tubos, se elige el que permite juntarlo con otro examen del mismo laboratorio; si ninguno lo permite, el primero (amarillo con gel antes que rojo) | Must | P: `test_elige_el_tubo_que_permite_juntarse_con_otro_examen`, `test_solo_se_junta_con_el_mismo_laboratorio`, `test_sin_con_quien_juntarse_elige_el_primero_amarillo_antes_que_rojo` |
| RF-3.3 | "Tubo con gel" y "tapa amarilla" se leen como el mismo tubo (amarillo con gel); el rojo es distinto | Must | P: `test_tubos.py`: `test_reconoce_el_tubo`, `test_sin_gel_no_es_amarillo` |
| RF-3.4 | Si el laboratorio pide 2 o más tubos para un examen, esos tubos son solo de ese examen y se suman al total | Must | P: `test_dos_tubos_de_un_examen_mas_uno_de_otro_son_tres`, `test_examen_que_necesita_dos_tubos_distintos`; `test_tubos.py`: `test_cantidad_de_tubos_que_pide_el_laboratorio` |
| RF-3.5 | Los tubos se numeran en el orden CLSI: hemocultivo, celeste, amarillo con gel, rojo, verde, jeringa de gases venosos, lila, gris; con el mismo tubo, primero el del recinto | Must | P: `test_orden_de_extraccion_clsi`, `test_mismo_tubo_primero_el_recinto` |
| RF-3.6 | Hemocultivo y gases venosos van en su propio contenedor; los gases arteriales son una punción aparte, fuera del orden | Must | P: `test_hemocultivo_nunca_se_comparte`, `test_gases_venosos_nunca_se_comparten`, `test_gases_arteriales_son_puncion_aparte_fuera_del_orden`; `test_tubos.py`: `test_gases_arteriales_y_venosos_se_distinguen_por_el_nombre` |
| RF-3.7 | Las muestras que no son sangre van en "Otras muestras", fuera del orden y sin contar como tubo | Should | P: `test_otras_muestras_van_aparte_y_no_cuentan_como_tubo`; `test_tubos.py`: `test_muestras_que_no_son_sangre` |
| RF-3.8 | Ayuno se advierte con la frase original del listado; protección de la luz es una advertencia sobre el tubo; hielo no se muestra | Should | P: `test_ayuno_es_advertencia_con_la_frase_del_listado`, `test_proteccion_de_la_luz_es_advertencia_sobre_el_tubo_completo`, `test_hielo_no_se_muestra_a_enfermeria`; `test_tubos.py`: `test_frases_se_copian_tal_cual` |
| RF-3.9 | Si el texto trae indicación para adultos y pediátricos, se usa la de adultos | Must | P: `test_tubos.py`: `test_solo_se_considera_la_parte_de_adultos` |
| RF-3.10 | Si la app no reconoce el tubo, muestra "Tubo: dato no disponible" y lo avisa; nunca lo adivina | Must | P: `test_tubo_no_disponible_se_avisa_y_no_se_adivina`; `test_tubos.py`: `test_si_no_es_claro_no_adivina`, `test_muestra_vacia_es_dato_no_disponible` |

### RF-4 Derivaciones y estabilidad · Archivo: `test_derivaciones.py`

| ID | Requisito | Prioridad | Verificación |
|---|---|---|---|
| RF-4.1 | Para cada derivado se muestran los días de proceso del laboratorio externo con palabras completas; los que no se entienden no se adivinan | Must | P: `test_leer_dias_proceso`, `test_describir_dias_con_palabras_completas`, `test_dias_que_no_se_entienden_no_se_adivinan`, `test_dia_de_proceso_no_disponible` |
| RF-4.2 | El día de proceso estimado considera el corte de las 15:00 en Vespucio, el proceso el mismo día solo si llega antes de las 8:00 y los feriados de Chile en los laboratorios externos | Must | P: `test_antes_de_las_15_se_recibe_ese_dia`, `test_desde_las_15_se_recibe_al_dia_siguiente`, `test_llega_antes_de_las_8_se_procesa_el_mismo_dia`, `test_despues_de_las_8_pasa_al_siguiente_dia_de_proceso`, `test_feriado_el_laboratorio_externo_no_recibe` |
| RF-4.3 | La estabilidad se decide con la refrigerada o, si no existe, con la ambiente (la congelada solo se informa), y con el tipo de muestra del tubo del examen | Must | P: `test_sin_refrigerada_se_usa_la_ambiente`, `test_solo_congelada_no_se_usa_para_decidir`, `test_se_usa_la_estabilidad_del_tipo_de_muestra_del_tubo`, `test_lila_sangre_total_y_plasma_son_lo_mismo_se_usa_la_mas_corta`, `test_tipo_de_muestra_que_no_corresponde_al_tubo_no_se_adivina` |
| RF-4.4 | El veredicto es "la estabilidad lo permite", "al límite, consultar" o "NO alcanza" | Must | P: `test_comparar`, `test_jueves_solo_lunes_estabilidad_7_dias_alcanza`, `test_viernes_antes_y_despues_de_las_15` |
| RF-4.5 | Si no alcanza, se advierte de forma destacada y se sugieren días de toma de la próxima semana | Should | P: `test_jueves_solo_lunes_estabilidad_2_dias_no_alcanza_y_sugiere_domingo`, `test_no_alcanza_ningun_dia_de_la_semana` |
| RF-4.6 | Si el listado no trae estabilidad, se muestra "dato no disponible" | Must | P: `test_sin_estabilidad_es_dato_no_disponible`, `test_sin_estabilidad_queda_vacia` |
| RF-4.7 | "Según demanda" no tiene veredicto: se muestra el tiempo de respuesta y se pide consultar con el laboratorio | Must | P: `test_segun_demanda`, `test_segun_demanda_no_da_veredicto_y_muestra_tiempo_de_respuesta` |
| RF-4.8 | Solo se revisan los exámenes que se derivan | Must | P: `test_solo_se_revisan_los_que_se_derivan`; `test_interfaz.py`: `test_examen_del_recinto_no_lleva_etiqueta_de_estabilidad` |

### RF-5 Resumen e impresión · Archivos: `test_interfaz.py`, `test_buscador.py`

| ID | Requisito | Prioridad | Verificación |
|---|---|---|---|
| RF-5.1 | El resumen muestra el total de tubos y los tubos numerados con su laboratorio y sus exámenes | Must | P: `test_buscador.py`: `test_pantalla_de_tubos_agrupa_y_ordena`, `test_ver_tubos_muestra_los_examenes_elegidos` |
| RF-5.2 | El tubo de un examen derivado lleva la etiqueta de su revisión de estabilidad | Must | P: `test_derivado_lleva_etiqueta_de_estabilidad_en_su_tubo`; `test_derivaciones.py`: `test_textos_para_la_pantalla` |
| RF-5.3 | Los botones "Volver a exámenes", "Imprimir resumen" y "Nueva consulta" aparecen una sola vez, al final; "Nueva consulta" borra la selección | Must | P: `test_botones_una_sola_vez_al_final`; `test_buscador.py`: `test_nueva_consulta_borra_la_seleccion` |
| RF-5.4 | Sin exámenes elegidos no se muestra el resumen | Should | P: `test_buscador.py`: `test_ver_tubos_sin_examenes_vuelve_al_buscador` |
| RF-5.5 | El resumen impreso es compacto y se lee completo | Should | D: imprimir un resumen con varios tubos, avisos y derivados |

### RF-6 Auditoría · Archivo: `test_auditoria.py`

| ID | Requisito | Prioridad | Verificación |
|---|---|---|---|
| RF-6.1 | Al ver el resumen se registra: fecha y hora, enfermera, exámenes y resultado entregado | Must | P: `test_ver_los_tubos_queda_registrado`, `test_resumen_del_resultado_entregado` |
| RF-6.2 | Recargar la pantalla no duplica el registro; cambiar los exámenes o hacer una nueva consulta sí es otro registro | Must | P: `test_recargar_la_pantalla_no_duplica`, `test_cambiar_los_examenes_es_otra_consulta`, `test_nueva_consulta_con_los_mismos_examenes_se_registra` |
| RF-6.3 | El registro no tiene datos de pacientes y la enfermera no ve un historial | Must | P: `test_la_tabla_no_tiene_datos_del_paciente`, `test_la_enfermera_no_ve_un_historial` |
| RF-6.4 | Cada semana (lunes a domingo) se envía por correo un CSV con el historial de la semana anterior, una sola vez, aunque no haya consultas | Must | P: `test_semana_anterior_es_de_lunes_a_domingo`, `test_exportar_solo_lo_anterior_a_esta_semana`, `test_no_se_envia_dos_veces_la_misma_semana`, `test_semana_sin_consultas_igual_se_informa` |
| RF-6.5 | Si el envío sale bien se borra lo enviado y se conserva la semana actual; si falla, no se borra nada | Must | P: `test_envio_exitoso_borra_lo_enviado_y_conserva_la_semana_actual`, `test_si_el_correo_falla_no_se_borra_nada` |
| RF-6.6 | Por defecto el correo está en modo prueba (se guarda como archivo); sin destinatarios no se envía; en modo real sin servidor se avisa | Must | P: `test_modo_prueba_guarda_el_correo_como_archivo`, `test_sin_destinatarios_no_se_envia`, `test_envio_real_sin_servidor_configurado_avisa`, `test_envio_real_usa_el_servidor_configurado` |
| RF-6.7 | Existe el comando `flask --app app auditoria-semanal` para enviarla a mano | Should | P: `test_comando_auditoria_semanal_en_modo_prueba` |
| RF-6.8 | El envío con el servidor de correo real funciona | Should | D: pendiente, cuando se configure el correo real (HU-22) |

### RF-7 Importación del listado técnico · Archivo: `test_importador.py`

| ID | Requisito | Prioridad | Verificación |
|---|---|---|---|
| RF-7.1 | El comando `flask --app app importar data/listado_tecnico.csv` encuentra los títulos después del encabezado del documento y ubica cada columna por su título; si falta una columna o la fila de títulos, se detiene con un mensaje claro | Must | P: `test_encuentra_titulos_despues_del_encabezado_del_documento`, `test_ubica_columnas_por_titulo_aunque_cambie_el_orden`, `test_falta_una_columna_y_se_detiene_con_mensaje_claro`, `test_sin_fila_de_titulos_se_detiene` |
| RF-7.2 | Limpia los saltos de línea de Windows e ignora filas vacías y títulos repetidos | Must | P: `test_saltos_de_linea_de_windows_se_limpian`, `test_ignora_filas_vacias_y_titulos_repetidos` |
| RF-7.3 | "Laboratorio Clínica Dávila Vespucio" es el recinto y los demás se derivan; los "Lab. Derivado" no numéricos se excluyen; con varios códigos en una celda se usa el mayor | Must | P: `test_davila_vespucio_es_el_recinto`, `test_otros_laboratorios_se_derivan`, `test_lab_derivado_no_numerico_se_excluye_y_se_avisa`, `test_dos_codigos_en_una_celda_se_guarda_el_mayor` |
| RF-7.4 | La estabilidad se guarda tal como la escribe el listado | Must | P: `test_estabilidad_se_copia_tal_como_viene_en_el_listado`, `test_estabilidad_reconoce_mayusculas_y_sin_tilde`, `test_sin_mencion_de_estabilidad_queda_vacia` |
| RF-7.5 | Genera `data/reporte_revision.csv` con campos vacíos, valores raros y duplicados para el tecnólogo médico | Must | P: `test_importar_guarda_en_la_base_y_escribe_reporte`, `test_examen_sin_tubo_se_avisa`, `test_examen_sin_laboratorio_se_avisa`, `test_examen_derivado_sin_dia_ni_estabilidad_se_avisa`, `test_nombre_repetido_se_avisa`, `test_dia_de_proceso_que_no_se_entiende_se_avisa` |
| RF-7.6 | Genera `data/tubos_por_revisar.csv` con los tubos que no reconoce; lo que completa el tecnólogo médico se usa y se conserva en la siguiente importación | Should | P: `test_tubo_ambiguo_va_a_la_tabla_y_queda_no_disponible`, `test_lo_que_completa_el_tecnologo_se_usa_y_se_conserva`, `test_valor_no_reconocido_en_la_tabla_se_avisa`, `test_tecnologo_puede_marcar_otra_muestra` |
| RF-7.7 | Importar de nuevo reemplaza los exámenes anteriores | Must | P: `test_importar_dos_veces_reemplaza_los_examenes` |

## 4. Reglas clínicas no negociables

- La aplicación nunca inventa tubos, estabilidades ni días de proceso: todo sale del listado técnico.
- Si falta un dato, se muestra "dato no disponible" y se pide consultar con el laboratorio.
- Ante la duda, la aplicación advierte; no decide en silencio.
- Cada regla y excepción tiene una prueba automática.

## 5. Requisitos no funcionales

Misma prioridad y mismos métodos de verificación que los requisitos
funcionales (sección 3). Cada requisito tiene un criterio que se puede medir o
comprobar.

| ID | Requisito | Criterio medible | Prioridad | Verificación |
|---|---|---|---|---|
| RNF-1 | Legibilidad para turnos de noche | Texto en pantalla de al menos 17 px (base de 18 px); campos de 54 a 60 px de alto; botones principales de 56 px; botones secundarios de al menos 44 px; esquinas de 10 a 16 px | Must | I: `app/static/estilos.css`. D: revisión en el navegador. **Observación:** el número dentro del círculo de cada paso de la cabecera mide 15 px (el título del paso mide 18 px) |
| RNF-2 | Nunca solo el color | Cada tubo y cada etiqueta llevan su nombre en texto; la muestra de color es solo un apoyo | Must | I: plantillas `tubos.html` y `examenes.html`. D: revisión en el navegador |
| RNF-3 | Accesibilidad | El buscador se usa con flechas, Enter y Escape; toda la app se recorre con Tab; las alertas usan `role="alert"` y el estado del buscador `aria-live` | Should | I: `buscador.js` y plantillas. D: recorrer la app solo con el teclado |
| RNF-4 | Textos sin punto final | Ningún texto que se muestra termina en punto; los puntos entre dos frases se mantienen | Should | P: `test_interfaz.py`: `test_filtro_sin_punto`, `test_textos_de_la_pantalla_de_tubos_sin_punto_final` |
| RNF-5 | Interfaz en español | Las pantallas, los títulos y las páginas de error están en español | Must | P: `test_interfaz.py`: `test_cada_pantalla_tiene_su_titulo`, `test_pagina_no_encontrada_en_espanol` |
| RNF-6 | Privacidad de pacientes | La app no pide ni guarda ningún dato de pacientes; la base no tiene columnas para ellos | Must | P: `test_auditoria.py`: `test_la_tabla_no_tiene_datos_del_paciente`. I: `app/modelos.py` |
| RNF-7 | Confidencialidad del listado | El listado real, la base, la auditoría y el `.env` no están en Git; al importar, la consola muestra solo conteos | Must | I: `.gitignore` y `git ls-files` (ningún archivo de `data/` ni `.env`). P: `test_importador.py`: `test_comando_importar_muestra_solo_conteos` |
| RNF-8 | Seguridad clínica | La app nunca inventa tubos, estabilidades ni días de proceso; si falta un dato muestra "dato no disponible" y advierte | Must | P: pruebas de RF-2.5, RF-3.10, RF-4.1, RF-4.3 y RF-4.6. V: casos reales con el tecnólogo médico (HU-20) |
| RNF-9 | Mantenibilidad | La lógica vive en clases del dominio; las rutas no escriben SQL; el importador está separado y acepta otro formato de listado sin cambiar el resto | Should | P: `test_clases.py`: `test_el_importador_acepta_otro_lector`, `test_repositorio_entrega_examenes_en_el_orden_pedido`. I: `app/rutas.py` sin SQL; diagramas de `docs/uml/` coinciden con `app/` |
| RNF-10 | Calidad continua | Todas las pruebas automáticas pasan en cada `push` a GitHub | Must | P: GitHub Actions (`.github/workflows/pruebas.yml`) |
| RNF-11 | Plataforma | Corre en un computador con Python 3 y un navegador de escritorio; solo pacientes adultos | Must | D: instalación con los comandos del `README.md` |

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
