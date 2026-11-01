"""Pruebas del buscador y de la selección de exámenes. Usan exámenes inventados."""

import pytest

from app.buscador import buscar, cargar_examenes, etiqueta_procesamiento
from app.modelos import conectar
from tests.conftest import cargar_examenes_de_prueba


@pytest.fixture
def examenes(ruta_base):
    cargar_examenes_de_prueba(ruta_base)
    conexion = conectar(ruta_base)
    lista = cargar_examenes(conexion)
    conexion.close()
    return lista


def nombres(resultados):
    return [examen["nombre"] for examen in resultados]


# ---------- Búsqueda ----------

def test_encuentra_sin_tildes(examenes):
    assert nombres(buscar("acido urico", examenes)) == ["ÁCIDO ÚRICO"]


def test_encuentra_con_minusculas_y_tildes(examenes):
    assert nombres(buscar("ácido úrico", examenes)) == ["ÁCIDO ÚRICO"]


def test_encuentra_sin_escribir_el_nombre_completo(examenes):
    assert nombres(buscar("hemog", examenes)) == ["HEMOGRAMA COMPLETO"]


def test_encuentra_con_palabras_incompletas(examenes):
    assert nombres(buscar("ac fol", examenes)) == ["ÁCIDO FÓLICO (FOLATO SÉRICO)"]


def test_encuentra_por_sinonimo_entre_parentesis(examenes):
    assert nombres(buscar("folato", examenes)) == ["ÁCIDO FÓLICO (FOLATO SÉRICO)"]


@pytest.mark.parametrize("con_error, esperado", [
    ("glucoza", "GLUCOSA"),
    ("feritina", "FERRITINA"),
    ("hemogrma", "HEMOGRAMA COMPLETO"),
])
def test_tolera_errores_de_tipeo(examenes, con_error, esperado):
    assert nombres(buscar(con_error, examenes))[0] == esperado


def test_no_autoselecciona_entrega_una_lista_de_sugerencias(examenes):
    # "gluc" calza con dos exámenes: se muestran ambos para que la enfermera elija
    assert nombres(buscar("gluc", examenes)) == ["GLUCOSA", "GLUCOSA POST CARGA"]


def test_ordena_primero_lo_escrito_sin_error(examenes):
    # "ferritin" calza exacto con el comienzo de FERRITINA;
    # una coincidencia con error de tipeo nunca queda antes
    assert nombres(buscar("ferritin", examenes))[0] == "FERRITINA"
    # Con igual parecido, va primero el nombre más corto
    assert nombres(buscar("glucosa", examenes)) == ["GLUCOSA", "GLUCOSA POST CARGA"]


def test_con_menos_de_2_letras_no_busca(examenes):
    assert buscar("g", examenes) == []
    assert buscar("  ", examenes) == []


def test_sin_parecido_no_muestra_nada(examenes):
    assert buscar("radiografia", examenes) == []


def test_palabras_cortas_no_toleran_errores(examenes):
    # Con 3 letras un error cambia demasiado el sentido: "glx" no es "glucosa"
    assert buscar("glx", examenes) == []


def test_muestra_como_maximo_8_sugerencias(examenes):
    muchos = examenes * 5
    assert len(buscar("gluc", muchos)) == 8


# ---------- Etiqueta recinto / derivación ----------

def test_etiqueta_recinto():
    examen = {"laboratorio": "Laboratorio Clínica Dávila Vespucio", "se_procesa_en_recinto": 1}
    assert etiqueta_procesamiento(examen) == {"tipo": "recinto", "texto": "Se procesa en el recinto"}


def test_etiqueta_deriva_con_nombre_del_laboratorio():
    examen = {"laboratorio": "Laboratorio Externo Prueba", "se_procesa_en_recinto": 0}
    assert etiqueta_procesamiento(examen) == {"tipo": "deriva", "texto": "Se deriva a Laboratorio Externo Prueba"}


def test_etiqueta_sin_laboratorio_dice_dato_no_disponible():
    examen = {"laboratorio": "", "se_procesa_en_recinto": 0}
    assert etiqueta_procesamiento(examen) == {"tipo": "aviso", "texto": "Laboratorio: dato no disponible"}


# ---------- Sugerencias desde la pantalla ----------

def test_sugerencias_sin_identificarse_no_responde(cliente):
    respuesta = cliente.get("/examenes/sugerencias?q=gluc")
    assert respuesta.status_code == 401


