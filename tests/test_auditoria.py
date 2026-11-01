"""Pruebas de la auditoría. Nunca se envía un correo real."""

import csv
import email
from datetime import date, datetime

import pytest

from app import create_app
from app.auditoria import (
    ErrorDeEnvio,
    enviar_correo,
    envio_semanal,
    exportar,
    registrar,
    resumir,
    revisar_envio_automatico,
    semana_anterior,
)
from app.modelos import conectar, crear_tablas
from tests.conftest import cargar_examenes_de_prueba

# Noviembre 2026: lunes 2, lunes 9, miércoles 11
LUNES_9 = date(2026, 11, 9)

RESUMEN = {
    "total_tubos": 2,
    "tubos": [
        {"numero": 1, "cantidad": 1, "nombre_tubo": "Tubo amarillo con gel", "en_recinto": False,
         "laboratorio": "Laboratorio Externo Prueba", "examenes": [{"nombre": "FERRITINA"}]},
        {"numero": 2, "cantidad": 2, "nombre_tubo": "Tubo lila (EDTA)", "en_recinto": True,
         "laboratorio": "Laboratorio Clínica Dávila Vespucio",
         "examenes": [{"nombre": "HEMOGRAMA"}, {"nombre": "VHS"}]},
    ],
    "punciones_aparte": [],
    "otras_muestras": [{"nombre": "ORINA COMPLETA"}],
    "sin_tubo": [],
}
DERIVADOS = [{"examen": {"nombre": "FERRITINA"}, "resultado": "no_alcanza", "dia_proceso_nombre": "lunes 9/11"}]

CONFIG_PRUEBA = {"destinatarios": ["direccion.de.prueba@example.com"], "remitente": "app@example.com",
                 "servidor": "", "puerto": 587, "usuario": "", "clave": "", "modo_prueba": True}


@pytest.fixture
def conexion(tmp_path):
    con = conectar(tmp_path / "prueba.db")
    crear_tablas(con)
    yield con
    con.close()


def registrar_en(conexion, momento, enfermera="Ana Soto"):
    registrar(conexion, enfermera, [{"nombre": "FERRITINA"}], RESUMEN, DERIVADOS, momento)


def cantidad_registros(conexion):
    return conexion.execute("SELECT COUNT(*) FROM auditoria").fetchone()[0]


# ---------- Qué se registra ----------

def test_resumen_del_resultado_entregado():
    datos = resumir(RESUMEN, DERIVADOS)
    assert datos["total_tubos"] == 2
    assert datos["tubos_en_orden"] == (
        "1. Tubo amarillo con gel (Laboratorio Externo Prueba): FERRITINA; "
        "2. 2 × Tubo lila (EDTA) (recinto): HEMOGRAMA, VHS"
    )
    assert datos["otras_muestras"] == "ORINA COMPLETA"
    assert datos["derivados"] == "FERRITINA: La estabilidad NO alcanza (se procesaría el lunes 9/11)"


def test_la_tabla_no_tiene_datos_del_paciente(conexion):
    columnas = {fila[1] for fila in conexion.execute("PRAGMA table_info(auditoria)")}
    assert columnas == {"id", "fecha_hora", "enfermera", "examenes", "total_tubos", "tubos_en_orden",
                        "punciones_aparte", "otras_muestras", "sin_tubo", "derivados"}


# ---------- Registro al ver los tubos ----------

def leer_auditoria(ruta_base):
    con = conectar(ruta_base)
    filas = [dict(f) for f in con.execute("SELECT * FROM auditoria ORDER BY id")]
    con.close()
    return filas


def agregar(cliente, consulta):
    id_examen = cliente.get(f"/examenes/sugerencias?q={consulta}").get_json()[0]["id"]
    cliente.post("/examenes/agregar", data={"id": id_examen})


def test_ver_los_tubos_queda_registrado(cliente_con_examenes, ruta_base):
    agregar(cliente_con_examenes, "hemograma")
    agregar(cliente_con_examenes, "ferritina")
    cliente_con_examenes.get("/tubos")

    filas = leer_auditoria(ruta_base)
    assert len(filas) == 1
    assert filas[0]["enfermera"] == "Ana Soto"
    assert filas[0]["examenes"] == "HEMOGRAMA COMPLETO, FERRITINA"
    assert filas[0]["total_tubos"] == 2
    assert "Tubo lila (EDTA)" in filas[0]["tubos_en_orden"]
    assert "FERRITINA:" in filas[0]["derivados"]


