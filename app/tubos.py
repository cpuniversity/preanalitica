"""Tipos de tubo, orden de extracción (CLSI) y lectura del tubo desde el listado.

Todas las reglas de este archivo fueron definidas por el tecnólogo médico.
"""

import re

from app.texto import normalizar

# Tipos de tubo o contenedor de sangre.
# "orden" es la posición en el orden de extracción según CLSI.
# Los que tienen orden None no entran en el orden: son una punción aparte.
# "exclusivo" = nunca se comparte con otro examen.
TIPOS_DE_TUBO = {
    "hemocultivo":      {"nombre": "Frasco de hemocultivo",                 "orden": 1,    "exclusivo": True},
    "celeste":          {"nombre": "Tubo celeste (citrato)",                "orden": 2,    "exclusivo": False},
    "amarillo":         {"nombre": "Tubo amarillo con gel",                 "orden": 3,    "exclusivo": False},
    "rojo":             {"nombre": "Tubo rojo",                             "orden": 4,    "exclusivo": False},
    "verde":            {"nombre": "Tubo verde (heparina)",                 "orden": 5,    "exclusivo": False},
    "jeringa-venosa":   {"nombre": "Jeringa con heparina (gases venosos)",  "orden": 6,    "exclusivo": True},
    "lila":             {"nombre": "Tubo lila (EDTA)",                      "orden": 7,    "exclusivo": False},
    "gris":             {"nombre": "Tubo gris (fluoruro)",                  "orden": 8,    "exclusivo": False},
    "jeringa-arterial": {"nombre": "Jeringa con heparina (gases arteriales)", "orden": None, "exclusivo": True},
}

# Palabras clave para reconocer cada tubo en el texto del listado
REGLAS = [
    ("hemocultivo", r"hemocultivo"),
    ("jeringa",     r"jeringa"),
    ("celeste",     r"celeste|citrato"),
    # "con gel" o "tapa amarilla" es el mismo tubo; "sin gel" no cuenta
    ("amarillo",    r"amarill|(?<!sin )\bgel\b"),
    ("rojo",        r"\broj[oa]s?\b"),
    ("verde",       r"verde|heparina"),
    ("lila",        r"\blila\b|edta"),
    ("gris",        r"\bgris\b|fluoruro|oxalato"),
]

# Valor que indica que el examen no es de sangre (va en "Otras muestras")
OTRA_MUESTRA = "otra muestra"


class FormatoDeTuboInvalido(ValueError):
    """El texto de tubos no tiene el formato esperado."""


def parte_de_adultos(texto):
    """Si el texto trae indicaciones para adultos y pediátricos, deja solo la de adultos."""
    texto = re.split(r"pediatric", texto)[0]
    return re.sub(r"^\s*adultos?\s*:\s*", "", texto).strip()


def es_sangre(texto):
    """¿La muestra es de sangre? Mira con qué empieza la descripción."""
    return bool(re.match(r"(sangre|suero|plasma|tubo|jeringa|frasco hemocultivo|\d+\s*(tubo|frasco))", texto))


# Comienzos de texto que indican claramente una muestra que no es sangre.
# Puede haber una cantidad antes: "10 ml orina", "1 torula", "1 - 5 ml del tracto...".
PATRON_OTRA_MUESTRA = (
    r"(\d+(\s*-\s*\d+)?\s*(ml\s+)?)?"
    r"(orina|fco orina|deposicion|medula|torula|hisopado|lba|liquido|frotis|lcr|raspado"
    r"|expectoracion|saliva|vellosidades|fibroblastos|secrecion|escamas|piel|set graham"
    r"|placa|cultivo|tarjeta pku|papel filtro|tomar en frasco|del tracto|abscesos"
    r"|muestras? (de|en|endocervical)|enviar (calculo|gusano))"
)


def es_otra_muestra(texto):
    """¿La descripción empieza con un tipo de muestra que no es sangre?"""
    return bool(re.match(PATRON_OTRA_MUESTRA, texto))


def tubos_mencionados(muestra):
    """Lista los tipos de tubo que menciona el texto (solo la parte de adultos)."""
    texto = parte_de_adultos(normalizar(muestra))
    tipos = [codigo for codigo, patron in REGLAS if re.search(patron, texto)]
    # La jeringa de gases trae heparina: no es un tubo verde aparte
    if "jeringa" in tipos and "verde" in tipos:
        tipos.remove("verde")
    return tipos


def clasificar(muestra, nombre_examen):
    """Lee el tubo desde el texto del listado.

    Devuelve el tubo en el formato de leer_tubos (por ejemplo "amarillo" o
    "2 celeste"), OTRA_MUESTRA si no es sangre, o "" si la app no puede
    decidirlo sola (queda para que lo revise el tecnólogo médico).
    """
    texto = parte_de_adultos(normalizar(muestra))
    if not texto:
        return ""  # el listado no dice la muestra: dato no disponible
    if not es_sangre(texto):
        if es_otra_muestra(texto):
            return OTRA_MUESTRA
        return ""  # no se sabe qué muestra es: lo revisa el tecnólogo médico

    tipos = tubos_mencionados(muestra)
    if len(tipos) != 1:
        return ""  # ninguno o varios tubos: lo revisa el tecnólogo médico

    tipo = tipos[0]
    if tipo == "jeringa":
        nombre = normalizar(nombre_examen)
        if "arterial" in nombre:
            tipo = "jeringa-arterial"
        elif "venos" in nombre:
            tipo = "jeringa-venosa"
        else:
            return ""

    # Cantidad, si el listado la indica: "2 tubos", "2 frascos"
    cantidad = re.search(r"(\d+)\s*(tubos?|frascos?)\b", texto)
    if cantidad and int(cantidad.group(1)) > 1:
        return f"{int(cantidad.group(1))} {tipo}"
    return tipo


def leer_tubos(texto):
    """Convierte el texto de tubos en una lista de opciones.

    Formato (el mismo que usa el tecnólogo médico en la tabla de revisión):
      - "amarillo"            -> un tubo amarillo
      - "2 celeste"           -> dos tubos celeste
      - "lila + celeste"      -> el examen necesita ambos tubos
      - "amarillo o rojo"     -> cualquiera de los dos (se prefiere el primero)

    Devuelve, por ejemplo, [[("lila", 1), ("celeste", 1)]] para "lila + celeste".
    """
    opciones = []
    for texto_opcion in normalizar(texto).split(" o "):
        opcion = []
        for parte in texto_opcion.split("+"):
            coincide = re.fullmatch(r"(?:(\d+)\s+)?([a-z-]+)", parte.strip())
            if not coincide or coincide.group(2) not in TIPOS_DE_TUBO:
                raise FormatoDeTuboInvalido(f"No se reconoce el tubo «{parte.strip()}»")
            cantidad = int(coincide.group(1) or 1)
            if cantidad < 1:
                raise FormatoDeTuboInvalido(f"Cantidad inválida en «{parte.strip()}»")
            opcion.append((coincide.group(2), cantidad))
        opciones.append(opcion)
    return opciones


def frases_con(texto, patron):
    """Devuelve las frases del texto que contienen el patrón, tal como están escritas.

    Se usa para advertencias (ayuno, luz): la enfermera lee la frase original
    y la app no la interpreta. Así "no requiere ayuno" no se confunde con "ayuno".
    """
    frases = []
    for linea in texto.split("\n"):
        for frase in re.split(r"(?<=\.)\s+", linea):
            frase = " ".join(frase.split())
            if frase and re.search(patron, normalizar(frase)) and frase not in frases:
                frases.append(frase)
    return frases
