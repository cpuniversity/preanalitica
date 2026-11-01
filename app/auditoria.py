"""Auditoría: registro de cada resumen de tubos entregado y envío semanal.

- Se registra: fecha y hora, nombre de la enfermera, exámenes elegidos y
  resultado entregado (tubos en orden y veredictos de estabilidad).
- Nunca se guarda ningún dato del paciente.
- Cada lunes (o en la primera consulta después del lunes) la app genera un
  CSV con el historial de la semana anterior, lo envía por correo y, solo si
  el envío salió bien, borra ese historial de la base.
"""

import csv
import os
import smtplib
import threading
import time
from contextlib import closing
from datetime import date, datetime, timedelta
from email.message import EmailMessage
from pathlib import Path

import click
from flask import current_app
from flask.cli import with_appcontext

from app.modelos import conectar, crear_tablas

# Cómo se escribe cada veredicto de estabilidad en el registro
VEREDICTOS = {
    "alcanza": "La estabilidad lo permite",
    "al_limite": "Al límite: consultar con el laboratorio",
    "no_alcanza": "La estabilidad NO alcanza",
    "segun_demanda": "Según demanda (sin veredicto)",
    "sin_dia": "Día de proceso: dato no disponible",
    "no_disponible": "Estabilidad: dato no disponible",
}

COLUMNAS_CSV = ["Fecha", "Hora", "Enfermera", "Exámenes", "Total de tubos", "Tubos en orden",
                "Punciones aparte", "Otras muestras", "Exámenes sin tubo", "Derivados y estabilidad"]

# Si un envío automático falla, se vuelve a intentar después de este tiempo
SEGUNDOS_ENTRE_REINTENTOS = 60 * 60


class ErrorDeEnvio(Exception):
    """No se pudo enviar el correo de auditoría."""


# ---------- Registrar ----------

def describir_laboratorio(contenedor):
    if contenedor["en_recinto"]:
        return "recinto"
    return contenedor["laboratorio"] or "laboratorio: dato no disponible"


def describir_contenedor(contenedor):
    """Ejemplo: "2 × Tubo celeste (citrato) (recinto): TIEMPO DE PROTROMBINA"."""
    cantidad = f"{contenedor['cantidad']} × " if contenedor["cantidad"] > 1 else ""
    examenes = ", ".join(examen["nombre"] for examen in contenedor["examenes"])
    return f"{cantidad}{contenedor['nombre_tubo']} ({describir_laboratorio(contenedor)}): {examenes}"


def resumir(resumen, derivados):
    """Convierte el resultado entregado en textos para guardar en la auditoría."""
    return {
        "total_tubos": resumen["total_tubos"],
        "tubos_en_orden": "; ".join(
            f"{tubo['numero']}. {describir_contenedor(tubo)}" for tubo in resumen["tubos"]
        ),
        "punciones_aparte": "; ".join(describir_contenedor(c) for c in resumen["punciones_aparte"]),
        "otras_muestras": ", ".join(examen["nombre"] for examen in resumen["otras_muestras"]),
        "sin_tubo": ", ".join(examen["nombre"] for examen in resumen["sin_tubo"]),
        "derivados": "; ".join(
            f"{d['examen']['nombre']}: {VEREDICTOS[d['resultado']]}"
            + (f" (se procesaría el {d['dia_proceso_nombre']})" if d.get("dia_proceso_nombre") else "")
            for d in derivados
        ),
    }


def registrar(conexion, enfermera, examenes, resumen, derivados, ahora):
    """Guarda en la auditoría un resumen de tubos entregado."""
    datos = resumir(resumen, derivados)
    with conexion:
        conexion.execute(
            "INSERT INTO auditoria (fecha_hora, enfermera, examenes, total_tubos, tubos_en_orden, "
            "punciones_aparte, otras_muestras, sin_tubo, derivados) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                ahora.strftime("%Y-%m-%d %H:%M:%S"),
                enfermera,
                ", ".join(examen["nombre"] for examen in examenes),
                datos["total_tubos"],
                datos["tubos_en_orden"],
                datos["punciones_aparte"],
                datos["otras_muestras"],
                datos["sin_tubo"],
                datos["derivados"],
            ),
        )


