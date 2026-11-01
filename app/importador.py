"""Lee el listado técnico (CSV) y lo carga en la base de datos.

El importador copia los datos tal como vienen y avisa lo raro en un
reporte de revisión. No interpreta reglas clínicas (días, tubos, etc.):
eso lo hacen otros módulos, con reglas validadas por el tecnólogo médico.
"""

import csv
from datetime import datetime
from pathlib import Path

import click
from flask import current_app
from flask.cli import with_appcontext

from app.modelos import conectar, crear_tablas
from app.texto import normalizar

# Laboratorio del recinto (todos los demás son laboratorios de derivación)
LABORATORIO_RECINTO = "Laboratorio Clínica Dávila Vespucio"

# Texto que se muestra cuando el listado no trae un dato
DATO_NO_DISPONIBLE = "dato no disponible"

# Título de cada columna en el listado, según el nombre que usamos en la base.
# Las columnas se buscan por su título, no por su posición.
TITULOS = {
    "codigo_vidalab": "CODIGOS VIDALAB",
    "codigo_medisyn": "CODIGOS MEDISYN",
    "nombre": "EXÁMENES (SINÓNIMOS)",
    "dias_proceso": "Día de proceso",
    "tiempo_respuesta": "Tiempo de Respuesta (Días hábiles)",
    "muestra": "TIPO DE MUESTRA, ENVASE Y CANTIDAD",
    "codigo_lab_derivado": "Lab. Derivado",
    "laboratorio": "Laboratorio",
    "procedimientos": "PROCEDIMIENTOS DE TOMA DE MUESTRAS PRO/INS",
    "instrucciones": "INSTRUCCIONES DE PREPARACIÓN DE PACIENTE, CONSERVACIÓN Y TRASLADO DE MUESTRAS",
}


class ErrorDeImportacion(Exception):
    """El archivo no tiene la forma esperada."""


def encontrar_fila_titulos(filas):
    """Devuelve el número de la fila que tiene los títulos de las columnas."""
    titulo_examen = normalizar(TITULOS["nombre"])
    for numero, fila in enumerate(filas):
        if titulo_examen in [normalizar(celda) for celda in fila]:
            return numero
    raise ErrorDeImportacion(f'No se encontró la fila de títulos (con "{TITULOS["nombre"]}").')


def ubicar_columnas(fila_titulos):
    """Devuelve en qué posición está cada columna. Falla si falta alguna."""
    titulos_del_archivo = [normalizar(celda) for celda in fila_titulos]
    posiciones = {}
    faltantes = []
    for campo, titulo in TITULOS.items():
        if normalizar(titulo) in titulos_del_archivo:
            posiciones[campo] = titulos_del_archivo.index(normalizar(titulo))
        else:
            faltantes.append(titulo)
    if faltantes:
        raise ErrorDeImportacion("Faltan columnas en el archivo: " + "; ".join(faltantes))
    return posiciones


def extraer_estabilidad(instrucciones):
    """Copia el texto de las instrucciones desde la línea que menciona la estabilidad.

    No interpreta nada: si el listado no menciona la estabilidad, devuelve "".
    """
    lineas = instrucciones.split("\n")
    for numero, linea in enumerate(lineas):
        if "estabil" in normalizar(linea):
            return "\n".join(lineas[numero:]).strip()
    return ""


def elegir_codigo_mayor(texto):
    """Si la celda trae varios códigos, se queda con el de número más grande.

    Para comparar se usan solo los dígitos: "03-02-048-01" se compara como 302004801.
    """
    codigos = texto.split()
    if not codigos:
        return ""
    return max(codigos, key=lambda codigo: int("".join(c for c in codigo if c.isdigit()) or 0))


def leer_listado(ruta):
    """Lee el CSV y devuelve (examenes, observaciones).

    examenes: lista de diccionarios, uno por examen.
    observaciones: filas que no se pudieron cargar.
    """
    with open(ruta, encoding="utf-8-sig", newline="") as archivo:
        filas = list(csv.reader(archivo))

    numero_titulos = encontrar_fila_titulos(filas)
    posiciones = ubicar_columnas(filas[numero_titulos])

    examenes = []
    observaciones = []
    # La fila del archivo se cuenta desde 1, como en Excel
    for numero, fila in enumerate(filas[numero_titulos + 1:], start=numero_titulos + 2):
        examen = {"fila_origen": numero}
        for campo, posicion in posiciones.items():
            examen[campo] = fila[posicion].strip() if posicion < len(fila) else ""

        # Fila totalmente vacía: se ignora
        if not any(examen[campo] for campo in TITULOS):
            continue
        # Fila que repite los títulos (por ejemplo, al cambiar de página)
        if normalizar(examen["nombre"]) == normalizar(TITULOS["nombre"]):
            continue
        if not examen["nombre"]:
            observaciones.append((numero, "", "Fila con datos pero sin nombre de examen: no se cargó"))
            continue
        # Indicación del tecnólogo médico: si "Lab. Derivado" no es un número
        # (por ejemplo "-" o "NOTA:"), el examen no se considera en la app
        codigo = examen["codigo_lab_derivado"]
        if codigo and not codigo.isdigit():
            observaciones.append((numero, examen["nombre"],
                                  f'Lab. Derivado dice "{codigo}": excluido, no se cargó'))
            continue

        examen["codigo_vidalab"] = elegir_codigo_mayor(examen["codigo_vidalab"])
        examen["codigo_medisyn"] = elegir_codigo_mayor(examen["codigo_medisyn"])
        examen["estabilidad"] = extraer_estabilidad(examen["instrucciones"])
        examen["se_procesa_en_recinto"] = int(
            normalizar(examen["laboratorio"]) == normalizar(LABORATORIO_RECINTO)
        )
        examenes.append(examen)

    return examenes, observaciones


