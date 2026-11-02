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

from dataclasses import dataclass, field

from app.texto import normalizar
from app.tubos import TIPOS_DE_TUBO, TipoDeTubo


@dataclass
class Contenedor:
    """Un tubo (o varios tubos iguales), frasco o jeringa, con los exámenes que lleva."""

    tipo: TipoDeTubo
    cantidad: int            # cuántos tubos iguales (el laboratorio puede pedir 2 o más)
    laboratorio: str
    en_recinto: bool
    examenes: list = field(default_factory=list)
    numero: int | None = None  # posición en el orden de extracción (se asigna al ordenar)

    def agregar(self, examen):
        self.examenes.append(examen)

    @property
    def nombre_tubo(self):
        return self.tipo.nombre

    @property
    def orden(self):
        return self.tipo.orden

    @property
    def proteger_luz(self):
        """Si un examen debe protegerse de la luz, se protege el tubo completo."""
        return any(examen.luz for examen in self.examenes)


@dataclass
class ResumenDeTubos:
    """Lo que ve la enfermera en la pantalla de tubos."""

    tubos: list              # Contenedor en orden de extracción, numerados
    punciones_aparte: list   # Contenedor fuera del orden (gases arteriales)
    otras_muestras: list     # Examen que no son sangre
    sin_tubo: list           # Examen con "Tubo: dato no disponible"
    examenes: list           # todos los exámenes elegidos

    @property
    def total_tubos(self):
        return sum(contenedor.cantidad for contenedor in self.tubos)

    @property
    def total_punciones_aparte(self):
        return sum(contenedor.cantidad for contenedor in self.punciones_aparte)

    @property
    def examenes_con_ayuno(self):
        return [examen for examen in self.examenes if examen.ayuno]


class Agrupador:
    """Aplica las reglas de agrupación de tubos a los exámenes elegidos."""

    def agrupar(self, examenes):
        """Recibe los exámenes elegidos (Examen) y devuelve un ResumenDeTubos."""
        self._contenedores = []
        self._compartibles = {}   # (tipo, laboratorio) -> Contenedor que otros exámenes pueden usar
        otras_muestras = []
        sin_tubo = []
        con_alternativas = []

        # 1) Separar por tipo de muestra y ubicar los exámenes con un solo tubo posible
        for examen in examenes:
            if examen.es_otra_muestra():
                otras_muestras.append(examen)
                continue
            opciones = examen.opciones_de_tubo()
            if not opciones:
                sin_tubo.append(examen)  # "Tubo: dato no disponible"
            elif len(opciones) == 1:
                for tipo, cantidad in opciones[0]:
                    self._poner_en_tubo(examen, tipo, cantidad)
            else:
                con_alternativas.append((examen, opciones))

        # 2) Exámenes con varios tubos posibles: la opción que agregue menos tubos.
        #    Si hay empate, min() se queda con la primera de la lista.
        for examen, opciones in con_alternativas:
            laboratorio = self._clave_laboratorio(examen)
            elegida = min(opciones, key=lambda opcion: self._tubos_nuevos(opcion, laboratorio))
            for tipo, cantidad in elegida:
                self._poner_en_tubo(examen, tipo, cantidad)

        # 3) Ordenar según CLSI. Con el mismo tubo: primero el recinto, luego por laboratorio
        en_orden = sorted(
            (c for c in self._contenedores if not c.tipo.es_puncion_aparte()),
            key=lambda c: (c.orden, not c.en_recinto, normalizar(c.laboratorio)),
        )
        for numero, contenedor in enumerate(en_orden, start=1):
            contenedor.numero = numero

        return ResumenDeTubos(
            tubos=en_orden,
            punciones_aparte=[c for c in self._contenedores if c.tipo.es_puncion_aparte()],
            otras_muestras=otras_muestras,
            sin_tubo=sin_tubo,
            examenes=list(examenes),
        )

    def _clave_laboratorio(self, examen):
        # Sin laboratorio no se sabe a dónde va: ese examen no comparte tubo
        return normalizar(examen.laboratorio) or None

    def _es_compartible(self, tipo, cantidad, laboratorio):
        return not TIPOS_DE_TUBO[tipo].exclusivo and cantidad == 1 and laboratorio is not None

    def _tubos_nuevos(self, opcion, laboratorio):
        """Cuántos tubos nuevos habría que agregar si se elige esta opción."""
        return sum(
            0 if self._es_compartible(tipo, cantidad, laboratorio) and (tipo, laboratorio) in self._compartibles
            else cantidad
            for tipo, cantidad in opcion
        )

    def _poner_en_tubo(self, examen, tipo, cantidad):
        laboratorio = self._clave_laboratorio(examen)
        if self._es_compartible(tipo, cantidad, laboratorio) and (tipo, laboratorio) in self._compartibles:
            self._compartibles[(tipo, laboratorio)].agregar(examen)
            return
        contenedor = Contenedor(TIPOS_DE_TUBO[tipo], cantidad, examen.laboratorio, examen.se_procesa_en_recinto)
        contenedor.agregar(examen)
        self._contenedores.append(contenedor)
        if self._es_compartible(tipo, cantidad, laboratorio):
            self._compartibles[(tipo, laboratorio)] = contenedor
