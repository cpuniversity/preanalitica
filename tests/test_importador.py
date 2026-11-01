"""Pruebas del importador. Usan exámenes inventados, nunca el listado real."""

import csv

import pytest

from app import create_app
from app.importador import (
    ErrorDeImportacion,
    extraer_estabilidad,
    importar,
    leer_listado,
    revisar,
)
from app.modelos import conectar

TITULOS = [
    "CODIGOS VIDALAB", "CODIGOS MEDISYN ", "EXÁMENES (SINÓNIMOS)", "Día de proceso",
    "Tiempo de Respuesta\n(Días hábiles)", "TIPO DE MUESTRA, ENVASE Y CANTIDAD",
    "Lab. Derivado", "Laboratorio", "PROCEDIMIENTOS DE TOMA DE MUESTRAS PRO/INS",
    "INSTRUCCIONES DE PREPARACIÓN DE PACIENTE, CONSERVACIÓN Y TRASLADO DE MUESTRAS", "",
]

# Filas de encabezado del documento, como en el listado real
ENCABEZADO_DOCUMENTO = [
    ["", "", "TOMA DE MUESTRAS", "", "", "", "Código:", "", "DOC 000"],
    ["", "", "", "", "", "", "Edición:", "", "1"],
]


def examen(nombre, laboratorio="Laboratorio Clínica Dávila Vespucio", dias="LU A DO",
           muestra="SANGRE, TUBO PRUEBA", instrucciones="", codigo_derivado="",
           codigo_vidalab="111", codigo_medisyn="222"):
    """Arma una fila del listado con datos inventados."""
    return [codigo_vidalab, codigo_medisyn, nombre, dias, "1", muestra,
            codigo_derivado, laboratorio, "Pro 01", instrucciones, ""]


def escribir_listado(ruta, filas, titulos=TITULOS):
    with open(ruta, "w", encoding="utf-8", newline="") as archivo:
        csv.writer(archivo).writerows(ENCABEZADO_DOCUMENTO + [titulos] + filas)
    return ruta


@pytest.fixture
def ruta(tmp_path):
    return tmp_path / "listado.csv"


# ---------- Lectura del archivo ----------

def test_encuentra_titulos_despues_del_encabezado_del_documento(ruta):
    escribir_listado(ruta, [examen("EXAMEN PRUEBA UNO")])
    examenes, _ = leer_listado(ruta)
    assert len(examenes) == 1
    assert examenes[0]["nombre"] == "EXAMEN PRUEBA UNO"
    # 2 filas de encabezado + 1 de títulos: el examen está en la fila 4
    assert examenes[0]["fila_origen"] == 4


def test_ubica_columnas_por_titulo_aunque_cambie_el_orden(ruta):
    # Intercambiamos las columnas "Día de proceso" y "CODIGOS VIDALAB"
    titulos = TITULOS.copy()
    titulos[0], titulos[3] = titulos[3], titulos[0]
    fila = examen("EXAMEN PRUEBA UNO", dias="MA", codigo_vidalab="999")
    fila[0], fila[3] = fila[3], fila[0]
    escribir_listado(ruta, [fila], titulos)

    examenes, _ = leer_listado(ruta)
    assert examenes[0]["dias_proceso"] == "MA"
    assert examenes[0]["codigo_vidalab"] == "999"


def test_falta_una_columna_y_se_detiene_con_mensaje_claro(ruta):
    titulos = [t for t in TITULOS if t != "Laboratorio"]
    escribir_listado(ruta, [], titulos)
    with pytest.raises(ErrorDeImportacion, match="Laboratorio"):
        leer_listado(ruta)


def test_sin_fila_de_titulos_se_detiene(ruta):
    with open(ruta, "w", encoding="utf-8", newline="") as archivo:
        csv.writer(archivo).writerows([["a", "b"], ["c", "d"]])
    with pytest.raises(ErrorDeImportacion, match="fila de títulos"):
        leer_listado(ruta)


