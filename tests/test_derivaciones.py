"""Pruebas de derivaciones y estabilidad, con fechas fijas.

Noviembre 2026: lunes 2, jueves 5, viernes 6, sábado 7, domingo 8, lunes 9.
"""

from datetime import date, datetime

import pytest

from app.derivaciones import (
    SEGUN_DEMANDA,
    comparar,
    dia_de_proceso,
    describir_dias,
    dia_de_recepcion,
    leer_dias_proceso,
    leer_estabilidad,
    revisar_derivaciones,
    revisar_derivado,
)

LUNES = {0}


def sin_feriados(dia):
    return False


def examen(dias="LU", estabilidad="", tubos="amarillo", tiempo_respuesta="3",
           laboratorio="Laboratorio Externo Prueba", recinto=0, muestra="SANGRE"):
    return {
        "nombre": "EXAMEN PRUEBA",
        "dias_proceso": dias,
        "estabilidad": estabilidad,
        "tubos": tubos,
        "tiempo_respuesta": tiempo_respuesta,
        "laboratorio": laboratorio,
        "se_procesa_en_recinto": recinto,
        "muestra": muestra,
    }


# ---------- Leer los días de proceso ----------

@pytest.mark.parametrize("texto, esperado", [
    ("LU A VI", {0, 1, 2, 3, 4}),
    ("L A V", {0, 1, 2, 3, 4}),
    ("LU A DO", {0, 1, 2, 3, 4, 5, 6}),
    ("MA Y JU", {1, 3}),
    ("MA  Y JU", {1, 3}),
    ("LU MI VI", {0, 2, 4}),
    ("LU,MI,VI", {0, 2, 4}),
    ("Mi y Sa", {2, 5}),
    ("MIÉRCOLES", {2}),
    ("JUEVES", {3}),
    ("VI A LU", {4, 5, 6, 0}),
])
def test_leer_dias_proceso(texto, esperado):
    assert leer_dias_proceso(texto) == esperado


@pytest.mark.parametrize("texto, esperado", [
    ("LU A SA", "Lunes a sábado"),
    ("LU A DO", "Lunes a domingo"),
    ("L A V", "Lunes a viernes"),
    ("MA Y JU", "Martes y jueves"),
    ("LU,MI,VI", "Lunes, miércoles y viernes"),
    ("MA", "Martes"),
    ("VI A LU", "Viernes a lunes"),
    ("SEGÚN DEMANDA", "Según demanda"),
    ("SIN DIA ESPECIFICO", "SIN DIA ESPECIFICO"),  # no se entiende: se deja tal cual
    ("", "dato no disponible"),
])
def test_describir_dias_con_palabras_completas(texto, esperado):
    assert describir_dias(texto) == esperado


def test_segun_demanda():
    assert leer_dias_proceso("SEGÚN DEMANDA") == SEGUN_DEMANDA
    assert leer_dias_proceso("SEGUN DEMANDA") == SEGUN_DEMANDA


@pytest.mark.parametrize("texto", [
    "", "SIN DIA ESPECIFICO",
    "TOMAR MUESTRA LU Y MI ( EXCEPTO QUE SEA FESTIVO EL DIA DE PROCESO)",
])
def test_dias_que_no_se_entienden_no_se_adivinan(texto):
    assert leer_dias_proceso(texto) is None


# ---------- Recepción y día de proceso ----------

def test_antes_de_las_15_se_recibe_ese_dia():
    assert dia_de_recepcion(datetime(2026, 11, 5, 14, 59)) == date(2026, 11, 5)


def test_desde_las_15_se_recibe_al_dia_siguiente():
    assert dia_de_recepcion(datetime(2026, 11, 5, 15, 0)) == date(2026, 11, 6)


def test_laboratorio_que_procesa_solo_lunes_tomado_el_jueves():
    assert dia_de_proceso(datetime(2026, 11, 5, 10, 0), LUNES, sin_feriados) == date(2026, 11, 9)


def test_llega_antes_de_las_8_se_procesa_el_mismo_dia():
    assert dia_de_proceso(datetime(2026, 11, 2, 7, 30), LUNES, sin_feriados) == date(2026, 11, 2)


def test_despues_de_las_8_pasa_al_siguiente_dia_de_proceso():
    assert dia_de_proceso(datetime(2026, 11, 2, 9, 0), LUNES, sin_feriados) == date(2026, 11, 9)


def test_feriado_el_laboratorio_externo_no_recibe():
    lunes_feriado = date(2026, 11, 9)
    resultado = dia_de_proceso(datetime(2026, 11, 5, 10, 0), LUNES, lambda dia: dia == lunes_feriado)
    assert resultado == date(2026, 11, 16)


# ---------- Leer la estabilidad ----------

