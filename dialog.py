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
        self.dem_file_path = None
        self.ecw_file_path = None  # New: Store ECW file path
        self.profiles_data = None  # Store generated profiles
        
        # Connect signals - UNIFIED: only one button now
        self.browse_dem_button.clicked.connect(self.browse_dem_file)
        self.browse_ecw_button.clicked.connect(self.browse_ecw_file)  # New: ECW browse button
        self.generate_profiles_button.clicked.connect(self.generate_and_visualize_profiles)
        
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
                
                # ✅ VALIDAR COBERTURA DE LA ALINEACIÓN
                if self.selected_wall:
                    from .core.dem_validator import DEMValidator
                    
                    alignment = self.alignment_data.get_alignment(self.selected_wall)
                    validation = DEMValidator.validate_dem_coverage(dem_info, alignment)
                    
                    if not validation['coverage_ok']:
                        # ❌ DEM NO CUBRE LA ALINEACIÓN
                        QMessageBox.critical(
                            self,
                            "Error - DEM Insuficiente",
                            f"El DEM seleccionado NO cubre la alineación del {self.selected_wall}.\n\n"
                            f"🎯 Área requerida (con buffer 50m):\n"
                            f"X: {validation['alignment_bounds']['xmin']:.1f} - {validation['alignment_bounds']['xmax']:.1f}\n"
                            f"Y: {validation['alignment_bounds']['ymin']:.1f} - {validation['alignment_bounds']['ymax']:.1f}\n\n"
                            f"📍 DEM disponible:\n"
                            f"X: {validation['dem_bounds']['xmin']:.1f} - {validation['dem_bounds']['xmax']:.1f}\n"
                            f"Y: {validation['dem_bounds']['ymin']:.1f} - {validation['dem_bounds']['ymax']:.1f}\n\n"
                            f"❌ Seleccione un DEM que cubra completamente la zona del muro."
                        )
                        return  # ❌ NO continuar si DEM no es válido
                    
                    # ✅ DEM válido - mostrar confirmación
                    QMessageBox.information(
                        self,
                        "✅ DEM Validado",
                        f"El DEM cubre correctamente la alineación del {self.selected_wall}."
                    )
                
                # ✅ Continuar con carga normal
                self.dem_file_path = file_path
                self.dem_path_label.setText(f"DEM: {os.path.basename(file_path)}")
                
                # Habilitar botón de generar perfiles solo cuando tenemos todos los archivos necesarios
                self.check_required_files()
                
                # Show DEM info
                info_text = f"Dimensiones: {dem_info['cols']} x {dem_info['rows']}\n"
                info_text += f"Resolución: {dem_info['cellsize']:.2f}m\n"
                info_text += f"Extensión: X({dem_info['xmin']:.2f}, {dem_info['xmax']:.2f}) Y({dem_info['ymin']:.2f}, {dem_info['ymax']:.2f})"
                self.dem_info_label.setText(info_text)
                
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Error",
                    f"No se pudo validar el DEM: {str(e)}"
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
                
                # ✅ VALIDAR COBERTURA DE LA ALINEACIÓN
                if self.selected_wall:
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
                    
                    if not validation['coverage_ok']:
                        # ❌ ECW NO CUBRE LA ALINEACIÓN
                        QMessageBox.critical(
                            self,
                            "Error - Ortomosaico Insuficiente",
                            f"El ortomosaico seleccionado NO cubre la alineación del {self.selected_wall}.\n\n"
                            f"🎯 Área requerida (con buffer 50m):\n"
                            f"X: {validation['alignment_bounds']['xmin']:.1f} - {validation['alignment_bounds']['xmax']:.1f}\n"
                            f"Y: {validation['alignment_bounds']['ymin']:.1f} - {validation['alignment_bounds']['ymax']:.1f}\n\n"
                            f"📍 Ortomosaico disponible:\n"
                            f"X: {validation['dem_bounds']['xmin']:.1f} - {validation['dem_bounds']['xmax']:.1f}\n"
                            f"Y: {validation['dem_bounds']['ymin']:.1f} - {validation['dem_bounds']['ymax']:.1f}\n\n"
                            f"❌ Seleccione un ortomosaico que cubra completamente la zona del muro."
                        )
                        return  # ❌ NO continuar si ECW no es válido
                    
                    # ✅ ECW válido - mostrar confirmación
                    QMessageBox.information(
                        self,
                        "✅ Ortomosaico Validado",
                        f"El ortomosaico cubre correctamente la alineación del {self.selected_wall}."
                    )
                
                # ✅ Continuar con carga normal
                self.ecw_file_path = file_path
                self.ecw_path_label.setText(f"ECW: {os.path.basename(file_path)}")
                
                # Habilitar botón de generar perfiles solo cuando tenemos todos los archivos necesarios
                self.check_required_files()
                
                # Show ECW info
                extent = ecw_layer.extent()
                width = ecw_layer.width()
                height = ecw_layer.height()
                
                pixel_size_x = (extent.xMaximum() - extent.xMinimum()) / width
                pixel_size_y = (extent.yMaximum() - extent.yMinimum()) / height
                
                info_text = f"Dimensiones: {width} x {height} píxeles\n"
                info_text += f"Resolución: {pixel_size_x:.2f}m/px\n"
                info_text += f"Extensión: X({extent.xMinimum():.2f}, {extent.xMaximum():.2f}) Y({extent.yMinimum():.2f}, {extent.yMaximum():.2f})"
                self.ecw_info_label.setText(info_text)
                
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Error",
                    f"No se pudo validar el ortomosaico: {str(e)}"
                )
                
    def check_required_files(self):
        """Check if all required files are selected and enable/disable buttons accordingly"""
        # Solo necesitamos el DEM para generar perfiles (ECW es opcional)
        if self.dem_file_path:
            self.generate_profiles_button.setEnabled(True)
        else:
            self.generate_profiles_button.setEnabled(False)
    
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
                wall_name=self.selected_wall 
            )
            
            progress.setValue(85)
            progress.setLabelText("Preparando visualizador interactivo...")
            QgsApplication.processEvents()
            
            # Update UI info
            self.profiles_info_label.setText(
                f"✅ Perfiles generados: {len(self.profiles_data)}\n"
                f"📏 Ancho de análisis: 80m\n"
                f"🎯 Rango: PK {alignment['start_pk']} hasta {alignment['end_pk']}\n"
                f"🔧 Herramientas de medición disponibles"
            )
            
            progress.setValue(95)
            QgsApplication.processEvents()
            
            progress.close()
            
            # 🚀 Launch interactive viewer directly
            try:
                from .profile_viewer_dialog import InteractiveProfileViewer
                viewer = InteractiveProfileViewer(self.profiles_data, self, self.ecw_file_path)
                viewer.exec_()
                
            except ImportError as ie:
                QMessageBox.critical(
                    self,
                    "Error - Módulo no encontrado",
                    f"No se pudo cargar el visualizador interactivo.\n\n"
                    f"Asegúrese de que el archivo 'profile_viewer_dialog.py' esté en la carpeta del plugin.\n\n"
                    f"Error técnico: {str(ie)}"
                )
            except Exception as ve:
                QMessageBox.critical(
                    self,
                    "Error del Visualizador",
                    f"Error al abrir el visualizador interactivo:\n\n{str(ve)}\n\n"
                    f"Los perfiles se generaron correctamente, pero no se pudo mostrar la interfaz."
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