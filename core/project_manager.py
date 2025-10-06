# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ProjectManager
                                 A QGIS plugin
 Gestor de Proyectos para Revanchas LT Plugin
                             -------------------
        begin                : 2025-10-02
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
import json
import datetime
from qgis.PyQt.QtWidgets import QFileDialog, QMessageBox


class ProjectManager:
    """Gestor de proyectos para guardar y cargar sesiones completas"""
    
    PROJECT_VERSION = "1.0"
    PROJECT_EXTENSION = ".rvlt"  # Revanchas LT Project
    
    def __init__(self):
        self.current_project_path = None
        self.project_data = {}
    
    def create_project_data(self, wall_name, dem_path, ecw_path, saved_measurements, operation_mode, auto_width_detection):
        """Crear estructura de datos del proyecto"""
        project_data = {
            "project_info": {
                "version": self.PROJECT_VERSION,
                "created_date": datetime.datetime.now().isoformat(),
                "last_modified": datetime.datetime.now().isoformat(),
                "plugin_version": "1.2.0"
            },
            "project_settings": {
                "wall_name": wall_name,
                "operation_mode": operation_mode,
                "auto_width_detection": auto_width_detection
            },
            "file_paths": {
                "dem_path": dem_path,
                "ecw_path": ecw_path
            },
            "measurements_data": saved_measurements,
            "statistics": {
                "total_profiles": 0,
                "measured_profiles": len(saved_measurements) if saved_measurements else 0,
                "completion_percentage": 0
            }
        }
        
        return project_data
    
    def save_project(self, wall_name, dem_path, ecw_path, saved_measurements, operation_mode, auto_width_detection, parent_widget=None):
        """Guardar proyecto en archivo JSON"""
        try:
            # Abrir diálogo para seleccionar ubicación
            file_dialog = QFileDialog()
            file_dialog.setAcceptMode(QFileDialog.AcceptSave)
            file_dialog.setNameFilter(f"Proyectos Revanchas LT (*{self.PROJECT_EXTENSION})")
            file_dialog.setDefaultSuffix(self.PROJECT_EXTENSION[1:])  # Sin el punto
            
            # Sugerir nombre por defecto
            suggested_name = f"Proyecto_{wall_name}_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}"
            file_dialog.selectFile(suggested_name)
            
            if file_dialog.exec_() == QFileDialog.Accepted:
                file_path = file_dialog.selectedFiles()[0]
                
                # Crear datos del proyecto
                project_data = self.create_project_data(
                    wall_name, dem_path, ecw_path, saved_measurements,
                    operation_mode, auto_width_detection
                )
                
                # Calcular estadísticas
                if saved_measurements:
                    total_measurements = len(saved_measurements)
                    project_data["statistics"]["measured_profiles"] = total_measurements
                    # Aquí podrías calcular el total de perfiles del muro para obtener porcentaje
                
                # Guardar archivo JSON
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(project_data, f, indent=4, ensure_ascii=False)
                
                self.current_project_path = file_path
                self.project_data = project_data
                
                # Mostrar mensaje de éxito
                QMessageBox.information(
                    parent_widget,
                    "Proyecto Guardado",
                    f"Proyecto guardado exitosamente en:\n{file_path}\n\n"
                    f"Perfiles medidos: {project_data['statistics']['measured_profiles']}\n"
                    f"Modo: {operation_mode}\n"
                    f"Fecha: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}"
                )
                
                return True, file_path
            
            return False, None
            
        except Exception as e:
            QMessageBox.critical(
                parent_widget,
                "Error al Guardar",
                f"No se pudo guardar el proyecto:\n{str(e)}"
            )
            return False, None
    
    def load_project(self, parent_widget=None):
        """Cargar proyecto desde archivo JSON"""
        try:
            # Abrir diálogo para seleccionar archivo
            file_dialog = QFileDialog()
            file_dialog.setAcceptMode(QFileDialog.AcceptOpen)
            file_dialog.setNameFilter(f"Proyectos Revanchas LT (*{self.PROJECT_EXTENSION})")
            
            if file_dialog.exec_() == QFileDialog.Accepted:
                file_path = file_dialog.selectedFiles()[0]
                
                # Leer archivo JSON
                with open(file_path, 'r', encoding='utf-8') as f:
                    project_data = json.load(f)
                
                # Validar estructura del proyecto
                if not self._validate_project_data(project_data):
                    QMessageBox.warning(
                        parent_widget,
                        "Archivo Inválido",
                        "El archivo seleccionado no es un proyecto válido de Revanchas LT."
                    )
                    return False, None
                
                # Verificar que los archivos existan
                missing_files = []
                dem_path = project_data.get("file_paths", {}).get("dem_path")
                ecw_path = project_data.get("file_paths", {}).get("ecw_path")
                
                if dem_path and not os.path.exists(dem_path):
                    missing_files.append(f"DEM: {dem_path}")
                
                if ecw_path and not os.path.exists(ecw_path):
                    missing_files.append(f"ECW: {ecw_path}")
                
                if missing_files:
                    result = QMessageBox.question(
                        parent_widget,
                        "Archivos No Encontrados",
                        f"Los siguientes archivos no se encontraron:\n\n" +
                        "\n".join(missing_files) +
                        "\n\n¿Desea continuar de todos modos?\n"
                        "(Podrá especificar nuevas rutas después)",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.Yes
                    )
                    
                    if result == QMessageBox.No:
                        return False, None
                
                self.current_project_path = file_path
                self.project_data = project_data
                
                # Actualizar fecha de última modificación
                project_data["project_info"]["last_modified"] = datetime.datetime.now().isoformat()
                
                # Mostrar información del proyecto cargado
                created_date = datetime.datetime.fromisoformat(
                    project_data["project_info"]["created_date"]
                ).strftime('%d/%m/%Y %H:%M')
                
                QMessageBox.information(
                    parent_widget,
                    "Proyecto Cargado",
                    f"Proyecto cargado exitosamente:\n\n"
                    f"Muro: {project_data['project_settings']['wall_name']}\n"
                    f"Modo: {project_data['project_settings']['operation_mode']}\n"
                    f"Perfiles medidos: {project_data['statistics']['measured_profiles']}\n"
                    f"Creado: {created_date}\n"
                    f"Archivo: {os.path.basename(file_path)}"
                )
                
                return True, project_data
            
            return False, None
            
        except Exception as e:
            QMessageBox.critical(
                parent_widget,
                "Error al Cargar",
                f"No se pudo cargar el proyecto:\n{str(e)}"
            )
            return False, None
    
    def _validate_project_data(self, project_data):
        """Validar estructura de datos del proyecto"""
        try:
            # Verificar estructura básica
            required_keys = ["project_info", "project_settings", "file_paths", "measurements_data"]
            for key in required_keys:
                if key not in project_data:
                    return False
            
            # Verificar version
            if "version" not in project_data["project_info"]:
                return False
            
            return True
            
        except Exception:
            return False
    
    def get_recent_projects(self, max_projects=5):
        """Obtener lista de proyectos recientes (para futuras implementaciones)"""
        # TODO: Implementar sistema de proyectos recientes
        return []
    
    def auto_save_project(self):
        """Guardar automáticamente el proyecto actual (para futuras implementaciones)"""
        # TODO: Implementar auto-guardado
        pass