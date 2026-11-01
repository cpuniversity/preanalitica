"""Funciones para preparar textos antes de compararlos."""

import unicodedata


def normalizar(texto):
    """Pasa a minúsculas, quita tildes y deja un solo espacio entre palabras.

    Ejemplo: "  ÁCIDO   Úrico " -> "acido urico"
    """
    sin_tildes = "".join(
        letra for letra in unicodedata.normalize("NFD", texto)
        if unicodedata.category(letra) != "Mn"
    )
    return " ".join(sin_tildes.lower().split())