# ---------- Exportar ----------

def lunes_de(dia):
    """El lunes de la semana de ese día."""
    return dia - timedelta(days=dia.weekday())


def semana_anterior(hoy):
    """(lunes, domingo) de la semana anterior a hoy."""
    inicio = lunes_de(hoy) - timedelta(days=7)
    return inicio, inicio + timedelta(days=6)


def exportar(conexion, hasta, ruta):
    """Escribe en un CSV los registros anteriores a "hasta" (un lunes). Devuelve cuántos son."""
    filas = conexion.execute(
        "SELECT * FROM auditoria WHERE fecha_hora < ? ORDER BY fecha_hora",
        (f"{hasta.isoformat()} 00:00:00",),
    ).fetchall()
    with open(ruta, "w", encoding="utf-8-sig", newline="") as archivo:
        escritor = csv.writer(archivo, delimiter=";")
        escritor.writerow(COLUMNAS_CSV)
        for fila in filas:
            fecha, hora = fila["fecha_hora"].split(" ")
            escritor.writerow([
                fecha, hora, fila["enfermera"], fila["examenes"], fila["total_tubos"],
                fila["tubos_en_orden"], fila["punciones_aparte"], fila["otras_muestras"],
                fila["sin_tubo"], fila["derivados"],
            ])
    return len(filas)


# ---------- Enviar por correo ----------

def configuracion_correo():
    """Lee la configuración del correo desde las variables de entorno (archivo .env)."""
    return {
        "destinatarios": [d.strip() for d in os.environ.get("CORREO_DESTINATARIOS", "").split(",") if d.strip()],
        "remitente": os.environ.get("CORREO_REMITENTE", "preanalitica@localhost"),
        "servidor": os.environ.get("SMTP_SERVIDOR", ""),
        "puerto": int(os.environ.get("SMTP_PUERTO", "587")),
        "usuario": os.environ.get("SMTP_USUARIO", ""),
        "clave": os.environ.get("SMTP_CLAVE", ""),
        # Mientras no se diga lo contrario, no se envía nada: se guarda el correo como archivo
        "modo_prueba": os.environ.get("CORREO_MODO_PRUEBA", "1") != "0",
    }


def enviar_correo(config, asunto, cuerpo, adjunto, carpeta):
    """Envía el correo con el CSV adjunto. En modo prueba lo guarda como archivo .eml."""
    if not config["destinatarios"]:
        raise ErrorDeEnvio("No hay destinatarios configurados (CORREO_DESTINATARIOS).")

    mensaje = EmailMessage()
    mensaje["From"] = config["remitente"]
    mensaje["To"] = ", ".join(config["destinatarios"])
    mensaje["Subject"] = asunto
    mensaje.set_content(cuerpo)
    mensaje.add_attachment(Path(adjunto).read_bytes(), maintype="text", subtype="csv",
                           filename=Path(adjunto).name)

    if config["modo_prueba"]:
        ruta = Path(carpeta) / f"correo_{Path(adjunto).stem}.eml"
        ruta.write_bytes(bytes(mensaje))
        return ruta

    if not config["servidor"]:
        raise ErrorDeEnvio("No hay servidor de correo configurado (SMTP_SERVIDOR).")
    try:
        with smtplib.SMTP(config["servidor"], config["puerto"], timeout=30) as servidor:
            servidor.starttls()
            if config["usuario"]:
                servidor.login(config["usuario"], config["clave"])
            servidor.send_message(mensaje)
    except (OSError, smtplib.SMTPException) as error:
        raise ErrorDeEnvio(f"No se pudo enviar el correo: {error}") from error
    return None


