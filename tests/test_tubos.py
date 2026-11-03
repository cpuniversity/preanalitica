"""Pruebas de la lectura del tubo desde el texto del listado.

Los textos imitan la forma en que el listado describe la muestra.
"""

import pytest

from app.tubos import OTRA_MUESTRA, FormatoDeTuboInvalido, clasificar, frases_con, leer_tubos


# ---------- Reconocer el tubo ----------

@pytest.mark.parametrize("muestra, esperado", [
    # Decisión del tecnólogo médico: "con gel" y "tapa amarilla" son el mismo tubo
    ("SANGRE, TUBO CON GEL 5 ML", "amarillo"),
    ("SANGRE, TUBO TAPA AMARILLA 5 ML", "amarillo"),
    ("SANGRE, TUBO AMARILLO CON GEL 5 ML", "amarillo"),
    # El rojo es distinto del amarillo con gel
    ("SANGRE, TUBO TAPA ROJA 5 ML", "rojo"),
    ("SANGRE, TUBO TAPA LILA 3 ML", "lila"),
    ("SANGRE, TUBO EDTA 3 ML", "lila"),
    ("SANGRE, TUBO TAPA CELESTE CITRATO DE SODIO 3,2%", "celeste"),
    ("SANGRE, TUBO HEPARINA DE LITIO 4 ML", "verde"),
    ("SANGRE, TUBO TAPA GRIS", "gris"),
    ("SANGRE, FRASCO HEMOCULTIVO", "hemocultivo"),
])
def test_reconoce_el_tubo(muestra, esperado):
    assert clasificar(muestra, "EXAMEN PRUEBA") == esperado


def test_sin_gel_no_es_amarillo():
    assert clasificar("SANGRE TOTAL, TUBO CON HEPARINA DE LITIO (SIN GEL) 4ML", "EXAMEN PRUEBA") == "verde"


def test_cantidad_de_tubos_que_pide_el_laboratorio():
    assert clasificar("SANGRE, 2 TUBOS TAPA CELESTE 3 ML", "EXAMEN PRUEBA") == "2 celeste"
    assert clasificar("SANGRE, 2 FRASCOS HEMOCULTIVO", "HEMOCULTIVO PRUEBA") == "2 hemocultivo"
    # Los mililitros no son cantidad de tubos
    assert clasificar("SANGRE, TUBO TAPA LILA 3 ML", "EXAMEN PRUEBA") == "lila"


def test_gases_arteriales_y_venosos_se_distinguen_por_el_nombre():
    muestra = "SANGRE, JERINGA C/HEPARINA, 2ML."
    assert clasificar(muestra, "GASES EN SANGRE ARTERIAL") == "jeringa-arterial"
    assert clasificar(muestra, "GASES EN SANGRE VENOSA") == "jeringa-venosa"
    # Si el nombre no lo dice, no se adivina
    assert clasificar(muestra, "GASES") == ""


def test_solo_se_considera_la_parte_de_adultos():
    muestra = "ADULTOS: SANGRE TOTAL, 1 TUBO TAPA LILA EDTA 3 ML; PEDIATRICOS: TUBO TAPA CELESTE"
    assert clasificar(muestra, "EXAMEN PRUEBA") == "lila"


@pytest.mark.parametrize("muestra", [
    "ORINA, 24 HRS, MEDIR Y ENVIAR 2 TUBOS DE 10 ML",
    "DEPOSICION, FRASCO ESTERIL",
    "LCR, TUBO ESTERIL",
    "MEDULA OSEA TUBO TAPA LILA (EDTA)",
])
def test_muestras_que_no_son_sangre(muestra):
    assert clasificar(muestra, "EXAMEN PRUEBA") == OTRA_MUESTRA


