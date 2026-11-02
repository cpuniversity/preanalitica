"""Exámenes que se derivan: día de proceso estimado y revisión de estabilidad.

Lo que necesita saber la enfermera: si toma la muestra ahora, ¿alcanza a
procesarse antes de que venza su estabilidad? Si no alcanza, el laboratorio
la rechazaría, así que la app lo advierte y sugiere cuándo tomarla.

Reglas (definidas por el tecnólogo médico):
- La muestra se considera recibida en Vespucio hoy si la consulta es antes
  de las 15:00; si es después, mañana.
- El laboratorio externo puede procesarla el mismo día solo si llega antes
  de las 8:00; si no, el día de proceso siguiente.
- Los laboratorios externos no reciben en feriados (Vespucio sí, es 24/7).
- La espera se cuenta en días desde la recepción hasta el día de proceso.
- Se decide con la estabilidad refrigerada; si no existe, con la ambiente.
  La congelada solo se informa.
- Si la espera es igual a la estabilidad: "al límite, consultar".
- "Según demanda": no se sabe el día de proceso, no se da veredicto.
"""

import re
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

import holidays

from app.texto import normalizar

DIAS_SEMANA = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]

# Abreviaturas que usa el listado para los días (0 = lunes ... 6 = domingo)
ABREVIATURAS = {
    "lu": 0, "lunes": 0, "l": 0,
    "ma": 1, "martes": 1,
    "mi": 2, "miercoles": 2,
    "ju": 3, "jueves": 3,
    "vi": 4, "viernes": 4, "v": 4,
    "sa": 5, "sabado": 5,
    "do": 6, "domingo": 6,
}

SEGUN_DEMANDA = "según demanda"

# Horarios de corte
HORA_LIMITE_RECEPCION = 15   # antes de las 15:00 la muestra cuenta como recibida ese día
HORA_LIMITE_MISMO_DIA = 8    # antes de las 8:00 alcanza a procesarse ese mismo día

# Cuántos días hacia adelante se busca un día de proceso o un día para sugerir
DIAS_A_BUSCAR = 60
DIAS_PARA_SUGERIR = 7


def es_feriado(dia):
    """¿Es feriado en Chile?"""
    return dia in holidays.country_holidays("CL", years=dia.year)


def nombre_del_dia(dia):
    """Ejemplo: date(2026, 11, 9) -> "lunes 9/11"."""
    return f"{DIAS_SEMANA[dia.weekday()]} {dia.day}/{dia.month}"


# ---------- Días de proceso ----------

def leer_dias_proceso(texto):
    """Convierte el texto del listado en los días de la semana en que se procesa.

    "LU A VI" -> {0, 1, 2, 3, 4}; "MA Y JU" -> {1, 3}; "SEGÚN DEMANDA" -> SEGUN_DEMANDA.
    Si el texto no se entiende con seguridad, devuelve None.
    """
    texto = normalizar(texto or "")
    if "demanda" in texto:
        return SEGUN_DEMANDA
    palabras = re.findall(r"[a-z]+", texto)
    if not palabras:
        return None

    dias = set()
    anterior = None   # último día leído
    rango = False     # se leyó una "a" (por ejemplo "lu a vi")
    for palabra in palabras:
        if palabra == "y":
            continue
        if palabra == "a" and anterior is not None:
            rango = True
            continue
        if palabra not in ABREVIATURAS:
            return None  # palabra desconocida: no se adivina
        dia = ABREVIATURAS[palabra]
        if rango:
            # Del día anterior hasta este, dando la vuelta a la semana si hace falta
            actual = anterior
            while actual != dia:
                actual = (actual + 1) % 7
                dias.add(actual)
            rango = False
        dias.add(dia)
        anterior = dia
    return dias if dias and not rango else None


def describir_dias(texto):
    """Escribe los días de proceso con palabras completas.

    "LU A SA" -> "Lunes a sábado"; "MA Y JU" -> "Martes y jueves";
    "LU,MI,VI" -> "Lunes, miércoles y viernes". Si no se entiende, deja el texto original.
    """
    dias = leer_dias_proceso(texto)
    if dias == SEGUN_DEMANDA:
        return "Según demanda"
    if not dias:
        return " ".join((texto or "").split()) or "dato no disponible"

    if len(dias) == 7:
        descripcion = "lunes a domingo"
    else:
        # ¿Son días seguidos? (por ejemplo lunes a sábado, o viernes a lunes)
        primero = next(dia for dia in range(7) if dia in dias and (dia - 1) % 7 not in dias)
        seguidos = [(primero + i) % 7 for i in range(len(dias))]
        if len(dias) >= 3 and set(seguidos) == dias:
            descripcion = f"{DIAS_SEMANA[seguidos[0]]} a {DIAS_SEMANA[seguidos[-1]]}"
        else:
            nombres = [DIAS_SEMANA[dia] for dia in sorted(dias)]
            descripcion = nombres[0] if len(nombres) == 1 else ", ".join(nombres[:-1]) + " y " + nombres[-1]
    return descripcion[0].upper() + descripcion[1:]