def test_recargar_la_pantalla_no_duplica(cliente_con_examenes, ruta_base):
    agregar(cliente_con_examenes, "hemograma")
    cliente_con_examenes.get("/tubos")
    cliente_con_examenes.get("/tubos")
    assert len(leer_auditoria(ruta_base)) == 1


def test_cambiar_los_examenes_es_otra_consulta(cliente_con_examenes, ruta_base):
    agregar(cliente_con_examenes, "hemograma")
    cliente_con_examenes.get("/tubos")
    agregar(cliente_con_examenes, "ferritina")
    cliente_con_examenes.get("/tubos")
    assert len(leer_auditoria(ruta_base)) == 2


def test_nueva_consulta_con_los_mismos_examenes_se_registra(cliente_con_examenes, ruta_base):
    agregar(cliente_con_examenes, "hemograma")
    cliente_con_examenes.get("/tubos")
    cliente_con_examenes.post("/nueva-consulta")
    agregar(cliente_con_examenes, "hemograma")
    cliente_con_examenes.get("/tubos")
    assert len(leer_auditoria(ruta_base)) == 2


def test_la_enfermera_no_ve_un_historial(cliente_con_examenes):
    # El registro es solo para auditoría: ninguna página muestra búsquedas anteriores
    agregar(cliente_con_examenes, "hemograma")
    cliente_con_examenes.get("/tubos")
    cliente_con_examenes.post("/nueva-consulta")
    html = cliente_con_examenes.get("/examenes").get_data(as_text=True)
    assert "HEMOGRAMA" not in html


# ---------- Semana y exportación ----------

@pytest.mark.parametrize("hoy", [date(2026, 11, 9), date(2026, 11, 11), date(2026, 11, 15)])
def test_semana_anterior_es_de_lunes_a_domingo(hoy):
    assert semana_anterior(hoy) == (date(2026, 11, 2), date(2026, 11, 8))


def test_exportar_solo_lo_anterior_a_esta_semana(conexion, tmp_path):
    registrar_en(conexion, datetime(2026, 11, 3, 10, 0))
    registrar_en(conexion, datetime(2026, 11, 8, 23, 59))
    registrar_en(conexion, datetime(2026, 11, 9, 0, 1))  # ya es la semana actual
    ruta = tmp_path / "auditoria.csv"

    assert exportar(conexion, LUNES_9, ruta) == 2
    with open(ruta, encoding="utf-8-sig", newline="") as archivo:
        filas = list(csv.reader(archivo, delimiter=";"))
    assert filas[0][:3] == ["Fecha", "Hora", "Enfermera"]
    assert [f[0] for f in filas[1:]] == ["2026-11-03", "2026-11-08"]


# ---------- Envío semanal ----------

def test_envio_exitoso_borra_lo_enviado_y_conserva_la_semana_actual(conexion, tmp_path):
    registrar_en(conexion, datetime(2026, 11, 3, 10, 0))
    registrar_en(conexion, datetime(2026, 11, 9, 8, 0))
    enviados = []

    resultado = envio_semanal(conexion, LUNES_9, CONFIG_PRUEBA, tmp_path,
                              enviar=lambda *datos: enviados.append(datos))

    assert len(enviados) == 1
    assert resultado["registros"] == 1
    assert resultado["archivo"].name == "auditoria_2026-11-02.csv"
    assert resultado["archivo"].exists()  # el CSV se conserva como respaldo
    assert cantidad_registros(conexion) == 1  # queda solo el del lunes 9


def test_no_se_envia_dos_veces_la_misma_semana(conexion, tmp_path):
    enviados = []
    envio_semanal(conexion, LUNES_9, CONFIG_PRUEBA, tmp_path, enviar=lambda *d: enviados.append(d))
    segundo = envio_semanal(conexion, date(2026, 11, 11), CONFIG_PRUEBA, tmp_path,
                            enviar=lambda *d: enviados.append(d))
    assert segundo is None
    assert len(enviados) == 1


