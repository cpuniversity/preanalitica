"""Pruebas de las clases del dominio y de los patrones de diseño (Repositorio y Strategy)."""

from datetime import datetime

from app.auditoria import CorreoDePrueba, CorreoSMTP, crear_enviador
from app.derivaciones import CalendarioDeProceso
from app.examen import Examen
from app.importador import Importador, LectorDeListado
from app.modelos import conectar, crear_tablas
from app.repositorio import RepositorioDeExamenes
from app.tubos import TIPOS_DE_TUBO
from tests.conftest import cargar_examenes_de_prueba

CONFIG = {"destinatarios": ["direccion.de.prueba@example.com"], "remitente": "app@example.com",
          "servidor": "", "puerto": 587, "usuario": "", "clave": "", "modo_prueba": True}


# ---------- Examen ----------

def test_examen_deja_el_nombre_en_una_linea():
    assert Examen(nombre="HEMOGRAMA\nCOMPLETO").nombre == "HEMOGRAMA COMPLETO"


def test_examen_derivado_solo_si_tiene_laboratorio_y_no_es_del_recinto():
    assert Examen(nombre="A", laboratorio="Laboratorio Externo Prueba").es_derivado()
    assert not Examen(nombre="B", laboratorio="Recinto", se_procesa_en_recinto=True).es_derivado()
    assert not Examen(nombre="C", laboratorio="").es_derivado()


def test_examen_con_tubo_no_reconocido_no_tiene_opciones():
    assert Examen(nombre="A", tubos="").opciones_de_tubo() is None
    assert Examen(nombre="B", tubos="morado").opciones_de_tubo() is None
    assert Examen(nombre="C", tubos="amarillo o rojo").opciones_de_tubo() == [[("amarillo", 1)], [("rojo", 1)]]


# ---------- TipoDeTubo y CalendarioDeProceso ----------

def test_gases_arteriales_son_puncion_aparte():
    assert TIPOS_DE_TUBO["jeringa-arterial"].es_puncion_aparte()
    assert not TIPOS_DE_TUBO["lila"].es_puncion_aparte()


def test_calendario_de_proceso():
    calendario = CalendarioDeProceso("MA Y JU", feriado=lambda dia: False)
    assert calendario.describir() == "Martes y jueves"
    assert calendario.se_entiende()
    # Jueves 5/11 a las 10:00: el siguiente día de proceso es el martes 10/11
    assert calendario.dia_de_proceso(datetime(2026, 11, 5, 10, 0)).day == 10
    assert CalendarioDeProceso("SEGÚN DEMANDA").es_segun_demanda()


# ---------- Repositorio ----------

def test_repositorio_entrega_examenes_en_el_orden_pedido(tmp_path):
    ruta = tmp_path / "prueba.db"
    cargar_examenes_de_prueba(ruta)
    repositorio = RepositorioDeExamenes(conectar(ruta))
    todos = repositorio.todos()
    ids = [todos[2].id, todos[0].id, 9999]  # 9999 no existe: se omite

    assert [e.id for e in repositorio.por_ids(ids)] == [todos[2].id, todos[0].id]
    assert repositorio.hay_listado()
    assert not repositorio.existe(9999)


def test_repositorio_sin_listado(tmp_path):
    conexion = conectar(tmp_path / "vacia.db")
    crear_tablas(conexion)
    assert not RepositorioDeExamenes(conexion).hay_listado()


# ---------- Strategy: enviador de correo ----------

def test_modo_prueba_usa_el_correo_de_prueba(tmp_path):
    assert isinstance(crear_enviador(CONFIG, tmp_path), CorreoDePrueba)


def test_modo_real_usa_smtp(tmp_path):
    assert isinstance(crear_enviador({**CONFIG, "modo_prueba": False}, tmp_path), CorreoSMTP)


# ---------- Strategy: lector del listado ----------

class LectorFalso(LectorDeListado):
    """Imita a un lector de otro formato (por ejemplo Excel): el Importador no necesita cambiar."""

    def leer(self, ruta):
        registro = {
            "fila_origen": 2, "codigo_vidalab": "1", "codigo_medisyn": "2", "nombre": "EXAMEN PRUEBA",
            "dias_proceso": "LU A VI", "tiempo_respuesta": "1", "muestra": "SANGRE, TUBO TAPA LILA",
            "codigo_lab_derivado": "", "laboratorio": "Laboratorio Clínica Dávila Vespucio",
            "procedimientos": "", "instrucciones": "", "estabilidad": "", "se_procesa_en_recinto": 1,
            "tubos": "lila", "tubos_automatico": "lila",
        }
        return [registro], []


def test_el_importador_acepta_otro_lector(tmp_path):
    conexion = conectar(tmp_path / "prueba.db")
    resumen = Importador(conexion, lector=LectorFalso()).importar(
        tmp_path / "listado.xlsx", tmp_path / "reporte.csv", tmp_path / "tubos.csv")

    assert resumen["examenes"] == 1
    assert [e.nombre for e in RepositorioDeExamenes(conexion).todos()] == ["EXAMEN PRUEBA"]
