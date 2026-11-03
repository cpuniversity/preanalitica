"""Pruebas del pulido de interfaz: títulos, navegación, ícono, errores y pantalla de tubos."""

from app.modelos import conectar

RECINTO = "Laboratorio Clínica Dávila Vespucio"


def cargar_examen(ruta_base, nombre, tubos, laboratorio=RECINTO, instrucciones="", dias_proceso="", estabilidad=""):
    """Agrega a la base temporal un examen inventado con los datos que necesita la prueba."""
    conexion = conectar(ruta_base)
    with conexion:
        conexion.execute(
            "INSERT INTO examenes (fila_origen, nombre, laboratorio, se_procesa_en_recinto, tubos, muestra, "
            "instrucciones, dias_proceso, estabilidad) VALUES (100, ?, ?, ?, ?, 'MUESTRA DE PRUEBA.', ?, ?, ?)",
            (nombre, laboratorio, 1 if laboratorio == RECINTO else 0, tubos, instrucciones, dias_proceso, estabilidad),
        )
    conexion.close()


def agregar(cliente, consulta):
    id_examen = cliente.get(f"/examenes/sugerencias?q={consulta}").get_json()[0]["id"]
    cliente.post("/examenes/agregar", data={"id": id_examen})
    return id_examen


# ---------- Título de la pestaña ----------

def test_cada_pantalla_tiene_su_titulo(cliente_con_examenes):
    assert "<title>Exámenes · Preanalítica</title>" in cliente_con_examenes.get("/examenes").get_data(as_text=True)
    agregar(cliente_con_examenes, "hemograma")
    assert "<title>Tubos · Preanalítica</title>" in cliente_con_examenes.get("/tubos").get_data(as_text=True)


def test_titulo_de_identificacion(cliente):
    assert "<title>Identificación · Preanalítica</title>" in cliente.get("/").get_data(as_text=True)


# ---------- Cabecera ----------

def test_desde_tubos_el_paso_examenes_es_un_enlace(cliente_con_examenes):
    agregar(cliente_con_examenes, "hemograma")
    html = cliente_con_examenes.get("/tubos").get_data(as_text=True)
    assert 'class="paso-enlace" href="/examenes"' in html


def test_en_examenes_los_pasos_no_son_enlaces(cliente_con_examenes):
    assert "paso-enlace" not in cliente_con_examenes.get("/examenes").get_data(as_text=True)


# ---------- Ícono y errores ----------

def test_icono_de_la_app(cliente):
    assert 'rel="icon"' in cliente.get("/").get_data(as_text=True)
    respuesta = cliente.get("/favicon.ico")
    assert respuesta.status_code == 302
    assert respuesta.headers["Location"].endswith("/static/icono.svg")


def test_pagina_no_encontrada_en_espanol(cliente):
    respuesta = cliente.get("/no-existe")
    html = respuesta.get_data(as_text=True)
    assert respuesta.status_code == 404
    assert "Página no encontrada" in html
    assert "Volver al inicio" in html


def test_pagina_no_encontrada_identificada_vuelve_a_examenes(cliente_con_examenes):
    html = cliente_con_examenes.get("/no-existe").get_data(as_text=True)
    assert "Volver a exámenes" in html


# ---------- Pantalla de tubos ----------

def test_botones_una_sola_vez_al_final(cliente_con_examenes):
    agregar(cliente_con_examenes, "hemograma")
    html = cliente_con_examenes.get("/tubos").get_data(as_text=True)
    assert html.count("Imprimir resumen") == 1
    assert html.count("Nueva consulta") == 1
    # Van después de la lista de tubos
    assert html.index("Tubo lila (EDTA)") < html.index("Imprimir resumen")


def test_derivado_lleva_etiqueta_de_estabilidad_en_su_tubo(cliente_con_examenes):
    id_ferritina = agregar(cliente_con_examenes, "ferritina")
    html = cliente_con_examenes.get("/tubos").get_data(as_text=True)
    # La etiqueta del tubo lleva al detalle en "Exámenes que se derivan"
    assert f'href="#derivado-{id_ferritina}"' in html
    assert f'id="derivado-{id_ferritina}"' in html
    # Los datos de prueba no traen día de proceso
    assert "Día de proceso: dato no disponible · ver detalle" in html