def revisar(examenes):
    """Busca datos que el tecnólogo médico debe revisar. Devuelve (fila, examen, problema)."""
    observaciones = []
    vistos = {}  # nombre normalizado -> primera fila donde apareció

    for examen in examenes:
        fila, nombre = examen["fila_origen"], examen["nombre"]

        if len(nombre) < 3:
            observaciones.append((fila, nombre, "Nombre de menos de 3 caracteres: revisar si es un examen"))

        if not examen["muestra"]:
            observaciones.append((fila, nombre, f"Tipo de muestra/tubo: {DATO_NO_DISPONIBLE}"))
        if not examen["laboratorio"]:
            observaciones.append((fila, nombre, f"Laboratorio: {DATO_NO_DISPONIBLE}"))

        # Datos que solo importan si el examen se deriva
        if examen["laboratorio"] and not examen["se_procesa_en_recinto"]:
            if not examen["dias_proceso"]:
                observaciones.append((fila, nombre, "Se deriva y el día de proceso no está disponible"))
            if not examen["estabilidad"]:
                observaciones.append((fila, nombre, f"Estabilidad: {DATO_NO_DISPONIBLE}"))

        clave = normalizar(nombre)
        if clave in vistos:
            observaciones.append((fila, nombre, f"Nombre repetido (también en la fila {vistos[clave]})"))
        else:
            vistos[clave] = fila

    return observaciones


def guardar_en_base(conexion, examenes, archivo, cantidad_observaciones):
    """Reemplaza los exámenes de la base por los recién leídos."""
    campos = list(TITULOS) + ["fila_origen", "estabilidad", "se_procesa_en_recinto"]
    marcadores = ", ".join("?" for _ in campos)
    # "with conexion" guarda todo junto: si algo falla, no queda nada a medias
    with conexion:
        conexion.execute("DELETE FROM examenes")
        conexion.executemany(
            f"INSERT INTO examenes ({', '.join(campos)}) VALUES ({marcadores})",
            [[examen[campo] for campo in campos] for examen in examenes],
        )
        conexion.execute(
            "INSERT INTO importaciones (fecha, archivo, examenes_cargados, observaciones) VALUES (?, ?, ?, ?)",
            (datetime.now().isoformat(timespec="seconds"), Path(archivo).name,
             len(examenes), cantidad_observaciones),
        )


def escribir_reporte(ruta, observaciones):
    """Escribe el reporte de revisión. utf-8-sig hace que Excel muestre bien las tildes."""
    with open(ruta, "w", encoding="utf-8-sig", newline="") as archivo:
        escritor = csv.writer(archivo, delimiter=";")
        escritor.writerow(["Fila del listado", "Examen", "Observación"])
        escritor.writerows(sorted(observaciones))


def importar(ruta_listado, conexion, ruta_reporte):
    """Lee el listado, lo guarda en la base y escribe el reporte. Devuelve un resumen."""
    examenes, observaciones = leer_listado(ruta_listado)
    observaciones += revisar(examenes)

    crear_tablas(conexion)
    guardar_en_base(conexion, examenes, ruta_listado, len(observaciones))
    escribir_reporte(ruta_reporte, observaciones)

    return {
        "examenes": len(examenes),
        "en_recinto": sum(examen["se_procesa_en_recinto"] for examen in examenes),
        "observaciones": len(observaciones),
    }


@click.command("importar")
@click.argument("ruta_listado", type=click.Path(exists=True, dir_okay=False))
@with_appcontext  # da acceso a la configuración de la app (ubicación de la base)
def comando_importar(ruta_listado):
    """Importa el listado técnico (CSV) a la base de datos."""
    ruta_base = current_app.config["BASE_DATOS"]
    ruta_reporte = Path(ruta_base).parent / "reporte_revision.csv"

    conexion = conectar(ruta_base)
    try:
        resumen = importar(ruta_listado, conexion, ruta_reporte)
    except ErrorDeImportacion as error:
        raise click.ClickException(str(error))
    finally:
        conexion.close()

    # Solo se muestran conteos, nunca el contenido del listado
    click.echo(f"Exámenes cargados: {resumen['examenes']}")
    click.echo(f"  Se procesan en el recinto: {resumen['en_recinto']}")
    click.echo(f"  Se derivan: {resumen['examenes'] - resumen['en_recinto']}")
    click.echo(f"Observaciones para revisar: {resumen['observaciones']}")
    click.echo(f"Reporte de revisión: {ruta_reporte}")
