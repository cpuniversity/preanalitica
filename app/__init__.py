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

    # Registramos las páginas definidas en rutas.py
    from app.rutas import paginas
    app.register_blueprint(paginas)

    # Comando de terminal: flask --app app importar <archivo.csv>
    from app.importador import comando_importar
    app.cli.add_command(comando_importar)

    return app