def dia_de_recepcion(ahora):
    """Día desde el que se cuenta la espera (recepción en Vespucio)."""
    if ahora.hour < HORA_LIMITE_RECEPCION:
        return ahora.date()
    return ahora.date() + timedelta(days=1)


def dia_de_proceso(ahora, dias_proceso, feriado=es_feriado):
    """Primer día en que el laboratorio externo procesaría una muestra tomada ahora."""
    hoy = ahora.date()
    for adelante in range(DIAS_A_BUSCAR):
        dia = hoy + timedelta(days=adelante)
        if dia.weekday() not in dias_proceso or feriado(dia):
            continue
        # Hoy solo sirve si la muestra llega antes de las 8:00
        if adelante == 0 and ahora.hour >= HORA_LIMITE_MISMO_DIA:
            continue
        return dia
    return None


# ---------- Estabilidad ----------

# Equivalencia de cada unidad de tiempo en horas (se reconoce por cómo empieza la palabra)
HORAS_POR_UNIDAD = [("min", 1 / 60), ("h", 1), ("dia", 24), ("semana", 168), ("mes", 720), ("ano", 8760)]

TEMPERATURAS = {
    "refrigerada": r"refrigerad",
    "ambiente": r"ambiente",
    "congelada": r"congelad",
}

# Tipos de muestra que puede nombrar el texto de estabilidad
TIPOS_DE_MUESTRA = ["suero", "plasma", "sangre total", "sangre entera", "sangre completa", "orina", "lcr"]

# Qué tipo de muestra corresponde a cada tubo (validado por el tecnólogo médico).
# Para el lila, sangre total y plasma EDTA son lo mismo: el laboratorio centrifuga.
TIPOS_POR_TUBO = {
    "amarillo": {"suero"},
    "rojo": {"suero"},
    "celeste": {"plasma"},
    "verde": {"plasma"},
    "gris": {"plasma"},
    "lila": {"sangre total", "sangre entera", "sangre completa", "plasma"},
}


def a_horas(numero, unidad):
    """Convierte "7", "dias" en 168 horas. "hrs", "horas" y "h" empiezan con "h"."""
    for comienzo, horas in HORAS_POR_UNIDAD:
        if unidad.startswith(comienzo):
            return float(numero.replace(",", ".")) * horas
    raise ValueError(f"Unidad de tiempo desconocida: {unidad}")


# Piezas que se buscan en el texto de estabilidad, en el orden en que aparecen:
# una temperatura, un "no aplica", o una duración (número con unidad de tiempo).
# Los números sin unidad, como "(2-8 °C)", no cuentan.
PIEZAS = re.compile(
    r"(?P<temperatura>refrigerad\w*|ambiente|congelad\w*)"
    r"|(?P<no_aplica>no aplica)"
    r"|(?P<numero>\d+(?:[.,]\d+)?)\s*(?P<unidad>horas?|hrs?|h|dias?|semanas?|meses|mes|anos?|min)\b"
)

# Distancia máxima (en letras) entre una temperatura y su duración
DISTANCIA_MAXIMA = 40


def cual_temperatura(palabra):
    """"refrigerado" -> "refrigerada", "ambiente" -> "ambiente", etc."""
    for temperatura, patron in TEMPERATURAS.items():
        if re.match(patron, palabra):
            return temperatura


