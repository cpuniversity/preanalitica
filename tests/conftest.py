"""Preparativos que comparten todas las pruebas.

Cada prueba usa su propia base de datos temporal, nunca la base real de data/.
"""

import pytest

from app import create_app
from app.modelos import conectar, crear_tablas

# Exámenes inventados para las pruebas: (nombre, laboratorio, ¿en el recinto?, tubos)
EXAMENES_DE_PRUEBA = [
    ("GLUCOSA", "Laboratorio Clínica Dávila Vespucio", 1, "gris"),
    ("GLUCOSA POST CARGA", "Laboratorio Clínica Dávila Vespucio", 1, "gris"),
    ("ÁCIDO FÓLICO (FOLATO SÉRICO)", "Laboratorio Externo Prueba", 0, "amarillo"),
    ("ÁCIDO ÚRICO", "Laboratorio Clínica Dávila Vespucio", 1, "amarillo"),
    ("HEMOGRAMA\nCOMPLETO", "Laboratorio Clínica Dávila Vespucio", 1, "lila"),
    ("FERRITINA", "Laboratorio Externo Prueba", 0, "amarillo"),
    ("EXAMEN SIN LABORATORIO", "", 0, ""),
    ("ORINA COMPLETA", "Laboratorio Clínica Dávila Vespucio", 1, "otra muestra"),
]


def cargar_examenes_de_prueba(ruta_base):
    conexion = conectar(ruta_base)
    crear_tablas(conexion)
    with conexion:
        for numero, (nombre, laboratorio, en_recinto, tubos) in enumerate(EXAMENES_DE_PRUEBA, start=1):
            conexion.execute(
                "INSERT INTO examenes (fila_origen, nombre, laboratorio, se_procesa_en_recinto, tubos, muestra) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (numero, nombre, laboratorio, en_recinto, tubos, "MUESTRA DE PRUEBA"),
            )
    conexion.close()


@pytest.fixture
def ruta_base(tmp_path, monkeypatch):
    """Base temporal vacía. La app la usa en vez de la base real."""
    ruta = tmp_path / "prueba.db"
    monkeypatch.setenv("BASE_DATOS", str(ruta))
    return ruta


@pytest.fixture
def cliente(ruta_base):
    """Un "navegador de prueba" que conversa con la app sin abrir el navegador real."""
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


@pytest.fixture
def cliente_con_examenes(ruta_base, cliente):
    """Cliente con exámenes inventados cargados y una enfermera ya identificada."""
    cargar_examenes_de_prueba(ruta_base)
    cliente.post("/", data={"nombre": "Ana", "apellido": "Soto"})
    return cliente
