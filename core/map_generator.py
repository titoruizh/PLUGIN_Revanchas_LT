# -*- coding: utf-8 -*-
"""
Map Generator Module - Revanchas LT Plugin
Genera mapas visuales con ortomosaico, diferencia de DEMs y sectores.
"""

import os
import processing
from qgis.core import (
    QgsProject, QgsRasterLayer, QgsVectorLayer, QgsPrintLayout, 
    QgsLayoutItemMap, QgsLayoutItemPicture, QgsLayoutItemLegend,
    QgsLayoutSize, QgsLayoutPoint, QgsUnitTypes, QgsRectangle,
    QgsMapSettings, QgsLayoutExporter, QgsPalettedRasterRenderer,
    QgsColorRampShader, QgsSingleBandPseudoColorRenderer,
    QgsRasterShader, QgsSingleSymbolRenderer, QgsSymbol,
    QgsSimpleFillSymbolLayer, QgsRasterBandStats,
    QgsLayoutItemScaleBar, QgsLayoutItemLabel, QgsApplication,
    QgsLayoutMeasurement
)
from qgis.PyQt.QtGui import QColor, QFont
from qgis.PyQt.QtCore import Qt

# Importar logging del plugin
try:
    from ..utils.logging_config import get_logger
except ImportError:
    get_logger = lambda x: __import__('logging').getLogger(x)

logger = get_logger(__name__)

