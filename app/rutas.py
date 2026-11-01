"""Páginas de la aplicación."""

import re

from flask import Blueprint, redirect, render_template, request, session, url_for

paginas = Blueprint("paginas", __name__)

# Largo máximo permitido para nombre y apellido
LARGO_MAXIMO = 60

# Un nombre válido son palabras hechas solo de letras (con tildes, ñ o ü),
# separadas por un espacio, un guion o un apóstrofo.
# Ejemplos válidos: "María José", "Pérez-Cotapos", "O'Higgins".
# [^\W\d_] significa "cualquier letra" (incluye á, é, ñ, ü, etc.).
PATRON_NOMBRE = re.compile(r"[^\W\d_]+([ '\-][^\W\d_]+)*")


def revisar_nombre(texto, campo):
    """Devuelve un mensaje de error si el texto no sirve como nombre, o None si está bien."""
    if not texto:
        return f"Escriba su {campo}."
    if len(texto) > LARGO_MAXIMO:
        return f"El {campo} no puede tener más de {LARGO_MAXIMO} caracteres."
    if not PATRON_NOMBRE.fullmatch(texto):
        return f"El {campo} solo puede tener letras, espacios, guion (-) o apóstrofo (')."
    return None


def limpiar_espacios(texto):
    """Quita espacios al inicio y al final, y deja un solo espacio entre palabras."""
    return " ".join(texto.split())


@paginas.route("/", methods=["GET", "POST"])
def ingreso():
    """Paso 1: la enfermera escribe su nombre y apellido."""
    errores = {}
    nombre = ""
    apellido = ""

    if request.method == "POST":
        nombre = limpiar_espacios(request.form.get("nombre", ""))
        apellido = limpiar_espacios(request.form.get("apellido", ""))

        # Revisamos cada campo; solo guardamos el error si hay uno
        error_nombre = revisar_nombre(nombre, "nombre")
        if error_nombre:
            errores["nombre"] = error_nombre

        error_apellido = revisar_nombre(apellido, "apellido")
        if error_apellido:
            errores["apellido"] = error_apellido

        if not errores:
            # Guardamos el nombre en la sesión para mostrarlo en la cabecera
            session["enfermera"] = f"{nombre} {apellido}"
            return redirect(url_for("paginas.examenes"))

    return render_template(
        "ingreso.html", paso=1, errores=errores, nombre=nombre, apellido=apellido
    )


@paginas.route("/examenes")
def examenes():
    """Paso 2: búsqueda de exámenes (todavía no implementada)."""
    # Sin nombre no se puede buscar: volvemos al paso 1
    if "enfermera" not in session:
        return redirect(url_for("paginas.ingreso"))
    return render_template("examenes.html", paso=2, enfermera=session["enfermera"])


@paginas.route("/cambiar")
def cambiar():
    """Borra el nombre guardado y vuelve al paso 1."""
    session.pop("enfermera", None)
    return redirect(url_for("paginas.ingreso"))
