"""Acceso a los exámenes guardados en la base de datos (patrón Repositorio).

Las páginas piden los exámenes al repositorio y no escriben SQL: si la base
de datos cambiara, solo habría que cambiar este archivo.
"""

from app.examen import Examen

COLUMNAS = ", ".join(Examen.CAMPOS)


class RepositorioDeExamenes:
    """Lee los exámenes del listado desde la base de datos."""

    def __init__(self, conexion):
        self.conexion = conexion

    def todos(self):
        return [Examen.desde_fila(fila) for fila in self.conexion.execute(f"SELECT {COLUMNAS} FROM examenes")]

    def por_id(self, id_examen):
        fila = self.conexion.execute(f"SELECT {COLUMNAS} FROM examenes WHERE id = ?", (id_examen,)).fetchone()
        return Examen.desde_fila(fila) if fila else None

    def por_ids(self, ids):
        """Los exámenes en el mismo orden de los ids. Un id que ya no existe se omite
        (puede pasar si el listado se volvió a importar)."""
        examenes = [self.por_id(id_examen) for id_examen in ids]
        return [examen for examen in examenes if examen]

    def existe(self, id_examen):
        return self.conexion.execute("SELECT 1 FROM examenes WHERE id = ?", (id_examen,)).fetchone() is not None

    def hay_listado(self):
        return self.conexion.execute("SELECT COUNT(*) FROM examenes").fetchone()[0] > 0