def test_examen_del_recinto_no_lleva_etiqueta_de_estabilidad(cliente_con_examenes):
    agregar(cliente_con_examenes, "hemograma")
    html = cliente_con_examenes.get("/tubos").get_data(as_text=True)
    assert "ver detalle" not in html


def test_ayuno_y_luz_van_al_lado_del_examen_y_no_en_un_recuadro_arriba(ruta_base, cliente_con_examenes):
    cargar_examen(ruta_base, "PROTEINAS PRUEBA", "amarillo", instrucciones="8 HRS AYUNO.\nProteger de la luz.")
    agregar(cliente_con_examenes, "proteinas prueba")
    html = cliente_con_examenes.get("/tubos").get_data(as_text=True)
    # La frase del listado, destacada y entre paréntesis, junto al nombre
    assert 'PROTEINAS PRUEBA <span class="aviso-examen">(8 HRS AYUNO. Proteger de la luz)</span>' in html
    # El tubo completo se protege de la luz
    assert "Proteger de la luz</span>" in html
    assert "Ayuno: revise lo que indica el listado" not in html
    assert "<strong>Luz:</strong>" not in html


def test_frase_con_ayuno_y_luz_se_muestra_una_vez(ruta_base, cliente_con_examenes):
    cargar_examen(ruta_base, "VITAMINA PRUEBA", "amarillo", instrucciones="Ayuno de 4 horas y proteger de la luz.")
    agregar(cliente_con_examenes, "vitamina prueba")
    html = cliente_con_examenes.get("/tubos").get_data(as_text=True)
    assert html.count("Ayuno de 4 horas y proteger de la luz") == 1


def test_examen_sin_tubo_va_en_su_tarjeta_despues_de_los_tubos(cliente_con_examenes):
    agregar(cliente_con_examenes, "hemograma")
    agregar(cliente_con_examenes, "examen sin laboratorio")
    html = cliente_con_examenes.get("/tubos").get_data(as_text=True)
    tarjeta = html.index("Tubo: dato no disponible · consulte con el laboratorio")
    assert html.index("Tubo lila (EDTA)") < tarjeta < html.index("EXAMEN SIN LABORATORIO")
    # Ya no hay recuadros amarillos antes de los tubos
    assert 'class="aviso"' not in html


def test_derivado_sin_estabilidad_muestra_un_solo_aviso(ruta_base, cliente_con_examenes):
    cargar_examen(ruta_base, "DERIVADO PRUEBA", "amarillo", laboratorio="Laboratorio Externo Prueba",
                  dias_proceso="LU A DO")
    agregar(cliente_con_examenes, "derivado prueba")
    html = cliente_con_examenes.get("/tubos").get_data(as_text=True)
    assert "<strong>Estabilidad según el listado:</strong>\n              dato no disponible. Consultar con el laboratorio" in html
    assert "<strong>Estabilidad: dato no disponible</strong>" not in html


def test_estabilidad_que_no_sirve_para_decidir_mantiene_el_aviso(ruta_base, cliente_con_examenes):
    cargar_examen(ruta_base, "CONGELADO PRUEBA", "amarillo", laboratorio="Laboratorio Externo Prueba",
                  dias_proceso="LU A DO", estabilidad="Congelado 1 mes")
    agregar(cliente_con_examenes, "congelado prueba")
    html = cliente_con_examenes.get("/tubos").get_data(as_text=True)
    # El listado trae estabilidad, pero solo congelada: la app advierte que no pudo revisarla
    assert "<strong>Estabilidad: dato no disponible</strong>" in html
    assert "Congelado 1 mes" in html


# ---------- Sin punto final ----------

def test_filtro_sin_punto():
    from app import create_app
    sin_punto = create_app().jinja_env.filters["sin_punto"]
    assert sin_punto("8 HRS AYUNO.") == "8 HRS AYUNO"
    assert sin_punto("  ESTABILIDAD\n 24 HORAS. ") == "ESTABILIDAD 24 HORAS"
    assert sin_punto("CITRATO 3.2%") == "CITRATO 3.2%"   # los puntos de adentro se mantienen
    assert sin_punto("") == ""


def test_textos_de_la_pantalla_de_tubos_sin_punto_final(cliente_con_examenes):
    agregar(cliente_con_examenes, "hemograma")
    html = cliente_con_examenes.get("/tubos").get_data(as_text=True)
    assert "Numerados en orden de extracción (CLSI)</p>" in html