def test_ignora_filas_vacias_y_titulos_repetidos(ruta):
    escribir_listado(ruta, [
        examen("EXAMEN PRUEBA UNO"),
        [""] * 11,
        TITULOS,
        examen("EXAMEN PRUEBA DOS"),
    ])
    examenes, observaciones = leer_listado(ruta)
    assert [e["nombre"] for e in examenes] == ["EXAMEN PRUEBA UNO", "EXAMEN PRUEBA DOS"]
    assert observaciones == []


def test_fila_con_datos_sin_nombre_no_se_carga_y_se_avisa(ruta):
    escribir_listado(ruta, [examen("")])
    examenes, observaciones = leer_listado(ruta)
    assert examenes == []
    assert "sin nombre de examen" in observaciones[0][2]


# ---------- Recinto o derivación ----------

def test_davila_vespucio_es_el_recinto(ruta):
    escribir_listado(ruta, [
        examen("EXAMEN PRUEBA UNO", laboratorio="Laboratorio Clínica Dávila Vespucio"),
        # Mismo laboratorio escrito sin tildes y con espacios de más
        examen("EXAMEN PRUEBA DOS", laboratorio="laboratorio clinica  davila vespucio"),
    ])
    examenes, _ = leer_listado(ruta)
    assert [e["se_procesa_en_recinto"] for e in examenes] == [1, 1]


def test_otros_laboratorios_se_derivan(ruta):
    escribir_listado(ruta, [
        examen("EXAMEN PRUEBA UNO", laboratorio="Laboratorio Externo Prueba"),
        # Otra sede de la misma clínica no es el recinto
        examen("EXAMEN PRUEBA DOS", laboratorio="Clínica Dávila"),
    ])
    examenes, _ = leer_listado(ruta)
    assert [e["se_procesa_en_recinto"] for e in examenes] == [0, 0]


# ---------- Estabilidad ----------

def test_estabilidad_se_copia_tal_como_viene_en_el_listado():
    instrucciones = "Preparación del paciente: ayuno\nEstabilidad de la muestra:\nSuero: 7 días"
    assert extraer_estabilidad(instrucciones) == "Estabilidad de la muestra:\nSuero: 7 días"


def test_estabilidad_reconoce_mayusculas_y_sin_tilde():
    assert extraer_estabilidad("ESTABILIDAD TEMPERATURA AMBIENTE: 2 HORAS") == \
        "ESTABILIDAD TEMPERATURA AMBIENTE: 2 HORAS"


def test_sin_mencion_de_estabilidad_queda_vacia():
    assert extraer_estabilidad("PACIENTE NO REQUIERE PREPARACIÓN") == ""


# ---------- Reporte de revisión ----------

def problemas(ruta, filas):
    escribir_listado(ruta, filas)
    examenes, _ = leer_listado(ruta)
    return [problema for _, _, problema in revisar(examenes)]


def test_examen_sin_tubo_se_avisa(ruta):
    assert "Tipo de muestra/tubo: dato no disponible" in problemas(ruta, [examen("EXAMEN PRUEBA UNO", muestra="")])


def test_examen_sin_laboratorio_se_avisa(ruta):
    assert "Laboratorio: dato no disponible" in problemas(ruta, [examen("EXAMEN PRUEBA UNO", laboratorio="")])


def test_examen_derivado_sin_dia_ni_estabilidad_se_avisa(ruta):
    lista = problemas(ruta, [examen("EXAMEN PRUEBA UNO", laboratorio="Laboratorio Externo Prueba",
                                    dias="", instrucciones="Sin indicaciones")])
    assert "Se deriva y el día de proceso no está disponible" in lista
    assert "Estabilidad: dato no disponible" in lista


def test_examen_del_recinto_sin_dia_ni_estabilidad_no_se_avisa(ruta):
    # El recinto trabaja 24/7: el día de proceso y la estabilidad no se revisan
    assert problemas(ruta, [examen("EXAMEN PRUEBA UNO", dias="", instrucciones="")]) == []


def test_nombre_de_menos_de_3_caracteres_se_avisa(ruta):
    lista = problemas(ruta, [examen("X"), examen("TSH")])
    assert lista == ["Nombre de menos de 3 caracteres: revisar si es un examen"]


