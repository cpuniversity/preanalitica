"""Páginas de la aplicación."""

import re
from contextlib import closing
from datetime import datetime

from flask import (Blueprint, current_app, jsonify, redirect, render_template,
                   request, session, url_for)

from app.agrupador import Agrupador
from app.auditoria import Auditoria
from app.buscador import Buscador
from app.derivaciones import RevisorDeEstabilidad
from app.modelos import conectar, crear_tablas
from app.repositorio import RepositorioDeExamenes

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
        return f"Escriba su {campo}"
    if len(texto) > LARGO_MAXIMO:
        return f"El {campo} no puede tener más de {LARGO_MAXIMO} caracteres"
    if not PATRON_NOMBRE.fullmatch(texto):
        return f"El {campo} solo puede tener letras, espacios, guion (-) o apóstrofo (')"
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


def abrir_base():
    """Abre la base de datos configurada. Se usa con "with closing(...)" para cerrarla al terminar."""
    conexion = conectar(current_app.config["BASE_DATOS"])
    crear_tablas(conexion)
    return conexion


@paginas.route("/examenes")
def examenes():
    """Paso 2: buscar y elegir exámenes."""
    # Sin nombre no se puede buscar: volvemos al paso 1
    if "enfermera" not in session:
        return redirect(url_for("paginas.ingreso"))
    with closing(abrir_base()) as conexion:
        repositorio = RepositorioDeExamenes(conexion)
        hay_listado = repositorio.hay_listado()
        seleccionados = repositorio.por_ids(session.get("seleccion", []))
    return render_template(
        "examenes.html", paso=2, enfermera=session["enfermera"],
        hay_listado=hay_listado, seleccionados=seleccionados,
    )


@paginas.route("/examenes/sugerencias")
def sugerencias():
    """Devuelve (en formato JSON) las sugerencias para lo que se ha escrito en el buscador."""
    if "enfermera" not in session:
        return jsonify({"error": "Debe identificarse primero"}), 401
    consulta = request.args.get("q", "")
    with closing(abrir_base()) as conexion:
        encontrados = Buscador(RepositorioDeExamenes(conexion).todos()).buscar(consulta)
    seleccion = session.get("seleccion", [])
    return jsonify([
        {
            "id": examen.id,
            "nombre": examen.nombre,
            "etiqueta": examen.etiqueta,
            "ya_seleccionado": examen.id in seleccion,
        }
        for examen in encontrados
    ])


@paginas.route("/examenes/agregar", methods=["POST"])
def agregar_examen():
    """Agrega un examen a la selección (sin repetirlo)."""
    if "enfermera" not in session:
        return redirect(url_for("paginas.ingreso"))
    id_examen = request.form.get("id", type=int)
    with closing(abrir_base()) as conexion:
        existe = RepositorioDeExamenes(conexion).existe(id_examen)
    seleccion = session.get("seleccion", [])
    if existe and id_examen not in seleccion:
        # Se asigna la lista completa para que Flask note el cambio en la sesión
        session["seleccion"] = seleccion + [id_examen]
    return redirect(url_for("paginas.examenes"))


@paginas.route("/examenes/quitar", methods=["POST"])
def quitar_examen():
    """Quita un examen de la selección."""
    id_examen = request.form.get("id", type=int)
    session["seleccion"] = [i for i in session.get("seleccion", []) if i != id_examen]
    return redirect(url_for("paginas.examenes"))


@paginas.route("/tubos")
def tubos():
    """Paso 3: resumen de tubos en orden de extracción."""
    if "enfermera" not in session:
        return redirect(url_for("paginas.ingreso"))
    ahora = datetime.now()
    with closing(abrir_base()) as conexion:
        seleccionados = RepositorioDeExamenes(conexion).por_ids(session.get("seleccion", []))
        # Sin exámenes elegidos no hay nada que mostrar
        if not seleccionados:
            return redirect(url_for("paginas.examenes"))
        resumen = Agrupador().agrupar(seleccionados)
        derivados = RevisorDeEstabilidad().revisar_derivados(seleccionados, ahora)

        # Auditoría: se registra el resultado entregado. Si se recarga la
        # pantalla con los mismos exámenes, no se registra de nuevo.
        if session.get("ultima_auditada") != session["seleccion"]:
            Auditoria(conexion).registrar(session["enfermera"], seleccionados, resumen, derivados, ahora)
            session["ultima_auditada"] = list(session["seleccion"])

    return render_template(
        "tubos.html", paso=3, enfermera=session["enfermera"],
        resumen=resumen, derivados=derivados,
        # Para mostrar en cada tubo una etiqueta con la estabilidad de sus exámenes derivados
        veredictos={d.examen.id: d for d in derivados},
        fecha=ahora.strftime("%d-%m-%Y %H:%M"),
    )


@paginas.route("/nueva-consulta", methods=["POST"])
def nueva_consulta():
    """Borra la selección de exámenes y vuelve al buscador."""
    session.pop("seleccion", None)
    session.pop("ultima_auditada", None)
    return redirect(url_for("paginas.examenes"))


@paginas.route("/favicon.ico")
def favicon():
    """Algunos navegadores piden el ícono en esta dirección: los mandamos al ícono de la app."""
    return redirect(url_for("static", filename="icono.svg"))


# ---------- Páginas de error en español ----------

@paginas.app_errorhandler(404)
def pagina_no_encontrada(error):
    return render_template(
        "error.html", paso=0, enfermera=session.get("enfermera"),
        titulo_error="Página no encontrada",
        mensaje="La dirección que buscó no existe en Preanalítica",
    ), 404


@paginas.app_errorhandler(500)
def error_interno(error):
    return render_template(
        "error.html", paso=0, enfermera=session.get("enfermera"),
        titulo_error="Ocurrió un problema",
        mensaje="La aplicación tuvo un error inesperado. Intente de nuevo; si se repite, avise a la persona a cargo del sistema",
    ), 500


@paginas.route("/cambiar")
def cambiar():
    """Borra el nombre y la selección, y vuelve al paso 1."""
    session.clear()
    return redirect(url_for("paginas.ingreso"))