class MapGenerator:
    """
    Clase para generar mapas de reporte con análisis espacial.
    """
    
    # Rotaciones por muro (clockwise, en grados)
    WALL_ROTATIONS = {
        "MP": 24.0,   # Muro Principal
        "MO": 87.0,   # Muro Oeste
        "ME": 303.0   # Muro Este
    }
    
    def __init__(self, plugin_dir):
        """
        Inicializa el generador de mapas.
        
        Args:
            plugin_dir: Ruta base del plugin para encontrar "INFO BASE REPORTE"
        """
        self.plugin_dir = plugin_dir
        self.info_base_dir = os.path.join(plugin_dir, "INFO BASE REPORTE")
        
        logger.debug(f"MapGenerator inicializado. Info Base: {self.info_base_dir}")
    
    def _cleanup_temp_files(self, wall_code):
        """Elimina archivos temporales del wall_code para evitar cache."""
        import tempfile
        import glob
        
        temp_dir = tempfile.gettempdir()
        patterns = [
            f"dem_diff_{wall_code}.*",
            f"clipped_diff_{wall_code}.*",
            f"mask_for_clip_{wall_code}.*",
            f"polygon_mask_{wall_code}.*"
        ]
        
        cleaned = 0
        for pattern in patterns:
            for file_path in glob.glob(os.path.join(temp_dir, pattern)):
                try:
                    os.remove(file_path)
                    cleaned += 1
                except Exception as e:
                    pass  # Ignorar errores de limpieza
        
        if cleaned > 0:
            print(f"🗑️ Limpiados {cleaned} archivos temporales de {wall_code}")

    def get_wall_code(self, wall_name):
        """Mapea nombre de muro a código de carpeta (MP/MO/ME)."""
        wall_lower = wall_name.lower()
        if "principal" in wall_lower or "muro 1" in wall_lower:
            return "MP"
        elif "oeste" in wall_lower or "muro 2" in wall_lower:
            return "MO"
        elif "este" in wall_lower or "muro 3" in wall_lower:
            return "ME"
        return "MP"  # Default

    def generate_map_image(self, 
                          wall_name, 
                          ortho_path, 
                          current_dem_path, 
                          previous_dem_path, 
                          output_path):
        """
        Genera una imagen de mapa completa con rotación, leyenda, escala y flecha norte.
        """
        try:
            logger.info(f"Iniciando generación de mapa para {wall_name}")
            
            # Obtener código de muro y rotación
            wall_code = self.get_wall_code(wall_name)
            rotation = self.WALL_ROTATIONS.get(wall_code, 0.0)
            
            # CRÍTICO: Limpiar archivos temp del muro para evitar cache
            self._cleanup_temp_files(wall_code)
            
            # 1. Preparar Capas
            # A. Cargar Ortomosaico (Base) - USAR SU CRS COMO REFERENCIA
            if ortho_path and os.path.exists(ortho_path):
                ortho_layer = QgsRasterLayer(ortho_path, "Ortomosaico")
                if not ortho_layer.isValid():
                    logger.warning("Ortomosaico inválido")
                    return False
            else:
                logger.warning("No se proporcionó ortomosaico")
                return False
            
            # Obtener CRS de referencia (del ortomosaico o default UTM 19S)
            reference_crs = ortho_layer.crs()
            if not reference_crs.isValid():
                # Default: UTM Zone 19S (Chile)
                from qgis.core import QgsCoordinateReferenceSystem
                reference_crs = QgsCoordinateReferenceSystem("EPSG:32719")
                print(f"⚠️ Ortomosaico sin CRS, usando default: EPSG:32719")
            else:
                print(f"✅ CRS de referencia (ortomosaico): {reference_crs.authid()}")
                
            # B. Cargar DXFs
            base_path = os.path.join(self.info_base_dir, wall_code)
            
            sectors_path = None
            perimeter_path = None
            
            if os.path.exists(base_path):
                for f in os.listdir(base_path):
                    if f.lower().endswith(".dxf"):
                        if "sectores" in f.lower():
                            sectors_path = os.path.join(base_path, f)
                        elif "perimetro" in f.lower() and "cubeta" in f.lower():
                            perimeter_path = os.path.join(base_path, f)
            
            if not sectors_path or not perimeter_path:
                logger.error(f"No se encontraron archivos DXF necesarios en {base_path}")
                return False

            # Cargar Sectores con estilo rojo
            sectors_layer = QgsVectorLayer(sectors_path, "Sectores", "ogr")
            if sectors_layer.isValid():
                # Asignar CRS si no tiene
                if not sectors_layer.crs().isValid():
                    sectors_layer.setCrs(reference_crs)
                self._style_sectors_layer(sectors_layer)
            
            # Cargar Perímetro para extent y visualización
            perimeter_layer = QgsVectorLayer(perimeter_path, "Perimetro", "ogr")
            if perimeter_layer.isValid():
                if not perimeter_layer.crs().isValid():
                    perimeter_layer.setCrs(reference_crs)
                print(f"✅ Perímetro cargado: {perimeter_layer.featureCount()} features")
                print(f"   Extent: {perimeter_layer.extent().toString()}")
            else:
                print(f"❌ ERROR: No se pudo cargar perímetro: {perimeter_path}")
            
            # C. Calcular Diferencia DEMs (pasando CRS y wall_code para temp files únicos)
            diff_layer = self._calculate_dem_difference(current_dem_path, previous_dem_path, reference_crs, wall_code)
            if not diff_layer:
                logger.error("Falló el cálculo de diferencia de DEMs")
                return False
                
            # D. Recortar Diferencia con Perímetro CUBETA
            clipped_diff_layer = self._clip_raster_by_mask(diff_layer, perimeter_path, reference_crs, wall_code)
            if not clipped_diff_layer:
                clipped_diff_layer = diff_layer
            
            # E. Estilizar Diferencia (Mapa de Calor)
            min_val, max_val = self._apply_heatmap_style(clipped_diff_layer)
            
            # 2. Crear Layout
            project = QgsProject.instance()
            layout = QgsPrintLayout(project)
            layout.initializeDefaults()
            
            # Página más horizontal/rectangular (cortar espacio vacío abajo)
            page = layout.pageCollection().page(0)
            page.setPageSize(QgsLayoutSize(297, 150, QgsUnitTypes.LayoutMillimeters))  # Más corto
            
            # Calcular extent para el mapa - usar SECTORES como base SIN margen
            # Los sectores cubren el área de trabajo visible mejor que el perímetro
            if sectors_layer and sectors_layer.isValid():
                extent = sectors_layer.extent()
                # Sin margen (1.0) - sectores ocupan 100% del frame (zoom máximo absoluto)
                # No se aplica scale() - extent exacto de los sectores
                extent_source = "sectores exactos (sin margen - 100% zoom)"
            elif perimeter_layer and perimeter_layer.isValid():
                extent = perimeter_layer.extent()
                extent.scale(1.05)  # Margen mínimo para fallback
                extent_source = "perímetro + 5% margen (fallback)"
            else:
                extent = ortho_layer.extent()
                extent_source = "ortomosaico completo (fallback)"
            
            # DEBUG: Información detallada para diagnosticar problemas de extent
            print(f"\n{'='*60}")
            print(f"📊 DEBUG EXTENT para {wall_name} ({wall_code})")
            print(f"{'='*60}")
            print(f"Extent source: {extent_source}")
            print(f"Ortho path: {ortho_path}")
            print(f"Ortho CRS: {ortho_layer.crs().authid()}")
            print(f"Ortho extent: {extent.toString()}")
            print(f"Ortho size (px): {ortho_layer.width()} x {ortho_layer.height()}")
            print(f"Extent width (m): {extent.width():.2f}")
            print(f"Extent height (m): {extent.height():.2f}")
            print(f"Extent aspect ratio: {extent.width()/extent.height():.3f}")
            print(f"Rotation: {rotation}°")
            print(f"Map item size (mm): 255 x 140")
            print(f"Map item aspect ratio: {255/140:.3f}")
            print(f"{'='*60}\n")
            
            # 3. Agregar Mapa Principal (con rotación) - Llenar toda la página
            map_item = QgsLayoutItemMap(layout)
            map_item.attemptResize(QgsLayoutSize(255, 140, QgsUnitTypes.LayoutMillimeters))
            map_item.attemptMove(QgsLayoutPoint(38, 5, QgsUnitTypes.LayoutMillimeters))
            
            # *** FIX: Agregar capa raster recortada al proyecto temporalmente para renderizado ***
            temp_layer_id = None
            if clipped_diff_layer and clipped_diff_layer.isValid():
                QgsProject.instance().addMapLayer(clipped_diff_layer)
                temp_layer_id = clipped_diff_layer.id()
            
            try:
                # Orden: Sectores (arriba), Raster (medio), Ortho (fondo)
                layers_list = [sectors_layer, ortho_layer]
                if clipped_diff_layer and clipped_diff_layer.isValid():
                    layers_list.insert(1, clipped_diff_layer)
                
                map_item.setLayers(layers_list)
                map_item.setCrs(reference_crs)
                
                print(f"📍 PASO 1 - Después de setLayers: {map_item.extent().toString()}")
                
                # IMPORTANTE: Para rotaciones cercanas a 90°, usar zoomToExtent
                # que calcula correctamente el extent visible post-rotación
                map_item.setMapRotation(rotation)
                print(f"📍 PASO 2 - Después de setMapRotation({rotation}°): {map_item.extent().toString()}")
                
                # Usar zoomToExtent en vez de setExtent para mejor control
                map_item.zoomToExtent(extent)
                print(f"📍 PASO 3 - Después de zoomToExtent: {map_item.extent().toString()}")
                
                # Agregar al layout
                layout.addLayoutItem(map_item)
                print(f"📍 PASO 4 - Después de addLayoutItem: {map_item.extent().toString()}")
                
                # 4. Agregar Leyenda (Escala de Colores) - Lado izquierdo
                self._add_color_legend(layout, min_val, max_val)
                
                # 5. Agregar Barra de Escala - Abajo
                self._add_scale_bar(layout, map_item)
                
                # 6. Agregar Flecha Norte - Esquina superior derecha
                self._add_north_arrow(layout, rotation)
                
                # 7. Agregar etiquetas de superficies DEM - Abajo a la derecha
                self._add_dem_labels(layout, current_dem_path, previous_dem_path)
                
                # 8. Exportar
                exporter = QgsLayoutExporter(layout)
                export_settings = QgsLayoutExporter.ImageExportSettings()
                export_settings.dpi = 200
                result = exporter.exportToImage(output_path, export_settings)
                
                if result == QgsLayoutExporter.Success:
                    try: logger.info(f"Mapa generado exitosamente en {output_path}")
                    except: pass
                    return True
                else:
                    try: logger.error(f"Error exportando imagen: {result}")
                    except: pass
                    return False
            finally:
                # Limpieza: Eliminar capa temporal del proyecto
                if temp_layer_id:
                    QgsProject.instance().removeMapLayer(temp_layer_id)

        except Exception as e:
            logger.error(f"Excepción en generación de mapa: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _style_sectors_layer(self, layer):
        """Estilo Sectores: Borde rojo, relleno transparente"""
        symbol = QgsSymbol.defaultSymbol(layer.geometryType())
        symbol.setOpacity(1.0)
        
        if symbol.symbolLayerCount() > 0:
            sym_layer = symbol.symbolLayer(0)
            
            if hasattr(sym_layer, 'setStrokeWidth'):
                sym_layer.setStrokeColor(QColor(180, 0, 0))  # Rojo oscuro
                sym_layer.setStrokeWidth(0.5)
                sym_layer.setFillColor(QColor(0, 0, 0, 0))
            elif hasattr(sym_layer, 'setWidth'):
                sym_layer.setColor(QColor(180, 0, 0))
                sym_layer.setWidth(0.5)
                
        layer.setRenderer(QgsSingleSymbolRenderer(symbol))

    def _add_color_legend(self, layout, min_val, max_val):
        """Agregar leyenda de colores visual (barra de gradiente) al lado izquierdo"""
        from qgis.core import QgsLayoutItemShape
        from qgis.PyQt.QtCore import QRectF
        
        # Configuración de la barra
        bar_x = 5      # Posición X
        bar_y = 25     # Posición Y inicio
        bar_width = 10 # Ancho de la barra
        bar_height = 120 # Alto total de la barra
        
        # Crear segmentos de color (de arriba = max a abajo = min)
        # Colores: Rojo (positivo/relleno) -> Amarillo -> Verde -> Azul (negativo/corte)
        color_stops = [
            (0.0, QColor(202, 0, 32)),      # Rojo (top = max)
            (0.25, QColor(255, 150, 50)),   # Naranja
            (0.5, QColor(255, 255, 150)),   # Amarillo claro
            (0.75, QColor(150, 220, 180)),  # Verde claro
            (1.0, QColor(5, 113, 176))      # Azul (bottom = min)
        ]
        
        num_segments = 20  # Más segmentos = gradiente más suave
        segment_height = bar_height / num_segments
        
        for i in range(num_segments):
            # Calcular posición normalizada (0 = top/max, 1 = bottom/min)
            t = i / num_segments
            
            # Interpolar color
            color = self._interpolate_color(t, color_stops)
            
            # Crear rectángulo de color usando QgsLayoutItemShape
            rect = QgsLayoutItemShape(layout)
            rect.setShapeType(QgsLayoutItemShape.Rectangle)
            rect.attemptMove(QgsLayoutPoint(bar_x, bar_y + i * segment_height, QgsUnitTypes.LayoutMillimeters))
            rect.attemptResize(QgsLayoutSize(bar_width, segment_height + 0.5, QgsUnitTypes.LayoutMillimeters))  # +0.5 para evitar gaps
            
            # Estilo del rectángulo
            symbol = rect.symbol()
            if symbol and symbol.symbolLayerCount() > 0:
                sym_layer = symbol.symbolLayer(0)
                sym_layer.setColor(color)
                sym_layer.setStrokeStyle(Qt.NoPen)  # Sin borde
            
            layout.addLayoutItem(rect)
        
        # Agregar etiquetas de valores a la derecha de la barra
        label_x = bar_x + bar_width + 2
        
        # Valores a mostrar (max, 0.75*max, 0.5*max, 0.25*max, 0, min)
        label_positions = [
            (0.0, max_val),
            (0.25, max_val * 0.75),
            (0.5, max_val * 0.5 if max_val > 0 else 0),
            (0.75, max_val * 0.25 if max_val > 0 else min_val * 0.5),
            (1.0, min_val)
        ]
        
        for t, val in label_positions:
            label = QgsLayoutItemLabel(layout)
            label.setText(f"{val:.2f} m")
            label.setFont(QFont("Arial", 7))
            label.attemptMove(QgsLayoutPoint(label_x, bar_y + t * bar_height - 2, QgsUnitTypes.LayoutMillimeters))
            label.attemptResize(QgsLayoutSize(25, 6, QgsUnitTypes.LayoutMillimeters))
            layout.addLayoutItem(label)
    
    def _interpolate_color(self, t, color_stops):
        """Interpola color en gradiente definido por stops"""
        # Encontrar los dos stops entre los que está t
        for i in range(len(color_stops) - 1):
            t1, c1 = color_stops[i]
            t2, c2 = color_stops[i + 1]
            if t1 <= t <= t2:
                # Interpolar linealmente
                local_t = (t - t1) / (t2 - t1) if t2 != t1 else 0
                r = int(c1.red() + local_t * (c2.red() - c1.red()))
                g = int(c1.green() + local_t * (c2.green() - c1.green()))
                b = int(c1.blue() + local_t * (c2.blue() - c1.blue()))
                return QColor(r, g, b)
        return color_stops[-1][1]

    def _add_scale_bar(self, layout, map_item):
        """Agregar barra de escala arriba a la derecha"""
        scale_bar = QgsLayoutItemScaleBar(layout)
        scale_bar.setLinkedMap(map_item)
        scale_bar.setStyle('Single Box')
        scale_bar.setUnits(QgsUnitTypes.DistanceMeters)
        scale_bar.setNumberOfSegments(4)
        scale_bar.setNumberOfSegmentsLeft(0)
        scale_bar.setUnitsPerSegment(125)  # 125m por segmento
        scale_bar.setUnitLabel("m")
        scale_bar.setFont(QFont("Arial", 8))
        scale_bar.attemptMove(QgsLayoutPoint(167, 5, QgsUnitTypes.LayoutMillimeters))  # Ajustado a la izquierda
        scale_bar.attemptResize(QgsLayoutSize(80, 8, QgsUnitTypes.LayoutMillimeters))
        layout.addLayoutItem(scale_bar)

    def _add_north_arrow(self, layout, map_rotation):
        """Agregar flecha norte con fondo naranja claro y borde negro"""
        from qgis.core import QgsLayoutItemShape
        
        # Posición ajustada más a la derecha (antes: 245, ahora: 253)
        x_pos = 253
        y_pos = 10
        width = 20
        height = 30
        
        # Crear etiqueta con símbolo de flecha color naranja
        north_label = QgsLayoutItemLabel(layout)
        north_label.setText("▲\nN")
        
        # Fuente grande y negrita
        font = QFont("Arial", 20, QFont.Bold)
        north_label.setFont(font)
        
        # Color naranja para el texto/flecha
        north_label.setFontColor(QColor(255, 140, 0))  # Naranja fuerte (DarkOrange)
        
        # Alineación centrada
        north_label.setHAlign(Qt.AlignCenter)
        north_label.setVAlign(Qt.AlignVCenter)
        
        # Posición y tamaño
        north_label.attemptMove(QgsLayoutPoint(x_pos, y_pos, QgsUnitTypes.LayoutMillimeters))
        north_label.attemptResize(QgsLayoutSize(width, height, QgsUnitTypes.LayoutMillimeters))
        
        # Fondo blanco semitransparente para contraste (sin marco)
        north_label.setBackgroundEnabled(True)
        north_label.setBackgroundColor(QColor(255, 255, 255, 200))  # Blanco con 78% opacidad
        north_label.setFrameEnabled(False)  # Sin marco para evitar cuadrado negro
        
        # Rotar la flecha para compensar la rotación del mapa
        north_label.setItemRotation(map_rotation)
        
        layout.addLayoutItem(north_label)

    def _add_dem_labels(self, layout, current_dem_path, previous_dem_path):
        """Agregar etiquetas de superficies DEM abajo a la derecha"""
        import os
        
        # Extraer nombres de archivo sin extensión y ruta
        current_name = os.path.splitext(os.path.basename(current_dem_path))[0] if current_dem_path else "N/A"
        previous_name = os.path.splitext(os.path.basename(previous_dem_path))[0] if previous_dem_path else "N/A"
        
        # Posición: abajo a la derecha del mapa
        x_pos = 175  # Alineado con barra de escala
        y_pos = 135  # Cerca del borde inferior (página tiene 150mm de alto)
        
        # Etiqueta 1: Superficie actual
        label1 = QgsLayoutItemLabel(layout)
        label1.setText(f"Superficie: {current_name}")
        label1.setFont(QFont("Arial", 8))
        label1.attemptMove(QgsLayoutPoint(x_pos, y_pos, QgsUnitTypes.LayoutMillimeters))
        label1.attemptResize(QgsLayoutSize(115, 5, QgsUnitTypes.LayoutMillimeters))
        label1.setHAlign(Qt.AlignLeft)
        layout.addLayoutItem(label1)
        
        # Etiqueta 2: Superficie comparación
        label2 = QgsLayoutItemLabel(layout)
        label2.setText(f"Superficie comparación: {previous_name}")
        label2.setFont(QFont("Arial", 8))
        label2.attemptMove(QgsLayoutPoint(x_pos, y_pos + 5, QgsUnitTypes.LayoutMillimeters))
        label2.attemptResize(QgsLayoutSize(115, 5, QgsUnitTypes.LayoutMillimeters))
        label2.setHAlign(Qt.AlignLeft)
        layout.addLayoutItem(label2)

    def _calculate_dem_difference(self, dem1_path, dem2_path, reference_crs=None, wall_code=""):
        """Calcula dem1 - dem2, preservando el CRS."""
        if not dem1_path or not dem2_path:
            return None
        
        print(f"\n{'='*60}")
        print(f"🔧 DEBUG: Calculando diferencia de DEMs para {wall_code}")
        print(f"{'='*60}")
        print(f"📁 DEM1 (actual): {dem1_path}")
        print(f"📁 DEM2 (anterior): {dem2_path}")
        if reference_crs:
            print(f"📎 CRS de referencia: {reference_crs.authid()}")
        
        dem1 = QgsRasterLayer(dem1_path, "DEM1")
        dem2 = QgsRasterLayer(dem2_path, "DEM2")
        
        if not dem1.isValid() or not dem2.isValid():
            print(f"❌ ERROR: Uno de los DEMs es inválido")
            print(f"   DEM1 válido: {dem1.isValid()}")
            print(f"   DEM2 válido: {dem2.isValid()}")
            logger.error("Uno de los DEMs es inválido")
            return None
        
        # Determinar CRS a usar: del DEM o del reference_crs
        source_crs = dem1.crs()
        if not source_crs.isValid() and reference_crs and reference_crs.isValid():
            source_crs = reference_crs
            print(f"⚠️ DEM sin CRS, usando CRS de referencia: {source_crs.authid()}")
            # Asignar CRS a los DEMs
            dem1.setCrs(source_crs)
            dem2.setCrs(source_crs)
        
        print(f"✅ DEMs cargados:")
        print(f"   DEM1 CRS: {dem1.crs().authid()}")
        print(f"   DEM1 Extent: {dem1.extent().toString()}")
        print(f"   DEM1 Size: {dem1.width()}x{dem1.height()}")
        print(f"   DEM2 CRS: {dem2.crs().authid()}")
        print(f"   CRS a usar: {source_crs.authid()}")
        
        import tempfile
        # Usar nombres únicos por muro para evitar cacheo
        output_diff = os.path.join(tempfile.gettempdir(), f"dem_diff_{wall_code}.tif")
        print(f"📁 Output file: {output_diff}")
        
        # Usar GDAL para calcular la diferencia (preserva CRS mejor que QgsRasterCalculator)
        try:
            print(f"\n🔄 Usando gdal:rastercalculator...")
            result = processing.run("gdal:rastercalculator", {
                'INPUT_A': dem1_path,
                'BAND_A': 1,
                'INPUT_B': dem2_path,
                'BAND_B': 1,
                'FORMULA': 'A - B',
                'NO_DATA': -9999,
                'RTYPE': 5,  # Float32
                'OUTPUT': output_diff
            })
            
            if result and 'OUTPUT' in result and os.path.exists(result['OUTPUT']):
                layer = QgsRasterLayer(result['OUTPUT'], "Difference")
                if layer.isValid():
                    # Verificar que el CRS se preservó
                    print(f"✅ Diferencia calculada con GDAL")
                    print(f"   Output CRS inicial: {layer.crs().authid()}")
                    
                    # Si el CRS no se preservó, asignarlo manualmente
                    if not layer.crs().isValid() and source_crs.isValid():
                        print(f"⚠️ Asignando CRS manualmente: {source_crs.authid()}")
                        layer.setCrs(source_crs)
                    
                    print(f"   Final CRS: {layer.crs().authid()}")
                    print(f"{'='*60}\n")
                    return layer
                    
        except Exception as e:
            print(f"⚠️ GDAL rastercalculator falló: {e}, intentando con QgsRasterCalculator...")
        
        # Fallback: QgsRasterCalculator
        from qgis.analysis import QgsRasterCalculator, QgsRasterCalculatorEntry
        
        entries = []
        
        entry1 = QgsRasterCalculatorEntry()
        entry1.ref = 'dem1@1'
        entry1.raster = dem1
        entry1.bandNumber = 1
        entries.append(entry1)
        
        entry2 = QgsRasterCalculatorEntry()
        entry2.ref = 'dem2@1'
        entry2.raster = dem2
        entry2.bandNumber = 1
        entries.append(entry2)
        
        # Usar constructor con CRS
        calc = QgsRasterCalculator(
            'dem1@1 - dem2@1', 
            output_diff, 
            'GTiff',
            dem1.extent(), 
            source_crs,  # Pasar CRS explícitamente
            dem1.width(), 
            dem1.height(), 
            entries
        )
        
        result = calc.processCalculation()
        if result == 0:
            layer = QgsRasterLayer(output_diff, "Difference")
            if layer.isValid():
                # Asegurar CRS
                if not layer.crs().isValid() and source_crs.isValid():
                    layer.setCrs(source_crs)
                print(f"✅ Diferencia calculada con QgsRasterCalculator")
                print(f"   CRS: {layer.crs().authid()}")
                print(f"{'='*60}\n")
                return layer
        
        print(f"❌ Error en cálculo de diferencia: {result}")
        logger.error(f"Error en QgsRasterCalculator: {result}")
        return None

    def _clip_raster_by_mask(self, raster_layer, mask_path, reference_crs=None, wall_code=""):
        """Recorta raster usando una capa vectorial de máscara (DXF)."""
        import tempfile
        
        # Usar nombres únicos por muro para evitar cacheo
        output_path = os.path.join(tempfile.gettempdir(), f"clipped_diff_{wall_code}.tif")
        
        print(f"\n{'='*60}")
        print(f"🔧 DEBUG: Iniciando proceso de clipping para {wall_code}")
        print(f"{'='*60}")
        print(f"📁 Raster input: {raster_layer.source() if raster_layer else 'None'}")
        print(f"📁 Máscara DXF: {mask_path}")
        print(f"📁 Output path: {output_path}")
        if reference_crs:
            print(f"📎 CRS de referencia: {reference_crs.authid()}")
        
        if not os.path.exists(mask_path):
            print(f"❌ ERROR: Máscara no existe: {mask_path}")
            logger.error(f"Máscara no existe: {mask_path}")
            return None
        
        # Asegurar que el raster tiene CRS asignado
        if not raster_layer.crs().isValid() and reference_crs and reference_crs.isValid():
            print(f"⚠️ Raster sin CRS, asignando: {reference_crs.authid()}")
            raster_layer.setCrs(reference_crs)
        
        # Cargar DXF
        dxf_layer = QgsVectorLayer(mask_path, "DXF_Mask", "ogr")
        
        if not dxf_layer.isValid():
            print(f"❌ ERROR: No se pudo cargar DXF: {mask_path}")
            logger.error(f"No se pudo cargar DXF: {mask_path}")
            return raster_layer
        
        # Asignar CRS al DXF si no tiene
        if not dxf_layer.crs().isValid() and reference_crs and reference_crs.isValid():
            print(f"⚠️ DXF sin CRS, asignando: {reference_crs.authid()}")
            dxf_layer.setCrs(reference_crs)
        
        print(f"✅ DXF cargado correctamente")
        print(f"   - Features: {dxf_layer.featureCount()}")
        print(f"   - CRS: {dxf_layer.crs().authid() if dxf_layer.crs().isValid() else 'NO DEFINIDO'}")
        print(f"   - Extent: {dxf_layer.extent().toString()}")
        
        # Verificar tipo de geometría
        from qgis.core import QgsWkbTypes
        geom_type = dxf_layer.geometryType()
        geom_type_name = {0: 'Point', 1: 'Line', 2: 'Polygon', 3: 'Unknown', 4: 'Null'}
        print(f"   - Tipo geometría: {geom_type} ({geom_type_name.get(geom_type, 'Unknown')})")
        
        # Debug: Mostrar información de cada feature
        for i, feat in enumerate(dxf_layer.getFeatures()):
            geom = feat.geometry()
            if geom:
                print(f"   - Feature {i}: WKB Type={geom.wkbType()}, Área={geom.area():.2f}, Perímetro={geom.length():.2f}")
                if i >= 2:  # Solo mostrar primeras 3
                    print(f"   - ... ({dxf_layer.featureCount()} features en total)")
                    break
        
        mask_layer = dxf_layer
        
        # Si es línea, convertir a polígono
        if geom_type == QgsWkbTypes.LineGeometry:
            print(f"\n⚠️ DXF es LÍNEA, intentando convertir a polígono...")
            try:
                # Usar nombre único por muro para evitar cacheo
                polygon_output = os.path.join(tempfile.gettempdir(), f"polygon_mask_{wall_code}.gpkg")
                print(f"   Output polígono: {polygon_output}")
                
                result = processing.run("qgis:linestopolygons", {
                    'INPUT': dxf_layer,
                    'OUTPUT': polygon_output
                })
                
                print(f"   Resultado processing: {result}")
                
                if result and 'OUTPUT' in result:
                    polygon_layer = QgsVectorLayer(result['OUTPUT'], "Polygon_Mask", "ogr")
                    if polygon_layer.isValid() and polygon_layer.featureCount() > 0:
                        mask_layer = polygon_layer
                        # Asignar CRS al polígono convertido
                        if not mask_layer.crs().isValid() and reference_crs and reference_crs.isValid():
                            mask_layer.setCrs(reference_crs)
                        print(f"✅ Conversión exitosa: {polygon_layer.featureCount()} polígonos")
                        print(f"   - CRS del polígono: {mask_layer.crs().authid()}")
                        
                        # Debug del polígono resultante
                        for feat in polygon_layer.getFeatures():
                            geom = feat.geometry()
                            if geom:
                                print(f"   - Polígono: Área={geom.area():.2f}m², Válido={geom.isGeosValid()}")
                                break
                    else:
                        print(f"❌ Conversión falló: Layer inválido o vacío")
                        print(f"   Valid: {polygon_layer.isValid()}, Features: {polygon_layer.featureCount() if polygon_layer.isValid() else 'N/A'}")
            except Exception as e:
                print(f"❌ Error en conversión: {e}")
                import traceback
                traceback.print_exc()
        elif geom_type == QgsWkbTypes.PolygonGeometry:
            print(f"✅ DXF ya es POLÍGONO, no requiere conversión")
        else:
            print(f"⚠️ Tipo de geometría no esperado: {geom_type}")
        
        # Verificar CRS - usar reference_crs si está disponible
        raster_crs = raster_layer.crs()
        mask_crs = mask_layer.crs()
        
        # Si ninguno tiene CRS válido, usar reference_crs
        working_crs = raster_crs if raster_crs.isValid() else (reference_crs if reference_crs and reference_crs.isValid() else None)
        
        print(f"\n🗺️ Verificación de CRS:")
        print(f"   - Raster CRS: {raster_crs.authid() if raster_crs.isValid() else 'NO DEFINIDO'}")
        print(f"   - Máscara CRS: {mask_crs.authid() if mask_crs.isValid() else 'NO DEFINIDO'}")
        print(f"   - Working CRS: {working_crs.authid() if working_crs else 'NINGUNO'}")
        
        if not mask_crs.isValid() and working_crs:
            print(f"⚠️ Asignando CRS a máscara: {working_crs.authid()}")
            mask_layer.setCrs(working_crs)
        
        if not raster_crs.isValid() and working_crs:
            print(f"⚠️ Asignando CRS a raster: {working_crs.authid()}")
            raster_layer.setCrs(working_crs)
        
        # *** IMPORTANTE: Guardar máscara a archivo único para evitar cacheo ***
        mask_temp_path = os.path.join(tempfile.gettempdir(), f"mask_for_clip_{wall_code}.gpkg")
        print(f"\n📁 Guardando máscara a archivo único: {mask_temp_path}")
        
        # FIX: Aplicar buffer(0) para reparar geometrías inválidas que fallan silenciosamente en GDAL
        print(f"🔧 Reparando geometrías con buffer(0)...")
        try:
             fixed_mask = processing.run("native:buffer", {
                'INPUT': mask_layer,
                'DISTANCE': 0,
                'SEGMENTS': 5,
                'END_CAP_STYLE': 0,
                'JOIN_STYLE': 0,
                'MITER_LIMIT': 2,
                'DISSOLVE': False,
                'OUTPUT': 'memory:'
            })['OUTPUT']
             mask_layer = fixed_mask
             print(f"✅ Geometrías reparadas")
        except Exception as e:
            print(f"⚠️ Falló reparación de geometrías: {e}, usando original")

        # Eliminar archivo anterior si existe para forzar recreación
        if os.path.exists(mask_temp_path):
            try:
                os.remove(mask_temp_path)
            except:
                pass
        
        # Guardar la máscara actual a un archivo nuevo
        from qgis.core import QgsVectorFileWriter
        save_options = QgsVectorFileWriter.SaveVectorOptions()
        save_options.driverName = "GPKG"
        save_options.fileEncoding = "UTF-8"
        
        error = QgsVectorFileWriter.writeAsVectorFormatV3(
            mask_layer,
            mask_temp_path,
            QgsProject.instance().transformContext(),
            save_options
        )
        
        if error[0] == QgsVectorFileWriter.NoError:
            print(f"✅ Máscara guardada correctamente")
            # Cargar la máscara desde el archivo
            saved_mask_layer = QgsVectorLayer(mask_temp_path, "Saved_Mask", "ogr")
            if saved_mask_layer.isValid():
                print(f"   Extent de máscara guardada: {saved_mask_layer.extent().toString()}")
                mask_to_use = mask_temp_path  # Usar el path del archivo
            else:
                print(f"⚠️ No se pudo cargar máscara guardada, usando layer original")
                mask_to_use = mask_layer
        else:
            print(f"⚠️ Error guardando máscara: {error}, usando layer original")
            mask_to_use = mask_layer
        
        # Ejecutar clip con CRS válido
        clip_crs = working_crs if working_crs else raster_layer.crs()
        
        # *** IMPORTANTE: Normalizar path para evitar problemas con Windows short paths ***
        # Normalizar el path del output para evitar LT_GAB~1 etc
        output_path_normalized = os.path.normpath(output_path)
        mask_path_normalized = os.path.normpath(mask_to_use) if isinstance(mask_to_use, str) else mask_to_use
        
        # Eliminar archivo anterior si existe
        if os.path.exists(output_path_normalized):
            try:
                os.remove(output_path_normalized)
                print(f"🗑️ Archivo anterior eliminado: {output_path_normalized}")
            except Exception as e:
                print(f"⚠️ No se pudo eliminar archivo anterior: {e}")
        
        # Usar path al archivo de máscara en vez de layer en memoria
        params = {
            'INPUT': raster_layer.source(),  # Usar source path directamente
            'MASK': mask_path_normalized,
            'SOURCE_CRS': clip_crs,
            'TARGET_CRS': clip_crs,
            'NODATA': -9999,
            'ALPHA_BAND': False,
            'CROP_TO_CUTLINE': True,
            'KEEP_RESOLUTION': True,
            'SET_RESOLUTION': False,
            'OUTPUT': output_path_normalized
        }
        
        print(f"\n🔄 Ejecutando gdal:cliprasterbymasklayer...")
        print(f"   Input raster: {params['INPUT']}")
        print(f"   Mask source: {mask_path_normalized}")
        print(f"   Output path: {output_path_normalized}")
        print(f"   CRS: {clip_crs.authid()}")
        
        try:
            # Usar feedback context para capturar errores de GDAL
            from qgis.core import QgsProcessingFeedback
            feedback = QgsProcessingFeedback()
            
            result = processing.run("gdal:cliprasterbymasklayer", params, feedback=feedback)
            
            print(f"   Resultado: {result}")
            
            if result and 'OUTPUT' in result:
                output_from_result = result['OUTPUT']
                
                # Intentar múltiples variaciones del path
                paths_to_check = [
                    output_from_result,
                    os.path.normpath(output_from_result),
                    output_path_normalized,
                    output_path
                ]
                
                # También buscar en temp dir cualquier archivo que contenga wall_code
                temp_dir = tempfile.gettempdir()
                print(f"   Buscando archivos en temp: {temp_dir}")
                try:
                    temp_files = [f for f in os.listdir(temp_dir) if wall_code in f and f.endswith('.tif')]
                    print(f"   Archivos con '{wall_code}': {temp_files}")
                except Exception as e:
                    print(f"   Error listando temp: {e}")
                
                found_path = None
                for path in paths_to_check:
                    if os.path.exists(path):
                        found_path = path
                        break
                
                if found_path:
                    file_size = os.path.getsize(found_path)
                    print(f"✅ Archivo de salida creado: {found_path} ({file_size} bytes)")
                    
                    layer = QgsRasterLayer(found_path, "Clipped Difference")
                    if layer.isValid():
                        print(f"✅ CLIPPING EXITOSO")
                        print(f"   - Extent clipped: {layer.extent().toString()}")
                        print(f"   - Size: {layer.width()}x{layer.height()}")
                        print(f"{'='*60}\n")
                        logger.info("Recorte exitoso")
                        return layer
                    else:
                        print(f"❌ Layer resultado es inválido")
                else:
                    print(f"❌ Archivo de salida NO existe en ninguna variación:")
                    for path in paths_to_check:
                        print(f"   - {path}: {'EXISTE' if os.path.exists(path) else 'NO EXISTE'}")
            else:
                print(f"❌ Resultado no contiene 'OUTPUT': {result}")
                
        except Exception as e:
            print(f"❌ EXCEPCIÓN en gdal:cliprasterbymasklayer: {e}")
            logger.error(f"Error recorte GDAL: {e}")
            import traceback
            traceback.print_exc()
        
        print(f"\n⚠️ CLIPPING FALLÓ - Retornando raster SIN recortar")
        print(f"{'='*60}\n")
        return raster_layer

    def _apply_heatmap_style(self, layer):
        """
        Aplica estilo PseudoColor al raster.
        Valores menores a 0.05m son TRANSPARENTES.
        Rango visible: 0.05m a 1.0m.
        """
        from qgis.core import QgsColorRampShader, QgsSingleBandPseudoColorRenderer, QgsRasterShader
        
        fcn = QgsColorRampShader()
        fcn.setColorRampType(QgsColorRampShader.Interpolated)
        
        # Rango fijo de valores: 0.05m a 1.0m
        min_val = 0.05
        max_val = 1.0
            
        # Escala de colores: Transparente (bajo) -> Verde/Amarillo -> Rojo (alto)
        # Valores < 0.05m serán transparentes
        lst = [
            QgsColorRampShader.ColorRampItem(0.0, QColor(0, 0, 0, 0), ""),                           # Transparente (< 0.05m)
            QgsColorRampShader.ColorRampItem(min_val, QColor(180, 230, 180, 100), f"{min_val:.2f}m"), # Verde muy claro semi-transparente
            QgsColorRampShader.ColorRampItem(0.25, QColor(180, 230, 150), "0.25m"),                  # Verde claro
            QgsColorRampShader.ColorRampItem(0.50, QColor(255, 255, 100), "0.50m"),                  # Amarillo
            QgsColorRampShader.ColorRampItem(0.75, QColor(255, 180, 50), "0.75m"),                   # Naranja
            QgsColorRampShader.ColorRampItem(max_val, QColor(202, 0, 32), f"{max_val:.2f}m")         # Rojo (1.0m)
        ]
        fcn.setColorRampItemList(lst)
        
        shader = QgsRasterShader()
        shader.setRasterShaderFunction(fcn)
        
        renderer = QgsSingleBandPseudoColorRenderer(layer.dataProvider(), 1, shader)
        layer.setRenderer(renderer)
        layer.setOpacity(0.85)  # Alta opacidad para valores visibles
        
        return min_val, max_val
