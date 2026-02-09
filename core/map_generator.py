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
    QgsLayoutItemScaleBar, QgsLayoutItemLabel, QgsApplication
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
        "MO": 0.0,    # Muro Oeste (ajustar según necesidad)
        "ME": 0.0     # Muro Este (ajustar según necesidad)
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

    def get_wall_code(self, wall_name):
        """Mapea nombre de muro a código de carpeta (MP/MO/ME)."""
        if "Muro 1" in wall_name or "Principal" in wall_name:
            return "MP"
        elif "Muro 2" in wall_name or "Oeste" in wall_name:
            return "MO"
        elif "Muro 3" in wall_name or "Este" in wall_name:
            return "ME"
        return "MP" # Default

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
            
            # 1. Preparar Capas
            # A. Cargar Ortomosaico (Base)
            if ortho_path and os.path.exists(ortho_path):
                ortho_layer = QgsRasterLayer(ortho_path, "Ortomosaico")
                if not ortho_layer.isValid():
                    logger.warning("Ortomosaico inválido")
                    return False
            else:
                logger.warning("No se proporcionó ortomosaico")
                return False
                
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
                self._style_sectors_layer(sectors_layer)
            
            # C. Calcular Diferencia DEMs
            diff_layer = self._calculate_dem_difference(current_dem_path, previous_dem_path)
            if not diff_layer:
                logger.error("Falló el cálculo de diferencia de DEMs")
                return False
                
            # D. Recortar Diferencia con Perímetro CUBETA
            clipped_diff_layer = self._clip_raster_by_mask(diff_layer, perimeter_path)
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
            
            # Calcular extent para el mapa - usar sectores para enfocar el área de interés
            extent = sectors_layer.extent()
            extent.grow(extent.width() * 0.10)  # Buffer 10%
            
            # 3. Agregar Mapa Principal (con rotación) - Llenar toda la página
            map_item = QgsLayoutItemMap(layout)
            map_item.attemptResize(QgsLayoutSize(255, 140, QgsUnitTypes.LayoutMillimeters))  # Ajustado a nueva altura
            map_item.attemptMove(QgsLayoutPoint(38, 5, QgsUnitTypes.LayoutMillimeters))
            map_item.setLayers([sectors_layer, clipped_diff_layer, ortho_layer])
            map_item.setExtent(extent)
            map_item.setCrs(ortho_layer.crs())
            
            # Aplicar rotación (positivo = clockwise en QGIS)
            map_item.setMapRotation(rotation)
            
            layout.addLayoutItem(map_item)
            
            # 4. Agregar Leyenda (Escala de Colores) - Lado izquierdo
            self._add_color_legend(layout, min_val, max_val)
            
            # 5. Agregar Barra de Escala - Abajo
            self._add_scale_bar(layout, map_item)
            
            # 6. Agregar Flecha Norte - Esquina superior derecha
            self._add_north_arrow(layout, rotation)
            
            # 7. Exportar
            exporter = QgsLayoutExporter(layout)
            export_settings = QgsLayoutExporter.ImageExportSettings()
            export_settings.dpi = 200
            result = exporter.exportToImage(output_path, export_settings)
            
            if result == QgsLayoutExporter.Success:
                logger.info(f"Mapa generado exitosamente en {output_path}")
                return True
            else:
                logger.error(f"Error exportando imagen: {result}")
                return False

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
        scale_bar.attemptMove(QgsLayoutPoint(175, 5, QgsUnitTypes.LayoutMillimeters))  # Arriba a la derecha
        scale_bar.attemptResize(QgsLayoutSize(80, 8, QgsUnitTypes.LayoutMillimeters))
        layout.addLayoutItem(scale_bar)

    def _add_north_arrow(self, layout, map_rotation):
        """Agregar flecha norte en esquina superior derecha"""
        # Crear etiqueta con símbolo de flecha
        north_label = QgsLayoutItemLabel(layout)
        north_label.setText("▲\nN")
        north_label.setFont(QFont("Arial", 24, QFont.Bold))
        north_label.setHAlign(Qt.AlignCenter)
        north_label.setVAlign(Qt.AlignTop)
        north_label.attemptMove(QgsLayoutPoint(270, 10, QgsUnitTypes.LayoutMillimeters))
        north_label.attemptResize(QgsLayoutSize(25, 35, QgsUnitTypes.LayoutMillimeters))
        
        # Rotar la flecha para compensar la rotación del mapa
        # (Si el mapa está rotado 24° CW, la flecha debe apuntar 24° CW del norte visual)
        north_label.setItemRotation(map_rotation)
        
        layout.addLayoutItem(north_label)

    def _calculate_dem_difference(self, dem1_path, dem2_path):
        """Calcula dem1 - dem2."""
        if not dem1_path or not dem2_path:
            return None
            
        dem1 = QgsRasterLayer(dem1_path, "DEM1")
        dem2 = QgsRasterLayer(dem2_path, "DEM2")
        
        if not dem1.isValid() or not dem2.isValid():
            logger.error("Uno de los DEMs es inválido")
            return None
            
        import tempfile
        output_diff = os.path.join(tempfile.gettempdir(), "temp_dem_diff.tif")
        
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
        
        calc = QgsRasterCalculator(
            'dem1@1 - dem2@1', 
            output_diff, 
            'GTiff',
            dem1.extent(), 
            dem1.width(), 
            dem1.height(), 
            entries
        )
        
        result = calc.processCalculation()
        if result == 0:
            layer = QgsRasterLayer(output_diff, "Difference")
            if layer.isValid():
                return layer
        
        logger.error(f"Error en QgsRasterCalculator: {result}")
        return None

    def _clip_raster_by_mask(self, raster_layer, mask_path):
        """Recorta raster usando una capa vectorial de máscara (DXF)."""
        import tempfile
        
        output_path = os.path.join(tempfile.gettempdir(), "temp_clipped_diff.tif")
        
        if not os.path.exists(mask_path):
            logger.error(f"Máscara no existe: {mask_path}")
            return None
        
        # Cargar DXF - puede ser líneas o polígonos
        dxf_layer = QgsVectorLayer(mask_path, "DXF_Mask", "ogr")
        
        if not dxf_layer.isValid():
            logger.error(f"No se pudo cargar DXF: {mask_path}")
            return raster_layer
        
        # Verificar tipo de geometría
        from qgis.core import QgsWkbTypes
        geom_type = dxf_layer.geometryType()
        logger.info(f"DXF tipo geometría: {geom_type}")
        
        mask_layer = dxf_layer
        
        # Si es línea, convertir a polígono
        if geom_type == QgsWkbTypes.LineGeometry:
            logger.info("DXF es línea, convirtiendo a polígono...")
            try:
                # Usar qgis:linestopolygons para convertir
                polygon_output = os.path.join(tempfile.gettempdir(), "temp_polygon_mask.gpkg")
                result = processing.run("qgis:linestopolygons", {
                    'INPUT': dxf_layer,
                    'OUTPUT': polygon_output
                })
                if result and 'OUTPUT' in result:
                    polygon_layer = QgsVectorLayer(result['OUTPUT'], "Polygon_Mask", "ogr")
                    if polygon_layer.isValid() and polygon_layer.featureCount() > 0:
                        mask_layer = polygon_layer
                        logger.info(f"Conversión exitosa: {polygon_layer.featureCount()} polígonos")
                    else:
                        logger.warning("Conversión falló, usando DXF original")
            except Exception as e:
                logger.error(f"Error convirtiendo líneas a polígonos: {e}")
        
        # Ejecutar clip
        params = {
            'INPUT': raster_layer,
            'MASK': mask_layer,
            'SOURCE_CRS': raster_layer.crs(),
            'TARGET_CRS': raster_layer.crs(),
            'NODATA': -9999,
            'ALPHA_BAND': False,
            'CROP_TO_CUTLINE': True,
            'KEEP_RESOLUTION': True,
            'SET_RESOLUTION': False,
            'OUTPUT': output_path
        }
        
        try:
            logger.info("Ejecutando gdal:cliprasterbymasklayer...")
            result = processing.run("gdal:cliprasterbymasklayer", params)
            
            if result and 'OUTPUT' in result and os.path.exists(result['OUTPUT']):
                layer = QgsRasterLayer(result['OUTPUT'], "Clipped Difference")
                if layer.isValid():
                    logger.info("Recorte exitoso")
                    return layer
                    
        except Exception as e:
            logger.error(f"Error recorte GDAL: {e}")
            import traceback
            traceback.print_exc()
            return raster_layer
            
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
