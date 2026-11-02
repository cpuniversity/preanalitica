# Diagramas de secuencia

Cada mensaje entre objetos es un método real: aparece en el diagrama de clases
(`clases.md`) y en el código (`app/`). Las rutas (`rutas.py`) son funciones de
Flask que reciben lo que hace la enfermera en el navegador.

## SD-1 Ver qué tubos usar (CU-03, CU-04, CU-09)

```mermaid
sequenceDiagram
    actor Enfermera
    participant Rutas as rutas.tubos()
    participant Repo as RepositorioDeExamenes
    participant Agrupador
    participant Examen
    participant Revisor as RevisorDeEstabilidad
    participant Calendario as CalendarioDeProceso
    participant Estabilidad
    participant Auditoria

    Enfermera->>Rutas: presiona "Ver qué tubos usar"
    Rutas->>Repo: por_ids(seleccion)
    Repo->>Examen: desde_fila(fila)
    Repo-->>Rutas: examenes
    Rutas->>Agrupador: agrupar(examenes)
    loop cada examen
        Agrupador->>Examen: es_otra_muestra()
        Agrupador->>Examen: opciones_de_tubo()
        Agrupador->>Agrupador: _poner_en_tubo(examen, tipo, cantidad)
    end
    Agrupador-->>Rutas: ResumenDeTubos
    Rutas->>Revisor: revisar_derivados(examenes, ahora)
    loop cada examen derivado
        Revisor->>Examen: es_derivado()
        Revisor->>Revisor: revisar(examen, ahora)
        Revisor->>Calendario: dia_de_proceso(ahora)
        Revisor->>Estabilidad: de_examen(examen)
        Revisor->>Estabilidad: para_decidir()
        opt la estabilidad NO alcanza
            Revisor->>Calendario: sugerir_dias_de_toma(ahora, horas_estabilidad)
        end
    end
    Revisor-->>Rutas: lista de RevisionDeDerivacion
    opt los exámenes cambiaron desde la última vez
        Rutas->>Auditoria: registrar(enfermera, examenes, resumen, derivados, ahora)
    end
    Rutas-->>Enfermera: pantalla de tubos en orden CLSI
```

## SD-2 Buscar un examen (CU-02)

```mermaid
sequenceDiagram
    actor Enfermera
    participant Navegador as buscador.js
    participant Rutas as rutas.sugerencias()
    participant Repo as RepositorioDeExamenes
    participant Buscador
    participant Examen

    Enfermera->>Navegador: escribe "glucoza"
    Navegador->>Rutas: GET /examenes/sugerencias?q=glucoza
    Rutas->>Repo: todos()
    Repo-->>Rutas: examenes
    Rutas->>Buscador: Buscador(examenes)
    Rutas->>Buscador: buscar(consulta, maximo)
    Buscador-->>Rutas: hasta 8 examenes, del más parecido al menos
    loop cada sugerencia
        Rutas->>Examen: etiqueta()
    end
    Rutas-->>Navegador: sugerencias en JSON
    Navegador-->>Enfermera: lista de sugerencias (no elige ninguna sola)
```

## SD-3 Importar el listado técnico (CU-06, CU-07)

```mermaid
sequenceDiagram
    actor Tecnologo as Tecnólogo médico
    participant Comando as comando_importar
    participant Importador
    participant Lector as LectorDeListadoCSV
    participant Base as Base de datos

    Tecnologo->>Comando: flask --app app importar listado_tecnico.csv
    Comando->>Importador: Importador(conexion)
    Comando->>Importador: importar(ruta_listado, ruta_reporte, ruta_tabla_tubos)
    Importador->>Lector: leer(ruta)
    Lector-->>Importador: registros y observaciones
    Note over Importador: aplica la tabla de tubos del tecnólogo médico<br>y revisa campos vacíos, duplicados y datos raros
    Importador->>Importador: _guardar_en_base(registros, archivo, cantidad_observaciones)
    Importador->>Base: reemplaza los exámenes
    Note over Importador: escribe reporte_revision.csv y tubos_por_revisar.csv
    Importador-->>Comando: resumen con conteos
    Comando-->>Tecnologo: solo conteos, nunca contenido del listado
```

## SD-4 Envío semanal de la auditoría (CU-08)

```mermaid
sequenceDiagram
    participant Reloj as revisar_envio_automatico
    participant Auditoria
    participant Enviador as EnviadorDeCorreo
    participant Base as Base de datos
    actor Jefatura

    Note over Reloj: en cada consulta, desde el lunes,<br>si la semana anterior no se ha enviado
    Reloj->>Reloj: crear_enviador(config, carpeta)
    Reloj->>Auditoria: envio_semanal(hoy, enviador, carpeta)
    Auditoria->>Auditoria: exportar(hasta, ruta)
    Auditoria->>Enviador: enviar(asunto, cuerpo, adjunto)
    alt CorreoSMTP (modo real)
        Enviador->>Jefatura: correo con el CSV adjunto
    else CorreoDePrueba (modo prueba)
        Note over Enviador: guarda el correo como archivo .eml
    end
    alt el envío salió bien
        Auditoria->>Base: borra el historial enviado y anota la semana
    else el envío falló (ErrorDeEnvio)
        Note over Auditoria: no borra nada, se reintenta más tarde
    end
```

`EnviadorDeCorreo` es la clase abstracta: `Auditoria` no sabe si el correo es
de prueba o real (patrón Strategy, ver `clases.md`).