def test_si_el_correo_falla_no_se_borra_nada(conexion, tmp_path):
    registrar_en(conexion, datetime(2026, 11, 3, 10, 0))

    def falla(*datos):
        raise ErrorDeEnvio("servidor caído")

    with pytest.raises(ErrorDeEnvio):
        envio_semanal(conexion, LUNES_9, CONFIG_PRUEBA, tmp_path, enviar=falla)
    assert cantidad_registros(conexion) == 1
    # Como no quedó marcado como enviado, se reintenta más tarde
    assert conexion.execute("SELECT COUNT(*) FROM envios_auditoria").fetchone()[0] == 0


def test_semana_sin_consultas_igual_se_informa(conexion, tmp_path):
    enviados = []
    resultado = envio_semanal(conexion, LUNES_9, CONFIG_PRUEBA, tmp_path, enviar=lambda *d: enviados.append(d))
    assert resultado["registros"] == 0
    assert len(enviados) == 1


# ---------- Correo ----------

def test_modo_prueba_guarda_el_correo_como_archivo(tmp_path):
    adjunto = tmp_path / "auditoria_2026-11-02.csv"
    adjunto.write_text("Fecha;Hora\n", encoding="utf-8-sig")

    ruta = enviar_correo(CONFIG_PRUEBA, "Asunto de prueba", "Cuerpo", adjunto, tmp_path)

    mensaje = email.message_from_bytes(ruta.read_bytes())
    assert mensaje["To"] == "direccion.de.prueba@example.com"
    assert mensaje["Subject"] == "Asunto de prueba"
    adjuntos = [parte.get_filename() for parte in mensaje.walk() if parte.get_filename()]
    assert adjuntos == ["auditoria_2026-11-02.csv"]


def test_sin_destinatarios_no_se_envia(tmp_path):
    adjunto = tmp_path / "a.csv"
    adjunto.write_text("x")
    with pytest.raises(ErrorDeEnvio, match="destinatarios"):
        enviar_correo({**CONFIG_PRUEBA, "destinatarios": []}, "A", "B", adjunto, tmp_path)


def test_envio_real_sin_servidor_configurado_avisa(tmp_path):
    adjunto = tmp_path / "a.csv"
    adjunto.write_text("x")
    with pytest.raises(ErrorDeEnvio, match="servidor"):
        enviar_correo({**CONFIG_PRUEBA, "modo_prueba": False}, "A", "B", adjunto, tmp_path)


def test_envio_real_usa_el_servidor_configurado(tmp_path, monkeypatch):
    """Se reemplaza el servidor de correo por uno simulado: no sale nada a internet."""
    enviados = []

    class ServidorSimulado:
        def __init__(self, servidor, puerto, timeout):
            enviados.append(("conexion", servidor, puerto))
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
        def starttls(self):
            enviados.append("starttls")
        def login(self, usuario, clave):
            enviados.append(("login", usuario))
        def send_message(self, mensaje):
            enviados.append(("mensaje", mensaje["To"]))

    monkeypatch.setattr("app.auditoria.smtplib.SMTP", ServidorSimulado)
    adjunto = tmp_path / "a.csv"
    adjunto.write_text("x")
    config = {**CONFIG_PRUEBA, "modo_prueba": False, "servidor": "smtp.example.com", "usuario": "usuario"}

    enviar_correo(config, "A", "B", adjunto, tmp_path)

    assert enviados == [("conexion", "smtp.example.com", 587), "starttls", ("login", "usuario"),
                        ("mensaje", "direccion.de.prueba@example.com")]


# ---------- Envío automático ----------

def test_en_pruebas_no_se_envia_automaticamente(ruta_base, monkeypatch):
    llamado = []
    monkeypatch.setattr("app.auditoria.threading.Thread", lambda **k: llamado.append(k))
    app = create_app()
    app.config["TESTING"] = True
    revisar_envio_automatico(app)
    assert llamado == []


def test_comando_auditoria_semanal_en_modo_prueba(ruta_base, monkeypatch):
    monkeypatch.setenv("CORREO_DESTINATARIOS", "direccion.de.prueba@example.com")
    monkeypatch.setenv("CORREO_MODO_PRUEBA", "1")
    cargar_examenes_de_prueba(ruta_base)

    resultado = create_app().test_cli_runner().invoke(args=["auditoria-semanal"])

    assert resultado.exit_code == 0
    assert "Auditoría enviada" in resultado.output
    assert "Modo prueba" in resultado.output
    assert list(ruta_base.parent.glob("correo_auditoria_*.eml"))
