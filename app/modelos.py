"""Base de datos SQLite: conexión y tablas."""

import sqlite3
from pathlib import Path

# Ubicación por defecto de la base (dentro de data/, que no va a Git)
RUTA_BASE_DATOS = Path(__file__).resolve().parent.parent / "data" / "preanalitica.db"


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
            fila_origen           INTEGER NOT NULL,  -- fila del archivo, para rastrear el dato
            codigo_vidalab        TEXT,
            codigo_medisyn        TEXT,
            nombre                TEXT NOT NULL,
            dias_proceso          TEXT,
            tiempo_respuesta      TEXT,
            muestra               TEXT,              -- tipo de muestra, envase y cantidad
            codigo_lab_derivado   TEXT,
            laboratorio           TEXT,
            procedimientos        TEXT,
            instrucciones         TEXT,              -- preparación, conservación y traslado
            estabilidad           TEXT,              -- texto copiado desde las instrucciones
            se_procesa_en_recinto INTEGER NOT NULL,  -- 1 = sí, 0 = se deriva
            tubos                 TEXT NOT NULL DEFAULT ''  -- ej. "amarillo", "2 celeste",
                                                     -- "otra muestra" o "" (dato no disponible)
        );

        -- Un registro por cada vez que se importa el listado.
        CREATE TABLE IF NOT EXISTS importaciones (
            id                 INTEGER PRIMARY KEY,
            fecha              TEXT NOT NULL,
            archivo            TEXT NOT NULL,
            examenes_cargados  INTEGER NOT NULL,
            observaciones      INTEGER NOT NULL      -- cantidad de avisos del reporte de revisión
        );
    """)

    # Bases creadas antes de existir la columna "tubos": se agrega vacía
    # (se llena al volver a importar el listado)
    columnas = [fila[1] for fila in conexion.execute("PRAGMA table_info(examenes)")]
    if "tubos" not in columnas:
        conexion.execute("ALTER TABLE examenes ADD COLUMN tubos TEXT NOT NULL DEFAULT ''")
        conexion.commit()