def test_sugerencias_devuelve_nombre_y_etiqueta(cliente_con_examenes):
    datos = cliente_con_examenes.get("/examenes/sugerencias?q=ferri").get_json()
    assert len(datos) == 1
    assert datos[0]["nombre"] == "FERRITINA"
    assert datos[0]["etiqueta"]["texto"] == "Se deriva a Laboratorio Externo Prueba"
    assert datos[0]["ya_seleccionado"] is False


# ---------- Selección de exámenes ----------

def id_de(cliente, consulta):
    return cliente.get(f"/examenes/sugerencias?q={consulta}").get_json()[0]["id"]


def test_agregar_examen_lo_muestra_en_la_lista(cliente_con_examenes):
    id_examen = id_de(cliente_con_examenes, "ferritina")
    cliente_con_examenes.post("/examenes/agregar", data={"id": id_examen})
    html = cliente_con_examenes.get("/examenes").get_data(as_text=True)
    assert "Exámenes seleccionados (1)" in html
    assert "FERRITINA" in html


def test_no_agrega_el_mismo_examen_dos_veces(cliente_con_examenes):
    id_examen = id_de(cliente_con_examenes, "ferritina")
    cliente_con_examenes.post("/examenes/agregar", data={"id": id_examen})
    cliente_con_examenes.post("/examenes/agregar", data={"id": id_examen})
    html = cliente_con_examenes.get("/examenes").get_data(as_text=True)
    assert "Exámenes seleccionados (1)" in html
    # La sugerencia avisa que ya está agregado
    assert cliente_con_examenes.get("/examenes/sugerencias?q=ferritina").get_json()[0]["ya_seleccionado"]


def test_no_agrega_un_examen_que_no_existe(cliente_con_examenes):
    cliente_con_examenes.post("/examenes/agregar", data={"id": 9999})
    html = cliente_con_examenes.get("/examenes").get_data(as_text=True)
    assert "Exámenes seleccionados (0)" in html


def test_quitar_examen(cliente_con_examenes):
    id_glucosa = id_de(cliente_con_examenes, "glucosa")
    id_ferritina = id_de(cliente_con_examenes, "ferritina")
    cliente_con_examenes.post("/examenes/agregar", data={"id": id_glucosa})
    cliente_con_examenes.post("/examenes/agregar", data={"id": id_ferritina})
    cliente_con_examenes.post("/examenes/quitar", data={"id": id_glucosa})
    html = cliente_con_examenes.get("/examenes").get_data(as_text=True)
    assert "Exámenes seleccionados (1)" in html
    assert "FERRITINA" in html


def test_ver_tubos_sin_examenes_vuelve_al_buscador(cliente_con_examenes):
    respuesta = cliente_con_examenes.get("/tubos")
    assert respuesta.status_code == 302
    assert respuesta.headers["Location"].endswith("/examenes")


def test_ver_tubos_muestra_los_examenes_elegidos(cliente_con_examenes):
    cliente_con_examenes.post("/examenes/agregar", data={"id": id_de(cliente_con_examenes, "ferritina")})
    html = cliente_con_examenes.get("/tubos").get_data(as_text=True)
    assert "FERRITINA" in html


def test_nueva_consulta_borra_la_seleccion(cliente_con_examenes):
    cliente_con_examenes.post("/examenes/agregar", data={"id": id_de(cliente_con_examenes, "ferritina")})
    cliente_con_examenes.post("/nueva-consulta")
    html = cliente_con_examenes.get("/examenes").get_data(as_text=True)
    assert "Exámenes seleccionados (0)" in html


def test_cambiar_de_enfermera_borra_la_seleccion(cliente_con_examenes):
    cliente_con_examenes.post("/examenes/agregar", data={"id": id_de(cliente_con_examenes, "ferritina")})
    cliente_con_examenes.get("/cambiar")
    cliente_con_examenes.post("/", data={"nombre": "Luis", "apellido": "Rojas"})
    html = cliente_con_examenes.get("/examenes").get_data(as_text=True)
    assert "Exámenes seleccionados (0)" in html


def test_sin_listado_cargado_avisa(cliente):
    cliente.post("/", data={"nombre": "Ana", "apellido": "Soto"})
    html = cliente.get("/examenes").get_data(as_text=True)
    assert "No hay listado de exámenes cargado" in html
