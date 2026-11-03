# Preanalítica

[![Pruebas](https://github.com/cpuniversity/preanalitica/actions/workflows/pruebas.yml/badge.svg)](https://github.com/cpuniversity/preanalitica/actions/workflows/pruebas.yml)

Aplicación web para personal de enfermería y matronería. A partir de los
exámenes indicados por el médico, muestra qué tubos usar y en qué orden
extraerlos, cuáles exámenes se procesan en el laboratorio del recinto y cuáles
se derivan, y si la estabilidad de cada muestra derivada alcanza.

Prototipo local para el curso Ingeniería de Software (UDP). Las reglas clínicas
las define el tecnólogo médico del proyecto.

## Cómo usarla

```
python -m venv venv
venv\Scripts\activate                              # Windows
source venv/bin/activate                           # Mac / Linux
pip install -r requirements.txt
copy .env.example .env                             # configuración del correo (una vez)
flask --app app importar data/listado_tecnico.csv  # carga el listado en la base
flask --app app run --debug                        # abre http://127.0.0.1:5000
pytest                                             # corre las pruebas automáticas
```

El listado técnico del laboratorio no está en el repositorio: se copia a mano
en `data/`.

## Documentación

- [Requisitos y estado del proyecto](docs/requisitos.md)
- [Arquitectura](docs/arquitectura.md) y [diagramas UML](docs/uml/)
- [Gestión ágil](docs/gestion_agil/): objetivo, backlog, historias e iteraciones
- [Plan de pruebas](docs/plan_de_pruebas.md) e [informe de resultados](docs/informe_de_pruebas.md)
- [Guía de la tabla de tubos](docs/tabla_de_tubos.md) para el tecnólogo médico
