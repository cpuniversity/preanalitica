"""Base de datos SQLite: conexión y tablas."""

import sqlite3
from pathlib import Path

# Ubicación por defecto de la base (dentro de data/, que no va a Git)
RUTA_BASE_DATOS = (
    Path(__file__).resolve().parent.parent / "data" / "preanalitica.db"
)


def conectar(ruta=RUTA_BASE_DATOS):
    """Abre la base de datos y devuelve la conexión."""
    Path(ruta).parent.mkdir(parents=True, exist_ok=True)
    conexion = sqlite3.connect(ruta)
    # Permite leer cada fila como diccionario: fila["nombre"]
    conexion.row_factory = sqlite3.Row
    return conexion


def crear_tablas(conexion):
    """Crea las tablas si todavía no existen."""
    conexion.executescript("""
        -- Un registro por examen del listado técnico.
        -- Los textos se guardan tal como vienen en el listado.
        CREATE TABLE IF NOT EXISTS examenes (
            id                    INTEGER PRIMARY KEY,
            -- fila del archivo, para rastrear el dato
            fila_origen           INTEGER NOT NULL,
            codigo_vidalab        TEXT,
            codigo_medisyn        TEXT,
            nombre                TEXT NOT NULL,
            dias_proceso          TEXT,
            tiempo_respuesta      TEXT,
            -- tipo de muestra, envase y cantidad
            muestra               TEXT,
            codigo_lab_derivado   TEXT,
            laboratorio           TEXT,
            procedimientos        TEXT,
            -- preparación, conservación y traslado
            instrucciones         TEXT,
            -- texto copiado desde las instrucciones
            estabilidad           TEXT,
            -- 1 = sí, 0 = se deriva
            se_procesa_en_recinto INTEGER NOT NULL,
            -- ej. "amarillo", "2 celeste", "otra muestra" o ""
            -- ("" = dato no disponible)
            tubos                 TEXT NOT NULL DEFAULT ''
        );

        -- Un registro por cada vez que se importa el listado.
        CREATE TABLE IF NOT EXISTS importaciones (
            id                 INTEGER PRIMARY KEY,
            fecha              TEXT NOT NULL,
            archivo            TEXT NOT NULL,
            examenes_cargados  INTEGER NOT NULL,
            -- cantidad de avisos del reporte de revisión
            observaciones      INTEGER NOT NULL
        );

        -- Auditoría: un registro por cada resumen de tubos entregado.
        -- Nunca se guarda ningún dato del paciente.
        CREATE TABLE IF NOT EXISTS auditoria (
            id                 INTEGER PRIMARY KEY,
            fecha_hora         TEXT NOT NULL,        -- "2026-11-09 10:30:00"
            enfermera          TEXT NOT NULL,        -- nombre y apellido
            examenes           TEXT NOT NULL,        -- exámenes elegidos
            total_tubos        INTEGER NOT NULL,
            tubos_en_orden     TEXT NOT NULL,
            punciones_aparte   TEXT NOT NULL,
            otras_muestras     TEXT NOT NULL,
            sin_tubo           TEXT NOT NULL,
            -- veredicto de estabilidad de cada derivado
            derivados          TEXT NOT NULL
        );

        -- Envíos semanales de la auditoría ya realizados
        CREATE TABLE IF NOT EXISTS envios_auditoria (
            id                 INTEGER PRIMARY KEY,
            -- lunes de la semana enviada
            semana_inicio      TEXT NOT NULL UNIQUE,
            fecha_envio        TEXT NOT NULL,
            archivo            TEXT NOT NULL,
            registros          INTEGER NOT NULL
        );
    """)

    # Bases creadas antes de existir la columna "tubos": se agrega vacía
    # (se llena al volver a importar el listado)
    columnas = [
        fila[1] for fila in conexion.execute("PRAGMA table_info(examenes)")
    ]
    if "tubos" not in columnas:
        conexion.execute(
            "ALTER TABLE examenes ADD COLUMN tubos TEXT NOT NULL DEFAULT ''"
        )
        conexion.commit()
