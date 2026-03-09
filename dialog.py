# -*- coding: utf-8 -*-
"""
/***************************************************************************
 RevanchasLTDialog
                                 A QGIS plugin
 Plugin para análisis de perfiles topográficos de muros de contención
                             -------------------
        begin                : 2024-01-01
        git sha              : $Format:%H$
        copyright            : (C) 2024 by Las Tortolas Project
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
from qgis.PyQt import uic
from qgis.PyQt import QtWidgets
from qgis.PyQt.QtWidgets import QFileDialog, QMessageBox, QProgressDialog
from qgis.PyQt.QtCore import Qt, QTimer
from qgis.core import QgsApplication, QgsRasterLayer

from .core.dem_processor import DEMProcessor
from .core.alignment_data import AlignmentData
from .core.profile_generator import ProfileGenerator
from .core.wall_analyzer import WallAnalyzer
from .core.project_manager import ProjectManager  # 🆕 Nuevo

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'dialog.ui'))


class RevanchasLTDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(RevanchasLTDialog, self).__init__(parent)
        # Set up the user interface from Designer through FORM_CLASS.
        # After self.setupUi() you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html#autconnecting-slots
        self.setupUi(self)
        
        # Initialize components
        self.selected_wall = None
        self.dem_processor = DEMProcessor()
        self.alignment_data = AlignmentData()
        self.profile_generator = ProfileGenerator()
        self.wall_analyzer = WallAnalyzer()
        self.project_manager = ProjectManager()  # 🆕 Nuevo
        self.dem_file_path = None
        self.previous_dem_file_path = None # 🆕 Previous DEM path
        self.ecw_file_path = None  # New: Store ECW file path
        self.profiles_data = None  # Store generated profiles
        self._cached_measurements = {}  # 🆕 Cache for measurements when viewer is closed
        
        # Connect signals - UNIFIED: only one button now
        self.browse_dem_button.clicked.connect(self.browse_dem_file)
        self.browse_ecw_button.clicked.connect(self.browse_ecw_file)  # New: ECW browse button
        self.generate_profiles_button.clicked.connect(self.generate_and_visualize_profiles)
        
        # 🆕 Project Management buttons - Create and connect them dynamically
        self.setup_project_management_buttons()
        
        # 🆕 Previous DEM UI - Create dynamically
        self.setup_previous_dem_ui()

        # 🆕 Excel Export UI - Create dynamically
        self.setup_excel_ui()
        
        # Initially disable button that requires DEM
        self.generate_profiles_button.setEnabled(False)
        
    def set_selected_wall(self, wall_name):
        """Set the selected wall and update UI"""
        self.selected_wall = wall_name
        self.wall_label.setText(f"Muro seleccionado: {wall_name}")
        
        # Load alignment data for the selected wall
        alignment = self.alignment_data.get_alignment(wall_name)
        if alignment:
            info_text = f"Alineación: PK {alignment['start_pk']} a {alignment['end_pk']}\n"
            info_text += f"Estaciones cada {alignment['interval']}m\n"
            info_text += f"Total de estaciones: {len(alignment['stations'])}"
            self.alignment_info_label.setText(info_text)
            
        # 🆕 LIMPIEZA DE CACHE AL CAMBIAR MURO
        # Esto previene que mediciones de un muro anterior aparezcan en el nuevo
        if hasattr(self, '_cached_measurements'):
            self._cached_measurements = {}
            print(f"🧹 Cache de mediciones limpiado por cambio de muro a: {wall_name}")
        
    def browse_dem_file(self):
        """Browse for DEM file with alignment coverage validation"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar archivo DEM",
            "",
            "ASCII Grid files (*.asc);;All files (*)"
        )
        
        if file_path:
            try:
                # Load DEM info
                dem_info = self.dem_processor.get_dem_info(file_path)
                
                # ADVERTIR si no hay muro seleccionado
                if not self.selected_wall:
                    QMessageBox.warning(
                        self,
                        "Muro no seleccionado",
                        "No hay un muro seleccionado.\n\n"
                        "El DEM se cargará sin validación espacial.\n"
                        "Seleccione un muro antes de cargar el DEM para verificar la cobertura."
                    )
                else:
                    # VALIDAR COBERTURA DE LA ALINEACIÓN
                    from .core.dem_validator import DEMValidator
                    
                    alignment = self.alignment_data.get_alignment(self.selected_wall)
                    validation = DEMValidator.validate_dem_coverage(dem_info, alignment)
                    coverage_pct = DEMValidator.calculate_coverage_percentage(dem_info, alignment)
                    
                    if not validation['coverage_ok']:
                        # DEM no cubre totalmente - preguntar si continuar igual
                        uncovered = DEMValidator.get_uncovered_stations(dem_info, alignment)
                        missing = validation['missing_coverage']
                        
                        reply = QMessageBox.warning(
                            self,
                            "Advertencia - Cobertura DEM parcial",
                            f"El DEM no cubre completamente la alineación del {self.selected_wall}.\n\n"
                            f"Cobertura: {coverage_pct:.1f}% de las estaciones "
                            f"({validation['stations_count'] - len(uncovered)}/{validation['stations_count']})\n\n"
                            f"Area requerida (buffer 50m):\n"
                            f"  X: {validation['alignment_bounds']['xmin']:.1f} - {validation['alignment_bounds']['xmax']:.1f}\n"
                            f"  Y: {validation['alignment_bounds']['ymin']:.1f} - {validation['alignment_bounds']['ymax']:.1f}\n\n"
                            f"DEM disponible:\n"
                            f"  X: {validation['dem_bounds']['xmin']:.1f} - {validation['dem_bounds']['xmax']:.1f}\n"
                            f"  Y: {validation['dem_bounds']['ymin']:.1f} - {validation['dem_bounds']['ymax']:.1f}\n\n"
                            f"Deficit X: {missing['x_deficit']:.1f}m   Deficit Y: {missing['y_deficit']:.1f}m\n\n"
                            f"Los perfiles fuera del DEM quedarán sin datos de elevacion.\n"
                            f"¿Desea continuar de todas formas?",
                            QMessageBox.Yes | QMessageBox.No,
                            QMessageBox.No
                        )
                        
                        if reply == QMessageBox.No:
                            return  # usuario eligió no continuar
                        
                        # Continuar con advertencia en el label
                        coverage_status = f" ⚠ Cobertura parcial ({coverage_pct:.0f}%)"
                    else:
                        coverage_status = f" ✓ Cubre alineacion ({coverage_pct:.0f}%)"
                
                # Continuar con carga normal
                self.dem_file_path = file_path
                coverage_note = coverage_status if self.selected_wall else " (sin validar)"
                self.dem_path_label.setText(f"DEM: {os.path.basename(file_path)}{coverage_note}")
                
                # Habilitar botón de generar perfiles solo cuando tenemos todos los archivos necesarios
                self.check_required_files()
                
                # Show DEM info in label (sin popup)
                info_text = f"Dimensiones: {dem_info['cols']} x {dem_info['rows']}\n"
                info_text += f"Resolución: {dem_info['cellsize']:.2f}m\n"
                info_text += f"Extension: X({dem_info['xmin']:.1f}, {dem_info['xmax']:.1f})  Y({dem_info['ymin']:.1f}, {dem_info['ymax']:.1f})"
                self.dem_info_label.setText(info_text)
                
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Error",
                    f"No se pudo cargar el DEM: {str(e)}"
                )
                
    def browse_ecw_file(self):
        """Browse for ECW file with alignment coverage validation"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar archivo Ortomosaico",
            "",
            "ECW files (*.ecw);;Todos los formatos de imagen (*.ecw *.tif *.jpg *.png);;All files (*)"
        )
        
        if file_path:
            try:
                # Create a temporary QgsRasterLayer to validate the ECW file
                ecw_layer = QgsRasterLayer(file_path, "temp_ecw_validator")
                
                if not ecw_layer.isValid():
                    QMessageBox.critical(
                        self,
                        "Error - Ortomosaico Inválido",
                        f"El archivo seleccionado no es un ortomosaico válido o no está georreferenciado.\n\n"
                        f"Por favor seleccione un archivo ECW válido con georreferencia."
                    )
                    return
                
                # VALIDAR COBERTURA DE LA ALINEACIÓN
                coverage_note = ""
                if not self.selected_wall:
                    coverage_note = " (sin validar)"
                else:
                    from .core.dem_validator import DEMValidator
                    
                    alignment = self.alignment_data.get_alignment(self.selected_wall)
                    
                    # Obtener extensión del ECW
                    ecw_extent = ecw_layer.extent()
                    ecw_info = {
                        'xmin': ecw_extent.xMinimum(),
                        'xmax': ecw_extent.xMaximum(),
                        'ymin': ecw_extent.yMinimum(),
                        'ymax': ecw_extent.yMaximum()
                    }
                    
                    validation = DEMValidator.validate_dem_coverage(ecw_info, alignment)
                    coverage_pct = DEMValidator.calculate_coverage_percentage(ecw_info, alignment)
                    
                    if not validation['coverage_ok']:
                        uncovered = DEMValidator.get_uncovered_stations(ecw_info, alignment)
                        missing = validation['missing_coverage']
                        
                        reply = QMessageBox.warning(
                            self,
                            "Advertencia - Cobertura ortomosaico parcial",
                            f"El ortomosaico no cubre completamente la alineación del {self.selected_wall}.\n\n"
                            f"Cobertura: {coverage_pct:.1f}% de las estaciones "
                            f"({validation['stations_count'] - len(uncovered)}/{validation['stations_count']})\n\n"
                            f"Area requerida (buffer 50m):\n"
                            f"  X: {validation['alignment_bounds']['xmin']:.1f} - {validation['alignment_bounds']['xmax']:.1f}\n"
                            f"  Y: {validation['alignment_bounds']['ymin']:.1f} - {validation['alignment_bounds']['ymax']:.1f}\n\n"
                            f"Ortomosaico disponible:\n"
                            f"  X: {validation['dem_bounds']['xmin']:.1f} - {validation['dem_bounds']['xmax']:.1f}\n"
                            f"  Y: {validation['dem_bounds']['ymin']:.1f} - {validation['dem_bounds']['ymax']:.1f}\n\n"
                            f"Deficit X: {missing['x_deficit']:.1f}m   Deficit Y: {missing['y_deficit']:.1f}m\n\n"
                            f"Las zonas fuera del ortomosaico no tendran imagen de fondo.\n"
                            f"¿Desea continuar de todas formas?",
                            QMessageBox.Yes | QMessageBox.No,
                            QMessageBox.No
                        )
                        
                        if reply == QMessageBox.No:
                            return
                        
                        coverage_note = f" ⚠ Cobertura parcial ({coverage_pct:.0f}%)"
                    else:
                        coverage_note = f" ✓ Cubre alineacion ({coverage_pct:.0f}%)"
                
                # Continuar con carga normal
                self.ecw_file_path = file_path
                self.ecw_path_label.setText(f"ECW: {os.path.basename(file_path)}{coverage_note}")
                
                # Habilitar botón de generar perfiles solo cuando tenemos todos los archivos necesarios
                self.check_required_files()
                
                # Show ECW info (sin popup)
                extent = ecw_layer.extent()
                width = ecw_layer.width()
                height = ecw_layer.height()
                
                pixel_size_x = (extent.xMaximum() - extent.xMinimum()) / width
                pixel_size_y = (extent.yMaximum() - extent.yMinimum()) / height
                
                info_text = f"Dimensiones: {width} x {height} pixeles\n"
                info_text += f"Resolucion: {pixel_size_x:.2f}m/px\n"
                info_text += f"Extension: X({extent.xMinimum():.1f}, {extent.xMaximum():.1f})  Y({extent.yMinimum():.1f}, {extent.yMaximum():.1f})"
                self.ecw_info_label.setText(info_text)
                
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Error",
                    f"No se pudo cargar el ortomosaico: {str(e)}"
                )
                
    def check_required_files(self):
        """Check if all required files are selected and enable/disable buttons accordingly"""
        # Solo necesitamos el DEM para generar perfiles (ECW es opcional)
        if self.dem_file_path:
            self.generate_profiles_button.setEnabled(True)
        else:
            self.generate_profiles_button.setEnabled(False)

    def setup_previous_dem_ui(self):
        """🆕 Create Previous DEM selection UI dynamically"""
        # Find the layout where DEM button is located (moved from ECW)
        if hasattr(self, 'browse_dem_button'):
            parent_widget = self.browse_dem_button.parent()
            parent_layout = parent_widget.layout()
            
            if parent_layout:
                # Create widgets
                self.browse_prev_dem_button = QtWidgets.QPushButton("📂 Seleccionar DEM Anterior (Ref)")
                self.browse_prev_dem_button.setToolTip("Cargar un DEM antiguo para comparación visual (Requerido para Reporte PDF)")
                self.browse_prev_dem_button.clicked.connect(self.browse_previous_dem_file)
                
                self.prev_dem_path_label = QtWidgets.QLabel("DEM Ant: No seleccionado (Opcional para visualización, Requerido para Reporte)")
                self.prev_dem_path_label.setStyleSheet("color: gray; font-style: italic;")
                
                # Add to layout
                # Try to add to the same layout as DEM button
                if isinstance(parent_layout, QtWidgets.QVBoxLayout) or isinstance(parent_layout, QtWidgets.QGridLayout):
                     parent_layout.addWidget(self.browse_prev_dem_button)
                     parent_layout.addWidget(self.prev_dem_path_label)

    def browse_previous_dem_file(self):
        """🆕 Browse for Previous DEM file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar DEM Anterior (Referencia)",
            "",
            "ASCII Grid files (*.asc);;All files (*)"
        )
        
        if file_path:
            self.previous_dem_file_path = file_path
            self.prev_dem_path_label.setText(f"DEM Ant: {os.path.basename(file_path)}")
            self.prev_dem_path_label.setStyleSheet("color: green;")

    def setup_excel_ui(self):
        """🆕 Create Excel Export UI dynamically"""
        # Access main layout
        if self.layout():
            layout = self.layout()
            
            # Create GroupBox
            self.excel_group = QtWidgets.QGroupBox("📊 Exportación a Excel (Opcional)")
            excel_layout = QtWidgets.QVBoxLayout()
            self.excel_group.setLayout(excel_layout)
            
            # Horizontal layout for file selection
            h_layout = QtWidgets.QHBoxLayout()
            
            self.excel_path_label = QtWidgets.QLabel("Excel: [No seleccionado - Exportación CSV estándar]")
            self.browse_excel_button = QtWidgets.QPushButton("📂 Seleccionar Plantilla Excel")
            self.browse_excel_button.setToolTip("Seleccione el archivo Excel para actualizar con las nuevas mediciones")
            self.browse_excel_button.clicked.connect(self.browse_excel_file)
            
            h_layout.addWidget(self.excel_path_label)
            h_layout.addStretch()
            h_layout.addWidget(self.browse_excel_button)
            
            excel_layout.addLayout(h_layout)
            
            # Add info label
            info_label = QtWidgets.QLabel("Si selecciona un Excel, las mediciones se insertarán en las columnas correspondientes manteniendo el formato.")
            info_label.setStyleSheet("color: gray; font-style: italic; font-size: 10px;")
            excel_layout.addWidget(info_label)
            
            # Insert BEFORE profiles group (which is usually near the end)
            index = -1
            for i in range(layout.count()):
                item = layout.itemAt(i)
                if item.widget() and item.widget().objectName() == "profiles_group":
                    index = i
                    break
            
            if index != -1:
                layout.insertWidget(index, self.excel_group)
            else:
                layout.addWidget(self.excel_group)
                
        self.excel_file_path = None

    def browse_excel_file(self):
        """Browse for Excel file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar Plantilla Excel",
            "",
            "Excel Files (*.xlsx *.xlsm);;All files (*)"
        )
        
        if file_path:
            self.excel_file_path = file_path
            self.excel_path_label.setText(f"Excel: {os.path.basename(file_path)}")
            self.excel_path_label.setStyleSheet("color: blue; font-weight: bold;")

    
    def generate_and_visualize_profiles(self):
        """🚀 UNIFIED METHOD: Generate profiles and launch interactive viewer"""
        if not self.dem_file_path or not self.selected_wall:
            QMessageBox.warning(
                self,
                "Error",
                "Seleccione un archivo DEM y un muro antes de continuar."
            )
            return
            
        # ECW es opcional - mostrar advertencia pero continuar
        if not self.ecw_file_path:
            QMessageBox.information(
                self,
                "Ortomosaico no disponible",
                "No se ha seleccionado un archivo ortomosaico (.ECW).\n\n" +
                "El visualizador de perfiles funcionará normalmente, pero no podrá ver\n" +
                "los perfiles sobre el ortomosaico."
            )
            
        try:
            # Create progress dialog
            progress = QProgressDialog("Procesando perfiles topográficos...", "Cancelar", 0, 100, self)
            progress.setWindowModality(Qt.WindowModal)
            progress.show()
            
            QgsApplication.processEvents()
            
            # Load DEM
            progress.setLabelText("Cargando DEM...")
            progress.setValue(10)
            QgsApplication.processEvents()
            
            dem_data = self.dem_processor.load_dem(self.dem_file_path)
            
            # 🆕 Load Previous DEM if selected
            prev_dem_data = None
            if self.previous_dem_file_path:
                progress.setLabelText("Cargando DEM Anterior...")
                progress.setValue(15)
                QgsApplication.processEvents()
                try:
                    prev_dem_data = self.dem_processor.load_dem(self.previous_dem_file_path)
                    print("✅ DEM Anterior cargado correctamente")
                except Exception as e:
                    print(f"⚠️ Error cargando DEM Anterior: {e}")
                    # Continue without it
            
            
            # Get alignment data
            progress.setLabelText("Obteniendo datos de alineación...")
            progress.setValue(20)
            QgsApplication.processEvents()
            
            alignment = self.alignment_data.get_alignment(self.selected_wall)
            
            # Generate profiles
            progress.setLabelText("Generando perfiles topográficos...")
            progress.setValue(30)
            QgsApplication.processEvents()
            
            self.profiles_data = self.profile_generator.generate_profiles(
                dem_data, 
                alignment, 
                progress_callback=lambda p: (
                    progress.setValue(30 + int(p * 0.5)),
                    QgsApplication.processEvents()
                ),
                wall_name=self.selected_wall,
                previous_dem_data=prev_dem_data  # 🆕 Pass previous DEM data
            )
            
            progress.setValue(85)
            progress.setLabelText("Preparando visualizador interactivo...")
            QgsApplication.processEvents()
            
            # Update UI info
            self.profiles_info_label.setText(
                f"✅ Perfiles generados: {len(self.profiles_data)}\n"
                f"📏 Ancho de análisis: 140m (Vista: ±40m, Max: ±70m)\n"
                f"🎯 Rango: PK {alignment['start_pk']} hasta {alignment['end_pk']}\n"
                f"🔧 Herramientas de medición disponibles"
            )
            
            progress.setValue(95)
            QgsApplication.processEvents()
            
            progress.close()
            
            # 🚀 Launch interactive viewer directly
            try:
                from .profile_viewer_dialog import InteractiveProfileViewer
                self.profile_viewer = InteractiveProfileViewer(
                    self.profiles_data, 
                    self, 
                    self.ecw_file_path,
                    excel_file_path=self.excel_file_path,
                    dem_path=self.dem_file_path  # We need this for the date extraction!
                )
                
                # 🔄 Connect close event to cache measurements
                self.profile_viewer.finished.connect(self.on_profile_viewer_closed)
                
                # 🆕 Restore cached measurements if available (from loaded project)
                if hasattr(self, '_cached_measurements') and self._cached_measurements:
                    print(f"🔄 Restaurando {len(self._cached_measurements.get('saved_measurements', {}))} mediciones cacheadas...")
                    try:
                        self.profile_viewer.restore_measurements(self._cached_measurements)
                        print("✅ Mediciones restauradas exitosamente")
                    except Exception as e:
                        print(f"⚠️ Error al restaurar mediciones: {e}")
                
                self.profile_viewer.exec_()
                
            except ImportError as ie:
                QMessageBox.critical(
                    self,
                    "Error - Módulo no encontrado",
                    f"No se pudo cargar el visualizador interactivo.\n\n"
                    f"Asegúrese de que el archivo 'profile_viewer_dialog.py' esté en la carpeta del plugin.\n\n"
                    f"Error técnico: {str(ie)}"
                )
            except Exception as ve:
                error_msg = str(ve)
                
                # Detect specific library compatibility issues
                if "_ARRAY_API" in error_msg:
                    specific_msg = (
                        "🔧 PROBLEMA DE COMPATIBILIDAD DETECTADO:\n\n"
                        "Error '_ARRAY_API not found' indica incompatibilidad entre versiones de NumPy y otras librerías.\n\n"
                        "SOLUCIÓN RECOMENDADA:\n"
                        "1. Actualice NumPy: pip install --upgrade numpy\n"
                        "2. Reinicie QGIS después de la actualización\n\n"
                        f"Error técnico: {error_msg}"
                    )
                elif "NavigationToolbar" in error_msg:
                    specific_msg = (
                        "🔧 PROBLEMA DE MATPLOTLIB DETECTADO:\n\n"
                        "NavigationToolbar no está disponible, posible incompatibilidad de versión.\n\n"
                        "SOLUCIÓN RECOMENDADA:\n"
                        "1. Actualice Matplotlib: pip install --upgrade matplotlib\n"
                        "2. Reinicie QGIS después de la actualización\n\n"
                        f"Error técnico: {error_msg}"
                    )
                else:
                    specific_msg = f"Error al abrir el visualizador interactivo:\n\n{error_msg}\n\n"
                
                QMessageBox.critical(
                    self,
                    "Error del Visualizador",
                    f"{specific_msg}\nLos perfiles se generaron correctamente, pero no se pudo mostrar la interfaz."
                )
            
        except Exception as e:
            if 'progress' in locals():
                progress.close()
            QMessageBox.critical(
                self,
                "Error",
                f"Error al generar perfiles: {str(e)}"
            )
    
    # 🗑️ REMOVED METHODS (no longer needed):
    # - generate_profiles() 
    # - analyze_profiles()
    
    def export_profiles_to_csv(self):
        """Optional: Export generated profiles to CSV"""
        if not hasattr(self, 'profiles_data') or not self.profiles_data:
            QMessageBox.warning(
                self,
                "Sin datos",
                "Primero debe generar los perfiles topográficos."
            )
            return
        
        # Get output file path
        output_path, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar perfiles como CSV",
            f"perfiles_{self.selected_wall.replace(' ', '_')}.csv",
            "CSV files (*.csv);;All files (*)"
        )
        
        if output_path:
            try:
                self.profile_generator.export_profiles_to_csv(self.profiles_data, output_path)
                QMessageBox.information(
                    self,
                    "Exportación exitosa",
                    f"Perfiles exportados correctamente a:\n{output_path}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error de exportación",
                    f"No se pudo exportar los perfiles:\n{str(e)}"
                )
    
    # 🆕 PROJECT MANAGEMENT METHODS
    
    def setup_project_management_buttons(self):
        """Create project management buttons dynamically"""
        from PyQt5.QtWidgets import QPushButton, QHBoxLayout
        
        # Create buttons
        self.save_project_button = QPushButton("💾 Guardar Proyecto")
        self.load_project_button = QPushButton("📂 Cargar Proyecto")
        
        # Set button styles
        button_style = """
        QPushButton {
            background-color: #4CAF50;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #45a049;
        }
        QPushButton:pressed {
            background-color: #3d8b40;
        }
        """
        
        load_button_style = """
        QPushButton {
            background-color: #2196F3;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #1976D2;
        }
        QPushButton:pressed {
            background-color: #1565C0;
        }
        """
        
        self.save_project_button.setStyleSheet(button_style)
        self.load_project_button.setStyleSheet(load_button_style)
        
        # Connect buttons
        self.save_project_button.clicked.connect(self.save_project)
        self.load_project_button.clicked.connect(self.load_project)
        
        # Add to layout (assuming there's a main layout)
        if hasattr(self, 'layout') and self.layout():
            project_layout = QHBoxLayout()
            project_layout.addWidget(self.save_project_button)
            project_layout.addWidget(self.load_project_button)
            self.layout().addLayout(project_layout)
    
    def save_project(self):
        """Save current project state"""
        try:
            # Get measurements from profile viewer if open or closed
            saved_measurements = {}
            operation_mode = "measurement"  # default
            auto_width_detection = False   # default
            
            if hasattr(self, 'profile_viewer') and self.profile_viewer:
                # Profile viewer is still open - get current measurements
                measurements_data = self.profile_viewer.get_all_measurements()
                saved_measurements = measurements_data.get('saved_measurements', {})
                operation_mode = measurements_data.get('operation_mode', 'measurement')
                auto_width_detection = measurements_data.get('auto_detection_enabled', False)
            elif hasattr(self, '_cached_measurements') and self._cached_measurements:
                # Profile viewer was closed but we have cached data
                saved_measurements = self._cached_measurements.get('saved_measurements', {})
                operation_mode = self._cached_measurements.get('operation_mode', 'measurement')
                auto_width_detection = self._cached_measurements.get('auto_detection_enabled', False)
            
            # Validate that we have the minimum required data
            if not self.selected_wall:
                QMessageBox.warning(
                    self,
                    "Datos incompletos",
                    "Debe seleccionar un muro antes de guardar el proyecto."
                )
                return
            
            # Save project using ProjectManager (it handles file dialog internally)
            success, file_path = self.project_manager.save_project(
                wall_name=self.selected_wall,
                dem_path=self.dem_file_path,
                ecw_path=self.ecw_file_path,
                saved_measurements=saved_measurements,
                operation_mode=operation_mode,
                auto_width_detection=auto_width_detection,
                prev_dem_path=self.previous_dem_file_path,
                excel_path=self.excel_file_path,
                parent_widget=self
            )
            
            if not success:
                QMessageBox.warning(
                    self,
                    "Guardado cancelado",
                    "El guardado del proyecto fue cancelado."
                )
                
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error de Guardado",
                f"Error al guardar el proyecto:\n{str(e)}"
            )
    
    def load_project(self):
        """Load project from file"""
        try:
            print("🔄 Iniciando carga de proyecto...")
            
            # Import QMessageBox explicitly to avoid conflicts
            from PyQt5.QtWidgets import QMessageBox as MsgBox
            
            # Load project using ProjectManager (it handles file dialog internally)
            success, project_data = self.project_manager.load_project(parent_widget=self)
            
            print(f"📋 ProjectManager retornó: success={success}, data={project_data is not None}")
            
            if not success:
                print("ℹ️ Carga cancelada por el usuario o error en ProjectManager")
                return
                
            if not project_data:
                print("⚠️ project_data está vacío")
                MsgBox.warning(
                    self,
                    "Error de Carga",
                    "No se pudo cargar el proyecto. El archivo puede estar corrupto."
                )
                return
            
            print("📊 Extrayendo datos del proyecto...")
            
            # Extract data from project structure
            file_paths = project_data.get('file_paths', {})
            project_settings = project_data.get('project_settings', {})
            measurements_data = project_data.get('measurements_data', {})
            
            print(f"📁 file_paths: {list(file_paths.keys())}")
            print(f"⚙️ project_settings: {list(project_settings.keys())}")
            print(f"📏 measurements_data: {len(measurements_data)} mediciones")
            
            # Restore project state
            self.dem_file_path = file_paths.get('dem_path')
            self.ecw_file_path = file_paths.get('ecw_path')
            self.previous_dem_file_path = file_paths.get('prev_dem_path')
            self.excel_file_path = file_paths.get('excel_path')
            self.selected_wall = project_settings.get('wall_name')
            
            print(f"🎯 Estado restaurado: muro={self.selected_wall}, dem={bool(self.dem_file_path)}, ecw={bool(self.ecw_file_path)}, prev_dem={bool(self.previous_dem_file_path)}, excel={bool(self.excel_file_path)}")
            
            # Update UI elements
            if hasattr(self, 'dem_path_label') and self.dem_file_path:
                self.dem_path_label.setText(f"DEM: {os.path.basename(self.dem_file_path)}")
                print("📁 DEM label actualizado")
                
                # Update DEM info if exists
                if hasattr(self, 'dem_info_label'):
                    if os.path.exists(self.dem_file_path):
                        self.dem_info_label.setText("✅ Archivo DEM cargado desde proyecto")
                    else:
                        self.dem_info_label.setText("⚠️ Archivo DEM no encontrado en la ruta guardada")
            
            if hasattr(self, 'ecw_path_label') and self.ecw_file_path:
                self.ecw_path_label.setText(f"ECW: {os.path.basename(self.ecw_file_path)}")
                print("🗺️ ECW label actualizado")
                
                # Update ECW info if exists
                if hasattr(self, 'ecw_info_label'):
                    if os.path.exists(self.ecw_file_path):
                        self.ecw_info_label.setText("✅ Archivo ECW cargado desde proyecto")
                    else:
                        self.ecw_info_label.setText("⚠️ Archivo ECW no encontrado en la ruta guardada")
                
            if hasattr(self, 'wall_combo') and self.selected_wall:
                wall_index = self.wall_combo.findText(self.selected_wall)
                if wall_index >= 0:
                    self.wall_combo.setCurrentIndex(wall_index)
                    print(f"🎯 Wall combo actualizado al índice {wall_index}")
                    
            if hasattr(self, 'prev_dem_path_label') and self.previous_dem_file_path:
                self.prev_dem_path_label.setText(f"DEM Ant: {os.path.basename(self.previous_dem_file_path)}")
                self.prev_dem_path_label.setStyleSheet("color: green;")
                
            if hasattr(self, 'excel_path_label') and self.excel_file_path:
                self.excel_path_label.setText(f"Excel: {os.path.basename(self.excel_file_path)}")
                self.excel_path_label.setStyleSheet("color: blue; font-weight: bold;")
            
            # Cache the loaded measurements for future save operations
            if measurements_data:
                self._cached_measurements = {
                    'saved_measurements': measurements_data,
                    'operation_mode': project_settings.get('operation_mode', 'measurement'),
                    'auto_detection_enabled': project_settings.get('auto_width_detection', False)
                }
                print(f"📦 Cached {len(measurements_data)} mediciones")
            else:
                self._cached_measurements = {}
                print("📦 No hay mediciones para cachear")
            
            print("✅ Proyecto cargado exitosamente")
            
            # Check if we can enable "Generate Profiles" button
            if (self.selected_wall and self.dem_file_path and 
                os.path.exists(self.dem_file_path) and 
                hasattr(self, 'generate_profiles_button')):
                
                self.generate_profiles_button.setEnabled(True)
                print("🚀 Botón 'Generar Perfiles' habilitado automáticamente")
                
                # Update button text to indicate ready state
                if hasattr(self, 'generate_profiles_button'):
                    self.generate_profiles_button.setText("🚀 Generar y Visualizar Perfiles (Proyecto Cargado)")
            
            # Note: ProjectManager already shows success message, so we don't duplicate it
            
        except Exception as e:
            print(f"❌ Error en load_project: {e}")
            import traceback
            traceback.print_exc()
            
            # Use explicit import to avoid conflicts
            from PyQt5.QtWidgets import QMessageBox as MsgBox
            MsgBox.critical(
                self,
                "Error de Carga",
                f"Error al cargar el proyecto:\n{str(e)}"
            )
    
    def on_profile_viewer_closed(self):
        """Cache measurements when profile viewer is closed"""
        try:
            if hasattr(self, 'profile_viewer') and self.profile_viewer:
                # Cache all measurements before the viewer is destroyed
                self._cached_measurements = self.profile_viewer.get_all_measurements()
                print(f"📦 Cached {len(self._cached_measurements.get('saved_measurements', {}))} measurements")
            else:
                self._cached_measurements = {}
        except Exception as e:
            print(f"⚠️ Error caching measurements: {e}")
            self._cached_measurements = {}