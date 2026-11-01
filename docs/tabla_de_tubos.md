# Guía: tabla de tubos por revisar

Al importar el listado técnico, la app reconoce sola el tubo de la mayoría de los
exámenes. Cuando el texto del listado no es claro (nombra varios tubos, ninguno,
o un tubo que la app no conoce), el examen queda en el archivo:

```
data/tubos_por_revisar.csv
```

Mientras no se complete, la app muestra ese examen como **"Tubo: dato no disponible"**
y pide consultar con el laboratorio. La app nunca adivina el tubo.

## Cómo completarla

1. Abrir `data/tubos_por_revisar.csv` con Excel.
2. Llenar solo la columna **"Tubo correcto (completar)"**. Las demás son de referencia.
3. Guardar como CSV (separado por punto y coma).
4. Volver a importar el listado:
   ```
   flask --app app importar data/listado_tecnico.csv
   ```
   Lo que se escribió en la tabla se conserva en cada importación.

## Qué escribir en "Tubo correcto"

Nombres de tubo que entiende la app:

| Escribir           | Tubo                                     |
|--------------------|------------------------------------------|
| `hemocultivo`      | Frasco de hemocultivo                    |
| `celeste`          | Tubo celeste (citrato)                   |
| `amarillo`         | Tubo amarillo con gel                    |
| `rojo`             | Tubo rojo                                |
| `verde`            | Tubo verde (heparina)                    |
| `jeringa-venosa`   | Jeringa con heparina (gases venosos)     |
| `lila`             | Tubo lila (EDTA)                         |
| `gris`             | Tubo gris (fluoruro)                     |
| `jeringa-arterial` | Jeringa con heparina (gases arteriales)  |
| `otra muestra`     | No es sangre: va en "Otras muestras"     |

Combinaciones:

| Escribir           | Significa                                                    |
|--------------------|--------------------------------------------------------------|
| `lila`             | un tubo lila                                                 |
| `2 celeste`        | el laboratorio pide 2 tubos celeste para este examen         |
| `lila + celeste`   | el examen necesita los dos tubos                             |
| `amarillo o rojo`  | sirve cualquiera; si no hay con qué juntarlo, se usa el primero |

Mayúsculas y tildes no importan. Si se escribe algo que la app no entiende, el examen
sigue como "dato no disponible" y el reporte de revisión lo avisa.
