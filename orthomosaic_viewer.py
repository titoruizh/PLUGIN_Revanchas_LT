# -*- coding: utf-8 -*-
"""
/***************************************************************************
 OrthomosaicViewer
                                 A QGIS plugin
 Visualizador de Ortomosaico para Revanchas LT Plugin
                             -------------------
        begin                : 2025-09-25
        git sha              : $Format:%H$
        copyright            : (C) 2025 by Las Tortolas Project
        email                : support@lastortolas.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os
import math
from qgis.PyQt.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                                QLabel, QToolBar, QAction, QStatusBar)
from qgis.PyQt.QtCore import Qt, QSize
from qgis.PyQt.QtGui import QIcon, QColor, QFont
from qgis.core import (QgsRasterLayer, QgsProject, QgsRectangle, 
                      QgsCoordinateReferenceSystem, QgsPointXY, QgsGeometry,
                      QgsVectorLayer, QgsFeature, QgsMarkerSymbol, QgsLineSymbol,
                      QgsSingleSymbolRenderer, QgsCategorizedSymbolRenderer,
                      QgsRendererCategory, QgsSymbol, QgsMapLayer, QgsWkbTypes)
from qgis.gui import QgsMapCanvas, QgsMapToolPan, QgsMapToolZoom, QgsRubberBand


class OrthomosaicViewer(QDialog):
    """Dialog to show orthomosaic at specific coordinates with synchronization support"""
    
    def __init__(self, ecw_path, x_coord, y_coord, profile_pk, parent=None, bearing=None):
        """Initialize with ECW path and coordinates"""
        super(OrthomosaicViewer, self).__init__(parent)
        
        self.ecw_path = ecw_path
        self.x_coord = x_coord
        self.y_coord = y_coord
        self.profile_pk = profile_pk
        self.bearing = bearing  # Ángulo de dirección de la alineación
        self.profile_width = 80.0  # Ancho total del perfil (-40m a +40m)
        self.zoom_size = 100  # default zoom extents in meters
        
        # 🆕 Establecer ventana como no modal para permitir interacción con el visualizador de perfiles
        self.setModal(False)
        
        self.setWindowTitle(f"Visualizador de Ortomosaico - Perfil {profile_pk}")
        self.setMinimumSize(800, 600)
        self.resize(1000, 700)
        
        # Create layout
        self.setup_ui()
        
        # Load and display the ECW
        self.load_orthomosaic()
        
    def closeEvent(self, event):
        """Limpiar recursos cuando se cierra la ventana"""
        try:
            # Limpiar rubber bands principales
            if hasattr(self, 'line_rubber') and self.line_rubber:
                self.line_rubber.reset()
                
            if hasattr(self, 'center_cross_rubber') and self.center_cross_rubber:
                self.center_cross_rubber.reset()
                
            # 🆕 Limpiar rubber bands de mediciones
            if hasattr(self, 'lama_rubber') and self.lama_rubber:
                self.lama_rubber.reset()
                
            if hasattr(self, 'crown_rubber') and self.crown_rubber:
                self.crown_rubber.reset()
                
            if hasattr(self, 'width_rubber') and self.width_rubber:
                self.width_rubber.reset()
                
            if hasattr(self, 'centerline_rubber') and self.centerline_rubber:
                self.centerline_rubber.reset()
                
            print("DEBUG - Recursos liberados correctamente")
        except Exception as e:
            print(f"ERROR al limpiar recursos: {str(e)}")
            
        # Continuar con el cierre normal
        super().closeEvent(event)
        
    def setup_ui(self):
        """Setup the UI components"""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create map canvas
        self.map_canvas = QgsMapCanvas()
        self.map_canvas.setCanvasColor(QColor(255, 255, 255))
        self.map_canvas.enableAntiAliasing(True)
        
        # Crear rubber bands para visualización temporal (más efectivo)
        self.line_rubber = None
        self.point_rubber = None
        
        # 🆕 RubberBands para mediciones sincronizadas
        self.lama_rubber = None      # Punto LAMA (amarillo)
        self.crown_rubber = None     # Punto coronamiento (verde)
        self.width_rubber = None     # Línea de ancho medido
        self.centerline_rubber = None # 🆕 Línea del eje de alineación
        
        # Create toolbar
        toolbar = QToolBar()
        toolbar.setIconSize(QSize(24, 24))
        
        # Add pan tool
        self.pan_tool = QgsMapToolPan(self.map_canvas)
        pan_action = QAction("Pan", self)
        pan_action.setCheckable(True)
        pan_action.triggered.connect(self.activate_pan)
        toolbar.addAction(pan_action)
        
        # Add zoom in tool
        self.zoom_in_tool = QgsMapToolZoom(self.map_canvas, False)  # False = zoom in
        zoom_in_action = QAction("Zoom In", self)
        zoom_in_action.setCheckable(True)
        zoom_in_action.triggered.connect(self.activate_zoom_in)
        toolbar.addAction(zoom_in_action)
        
        # Add zoom out tool
        self.zoom_out_tool = QgsMapToolZoom(self.map_canvas, True)  # True = zoom out
        zoom_out_action = QAction("Zoom Out", self)
        zoom_out_action.setCheckable(True)
        zoom_out_action.triggered.connect(self.activate_zoom_out)
        toolbar.addAction(zoom_out_action)
        
        # Add zoom to profile extent button
        zoom_to_profile_action = QAction("Zoom a Perfil", self)
        zoom_to_profile_action.triggered.connect(self.zoom_to_profile)
        toolbar.addAction(zoom_to_profile_action)
        
        # Add separator
        toolbar.addSeparator()
        
        # Add zoom size controls
        zoom_label = QLabel("Tamaño de Zoom:")
        toolbar.addWidget(zoom_label)
        
        for zoom_size in [50, 100, 200, 500]:
            zoom_btn = QPushButton(f"{zoom_size}m")
            zoom_btn.setMaximumWidth(60)
            zoom_btn.clicked.connect(lambda checked, s=zoom_size: self.set_zoom_size(s))
            toolbar.addWidget(zoom_btn)
            
        # Add status bar
        self.status_bar = QStatusBar()
        self.status_bar.showMessage(f"Coordenadas: X={self.x_coord:.2f}, Y={self.y_coord:.2f} | Perfil: {self.profile_pk}")
        
        # Info label - 🆕 ahora guardamos la referencia como atributo para poder actualizarlo
        self.info_label = QLabel(f"Visualizando ortomosaico en {self.profile_pk} - Coordenadas: X={self.x_coord:.2f}, Y={self.y_coord:.2f}")
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setFont(QFont("Arial", 10, QFont.Bold))
        self.info_label.setStyleSheet("background-color: #f0f0f0; padding: 5px;")
        
        # Add components to layout
        main_layout.addWidget(self.info_label)
        main_layout.addWidget(toolbar)
        main_layout.addWidget(self.map_canvas)
        main_layout.addWidget(self.status_bar)
        
        # Set layout
        self.setLayout(main_layout)
        
        # Activate pan tool by default
        self.activate_pan()
        
    def load_orthomosaic(self):
        """Load the ECW file and display it"""
        try:
            print("DEBUG - Cargando ortomosaico...")
            
            # Create a temporary layer ID
            import uuid
            layer_id = f"ecw_viewer_{uuid.uuid4().hex[:8]}"
            
            # Create raster layer
            self.ortho_layer = QgsRasterLayer(self.ecw_path, layer_id)
            
            if not self.ortho_layer.isValid():
                print(f"ERROR - El ortomosaico no es válido: {self.ecw_path}")
                self.status_bar.showMessage("Error: No se pudo cargar el archivo ortomosaico")
                return
            else:
                print(f"DEBUG - Ortomosaico cargado correctamente: {layer_id}")
                print(f"  - Extensión: {self.ortho_layer.extent().toString()}")
                print(f"  - CRS: {self.ortho_layer.crs().authid()}")
                
            # Set up layer list - solo la capa raster
            self.layers = [self.ortho_layer]
            
            # Establecer capa raster en el canvas
            self.map_canvas.setLayers(self.layers)
            print(f"DEBUG - Capa raster asignada al canvas")
            
            # Realizar zoom a la ubicación del perfil
            self.zoom_to_profile()
            
            # IMPORTANTE: Añadir la visualización del perfil DESPUÉS de configurar el canvas
            # para que se dibuje encima del ortomosaico
            self.add_profile_visualization()
            
        except Exception as e:
            import traceback
            print(f"ERROR - Excepción al cargar ortomosaico: {str(e)}")
            print(traceback.format_exc())
            self.status_bar.showMessage(f"Error: {str(e)}")
    
    def add_profile_visualization(self):
        """Add profile visualization using QgsRubberBand for direct canvas drawing"""
        try:
            print("DEBUG - Añadiendo visualización de perfil con RubberBand...")
            
            # Obtener coordenadas para línea perpendicular (-40m a +40m)
            perp_coords = self._calculate_perpendicular_line()
            
            # Crear los puntos para la línea del perfil
            line_points = [
                QgsPointXY(perp_coords['left_x'], perp_coords['left_y']),
                QgsPointXY(perp_coords['right_x'], perp_coords['right_y'])
            ]
            
            print(f"DEBUG - Puntos de la línea:")
            print(f"  - Izquierdo: X={perp_coords['left_x']:.2f}, Y={perp_coords['left_y']:.2f}")
            print(f"  - Derecho: X={perp_coords['right_x']:.2f}, Y={perp_coords['right_y']:.2f}")
            
            # Crear RubberBand para la línea del perfil (tipo línea)
            from qgis.core import QgsWkbTypes
            self.line_rubber = QgsRubberBand(self.map_canvas, QgsWkbTypes.LineGeometry)
            self.line_rubber.setToGeometry(
                QgsGeometry.fromPolylineXY(line_points), 
                None
            )
            
            # Establecer estilo para la línea (roja, gruesa)
            self.line_rubber.setColor(QColor(255, 0, 0))
            self.line_rubber.setWidth(5)
            self.line_rubber.setLineStyle(Qt.SolidLine)
            
            # Crear un RubberBand para la marca central (línea perpendicular al perfil)
            self.center_cross_rubber = QgsRubberBand(self.map_canvas, QgsWkbTypes.LineGeometry)
            
            # 🆕 Crear una línea perpendicular al perfil en lugar de cruz
            line_size = 8  # tamaño de la línea en metros
            
            # Calcular bearing perpendicular para la línea central
            if self.bearing is None:
                bearing_rad = 0
            else:
                bearing_rad = math.radians(self.bearing)
            
            # Dirección perpendicular (90° desde bearing del perfil)
            perp_bearing_rad = bearing_rad + math.pi / 2
            
            # Crear línea perpendicular centrada en el punto del perfil
            perpendicular_line = [
                QgsPointXY(
                    self.x_coord + (line_size/2) * math.cos(perp_bearing_rad),
                    self.y_coord + (line_size/2) * math.sin(perp_bearing_rad)
                ),
                QgsPointXY(
                    self.x_coord - (line_size/2) * math.cos(perp_bearing_rad),
                    self.y_coord - (line_size/2) * math.sin(perp_bearing_rad)
                )
            ]
            
            # Añadir la línea al rubber band
            self.center_cross_rubber.addGeometry(
                QgsGeometry.fromPolylineXY(perpendicular_line), 
                None
            )
            
            # Establecer estilo para la cruz central (roja, gruesa)
            self.center_cross_rubber.setColor(QColor(255, 0, 0))
            self.center_cross_rubber.setWidth(3)
            self.center_cross_rubber.setLineStyle(Qt.SolidLine)
            
            # 🆕 Crear línea del eje de alineación (centerline)
            self._create_centerline_visualization()
            
            # 🆕 Añadir información de bearing para diagnóstico
            bearing_info = ""
            if self.bearing is not None:
                bearing_info = f", Bearing={self.bearing:.1f}°"
            
            # Mostrar información en la barra de estado
            self.status_bar.showMessage(
                f"Perfil {self.profile_pk} visualizado: X={self.x_coord:.2f}, Y={self.y_coord:.2f}" +
                f"{bearing_info}, Ancho={self.profile_width}m (-40m a +40m)"
            )
            
            print("DEBUG - Visualización de perfil completada con RubberBand")
            
        except Exception as e:
            import traceback
            print(f"ERROR - Excepción al crear visualización de perfil: {str(e)}")
            print(traceback.format_exc())
            self.status_bar.showMessage(f"Error al crear visualización de perfil: {str(e)}")
            
    def _calculate_perpendicular_line(self):
        """Calcula coordenadas de la línea perpendicular al perfil con soporte mejorado para curvas"""
        # Información de debug
        print(f"DEBUG - Cálculo de línea perpendicular:")
        print(f"  - Coordenadas centro: X={self.x_coord:.2f}, Y={self.y_coord:.2f}")
        print(f"  - Bearing recibido: {self.bearing}")
        print(f"  - PK: {self.profile_pk}")
        
        # Si no tenemos bearing, usamos un valor predeterminado (norte)
        if self.bearing is None:
            self.bearing = 0
            print("  ⚠️ ADVERTENCIA: Usando bearing por defecto (0°)")
        
        # 🔧 MEJORADO: Convertir bearing recibido a radianes
        # Nota: El bearing_tangent ya debería estar en el sistema de coordenadas adecuado
        bearing_deg = self.bearing
        print(f"  - Bearing final en grados: {bearing_deg:.2f}°")
        bearing_rad = math.radians(bearing_deg)
        
        # 🔧 MEJORADO: Calcular dirección perpendicular (90° desde bearing)
        # Para perfiles perpendiculares, sumamos pi/2 (90°) al bearing
        perp_bearing_rad = bearing_rad + math.pi / 2
        print(f"  - Perpendicular en radianes: {perp_bearing_rad:.6f}")
        print(f"  - Perpendicular en grados: {math.degrees(perp_bearing_rad):.2f}°")
        
        # Mitad del ancho del perfil (40 metros a cada lado)
        half_width = self.profile_width / 2
        
        # Calcular punto izquierdo (-40m)
        left_x = self.x_coord + half_width * math.cos(perp_bearing_rad)
        left_y = self.y_coord + half_width * math.sin(perp_bearing_rad)
        
        # Calcular punto derecho (+40m)
        right_x = self.x_coord - half_width * math.cos(perp_bearing_rad)
        right_y = self.y_coord - half_width * math.sin(perp_bearing_rad)
        
        print(f"  - Punto izquierdo: X={left_x:.2f}, Y={left_y:.2f}")
        print(f"  - Punto derecho: X={right_x:.2f}, Y={right_y:.2f}")
        
        # 🆕 Validar que los puntos están realmente a la distancia correcta del centro
        dist_left = math.hypot(left_x - self.x_coord, left_y - self.y_coord)
        dist_right = math.hypot(right_x - self.x_coord, right_y - self.y_coord)
        print(f"  - Distancia punto izquierdo: {dist_left:.2f}m (debe ser ~{half_width:.1f}m)")
        print(f"  - Distancia punto derecho: {dist_right:.2f}m (debe ser ~{half_width:.1f}m)")
        
        if abs(dist_left - half_width) > 0.1 or abs(dist_right - half_width) > 0.1:
            print("  ⚠️ ADVERTENCIA: Las distancias calculadas no coinciden con el ancho esperado")
        
        return {
            'left_x': left_x, 
            'left_y': left_y,
            'right_x': right_x, 
            'right_y': right_y
        }
    
    def _convert_profile_to_world_coords(self, profile_x, profile_y):
        """🆕 Convierte coordenadas del perfil (relativas) a coordenadas del mundo real"""
        try:
            # profile_x es la distancia desde el eje de alineación (-40m a +40m)
            # profile_y es la elevación del terreno
            
            # Calcular bearing perpendicular para obtener la dirección correcta
            if self.bearing is None:
                bearing_rad = 0
            else:
                bearing_rad = math.radians(self.bearing)
            
            # Dirección perpendicular (90° desde bearing)
            perp_bearing_rad = bearing_rad + math.pi / 2
            
            # Calcular coordenadas del mundo real
            world_x = self.x_coord + profile_x * math.cos(perp_bearing_rad)
            world_y = self.y_coord + profile_x * math.sin(perp_bearing_rad)
            
            return world_x, world_y
            
        except Exception as e:
            print(f"ERROR al convertir coordenadas: {str(e)}")
            return self.x_coord, self.y_coord
    
    def _create_centerline_visualization(self):
        """🆕 Crear visualización del eje de alineación (centerline)"""
        try:
            print("DEBUG - Creando línea del eje de alineación...")
            
            # Longitud de la línea del eje (en metros)
            centerline_length = 20  # 10m hacia cada lado del punto

            # Calcular bearing del eje de alineación
            if self.bearing is None:
                bearing_rad = 0
            else:
                bearing_rad = math.radians(self.bearing)
            
            # Crear línea a lo largo del bearing del eje (longitudinal)
            centerline_points = [
                QgsPointXY(
                    self.x_coord - (centerline_length/2) * math.cos(bearing_rad),
                    self.y_coord - (centerline_length/2) * math.sin(bearing_rad)
                ),
                QgsPointXY(
                    self.x_coord + (centerline_length/2) * math.cos(bearing_rad),
                    self.y_coord + (centerline_length/2) * math.sin(bearing_rad)
                )
            ]
            
            print(f"DEBUG - Puntos del eje de alineación:")
            print(f"  - Inicio: X={centerline_points[0].x():.2f}, Y={centerline_points[0].y():.2f}")
            print(f"  - Fin: X={centerline_points[1].x():.2f}, Y={centerline_points[1].y():.2f}")
            print(f"  - Bearing: {self.bearing:.2f}°" if self.bearing else "  - Bearing: 0° (por defecto)")
            
            # Crear RubberBand para la línea del eje
            from qgis.core import QgsWkbTypes
            self.centerline_rubber = QgsRubberBand(self.map_canvas, QgsWkbTypes.LineGeometry)
            self.centerline_rubber.setToGeometry(
                QgsGeometry.fromPolylineXY(centerline_points), 
                None
            )
            
            # Establecer estilo para la línea del eje (amarillo discontinuo para diferenciarlo)
            self.centerline_rubber.setColor(QColor(255, 0, 0))  # Rojo
            self.centerline_rubber.setWidth(2)
            self.centerline_rubber.setLineStyle(Qt.DashLine)  # Línea discontinua
            
            print("DEBUG - Línea del eje de alineación creada exitosamente")
            
        except Exception as e:
            import traceback
            print(f"ERROR al crear línea del eje: {str(e)}")
            print(traceback.format_exc())
    
    def set_zoom_size(self, size):
        """Set the zoom size and update the view"""
        self.zoom_size = size
        self.zoom_to_profile()
        
    def zoom_to_profile(self):
        """Zoom to the profile location"""
        print("DEBUG - Haciendo zoom al perfil...")
        
        # Verificar que la capa raster esté presente
        if len(self.layers) > 0:
            print(f"DEBUG - Capa raster disponible: {self.layers[0].name()}")
        else:
            print("ERROR - No hay capa raster disponible para mostrar")
        
        # Crear rectángulo de zoom con un poco más de margen para visualizar bien el perfil
        # Asegurar que el zoom muestre el perfil completo de -40m a +40m
        margin = max(self.zoom_size, self.profile_width + 20) / 2
        
        zoom_rect = QgsRectangle(
            self.x_coord - margin,
            self.y_coord - margin,
            self.x_coord + margin,
            self.y_coord + margin
        )
        print(f"DEBUG - Rectángulo de zoom: {zoom_rect.toString()}")
        
        # Aplicar zoom
        self.map_canvas.setExtent(zoom_rect)
        self.map_canvas.refresh()
        
        # Actualizar mensaje de la barra de estado
        self.status_bar.showMessage(
            f"Perfil {self.profile_pk}: X={self.x_coord:.2f}, Y={self.y_coord:.2f} | " +
            f"Ancho={self.profile_width}m (-40m a +40m) | Zoom: {self.zoom_size}m"
        )
        
        # Forzar una actualización final del lienzo para asegurar la visualización correcta
        self.map_canvas.update()
    
    def activate_pan(self):
        """Activate pan tool"""
        self.map_canvas.setMapTool(self.pan_tool)
        self.status_bar.showMessage(f"Herramienta: Pan | Coordenadas: X={self.x_coord:.2f}, Y={self.y_coord:.2f}")
    
    def activate_zoom_in(self):
        """Activate zoom in tool"""
        self.map_canvas.setMapTool(self.zoom_in_tool)
        self.status_bar.showMessage(f"Herramienta: Zoom In | Coordenadas: X={self.x_coord:.2f}, Y={self.y_coord:.2f}")
    
    def activate_zoom_out(self):
        """Activate zoom out tool"""
        self.map_canvas.setMapTool(self.zoom_out_tool)
        self.status_bar.showMessage(f"Herramienta: Zoom Out | Coordenadas: X={self.x_coord:.2f}, Y={self.y_coord:.2f}")
        
    def update_to_profile(self, profile):
        """🆕 Actualiza la visualización al perfil especificado (permite sincronización)"""
        try:
            # Obtener datos necesarios del perfil
            if 'centerline_x' not in profile or 'centerline_y' not in profile:
                print(f"❌ Error: No se encontraron coordenadas para el perfil {profile.get('pk', 'desconocido')}")
                return False
                
            # Actualizar atributos
            new_x_coord = profile['centerline_x']
            new_y_coord = profile['centerline_y']
            new_pk = profile['pk']
            
            # Obtener bearing
            new_bearing = None
            
            # Intentar obtener bearing_tangent para curvas si está disponible
            if 'station' in profile:
                station_data = profile['station']
                
                if ('alignment_type' in station_data and 
                    station_data['alignment_type'] == 'curved' and
                    'bearing_tangent' in station_data):
                    new_bearing = station_data['bearing_tangent']
                elif 'bearing' in station_data:
                    new_bearing = station_data['bearing']
            
            # Si aún no tenemos bearing, intentar obtenerlo del profile
            if new_bearing is None and 'bearing' in profile:
                new_bearing = profile['bearing']
                
            # Actualizar atributos internos
            self.x_coord = new_x_coord
            self.y_coord = new_y_coord
            self.profile_pk = new_pk
            if new_bearing is not None:
                self.bearing = new_bearing
            
            # Actualizar título de la ventana
            self.setWindowTitle(f"Visualizador de Ortomosaico - Perfil {new_pk} [Sincronizado]")
            
            # Limpiar visualización actual
            if hasattr(self, 'line_rubber') and self.line_rubber:
                self.line_rubber.reset()
                
            if hasattr(self, 'center_cross_rubber') and self.center_cross_rubber:
                self.center_cross_rubber.reset()
                
            if hasattr(self, 'centerline_rubber') and self.centerline_rubber:
                self.centerline_rubber.reset()
                
            # 🆕 Limpiar mediciones anteriores al cambiar de perfil
            self._clear_measurement_rubber_bands()
                
            # Actualizar zoom y visualización
            self.zoom_to_profile()
            self.add_profile_visualization()
            
            # Actualizar información
            info_text = f"Visualizando ortomosaico en {new_pk} - Coordenadas: X={new_x_coord:.2f}, Y={new_y_coord:.2f}"
            if hasattr(self, 'info_label') and self.info_label:
                self.info_label.setText(info_text)
            
            # Actualizar barra de estado
            bearing_info = ""
            if self.bearing is not None:
                bearing_info = f", Bearing={self.bearing:.1f}°"
                
            status_text = f"Perfil {new_pk}: X={new_x_coord:.2f}, Y={new_y_coord:.2f}{bearing_info} | Ancho={self.profile_width}m (-40m a +40m)"
            if hasattr(self, 'status_bar') and self.status_bar:
                self.status_bar.showMessage(status_text)
            
            print(f"✅ Visualizador de ortomosaico actualizado al perfil {new_pk}")
            return True
            
        except Exception as e:
            import traceback
            print(f"❌ Error al actualizar visualizador de ortomosaico: {str(e)}")
            print(traceback.format_exc())
            return False
    
    def update_measurements_display(self, measurements_data):
        """🆕 Actualiza la visualización de mediciones en el ortomosaico"""
        try:
            print(f"DEBUG - Actualizando mediciones en ortomosaico para PK {self.profile_pk}")
            print(f"DEBUG - Datos recibidos: {measurements_data}")
            
            # Limpiar mediciones anteriores
            self._clear_measurement_rubber_bands()
            
            if not measurements_data:
                print("DEBUG - No hay mediciones para mostrar")
                return
            
            # 1. Mostrar punto LAMA (amarillo) - manejar ambos nombres
            if 'lama_selected' in measurements_data:
                lama_data = measurements_data['lama_selected']
                self._show_lama_point(lama_data['x'], lama_data['y'])
                print(f"DEBUG - Punto LAMA (lama_selected) mostrado: x={lama_data['x']:.2f}, y={lama_data['y']:.2f}")
            elif 'lama' in measurements_data:
                lama_data = measurements_data['lama']
                self._show_lama_point(lama_data['x'], lama_data['y'])
                print(f"DEBUG - Punto LAMA (lama) mostrado: x={lama_data['x']:.2f}, y={lama_data['y']:.2f}")
            
            # 2. Mostrar punto coronamiento (verde)
            if 'crown' in measurements_data:
                crown_data = measurements_data['crown']
                self._show_crown_point(crown_data['x'], crown_data['y'])
                print(f"DEBUG - Punto coronamiento mostrado: x={crown_data['x']:.2f}, y={crown_data['y']:.2f}")
            
            # 3. Mostrar línea de ancho medido
            if 'width' in measurements_data:
                width_data = measurements_data['width']
                if 'p1' in width_data and 'p2' in width_data:
                    self._show_width_line(width_data['p1'], width_data['p2'])
                    print(f"DEBUG - Línea de ancho mostrada: {width_data['distance']:.2f}m")
            
            # Refrescar el canvas para mostrar los cambios
            self.map_canvas.refresh()
            
        except Exception as e:
            import traceback
            print(f"ERROR al actualizar mediciones: {str(e)}")
            print(traceback.format_exc())
    
    def _clear_measurement_rubber_bands(self):
        """Limpiar RubberBands de mediciones anteriores"""
        try:
            if self.lama_rubber:
                self.lama_rubber.reset()
                self.lama_rubber = None
                
            if self.crown_rubber:
                self.crown_rubber.reset()
                self.crown_rubber = None
                
            if self.width_rubber:
                self.width_rubber.reset()
                self.width_rubber = None
                
            # 🆕 No limpiar centerline aquí ya que es parte de la visualización base
                
        except Exception as e:
            print(f"ERROR al limpiar mediciones: {str(e)}")
    
    def _show_lama_point(self, profile_x, profile_y):
        """Mostrar punto LAMA (amarillo) en el ortomosaico"""
        try:
            # Convertir coordenadas del perfil a coordenadas del mundo
            world_x, world_y = self._convert_profile_to_world_coords(profile_x, profile_y)
            
            # Crear RubberBand para punto LAMA
            from qgis.core import QgsWkbTypes
            self.lama_rubber = QgsRubberBand(self.map_canvas, QgsWkbTypes.PointGeometry)
            self.lama_rubber.addPoint(QgsPointXY(world_x, world_y))
            
            # Establecer estilo amarillo para LAMA
            self.lama_rubber.setColor(QColor(255, 255, 0))  # Amarillo
            self.lama_rubber.setWidth(8)
            self.lama_rubber.setIconSize(12)
            
        except Exception as e:
            print(f"ERROR al mostrar punto LAMA: {str(e)}")
    
    def _show_crown_point(self, profile_x, profile_y):
        """Mostrar punto coronamiento (verde) en el ortomosaico"""
        try:
            # Convertir coordenadas del perfil a coordenadas del mundo
            world_x, world_y = self._convert_profile_to_world_coords(profile_x, profile_y)
            
            # Crear RubberBand para punto coronamiento
            from qgis.core import QgsWkbTypes
            self.crown_rubber = QgsRubberBand(self.map_canvas, QgsWkbTypes.PointGeometry)
            self.crown_rubber.addPoint(QgsPointXY(world_x, world_y))
            
            # Establecer estilo verde para coronamiento
            self.crown_rubber.setColor(QColor(0, 255, 0))  # Verde
            self.crown_rubber.setWidth(8)
            self.crown_rubber.setIconSize(12)
            
        except Exception as e:
            print(f"ERROR al mostrar punto coronamiento: {str(e)}")
    
    def _show_width_line(self, point1, point2):
        """Mostrar línea de ancho medido en el ortomosaico"""
        try:
            # 🔧 CORREGIDO: Manejar múltiples formatos de puntos
            # Formato desde saved_measurements: (x, y) o [x, y]
            # Formato desde current_width_points convertido: {'x': x, 'y': y}
            
            if isinstance(point1, (tuple, list)):
                # Formato de tupla (x, y) o lista [x, y]
                x1, y1 = point1[0], point1[1]
                x2, y2 = point2[0], point2[1]
            else:
                # Formato de diccionario {'x': x, 'y': y}
                x1, y1 = point1['x'], point1['y']
                x2, y2 = point2['x'], point2['y']
            
            print(f"DEBUG - Puntos de ancho convertidos: P1=({x1:.2f}, {y1:.2f}), P2=({x2:.2f}, {y2:.2f})")
            
            # Convertir ambos puntos a coordenadas del mundo
            world_x1, world_y1 = self._convert_profile_to_world_coords(x1, y1)
            world_x2, world_y2 = self._convert_profile_to_world_coords(x2, y2)
            
            print(f"DEBUG - Puntos de ancho en mundo: P1=({world_x1:.2f}, {world_y1:.2f}), P2=({world_x2:.2f}, {world_y2:.2f})")
            
            # Crear línea entre los dos puntos
            line_points = [
                QgsPointXY(world_x1, world_y1),
                QgsPointXY(world_x2, world_y2)
            ]
            
            # Crear RubberBand para línea de ancho
            from qgis.core import QgsWkbTypes
            self.width_rubber = QgsRubberBand(self.map_canvas, QgsWkbTypes.LineGeometry)
            self.width_rubber.setToGeometry(
                QgsGeometry.fromPolylineXY(line_points), 
                None
            )
            
            # Establecer estilo para línea de ancho (azul)
            self.width_rubber.setColor(QColor(0, 150, 255))  # Azul
            self.width_rubber.setWidth(4)
            self.width_rubber.setLineStyle(Qt.SolidLine)
            
            print(f"✅ Línea de ancho mostrada en ortomosaico")
            
        except Exception as e:
            print(f"ERROR al mostrar línea de ancho: {str(e)}")
            import traceback
            traceback.print_exc()