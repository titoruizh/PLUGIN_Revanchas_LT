# Documentación Técnica: Generación de Mapas en Revanchas LT

## 1. Visión General
El módulo de generación de mapas (`core/map_generator.py`) es responsable de crear visualizaciones cartográficas automáticas para los muros (Principal, Oeste, Este). Combina ortomosaicos, datos vectoriales (perímetros/sectores) y análisis raster (diferencia de DEMs) en una composición de impresión de QGIS automatizada.

## 2. Flujo de Trabajo

### A. Preparación de Capas
1. **Ortomosaico**: Se carga la imagen ECW/TIF base. Se utiliza su CRS como sistema de referencia del proyecto temporal.
2. **Sectores/Perímetro**: Se cargan los archivos DXF ubicados en `INFO BASE REPORTE/<WALL_CODE>/`.
   - `SECTORES.dxf`: Usado para calcular la extensión (Zoom) óptima.
   - `PERIMETRO CUBETA.dxf`: Usado para recortar la diferencia de DEMs.
3. **Cálculo de Diferencia (Raster Calc)**:
   - Se calcula `DEM_Actual - DEM_Anterior`.
   - Se guarda en archivo temporal `dem_diff_<WALL>.tif`.
4. **Recorte (Clipping)**:
   - Se recorta la diferencia usando el `PERIMETRO CUBETA.dxf`.
   - **Optimización**: Se aplica un `buffer(0)` a la máscara vectorial para corregir errores de topología antes del recorte.
   - Se guarda como `clipped_diff_<WALL>.tif`.

### B. Gestión de Caché (CRÍTICO)
Para evitar que QGIS/GDAL reutilicen archivos temporales antiguos (lo que causaba que se mostraran datos de fechas pasadas), se implementó una **limpieza agresiva**:
- Al inicio de cada generación, se borran: `dem_diff_<WALL>.*`, `clipped_diff_<WALL>.*`, `mask_for_clip_<WALL>.*`.
- Esto obliga a recalcular los rasters en cada ejecución.

### C. Configuración del Layout (Composición)
1. **Página**: Se configura un tamaño personalizado (297x150mm) para adaptarse a la geometría de los muros.
2. **Rotación**: Se aplica rotación específica por muro para alinearlos horizontalmente:
   - **MP (Muro Principal)**: 24°
   - **MO (Muro Oeste)**: 87°
   - **ME (Muro Este)**: 303°

### D. Estrategia de Extensión (Zoom)
El cálculo del área visible (Extent) ha evolucionado para solucionar problemas de "zoom excesivo" o "imágenes cortadas":

| Estrategia | Descripción | Estado |
|------------|-------------|--------|
| Ortomosaico Completo | Usaba todo el ortofoto. Resultaba en mucho espacio vacío. | Descartado |
| Perímetro + Margen | Usaba el perímetro de cubeta. A veces insuficiente. | Descartado |
| **Sectores + 30%** | **Actual**. Usa el extent de `SECTORES.dxf` + 30% margen. Centra perfectamente el área de trabajo. | **Activo** |

**Lógica de Aplicación:**
1. Se obtiene el extent de la capa `SECTORES`.
2. Se aplica un factor de escala (`1.3` o 30% extra).
3. Se usa `map_item.zoomToExtent(extent)` para asegurar que el área sea visible después de la rotación.

### E. Solución de Renderizado
Se detectó un bug donde la capa raster recortada (`clipped_diff`) no aparecía en el mapa final a pesar de existir.
- **Causa**: QGIS Layout Engine a veces ignora capas que no están en el "Árbol de Capas" principal.
- **Solución**: Se agrega temporalmente la capa al `QgsProject.instance()` justo antes de exportar y se quita después (aunque en el script actual se deja para depuración, la limpieza de caché maneja los conflictos).

## 3. Integración en Reportes (QPT)
Para integrar estos mapas en la plantilla maestra `report_template.qpt`:
1. El script genera la imagen del mapa (PNG/JPG).
2. La plantilla QPT debe tener un elemento **Imagen** con ID específico (ej. `main_map`).
3. El código de reporte inyecta la ruta de la imagen generada en ese elemento.
