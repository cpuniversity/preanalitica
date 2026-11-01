"""Agrupa los exámenes elegidos en tubos y los ordena según CLSI.

Reglas (definidas por el tecnólogo médico):
- Comparten tubo los exámenes con el mismo tipo de tubo y el mismo laboratorio.
- Hemocultivo y gases van siempre en su propio contenedor (frasco o jeringa).
- Si el laboratorio pide 2 o más tubos para un examen, esos tubos son solo de ese examen.
- Si un examen admite varios tubos, se elige el que permita juntarlo con otro
  examen; si ninguno lo permite, el primero de la lista (ej.: amarillo antes que rojo).
- Gases arteriales: punción aparte, fuera del orden de extracción.
- Muestras que no son sangre: van en "Otras muestras", fuera del orden.
- Ayuno y protección de la luz: solo advertencias, con la frase original del listado.
"""

from app.texto import normalizar
from app.tubos import OTRA_MUESTRA, TIPOS_DE_TUBO, FormatoDeTuboInvalido, frases_con, leer_tubos


def agregar_advertencias(examen):
    """Agrega al examen las frases del listado sobre ayuno y luz (sin interpretarlas)."""
    instrucciones = examen.get("instrucciones") or ""
    muestra = examen.get("muestra") or ""
    examen["ayuno"] = frases_con(instrucciones, r"ayun")
    examen["luz"] = frases_con(muestra + "\n" + instrucciones, r"\bluz\b")
    return examen


def agrupar(examenes):
    """Recibe los exámenes elegidos y devuelve el resumen de tubos.

    Cada examen es un diccionario con al menos: nombre, laboratorio,
    se_procesa_en_recinto, tubos, muestra e instrucciones.
    """
    contenedores = []   # cada uno: un tubo (o varios iguales), frasco o jeringa
    compartibles = {}   # (tipo, laboratorio) -> contenedor que otros exámenes pueden usar
    otras_muestras = []
    sin_tubo = []
    con_alternativas = []

    def clave_laboratorio(examen):
        # Sin laboratorio no se sabe a dónde va: ese examen no comparte tubo
        return normalizar(examen["laboratorio"] or "") or None

    def es_compartible(tipo, cantidad, laboratorio):
        return not TIPOS_DE_TUBO[tipo]["exclusivo"] and cantidad == 1 and laboratorio is not None

    def tubos_nuevos(opcion, laboratorio):
        """Cuántos tubos nuevos habría que agregar si se elige esta opción."""
        return sum(
            0 if es_compartible(tipo, cantidad, laboratorio) and (tipo, laboratorio) in compartibles
            else cantidad
            for tipo, cantidad in opcion
        )

    def poner_en_tubo(examen, tipo, cantidad):
        laboratorio = clave_laboratorio(examen)
        if es_compartible(tipo, cantidad, laboratorio) and (tipo, laboratorio) in compartibles:
            compartibles[(tipo, laboratorio)]["examenes"].append(examen)
            return
        contenedor = {
            "tipo": tipo,
            "nombre_tubo": TIPOS_DE_TUBO[tipo]["nombre"],
            "orden": TIPOS_DE_TUBO[tipo]["orden"],
            "cantidad": cantidad,
            "laboratorio": examen["laboratorio"],
            "en_recinto": bool(examen["se_procesa_en_recinto"]),
            "examenes": [examen],
        }
        contenedores.append(contenedor)
        if es_compartible(tipo, cantidad, laboratorio):
            compartibles[(tipo, laboratorio)] = contenedor

    # Copia de cada examen con sus advertencias (no se modifica lo recibido)
    preparados = [agregar_advertencias(dict(examen)) for examen in examenes]

    # 1) Separar por tipo de muestra y ubicar los exámenes con un solo tubo posible
    for examen in preparados:
        if examen["tubos"] == OTRA_MUESTRA:
            otras_muestras.append(examen)
            continue
        try:
            opciones = leer_tubos(examen["tubos"]) if examen["tubos"] else None
        except FormatoDeTuboInvalido:
            opciones = None
        if not opciones:
            sin_tubo.append(examen)  # "Tubo: dato no disponible"
        elif len(opciones) == 1:
            for tipo, cantidad in opciones[0]:
                poner_en_tubo(examen, tipo, cantidad)
        else:
            con_alternativas.append((examen, opciones))

    # 2) Exámenes con varios tubos posibles: la opción que agregue menos tubos.
    #    Si hay empate, min() se queda con la primera de la lista.
    for examen, opciones in con_alternativas:
        laboratorio = clave_laboratorio(examen)
        elegida = min(opciones, key=lambda opcion: tubos_nuevos(opcion, laboratorio))
        for tipo, cantidad in elegida:
            poner_en_tubo(examen, tipo, cantidad)

    # 3) Ordenar según CLSI. Con el mismo tubo: primero el recinto, luego por laboratorio
    en_orden = sorted(
        (c for c in contenedores if c["orden"] is not None),
        key=lambda c: (c["orden"], not c["en_recinto"], normalizar(c["laboratorio"] or "")),
    )
    for numero, contenedor in enumerate(en_orden, start=1):
        contenedor["numero"] = numero
    punciones_aparte = [c for c in contenedores if c["orden"] is None]

    # Si un examen debe protegerse de la luz, se protege el tubo completo
    for contenedor in contenedores:
        contenedor["proteger_luz"] = any(examen["luz"] for examen in contenedor["examenes"])

    return {
        "tubos": en_orden,
        "punciones_aparte": punciones_aparte,
        "otras_muestras": otras_muestras,
        "sin_tubo": sin_tubo,
        "total_tubos": sum(c["cantidad"] for c in en_orden),
        "total_punciones_aparte": sum(c["cantidad"] for c in punciones_aparte),
        "examenes_con_ayuno": [examen for examen in preparados if examen["ayuno"]],
    }
