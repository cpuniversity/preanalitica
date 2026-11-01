"""Páginas de la aplicación."""

import re
from contextlib import closing

from flask import (Blueprint, current_app, jsonify, redirect, render_template,
                   request, session, url_for)

from app.buscador import buscar, cargar_examenes, etiqueta_procesamiento, nombre_en_una_linea
from app.modelos import conectar, crear_tablas

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


def abrir_base():
    """Abre la base de datos configurada. Se usa con "with closing(...)" para cerrarla al terminar."""
    conexion = conectar(current_app.config["BASE_DATOS"])
    crear_tablas(conexion)
    return conexion


def leer_seleccionados(conexion):
    """Devuelve los exámenes elegidos por la enfermera, en el orden en que los agregó."""
    seleccionados = []
    for id_examen in session.get("seleccion", []):
        fila = conexion.execute(
            "SELECT id, nombre, laboratorio, se_procesa_en_recinto FROM examenes WHERE id = ?",
            (id_examen,),
        ).fetchone()
        if fila:  # si el listado se volvió a importar, un id antiguo puede ya no existir
            examen = dict(fila)
            examen["nombre"] = nombre_en_una_linea(examen["nombre"])
            examen["etiqueta"] = etiqueta_procesamiento(examen)
            seleccionados.append(examen)
    return seleccionados


@paginas.route("/examenes")
def examenes():
    """Paso 2: buscar y elegir exámenes."""
    # Sin nombre no se puede buscar: volvemos al paso 1
    if "enfermera" not in session:
        return redirect(url_for("paginas.ingreso"))
    with closing(abrir_base()) as conexion:
        hay_listado = conexion.execute("SELECT COUNT(*) FROM examenes").fetchone()[0] > 0
        seleccionados = leer_seleccionados(conexion)
    return render_template(
        "examenes.html", paso=2, enfermera=session["enfermera"],
        hay_listado=hay_listado, seleccionados=seleccionados,
    )


@paginas.route("/examenes/sugerencias")
def sugerencias():
    """Devuelve (en formato JSON) las sugerencias para lo que se ha escrito en el buscador."""
    if "enfermera" not in session:
        return jsonify({"error": "Debe identificarse primero."}), 401
    consulta = request.args.get("q", "")
    with closing(abrir_base()) as conexion:
        encontrados = buscar(consulta, cargar_examenes(conexion))
    seleccion = session.get("seleccion", [])
    return jsonify([
        {
            "id": examen["id"],
            "nombre": examen["nombre"],
            "etiqueta": etiqueta_procesamiento(examen),
            "ya_seleccionado": examen["id"] in seleccion,
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
        existe = conexion.execute("SELECT 1 FROM examenes WHERE id = ?", (id_examen,)).fetchone()
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
    """Paso 3: resumen de tubos (la agrupación todavía no está implementada)."""
    if "enfermera" not in session:
        return redirect(url_for("paginas.ingreso"))
    with closing(abrir_base()) as conexion:
        seleccionados = leer_seleccionados(conexion)
    # Sin exámenes elegidos no hay nada que mostrar
    if not seleccionados:
        return redirect(url_for("paginas.examenes"))
    return render_template(
        "tubos.html", paso=3, enfermera=session["enfermera"], seleccionados=seleccionados
    )


@paginas.route("/nueva-consulta", methods=["POST"])
def nueva_consulta():
    """Borra la selección de exámenes y vuelve al buscador."""
    session.pop("seleccion", None)
    return redirect(url_for("paginas.examenes"))


@paginas.route("/cambiar")
def cambiar():
    """Borra el nombre y la selección, y vuelve al paso 1."""
    session.clear()
    return redirect(url_for("paginas.ingreso"))
