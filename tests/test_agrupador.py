"""Pruebas de las reglas de agrupación de tubos. Cada regla tiene su caso.

Los exámenes son inventados; las reglas son las que definió el tecnólogo médico.
"""

from app.agrupador import Agrupador
from app.examen import Examen

RECINTO = "Laboratorio Clínica Dávila Vespucio"
EXTERNO = "Laboratorio Externo Prueba"
OTRO_EXTERNO = "Otro Laboratorio Prueba"


def examen(nombre, tubos, laboratorio=RECINTO, muestra="SANGRE", instrucciones=""):
    return Examen(nombre=nombre, tubos=tubos, laboratorio=laboratorio,
                  se_procesa_en_recinto=laboratorio == RECINTO, muestra=muestra,
                  instrucciones=instrucciones)


def agrupar(examenes):
    return Agrupador().agrupar(examenes)


def resumen_simple(resumen):
    """(número, tipo, cantidad, [exámenes]) de cada tubo, para comparar fácil."""
    return [
        (t.numero, t.tipo.codigo, t.cantidad, [e.nombre for e in t.examenes])
        for t in resumen.tubos
    ]


# ---------- Compartir tubo ----------

def test_mismo_tubo_y_mismo_laboratorio_comparten_tubo():
    resumen = agrupar([examen("A", "amarillo"), examen("B", "amarillo")])
    assert resumen_simple(resumen) == [(1, "amarillo", 1, ["A", "B"])]
    assert resumen.total_tubos == 1


def test_mismo_tubo_recinto_y_derivado_van_en_tubos_distintos():
    resumen = agrupar([examen("A", "amarillo"), examen("B", "amarillo", laboratorio=EXTERNO)])
    assert resumen_simple(resumen) == [(1, "amarillo", 1, ["A"]), (2, "amarillo", 1, ["B"])]


def test_mismo_tubo_dos_laboratorios_externos_distintos_van_aparte():
    resumen = agrupar([examen("A", "lila", laboratorio=EXTERNO), examen("B", "lila", laboratorio=OTRO_EXTERNO)])
    assert resumen.total_tubos == 2


def test_dos_derivados_al_mismo_laboratorio_comparten_tubo():
    resumen = agrupar([examen("A", "lila", laboratorio=EXTERNO), examen("B", "lila", laboratorio=EXTERNO)])
    assert resumen_simple(resumen) == [(1, "lila", 1, ["A", "B"])]


def test_tubos_distintos_no_se_comparten():
    resumen = agrupar([examen("A", "amarillo"), examen("B", "lila")])
    assert resumen.total_tubos == 2


def test_sin_laboratorio_no_comparte_tubo():
    resumen = agrupar([examen("A", "lila", laboratorio=""), examen("B", "lila", laboratorio="")])
    assert resumen.total_tubos == 2


def test_examen_que_necesita_dos_tubos_distintos():
    resumen = agrupar([examen("A", "lila + celeste"), examen("B", "lila")])
    assert resumen_simple(resumen) == [(1, "celeste", 1, ["A"]), (2, "lila", 1, ["A", "B"])]


# ---------- Cantidad de tubos que pide el laboratorio ----------

def test_dos_tubos_de_un_examen_mas_uno_de_otro_son_tres():
    # Decisión del tecnólogo médico: si el laboratorio pide 2 tubos, son de ese examen
    resumen = agrupar([examen("A", "2 celeste"), examen("B", "celeste")])
    assert resumen.total_tubos == 3
    assert sorted((t.cantidad, [e.nombre for e in t.examenes]) for t in resumen.tubos) == \
        [(1, ["B"]), (2, ["A"])]


# ---------- Exámenes con varios tubos posibles ----------

def test_elige_el_tubo_que_permite_juntarse_con_otro_examen():
    resumen = agrupar([examen("A", "rojo"), examen("B", "amarillo o rojo")])
    assert resumen_simple(resumen) == [(1, "rojo", 1, ["A", "B"])]


def test_sin_con_quien_juntarse_elige_el_primero_amarillo_antes_que_rojo():
    resumen = agrupar([examen("B", "amarillo o rojo")])
    assert resumen_simple(resumen) == [(1, "amarillo", 1, ["B"])]


def test_solo_se_junta_con_el_mismo_laboratorio():
    # El rojo existente es de otro laboratorio: no sirve para juntarse
    resumen = agrupar([examen("A", "rojo", laboratorio=EXTERNO), examen("B", "amarillo o rojo")])
    assert [t.tipo.codigo for t in resumen.tubos] == ["amarillo", "rojo"]


# ---------- Orden de extracción CLSI ----------

