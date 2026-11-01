"""Crea la aplicación Flask de Preanalítica."""

import os

from flask import Flask


def create_app():
    app = Flask(__name__)

    # Clave para firmar la "sesión" (donde guardamos el nombre de la enfermera
    # mientras usa la app). En el prototipo usamos una clave de desarrollo;
    # si existe la variable de entorno SECRET_KEY, se usa esa.
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "clave-solo-para-desarrollo")

    # Ubicación de la base de datos SQLite
    from app.modelos import RUTA_BASE_DATOS
    app.config["BASE_DATOS"] = os.environ.get("BASE_DATOS", str(RUTA_BASE_DATOS))

    # Filtro para las plantillas: {{ texto|sin_punto }} deja el texto en una sola
    # línea y sin punto final (el listado a veces lo trae y a veces no)
    @app.template_filter("sin_punto")
    def sin_punto(texto):
        return " ".join((texto or "").split()).rstrip(". ")

    # Registramos las páginas definidas en rutas.py
    from app.rutas import paginas
    app.register_blueprint(paginas)

    # Comando de terminal: flask --app app importar <archivo.csv>
    from app.importador import comando_importar
    app.cli.add_command(comando_importar)

    # Auditoría semanal: la app la envía sola cuando corresponde (ver auditoria.py).
    # También se puede enviar a mano: flask --app app auditoria-semanal
    from app.auditoria import comando_auditoria_semanal, revisar_envio_automatico
    app.config["AUDITORIA_AUTOMATICA"] = os.environ.get("AUDITORIA_AUTOMATICA", "1") != "0"
    app.before_request(lambda: revisar_envio_automatico(app))
    app.cli.add_command(comando_auditoria_semanal)

    return app