def duraciones_por_temperatura(texto):
    """Busca "Refrigerado (2-8 °C) 7 días" y similares. Devuelve {temperatura: horas}.

    Cada duración se asigna a una temperatura:
    - En general, a la temperatura que va justo antes ("Refrigerado (2-8°C) 7 días").
    - A la que va justo después solo si esa no tiene su propia duración
      ("menor a 24 hrs refrigerada"). Así, en "Ambiente: máximo 4 hrs
      Refrigerada (2-8 °C): 24 hrs", las 4 hrs son de ambiente.
    - Si justo antes hay un "no aplica", la duración no se asigna.
    Si una temperatura aparece varias veces, se queda con la duración más corta.
    """
    piezas = list(PIEZAS.finditer(texto))
    duraciones = {}

    def es_temperatura(posicion):
        return 0 <= posicion < len(piezas) and piezas[posicion].group("temperatura")

    def tiene_su_dato(posicion):
        """¿Después de esta pieza viene una duración o un "no aplica"?"""
        return 0 <= posicion < len(piezas) and (piezas[posicion].group("numero") or piezas[posicion].group("no_aplica"))

    for posicion, pieza in enumerate(piezas):
        if not pieza.group("numero"):
            continue
        horas = a_horas(pieza.group("numero"), pieza.group("unidad"))
        temperatura = None

        # ¿La temperatura que sigue va pegada a esta duración y no tiene la suya?
        siguiente = posicion + 1
        if es_temperatura(siguiente) and not tiene_su_dato(siguiente + 1):
            entre = texto[pieza.end():piezas[siguiente].start()]
            if re.fullmatch(r"\s*(a\s+)?(temperatura\s+)?", entre):
                temperatura = cual_temperatura(piezas[siguiente].group())

        # Si no, la temperatura que va justo antes (si está cerca)
        anterior = posicion - 1
        if temperatura is None and es_temperatura(anterior):
            if pieza.start() - piezas[anterior].end() <= DISTANCIA_MAXIMA:
                temperatura = cual_temperatura(piezas[anterior].group())

        if temperatura:
            duraciones[temperatura] = min(horas, duraciones.get(temperatura, horas))
    return duraciones


def tipos_aceptados(examen):
    """Tipos de muestra que corresponden al examen, según su tubo o su muestra."""
    if examen.es_otra_muestra():
        muestra = normalizar(examen.muestra)
        return {tipo for tipo in TIPOS_DE_MUESTRA if tipo in muestra}
    opciones = examen.opciones_de_tubo() or []
    aceptados = [TIPOS_POR_TUBO.get(tipo, set()) for opcion in opciones for tipo, _ in opcion]
    # Si el examen usa tubos con distintos tipos de muestra, no se puede elegir con seguridad
    if not aceptados or any(tipos != aceptados[0] for tipos in aceptados):
        return set()
    return aceptados[0]


def leer_estabilidad(examen):
    """Duraciones de estabilidad que corresponden a la muestra de este examen.

    Devuelve {temperatura: horas}, o {} si no se puede saber con seguridad.
    """
    texto = normalizar(examen.estabilidad)
    if not texto:
        return {}

    # Dónde nombra el texto cada tipo de muestra
    menciones = sorted(
        (m.start(), tipo)
        for tipo in TIPOS_DE_MUESTRA
        for m in re.finditer(rf"\b{tipo}\b", texto)
    )
    if not menciones:
        # El texto no distingue tipos de muestra: la estabilidad es una sola
        return duraciones_por_temperatura(texto)

    aceptados = tipos_aceptados(examen)
    duraciones = {}
    for numero, (inicio, tipo) in enumerate(menciones):
        if tipo not in aceptados:
            continue
        fin = menciones[numero + 1][0] if numero + 1 < len(menciones) else len(texto)
        for temperatura, horas in duraciones_por_temperatura(texto[inicio:fin]).items():
            # Si hay más de un dato que sirve, se usa el más corto (más seguro)
            duraciones[temperatura] = min(horas, duraciones.get(temperatura, horas))
    return duraciones


