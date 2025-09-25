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
            # Limpiar rubber bands
            if hasattr(self, 'line_rubber') and self.line_rubber:
                self.line_rubber.reset()
                
            if hasattr(self, 'center_cross_rubber') and self.center_cross_rubber:
                self.center_cross_rubber.reset()
                
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
            
            # Crear un RubberBand para la cruz central (usando líneas cruzadas)
            self.center_cross_rubber = QgsRubberBand(self.map_canvas, QgsWkbTypes.LineGeometry)
            
            # Crear una cruz con dos líneas perpendiculares
            cross_size = 10  # tamaño de la cruz en metros
            
            # Línea vertical de la cruz
            vertical_line = [
                QgsPointXY(self.x_coord, self.y_coord - cross_size/2),
                QgsPointXY(self.x_coord, self.y_coord + cross_size/2)
            ]
            
            # Línea horizontal de la cruz
            horizontal_line = [
                QgsPointXY(self.x_coord - cross_size/2, self.y_coord),
                QgsPointXY(self.x_coord + cross_size/2, self.y_coord)
            ]
            
            # Añadir las líneas al rubber band
            self.center_cross_rubber.addGeometry(
                QgsGeometry.fromPolylineXY(vertical_line), 
                None
            )
            self.center_cross_rubber.addGeometry(
                QgsGeometry.fromPolylineXY(horizontal_line), 
                None
            )
            
            # Establecer estilo para la cruz central (roja, gruesa)
            self.center_cross_rubber.setColor(QColor(255, 0, 0))
            self.center_cross_rubber.setWidth(3)
            self.center_cross_rubber.setLineStyle(Qt.SolidLine)
            
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