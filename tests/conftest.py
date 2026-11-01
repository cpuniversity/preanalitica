"""Preparativos que comparten todas las pruebas.

Cada prueba usa su propia base de datos temporal, nunca la base real de data/.
"""

import pytest

from app import create_app
from app.modelos import conectar, crear_tablas

# Exámenes inventados para las pruebas: (nombre, laboratorio, ¿en el recinto?)
EXAMENES_DE_PRUEBA = [
    ("GLUCOSA", "Laboratorio Clínica Dávila Vespucio", 1),
    ("GLUCOSA POST CARGA", "Laboratorio Clínica Dávila Vespucio", 1),
    ("ÁCIDO FÓLICO (FOLATO SÉRICO)", "Laboratorio Externo Prueba", 0),
    ("ÁCIDO ÚRICO", "Laboratorio Clínica Dávila Vespucio", 1),
    ("HEMOGRAMA\nCOMPLETO", "Laboratorio Clínica Dávila Vespucio", 1),
    ("FERRITINA", "Laboratorio Externo Prueba", 0),
    ("EXAMEN SIN LABORATORIO", "", 0),
]


def cargar_examenes_de_prueba(ruta_base):
    conexion = conectar(ruta_base)
    crear_tablas(conexion)
    with conexion:
        for numero, (nombre, laboratorio, en_recinto) in enumerate(EXAMENES_DE_PRUEBA, start=1):
            conexion.execute(
                "INSERT INTO examenes (fila_origen, nombre, laboratorio, se_procesa_en_recinto) "
                "VALUES (?, ?, ?, ?)",
                (numero, nombre, laboratorio, en_recinto),
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