@pytest.mark.parametrize("muestra", [
    "1 FRASCO CON MUESTRA DE DEPOSICIÓN FRESCA EN FRASCO ESTERIL",
    "1 FRASCO CON ORINA DE SEGUNDO CHORRO",
    "2 FRASCOS DEPOSICION",
])
def test_frasco_con_muestra_que_no_es_sangre_es_otra_muestra(muestra):
    assert clasificar(muestra, "EXAMEN PRUEBA") == OTRA_MUESTRA


@pytest.mark.parametrize("muestra, esperado", [
    ("2 FRASCOS HEMOCULTIVO", "2 hemocultivo"),  # el frasco de hemocultivo sigue siendo sangre
    ("1 FRASCO ESPECIAL", ""),                   # no se sabe qué muestra es: no se adivina
])
def test_frasco_sin_otra_muestra_no_cambia(muestra, esperado):
    assert clasificar(muestra, "EXAMEN PRUEBA") == esperado


@pytest.mark.parametrize("muestra", [
    "SANGRE, TUBO AMARILLO O ROJO CON GEL 5 ML",   # alternativas
    "SANGRE, TUBO TAPA LILA Y TUBO TAPA CELESTE",  # dos tubos distintos
    "SANGRE, FRASCO ESPECIAL",                     # ninguno conocido
])
def test_si_no_es_claro_no_adivina(muestra):
    assert clasificar(muestra, "EXAMEN PRUEBA") == ""


@pytest.mark.parametrize("muestra", [
    "NO APLICA",
    "LAS SIGUIENTES MUESTRAS DEBEN RECOLECTARSE DE MANERA CONJUNTA. SANGRE, TUBO TAPA AMARILLA",
    "2 A 3 TUBOS TAPA ROJA ESTERILES DE 10 ML",
    "LABORATORIO EXTERNO PRUEBA",  # dato corrido de columna
])
def test_si_no_se_sabe_que_muestra_es_no_adivina(muestra):
    assert clasificar(muestra, "EXAMEN PRUEBA") == ""


@pytest.mark.parametrize("muestra", ["10 ML ORINA 2DO CHORRO, FRASCO ESTERIL", "1 TORULA POR 1/3 VAGINA"])
def test_otra_muestra_con_cantidad_al_inicio(muestra):
    assert clasificar(muestra, "EXAMEN PRUEBA") == OTRA_MUESTRA


def test_muestra_vacia_es_dato_no_disponible():
    assert clasificar("", "EXAMEN PRUEBA") == ""


# ---------- Formato de la tabla del tecnólogo médico ----------

def test_leer_un_tubo():
    assert leer_tubos("amarillo") == [[("amarillo", 1)]]


def test_leer_cantidad():
    assert leer_tubos("2 celeste") == [[("celeste", 2)]]


def test_leer_tubos_que_se_necesitan_juntos():
    assert leer_tubos("lila + celeste") == [[("lila", 1), ("celeste", 1)]]


def test_leer_alternativas_en_el_orden_escrito():
    assert leer_tubos("Amarillo o Rojo") == [[("amarillo", 1)], [("rojo", 1)]]


@pytest.mark.parametrize("texto", ["morado", "2", "lila +", "0 lila"])
def test_formato_invalido(texto):
    with pytest.raises(FormatoDeTuboInvalido):
        leer_tubos(texto)


# ---------- Frases para advertencias ----------

def test_frases_se_copian_tal_cual():
    texto = "Preparación del paciente: Ayuno de 8 horas. Traer orden médica."
    assert frases_con(texto, r"ayun") == ["Preparación del paciente: Ayuno de 8 horas."]


def test_no_requiere_ayuno_se_muestra_completo_sin_interpretar():
    assert frases_con("PACIENTE NO REQUIERE AYUNO", r"ayun") == ["PACIENTE NO REQUIERE AYUNO"]


def test_luz_reconoce_la_palabra_completa():
    assert frases_con("Proteger de la luz.", r"\bluz\b") == ["Proteger de la luz."]
    assert frases_con("Muestra en lucite.", r"\bluz\b") == []