def test_estabilidad_simple():
    assert leer_estabilidad(examen(estabilidad="Estabilidad: Refrigerado (2-8°C) 7 días")) == {"refrigerada": 168}


def test_estabilidad_con_tres_temperaturas():
    texto = ("Estabilidad de la muestra: -Ambiente (15-25°C) 2 horas "
             "-Refrigerado (2-8 °C) 7 días -Congelado (-20°C) 1 mes")
    assert leer_estabilidad(examen(estabilidad=texto)) == {"ambiente": 2, "refrigerada": 168, "congelada": 720}


def test_no_aplica_no_toma_un_numero_de_mas_adelante():
    texto = "Suero: -Ambiente (15-25°C) No aplica 2 días después centrifugar -Refrigerado (2-8°C) 7 días"
    assert leer_estabilidad(examen(estabilidad=texto)) == {"refrigerada": 168}


def test_cada_tipo_de_muestra_con_su_bloque():
    # Caso real: el "no aplica" refrigerado es de la sangre total, no del suero
    texto = ("Estabilidad de las muestras sangre total temperatura ambiente (20-25°c): 8 horas "
             "refrigerada (2-8 °c): no aplica. Estabilidad de las muestras suero temperatura "
             "ambiente (20-25°c): 1 dia refrigerada (2-8 °c): 8 dias congelada (-20°c): 4 meses")
    assert leer_estabilidad(examen(estabilidad=texto, tubos="amarillo")) == \
        {"ambiente": 24, "refrigerada": 192, "congelada": 2880}
    assert leer_estabilidad(examen(estabilidad=texto, tubos="lila")) == {"ambiente": 8}


def test_numero_antes_de_la_temperatura():
    # Caso real: las 24 hrs son de refrigerada; el "12" no tiene unidad y no se usa
    texto = "Estabilidad: menor a 12 a temperatura ambiente menor a 24 hrs refrigerada"
    assert leer_estabilidad(examen(estabilidad=texto)) == {"refrigerada": 24}


def test_numero_antes_de_una_temperatura_que_tiene_el_suyo_es_de_la_anterior():
    # Caso real: las 4 hrs son de ambiente, porque refrigerada tiene sus 24 hrs
    texto = ("Estabilidad de las muestras sangre EDTA temperatura ambiente (20-25°C): maximo 4 hrs "
             "refrigerada (2-8 °C): 24 hrs congelada (-20°C): no aplica")
    assert leer_estabilidad(examen(estabilidad=texto, tubos="lila")) == {"ambiente": 4, "refrigerada": 24}


def test_sangre_completa_es_un_tipo_de_muestra_aparte_del_plasma():
    # Caso real: las 8 horas son de la sangre completa, no del plasma del tubo celeste
    texto = ("Centrifugar, separar el plasma y congelar. Estabilidad de las muestras sangre completa: "
             "temperatura ambiente (20-25°C): 8 horas")
    assert leer_estabilidad(examen(estabilidad=texto, tubos="celeste")) == {}


def test_almacenar_refrigerada_y_luego_la_duracion():
    texto = "Almacenar y trasladar muestra refrigerada. Estabilidad 2 dias refrigerada."
    assert leer_estabilidad(examen(estabilidad=texto)) == {"refrigerada": 48}


def test_estabilidad_en_semanas_y_hrs():
    assert leer_estabilidad(examen(estabilidad="Refrigerada: 2 semanas. Ambiente 8 hrs")) == \
        {"refrigerada": 336, "ambiente": 8}


def test_se_usa_la_estabilidad_del_tipo_de_muestra_del_tubo():
    texto = "Estabilidad: Suero: Refrigerado 7 días. Sangre total: Refrigerado 2 horas."
    # Tubo amarillo -> suero
    assert leer_estabilidad(examen(estabilidad=texto, tubos="amarillo")) == {"refrigerada": 168}
    # Tubo lila -> sangre total
    assert leer_estabilidad(examen(estabilidad=texto, tubos="lila")) == {"refrigerada": 2}


def test_lila_sangre_total_y_plasma_son_lo_mismo_se_usa_la_mas_corta():
    texto = "Estabilidad: Sangre total: refrigerada 2 días. Plasma: refrigerado 5 días."
    assert leer_estabilidad(examen(estabilidad=texto, tubos="lila")) == {"refrigerada": 48}


def test_tipo_de_muestra_que_no_corresponde_al_tubo_no_se_adivina():
    texto = "Estabilidad: Orina: refrigerada 7 días."
    assert leer_estabilidad(examen(estabilidad=texto, tubos="amarillo")) == {}