def describir_duracion(horas):
    """168 -> "7 días"; 8 -> "8 horas"."""
    if horas >= 24 and horas % 24 == 0:
        dias = int(horas // 24)
        return f"{dias} día" if dias == 1 else f"{dias} días"
    horas_redondeadas = round(horas, 1) if horas % 1 else int(horas)
    return f"{horas_redondeadas} hora" if horas_redondeadas == 1 else f"{horas_redondeadas} horas"




# ---------- Revisión de un examen derivado ----------

def comparar(espera_dias, horas_estabilidad):
    """Compara la espera con la estabilidad: "alcanza", "al_limite" o "no_alcanza"."""
    # Con estabilidades de menos de un día, contar en días no es suficiente
    if horas_estabilidad < 24:
        return "al_limite"
    espera_horas = espera_dias * 24
    if espera_horas < horas_estabilidad:
        return "alcanza"
    if espera_horas == horas_estabilidad:
        return "al_limite"
    return "no_alcanza"


def tiempo_de_respuesta(texto):
    """El listado da el tiempo de respuesta en días hábiles, salvo que diga otra unidad."""
    texto = " ".join((texto or "").split())
    if not texto:
        return "dato no disponible"
    return f"{texto} días hábiles" if texto.isdigit() else texto.lower()


class CalendarioDeProceso:
    """Los días en que un laboratorio externo procesa un examen."""

    def __init__(self, texto, feriado=es_feriado):
        self.texto = texto or ""
        self.dias = leer_dias_proceso(texto)   # conjunto de días, SEGUN_DEMANDA o None
        self.feriado = feriado

    def es_segun_demanda(self):
        return self.dias == SEGUN_DEMANDA

    def se_entiende(self):
        """¿Se pudo leer con seguridad qué días procesa?"""
        return bool(self.dias) and not self.es_segun_demanda()

    def describir(self):
        """Ejemplo: "Lunes a sábado"."""
        return describir_dias(self.texto)

    def dia_de_proceso(self, ahora):
        """Primer día en que se procesaría una muestra tomada ahora."""
        return dia_de_proceso(ahora, self.dias, self.feriado)

    def sugerir_dias_de_toma(self, ahora, horas_estabilidad):
        """Días de la próxima semana en que, tomando la muestra antes de las 15:00, alcanza."""
        sugeridos = []
        for adelante in range(DIAS_PARA_SUGERIR + 1):
            dia = ahora.date() + timedelta(days=adelante)
            # Se supone que se toma a las 10:00 (antes de las 15:00 y después de las 8:00)
            toma = datetime(dia.year, dia.month, dia.day, 10, 0)
            if toma < ahora:
                continue
            proceso = self.dia_de_proceso(toma)
            if proceso and comparar((proceso - dia).days, horas_estabilidad) == "alcanza":
                sugeridos.append(dia)
        return sugeridos


@dataclass
class Estabilidad:
    """La estabilidad de la muestra de un examen, según el listado."""

    texto: str          # tal como lo escribe el listado
    duraciones: dict    # {temperatura: horas} para el tipo de muestra del examen

    @classmethod
    def de_examen(cls, examen):
        return cls(" ".join(examen.estabilidad.split()), leer_estabilidad(examen))

    def para_decidir(self):
        """(temperatura, horas) con que se decide: refrigerada; si no hay, ambiente. None si no hay."""
        for temperatura in ("refrigerada", "ambiente"):
            if temperatura in self.duraciones:
                return temperatura, self.duraciones[temperatura]
        return None


@dataclass
class RevisionDeDerivacion:
    """Lo que se le muestra a la enfermera sobre un examen derivado."""

    examen: object
    resultado: str              # alcanza, al_limite, no_alcanza, segun_demanda, sin_dia o no_disponible
    dias_proceso_texto: str
    estabilidad_texto: str
    dia_proceso: date | None = None
    espera_dias: int | None = None
    temperatura_usada: str | None = None
    estabilidad_usada: str | None = None
    tiempo_respuesta: str | None = None
    duraciones: dict = field(default_factory=dict)
    sugerencia: list = field(default_factory=list)

    @property
    def dia_proceso_nombre(self):
        return nombre_del_dia(self.dia_proceso) if self.dia_proceso else None

    @property
    def sugerencia_texto(self):
        return [nombre_del_dia(dia) for dia in self.sugerencia]


class RevisorDeEstabilidad:
    """Revisa si la estabilidad de cada examen derivado alcanza hasta su día de proceso."""

    def __init__(self, feriado=es_feriado):
        self.feriado = feriado

    def revisar(self, examen, ahora):
        """Revisa un examen derivado y devuelve una RevisionDeDerivacion."""
        calendario = CalendarioDeProceso(examen.dias_proceso, self.feriado)
        estabilidad = Estabilidad.de_examen(examen)
        revision = RevisionDeDerivacion(
            examen=examen,
            resultado="",
            dias_proceso_texto=calendario.describir(),
            estabilidad_texto=estabilidad.texto,
            duraciones=estabilidad.duraciones,
        )

        if calendario.es_segun_demanda():
            revision.resultado = "segun_demanda"
            revision.tiempo_respuesta = tiempo_de_respuesta(examen.tiempo_respuesta)
            return revision
        if not calendario.se_entiende():
            revision.resultado = "sin_dia"
            revision.duraciones = {}
            return revision

        proceso = calendario.dia_de_proceso(ahora)
        revision.dia_proceso = proceso
        revision.espera_dias = (proceso - dia_de_recepcion(ahora)).days if proceso else None

        decision = estabilidad.para_decidir()
        if proceso is None or decision is None:
            revision.resultado = "no_disponible"
            return revision

        temperatura, horas = decision
        revision.temperatura_usada = temperatura
        revision.estabilidad_usada = describir_duracion(horas)
        revision.resultado = comparar(revision.espera_dias, horas)
        if revision.resultado == "no_alcanza":
            revision.sugerencia = calendario.sugerir_dias_de_toma(ahora, horas)
        return revision

    def revisar_derivados(self, examenes, ahora=None):
        """Revisa todos los exámenes elegidos que se derivan a otro laboratorio."""
        ahora = ahora or datetime.now()
        return [self.revisar(examen, ahora) for examen in examenes if examen.es_derivado()]
