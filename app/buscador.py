"""Búsqueda de exámenes tolerante a errores de tipeo y sin importar tildes."""

import re

from rapidfuzz import fuzz

from app.texto import normalizar

# Cantidad máxima de sugerencias que se muestran
MAXIMO_SUGERENCIAS = 8

# Letras mínimas para empezar a buscar
LARGO_MINIMO = 2

# Parecido mínimo (de 0 a 100) para aceptar una palabra con error de tipeo.
# Ejemplo: "glucoza" y "glucosa" tienen un parecido de 86.
PARECIDO_MINIMO = 80

# Las palabras más cortas que esto deben coincidir exactamente con el
# comienzo de una palabra del examen: con 2 o 3 letras un error de tipeo
# cambia demasiado el sentido.
LARGO_PARA_TOLERAR_ERRORES = 4


def separar_palabras(texto):
    """Normaliza el texto y lo separa en palabras, sin signos de puntuación.

    Ejemplo: "ÁCIDO FÓLICO (FOLATO SÉRICO)" -> ["acido", "folico", "folato", "serico"]
    """
    return re.sub(r"[^a-z0-9]+", " ", normalizar(texto)).split()


def nombre_en_una_linea(nombre):
    """Algunos nombres del listado traen saltos de línea: los deja en una línea."""
    return " ".join(nombre.split())


def etiqueta_procesamiento(examen):
    """Dice si el examen se procesa en el recinto o se deriva.

    Devuelve un diccionario con el tipo (para el color) y el texto que se muestra.
    """
    if not examen["laboratorio"]:
        return {"tipo": "aviso", "texto": "Laboratorio: dato no disponible"}
    if examen["se_procesa_en_recinto"]:
        return {"tipo": "recinto", "texto": "Se procesa en el recinto"}
    return {"tipo": "deriva", "texto": "Se deriva a " + nombre_en_una_linea(examen["laboratorio"])}


def cargar_examenes(conexion):
    """Lee los exámenes de la base y los prepara para buscar."""
    examenes = []
    for fila in conexion.execute(
        "SELECT id, nombre, laboratorio, se_procesa_en_recinto FROM examenes"
    ):
        examen = dict(fila)
        examen["nombre"] = nombre_en_una_linea(examen["nombre"])
        examen["palabras"] = separar_palabras(examen["nombre"])
        examenes.append(examen)
    return examenes


def puntaje_palabra(palabra_buscada, palabras_examen):
    """Qué tan bien calza una palabra buscada con el nombre de un examen (0 a 100)."""
    # Coincide con el comienzo de alguna palabra: "fol" en "folico"
    if any(palabra.startswith(palabra_buscada) for palabra in palabras_examen):
        return 100
    if len(palabra_buscada) < LARGO_PARA_TOLERAR_ERRORES:
        return 0
    # Error de tipeo: se compara con la palabra completa y con su comienzo
    # ("glucoz" se compara con "glucos", el comienzo de "glucosa")
    mejor = 0
    for palabra in palabras_examen:
        comienzo = palabra[:len(palabra_buscada)]
        mejor = max(mejor, fuzz.ratio(palabra_buscada, palabra), fuzz.ratio(palabra_buscada, comienzo))
    return mejor


def buscar(consulta, examenes, maximo=MAXIMO_SUGERENCIAS):
    """Devuelve los exámenes que más se parecen a la consulta, del más parecido al menos.

    Todas las palabras escritas deben calzar con el nombre del examen.
    Si nada se parece lo suficiente, devuelve una lista vacía.
    """
    palabras_buscadas = separar_palabras(consulta)
    if len("".join(palabras_buscadas)) < LARGO_MINIMO:
        return []

    encontrados = []
    for examen in examenes:
        puntajes = [puntaje_palabra(p, examen["palabras"]) for p in palabras_buscadas]
        if min(puntajes) < PARECIDO_MINIMO:
            continue
        puntaje = sum(puntajes) / len(puntajes)
        # Preferimos los exámenes cuyo nombre empieza con lo escrito
        empieza_igual = examen["palabras"][0].startswith(palabras_buscadas[0])
        encontrados.append((puntaje, empieza_igual, examen))

    # Orden: más puntaje, luego los que empiezan igual, luego los nombres más cortos
    encontrados.sort(key=lambda e: (-e[0], not e[1], len(e[2]["nombre"]), e[2]["nombre"]))
    return [examen for _, _, examen in encontrados[:maximo]]