def test_otra_muestra_usa_el_tipo_que_dice_su_muestra():
    texto = "Estabilidad: Orina: refrigerada 7 días. Suero: refrigerado 2 días."
    resultado = leer_estabilidad(examen(estabilidad=texto, tubos="otra muestra", muestra="ORINA 24 HRS"))
    assert resultado == {"refrigerada": 168}


def test_sin_estabilidad_queda_vacia():
    assert leer_estabilidad(examen(estabilidad="")) == {}


# ---------- Comparar espera con estabilidad ----------

def test_comparar():
    assert comparar(3, 7 * 24) == "alcanza"
    assert comparar(2, 48) == "al_limite"       # justo igual: consultar
    assert comparar(3, 48) == "no_alcanza"
    assert comparar(0, 8) == "al_limite"        # menos de un día: no basta contar en días


# ---------- Revisión completa de un examen derivado ----------

JUEVES_10 = datetime(2026, 11, 5, 10, 0)


def revisar(examen_prueba, ahora=JUEVES_10):
    return revisar_derivado(examen_prueba, ahora, sin_feriados)


def test_jueves_solo_lunes_estabilidad_2_dias_no_alcanza_y_sugiere_domingo():
    revision = revisar(examen(dias="LU", estabilidad="Refrigerado 2 días"))
    assert revision["dia_proceso"] == date(2026, 11, 9)
    assert revision["espera_dias"] == 4
    assert revision["resultado"] == "no_alcanza"
    # El sábado la espera sería 2 días (al límite); el domingo, 1 día
    assert revision["sugerencia"] == [date(2026, 11, 8)]


def test_jueves_solo_lunes_estabilidad_7_dias_alcanza():
    revision = revisar(examen(dias="LU", estabilidad="Refrigerado 7 días"))
    assert revision["resultado"] == "alcanza"
    assert revision["temperatura_usada"] == "refrigerada"
    assert revision["estabilidad_usada"] == "7 días"


def test_viernes_antes_y_despues_de_las_15():
    estabilidad = "Refrigerado 3 días"
    # Antes de las 15:00: recepción viernes, proceso lunes, espera 3 días = estabilidad
    assert revisar(examen(estabilidad=estabilidad), datetime(2026, 11, 6, 14, 0))["resultado"] == "al_limite"
    # Después de las 15:00: recepción sábado, espera 2 días
    assert revisar(examen(estabilidad=estabilidad), datetime(2026, 11, 6, 16, 0))["resultado"] == "alcanza"


def test_sin_refrigerada_se_usa_la_ambiente():
    revision = revisar(examen(dias="LU", estabilidad="Ambiente 7 días. Congelado 1 mes"))
    assert revision["temperatura_usada"] == "ambiente"
    assert revision["resultado"] == "alcanza"


def test_solo_congelada_no_se_usa_para_decidir():
    revision = revisar(examen(dias="LU", estabilidad="Congelado 1 mes"))
    assert revision["resultado"] == "no_disponible"
    assert revision["duraciones"] == {"congelada": 720}


def test_sin_estabilidad_es_dato_no_disponible():
    assert revisar(examen(dias="LU", estabilidad=""))["resultado"] == "no_disponible"


def test_segun_demanda_no_da_veredicto_y_muestra_tiempo_de_respuesta():
    revision = revisar(examen(dias="SEGÚN DEMANDA", estabilidad="Refrigerado 2 días", tiempo_respuesta="6"))
    assert revision["resultado"] == "segun_demanda"
    assert revision["tiempo_respuesta"] == "6 días hábiles"


def test_dia_de_proceso_no_disponible():
    assert revisar(examen(dias="SIN DIA ESPECIFICO", estabilidad="Refrigerado 7 días"))["resultado"] == "sin_dia"


def test_no_alcanza_ningun_dia_de_la_semana():
    # Estabilidad de 1 día y proceso solo lunes: ni tomándola el domingo alcanza (espera 1 = al límite)
    revision = revisar(examen(dias="LU", estabilidad="Refrigerado 1 día"))
    assert revision["resultado"] == "no_alcanza"
    assert revision["sugerencia"] == []


def test_solo_se_revisan_los_que_se_derivan():
    examenes = [
        examen(),
        examen(laboratorio="Laboratorio Clínica Dávila Vespucio", recinto=1),
        examen(laboratorio=""),  # sin laboratorio: no se sabe si se deriva
    ]
    assert len(revisar_derivaciones(examenes, JUEVES_10, sin_feriados)) == 1


def test_textos_para_la_pantalla():
    revision = revisar_derivaciones([examen(dias="LU", estabilidad="Refrigerado 2 días. Congelado 1 mes")],
                                    JUEVES_10, sin_feriados)[0]
    assert revision["dia_proceso_nombre"] == "lunes 9/11"
    assert revision["sugerencia_texto"] == ["domingo 8/11"]