def envio_semanal(conexion, hoy, config, carpeta, enviar=enviar_correo):
    """Exporta, envía y borra el historial anterior a esta semana.

    Si la semana anterior ya se envió, no hace nada y devuelve None.
    Si el correo falla, lanza ErrorDeEnvio y no borra nada.
    """
    inicio, fin = semana_anterior(hoy)
    ya_enviada = conexion.execute(
        "SELECT 1 FROM envios_auditoria WHERE semana_inicio = ?", (inicio.isoformat(),)
    ).fetchone()
    if ya_enviada:
        return None

    hasta = lunes_de(hoy)
    ruta = Path(carpeta) / f"auditoria_{inicio.isoformat()}.csv"
    registros = exportar(conexion, hasta, ruta)

    asunto = f"Preanalítica: auditoría semanal hasta el domingo {fin.strftime('%d/%m/%Y')}"
    cuerpo = (
        f"Se adjunta el historial de consultas de Preanalítica hasta el domingo "
        f"{fin.strftime('%d/%m/%Y')}.\n"
        f"Consultas registradas: {registros}.\n\n"
        "El archivo no contiene datos de pacientes. Este historial ya fue eliminado de la base."
    )
    enviar(config, asunto, cuerpo, ruta, carpeta)

    # Solo si el envío salió bien se borra el historial enviado
    with conexion:
        conexion.execute("DELETE FROM auditoria WHERE fecha_hora < ?", (f"{hasta.isoformat()} 00:00:00",))
        conexion.execute(
            "INSERT INTO envios_auditoria (semana_inicio, fecha_envio, archivo, registros) VALUES (?, ?, ?, ?)",
            (inicio.isoformat(), datetime.now().isoformat(timespec="seconds"), ruta.name, registros),
        )
    return {"archivo": ruta, "registros": registros, "desde": inicio, "hasta": fin}


# ---------- Envío automático ----------

_bloqueo = threading.Lock()
_semana_enviada = None   # lunes de la semana anterior que ya se revisó en esta ejecución
_ultimo_intento = 0.0    # para no reintentar en cada consulta si el correo falla


def revisar_envio_automatico(app):
    """Se llama en cada consulta: si toca enviar la auditoría, lo hace en segundo plano."""
    global _ultimo_intento
    if app.config.get("TESTING") or not app.config.get("AUDITORIA_AUTOMATICA", True):
        return
    inicio, _ = semana_anterior(date.today())
    if _semana_enviada == inicio or time.time() - _ultimo_intento < SEGUNDOS_ENTRE_REINTENTOS:
        return
    if not _bloqueo.acquire(blocking=False):
        return  # ya hay un envío en curso
    _ultimo_intento = time.time()
    ruta_base = app.config["BASE_DATOS"]

    def tarea():
        global _semana_enviada, _ultimo_intento
        try:
            with closing(conectar(ruta_base)) as conexion:
                crear_tablas(conexion)
                envio_semanal(conexion, date.today(), configuracion_correo(), Path(ruta_base).parent)
            _semana_enviada = inicio
            _ultimo_intento = 0.0
        except Exception as error:  # se reintenta más tarde; la enfermera no se ve afectada
            app.logger.warning("No se pudo enviar la auditoría semanal: %s", error)
        finally:
            _bloqueo.release()

    threading.Thread(target=tarea, daemon=True).start()


@click.command("auditoria-semanal")
@with_appcontext
def comando_auditoria_semanal():
    """Envía ahora la auditoría de la semana anterior (si no se envió ya)."""
    ruta_base = current_app.config["BASE_DATOS"]
    with closing(conectar(ruta_base)) as conexion:
        crear_tablas(conexion)
        try:
            resultado = envio_semanal(conexion, date.today(), configuracion_correo(), Path(ruta_base).parent)
        except ErrorDeEnvio as error:
            raise click.ClickException(f"{error} No se borró nada del historial.")
    if resultado is None:
        click.echo("La auditoría de la semana anterior ya fue enviada.")
        return
    click.echo(f"Auditoría enviada: {resultado['registros']} consultas hasta el domingo "
               f"{resultado['hasta'].strftime('%d/%m/%Y')}.")
    click.echo(f"Archivo: {resultado['archivo']}")
    if configuracion_correo()["modo_prueba"]:
        click.echo("Modo prueba: el correo se guardó como archivo .eml en la carpeta data, no se envió.")