def test_nombre_repetido_se_avisa(ruta):
    lista = problemas(ruta, [examen("EXAMEN PRUEBA UNO"), examen("Examen Prueba Uno")])
    assert lista == ["Nombre repetido (también en la fila 4)"]


@pytest.mark.parametrize("codigo", ["-", "NOTA:"])
def test_lab_derivado_no_numerico_se_excluye_y_se_avisa(ruta, codigo):
    escribir_listado(ruta, [examen("EXAMEN PRUEBA UNO", codigo_derivado=codigo),
                            examen("EXAMEN PRUEBA DOS", codigo_derivado="3")])
    examenes, observaciones = leer_listado(ruta)
    assert [e["nombre"] for e in examenes] == ["EXAMEN PRUEBA DOS"]
    assert observaciones == [(4, "EXAMEN PRUEBA UNO", f'Lab. Derivado dice "{codigo}": excluido, no se cargó')]


def test_dos_codigos_en_una_celda_se_guarda_el_mayor(ruta):
    escribir_listado(ruta, [examen("EXAMEN PRUEBA UNO",
                                   codigo_vidalab="0302048-00 \n030204801",
                                   codigo_medisyn="03-02-048-01\n03-02-048-00")])
    examenes, _ = leer_listado(ruta)
    assert examenes[0]["codigo_vidalab"] == "030204801"
    assert examenes[0]["codigo_medisyn"] == "03-02-048-01"
    # Ya no es una observación para revisar
    assert revisar(examenes) == []


# ---------- Guardado en la base ----------

def test_importar_guarda_en_la_base_y_escribe_reporte(ruta, tmp_path):
    escribir_listado(ruta, [examen("EXAMEN PRUEBA UNO"), examen("EXAMEN PRUEBA DOS", muestra="")])
    conexion = conectar(tmp_path / "prueba.db")
    reporte = tmp_path / "reporte.csv"

    resumen = importar(ruta, conexion, reporte)

    assert resumen == {"examenes": 2, "en_recinto": 2, "observaciones": 1}
    nombres = [f["nombre"] for f in conexion.execute("SELECT nombre FROM examenes ORDER BY id")]
    assert nombres == ["EXAMEN PRUEBA UNO", "EXAMEN PRUEBA DOS"]
    assert conexion.execute("SELECT COUNT(*) FROM importaciones").fetchone()[0] == 1
    assert "EXAMEN PRUEBA DOS" in reporte.read_text(encoding="utf-8-sig")


def test_importar_dos_veces_reemplaza_los_examenes(ruta, tmp_path):
    conexion = conectar(tmp_path / "prueba.db")
    reporte = tmp_path / "reporte.csv"
    importar(escribir_listado(ruta, [examen("EXAMEN PRUEBA UNO")]), conexion, reporte)
    importar(escribir_listado(ruta, [examen("EXAMEN PRUEBA DOS")]), conexion, reporte)

    nombres = [f["nombre"] for f in conexion.execute("SELECT nombre FROM examenes")]
    assert nombres == ["EXAMEN PRUEBA DOS"]
    assert conexion.execute("SELECT COUNT(*) FROM importaciones").fetchone()[0] == 2


# ---------- Comando de terminal ----------

def test_comando_importar_muestra_solo_conteos(ruta, tmp_path, monkeypatch):
    monkeypatch.setenv("BASE_DATOS", str(tmp_path / "prueba.db"))
    escribir_listado(ruta, [examen("EXAMEN PRUEBA UNO"),
                            examen("EXAMEN PRUEBA DOS", laboratorio="Laboratorio Externo Prueba")])

    resultado = create_app().test_cli_runner().invoke(args=["importar", str(ruta)])

    assert resultado.exit_code == 0
    assert "Exámenes cargados: 2" in resultado.output
    assert "Se derivan: 1" in resultado.output
    # El contenido del listado no aparece en la consola
    assert "EXAMEN PRUEBA" not in resultado.output
