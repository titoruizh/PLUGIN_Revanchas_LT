# Skill: Integración de Exportación Excel (Revanchas)

Este documento describe la arquitectura, configuración y soluciones técnicas implementadas para la exportación de mediciones a plantillas Excel preexistentes en el plugin QGIS "Revanchas LT".

## 1. Propósito
Permitir la actualización directa de archivos Excel de reporte, preservando fórmulas y formato, mediante:
1.  **Desplazamiento de Datos Antiguos**: Mover columnas "Actuales" a "Anteriores".
2.  **Inserción de Nuevos Datos**: Escribir nuevas mediciones desde la App de QGIS.
3.  **Actualización de Metadatos**: Fecha del DEM y Título del Gráfico.

## 2. Arquitectura: `ExcelUpdater`

La clase principal es `core/excel_updater.py`.

### Flujo de Trabajo (`update_wall_data`)
1.  **Carga Dual**: Se cargan dos instancias del Excel:
    *   `wb` (data_only=False): Para **escribir** y preservar fórmulas.
    *   `wb_values` (data_only=True): Para **leer valores calculados** (ej. Revancha) y moverlos como texto plano.
2.  **Identificación de Muro**: Normaliza nombres (ej. "Muro 2" -> "Muro Oeste").
3.  **Búsqueda de Hoja**: Busca por nombre exacto o palabras clave ("REV", "Principal", etc.).
4.  **Desplazamiento (`_shift_data`)**: Lee de `wb_values`, escribe en `wb`.
5.  **Escritura (`_write_new_data`)**: Normaliza PKs y escribe en `wb`.
6.  **Actualización Global**: Fecha y Título de Gráfico.

## 3. Configuración (`WALL_CONFIG`)

Cada muro se define en un diccionario dentro de la clase:

```python
"Nombre del Muro": {
    "sheet_name": "NombreHoja",  # Nombre exacto o substring único
    "rows_range": (Inicio, Fin), # Tupla (FilaInicial, FilaFinal) ej. (13, 85)
    "pk_col_idx": 9,             # Índice de columna PK (Base 1: A=1, I=9)
    
    # Mapeo de Desplazamiento (Origen -> Destino)
    "shift_map": [
        ("C", "Q"), # Col C (Valor) -> Col Q (Estático)
        ("E", "M"), # Col E (Fórmula) -> Col M (Estático/Valor)
    ],
    
    # Mapeo de Escritura (Dato App -> Columna Destino)
    "write_map": {
        "crown": "C", # Cota Coronamiento
        "lama": "F",  # Cota Lama
        "width": "H", # Ancho
    },
    
    "date_cell": "F6",
    "chart_name_contains": "Gráfico 1", 
    "chart_title_prefix": "Título del Gráfico "
}
```

## 4. Soluciones Técnicas Clave (Gotchas)

### A. Normalización de PK (`_normalize_pk`)
**Problema**: La App entrega PKs como strings ("0+140"), floats (140.0) o enteros (140). El Excel puede tener "0+140.00" (texto) o 140 (número con formato personalizado).
**Solución**: Función `_normalize_pk` que convierte todo a float (metros):
*   `"0+140"` -> `140.0`
*   `"0+140.00"` -> `140.0`
*   `140` -> `140.0`
Esto permite un match exacto (con tolerancia de 10-15cm).

### B. Fórmula vs Valor (Revancha)
**Problema**: La columna "Revancha" (E) es una fórmula (`=C-F`). Al moverla a "Revancha Anterior" (M), si copiamos la celda normal, copiamos la fórmula (referencias rotas).
**Solución**: Leemos el valor desde `wb_values` (que tiene el resultado calculado) y escribimos ese número en `wb`.

### C. Actualización de Gráficos
**Problema**: `openpyxl` tiene soporte limitado para modificar títulos de gráficos complejos (RichText).
**Solución**: Iteramos sobre `sheet._charts` e intentamos asignar `chart.title = "Nuevo Título"` forzosamente, ignorando la estructura compleja si existe.

### D. Búsqueda de Hojas Flexible
**Problema**: El nombre de la hoja puede variar ligeramente ("Muro Principal" vs "REV_MP").
**Solución**: Si no encuentra el nombre exacto, busca substrings en `wb.sheetnames` (ej. busca "rev" o "principal").

## 5. Cómo agregar un nuevo muro
1.  Obtener:
    *   Nombre de Hoja
    *   Rango de filas (donde están los datos)
    *   Columna del PK (I=9 normalmente)
    *   Mapeo de columnas (Qué letra va a dónde)
2.  Agregar entrada a `WALL_CONFIG` en `core/excel_updater.py`.
3.  Agregar **alias** en `update_wall_data` si el nombre de la UI difiere (ej. "Muro 2" -> "Muro Oeste").