def test_orden_de_extraccion_clsi():
    # Se eligen en desorden a propósito
    resumen = agrupar([
        examen("Gris", "gris"),
        examen("Lila", "lila"),
        examen("Gases venosos", "jeringa-venosa"),
        examen("Verde", "verde"),
        examen("Rojo", "rojo"),
        examen("Amarillo", "amarillo"),
        examen("Celeste", "celeste"),
        examen("Hemocultivo", "hemocultivo"),
    ])
    assert [t.tipo.codigo for t in resumen.tubos] == [
        "hemocultivo", "celeste", "amarillo", "rojo", "verde", "jeringa-venosa", "lila", "gris",
    ]
    assert [t.numero for t in resumen.tubos] == [1, 2, 3, 4, 5, 6, 7, 8]


def test_mismo_tubo_primero_el_recinto():
    resumen = agrupar([examen("B", "lila", laboratorio=EXTERNO), examen("A", "lila")])
    assert [t.en_recinto for t in resumen.tubos] == [True, False]


# ---------- Excepciones ----------

def test_hemocultivo_nunca_se_comparte():
    resumen = agrupar([examen("A", "hemocultivo"), examen("B", "hemocultivo")])
    assert resumen_simple(resumen) == [(1, "hemocultivo", 1, ["A"]), (2, "hemocultivo", 1, ["B"])]


def test_gases_venosos_nunca_se_comparten():
    resumen = agrupar([examen("A", "jeringa-venosa"), examen("B", "jeringa-venosa")])
    assert resumen.total_tubos == 2


def test_gases_arteriales_son_puncion_aparte_fuera_del_orden():
    resumen = agrupar([examen("A", "lila"), examen("Gases arteriales", "jeringa-arterial")])
    assert resumen_simple(resumen) == [(1, "lila", 1, ["A"])]
    assert [c.examenes[0].nombre for c in resumen.punciones_aparte] == ["Gases arteriales"]
    assert resumen.total_tubos == 1
    assert resumen.total_punciones_aparte == 1


def test_otras_muestras_van_aparte_y_no_cuentan_como_tubo():
    resumen = agrupar([examen("A", "lila"), examen("Orina", "otra muestra", muestra="ORINA AISLADA")])
    assert [e.nombre for e in resumen.otras_muestras] == ["Orina"]
    assert resumen.total_tubos == 1


def test_tubo_no_disponible_se_avisa_y_no_se_adivina():
    resumen = agrupar([examen("A", "lila"), examen("Sin tubo", "")])
    assert [e.nombre for e in resumen.sin_tubo] == ["Sin tubo"]
    assert resumen.total_tubos == 1


def test_proteccion_de_la_luz_es_advertencia_sobre_el_tubo_completo():
    resumen = agrupar([
        examen("A", "amarillo", instrucciones="Proteger de la luz."),
        examen("B", "amarillo"),
    ])
    # No va en tubo aparte: comparte tubo y se protege el tubo completo
    assert resumen.total_tubos == 1
    assert resumen.tubos[0].proteger_luz is True
    assert resumen.tubos[0].examenes[0].luz == ["Proteger de la luz."]


def test_ayuno_es_advertencia_con_la_frase_del_listado():
    resumen = agrupar([
        examen("A", "amarillo", instrucciones="Preparación del paciente: Ayuno de 8 horas."),
        examen("B", "amarillo", instrucciones="PACIENTE NO REQUIERE AYUNO"),
        examen("C", "amarillo"),
    ])
    # No cambia los tubos
    assert resumen.total_tubos == 1
    # Se muestran las frases tal cual; la app no decide si hay o no ayuno
    assert {e.nombre: e.ayuno for e in resumen.examenes_con_ayuno} == {
        "A": ["Preparación del paciente: Ayuno de 8 horas."],
        "B": ["PACIENTE NO REQUIERE AYUNO"],
    }


def test_hielo_no_se_muestra_a_enfermeria():
    # Decisión del tecnólogo médico: el hielo lo maneja el laboratorio
    resumen = agrupar([examen("A", "amarillo", instrucciones="Enviar en hielo.")])
    examen_resultado = resumen.tubos[0].examenes[0]
    assert examen_resultado.ayuno == []
    assert examen_resultado.luz == []
    assert resumen.tubos[0].proteger_luz is False


def test_examen_con_dos_tubos_aparece_una_vez_en_ayuno():
    resumen = agrupar([examen("A", "lila + celeste", instrucciones="Ayuno de 8 horas.")])
    assert [e.nombre for e in resumen.examenes_con_ayuno] == ["A"]
