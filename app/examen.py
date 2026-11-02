"""El examen: la pieza central del dominio de la app."""

from dataclasses import dataclass

from app.tubos import OTRA_MUESTRA, FormatoDeTuboInvalido, frases_con, leer_tubos


@dataclass
class Examen:
    """Un examen del listado técnico, con los datos que usa la app.

    Los textos se guardan tal como vienen en el listado.
    """

    nombre: str
    id: int | None = None
    laboratorio: str = ""
    se_procesa_en_recinto: bool = False
    tubos: str = ""              # ej. "amarillo", "2 celeste", "otra muestra" o "" (no disponible)
    muestra: str = ""
    instrucciones: str = ""
    dias_proceso: str = ""
    tiempo_respuesta: str = ""
    estabilidad: str = ""

    # Columnas de la base de datos que corresponden a cada atributo
    CAMPOS = ("id", "nombre", "laboratorio", "se_procesa_en_recinto", "tubos", "muestra",
              "instrucciones", "dias_proceso", "tiempo_respuesta", "estabilidad")

    def __post_init__(self):
        # Algunos nombres del listado traen saltos de línea: se dejan en una línea
        self.nombre = " ".join((self.nombre or "").split())
        # Un dato vacío en la base llega como None: se deja como texto vacío
        for campo in ("laboratorio", "tubos", "muestra", "instrucciones",
                      "dias_proceso", "tiempo_respuesta", "estabilidad"):
            setattr(self, campo, getattr(self, campo) or "")
        self.se_procesa_en_recinto = bool(self.se_procesa_en_recinto)

    @classmethod
    def desde_fila(cls, fila):
        """Crea un Examen desde una fila de la base de datos (o un diccionario)."""
        return cls(**{campo: fila[campo] for campo in cls.CAMPOS if campo in fila.keys()})

    def es_derivado(self):
        """¿Se procesa en otro laboratorio? (Sin laboratorio no se sabe: no cuenta como derivado)."""
        return bool(self.laboratorio) and not self.se_procesa_en_recinto

    def es_otra_muestra(self):
        """¿Es una muestra que no es sangre (orina, deposición, etc.)?"""
        return self.tubos == OTRA_MUESTRA

    def opciones_de_tubo(self):
        """Los tubos posibles, como los entrega leer_tubos. None si el tubo no está disponible."""
        if not self.tubos or self.es_otra_muestra():
            return None
        try:
            return leer_tubos(self.tubos)
        except FormatoDeTuboInvalido:
            return None

    @property
    def etiqueta(self):
        """Si se procesa en el recinto o se deriva: tipo (para el color) y texto que se muestra."""
        if not self.laboratorio:
            return {"tipo": "aviso", "texto": "Laboratorio: dato no disponible"}
        if self.se_procesa_en_recinto:
            return {"tipo": "recinto", "texto": "Se procesa en el recinto"}
        return {"tipo": "deriva", "texto": "Se deriva a " + " ".join(self.laboratorio.split())}

    @property
    def ayuno(self):
        """Frases del listado que hablan de ayuno, tal como están escritas."""
        return frases_con(self.instrucciones, r"ayun")

    @property
    def luz(self):
        """Frases del listado que hablan de proteger de la luz, tal como están escritas."""
        return frases_con(self.muestra + "\n" + self.instrucciones, r"\bluz\b")
