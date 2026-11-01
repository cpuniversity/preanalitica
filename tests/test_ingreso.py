"""Pruebas de la pantalla de ingreso (paso 1)."""

import pytest

from app import create_app


@pytest.fixture
def cliente():
    # Un "navegador de prueba" que conversa con la app sin abrir el navegador real
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


def test_la_pagina_de_inicio_pide_nombre_y_apellido(cliente):
    respuesta = cliente.get("/")
    html = respuesta.get_data(as_text=True)
    assert respuesta.status_code == 200
    assert 'name="nombre"' in html
    assert 'name="apellido"' in html
    assert "no se ingresan datos del paciente" in html


def test_sin_nombre_no_avanza(cliente):
    respuesta = cliente.post("/", data={"nombre": "  ", "apellido": "Soto"})
    assert respuesta.status_code == 200
    assert "Escriba su nombre." in respuesta.get_data(as_text=True)


@pytest.fixture(params=["123", "Ana2", "@#$%", "---", "Ana_Soto", ".", "Ana  -  "])
def texto_invalido(request):
    return request.param


def test_nombre_con_numeros_o_signos_no_avanza(cliente, texto_invalido):
    respuesta = cliente.post("/", data={"nombre": texto_invalido, "apellido": "Soto"})
    assert respuesta.status_code == 200
    assert "solo puede tener letras" in respuesta.get_data(as_text=True)


def test_apellido_con_numeros_o_signos_no_avanza(cliente, texto_invalido):
    respuesta = cliente.post("/", data={"nombre": "Ana", "apellido": texto_invalido})
    assert respuesta.status_code == 200
    assert "solo puede tener letras" in respuesta.get_data(as_text=True)


@pytest.mark.parametrize("nombre, apellido", [
    ("María José", "Núñez"),
    ("Ana", "Pérez-Cotapos"),
    ("Bernardo", "O'Higgins"),
    ("Begoña", "Argüello"),
])
def test_nombres_reales_con_tildes_guion_o_apostrofo_avanzan(cliente, nombre, apellido):
    respuesta = cliente.post("/", data={"nombre": nombre, "apellido": apellido})
    assert respuesta.status_code == 302


def test_espacios_de_mas_se_ordenan(cliente):
    cliente.post("/", data={"nombre": "  María   José ", "apellido": " Soto "})
    html = cliente.get("/examenes").get_data(as_text=True)
    assert "María José Soto" in html


def test_con_nombre_y_apellido_avanza_al_paso_2(cliente):
    respuesta = cliente.post("/", data={"nombre": "Ana", "apellido": "Soto"})
    assert respuesta.status_code == 302
    assert respuesta.headers["Location"].endswith("/examenes")

    # En el paso 2 la cabecera muestra el nombre de la enfermera
    html = cliente.get("/examenes").get_data(as_text=True)
    assert "Ana Soto" in html
    assert "Cambiar" in html


def test_sin_identificarse_no_se_puede_entrar_al_paso_2(cliente):
    respuesta = cliente.get("/examenes")
    assert respuesta.status_code == 302
    assert respuesta.headers["Location"].endswith("/")


def test_cambiar_borra_el_nombre(cliente):
    cliente.post("/", data={"nombre": "Ana", "apellido": "Soto"})
    cliente.get("/cambiar")
    respuesta = cliente.get("/examenes")
    assert respuesta.status_code == 302
