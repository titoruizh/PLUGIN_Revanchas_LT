# -*- coding: utf-8 -*-
"""
Project Manager Module - Revanchas LT Plugin
Gestor de proyectos para guardar y cargar sesiones completas

Refactorizado con type hints y logging estructurado.

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
from typing import Dict, Any, Optional, List, Tuple

from qgis.PyQt.QtWidgets import QFileDialog, QMessageBox, QWidget

# Importar logging del plugin
try:
    from ..utils.logging_config import get_logger
except ImportError:
    get_logger = lambda x: __import__('logging').getLogger(x)

logger = get_logger(__name__)


class ProjectManager:
    """
    Gestor de proyectos para guardar y cargar sesiones completas.
    
    Maneja la persistencia de datos del plugin incluyendo mediciones,
    configuraciones y rutas de archivos.
    """
    
    PROJECT_VERSION: str = "1.0"
    PROJECT_EXTENSION: str = ".rvlt"  # Revanchas LT Project
    PLUGIN_VERSION: str = "1.2.0"
    
    def __init__(self):
        """Inicializa el gestor de proyectos."""
        self.current_project_path: Optional[str] = None
        self.project_data: Dict[str, Any] = {}
        self._is_modified: bool = False
        
        logger.debug("ProjectManager inicializado")
    
    def create_project_data(self, 
                            wall_name: str,
                            dem_path: Optional[str],
                            ecw_path: Optional[str],
                            saved_measurements: Optional[Dict[str, Any]],
                            operation_mode: str,
                            auto_width_detection: bool) -> Dict[str, Any]:
        """
        Crea estructura de datos del proyecto.
        
        Args:
            wall_name: Nombre del muro
            dem_path: Ruta al archivo DEM
            ecw_path: Ruta al archivo ECW
            saved_measurements: Diccionario con mediciones guardadas
            operation_mode: Modo de operación
            auto_width_detection: Estado de detección automática de ancho
            
        Returns:
            Diccionario con datos del proyecto
        """
        now = datetime.datetime.now()
        
        project_data: Dict[str, Any] = {
            "project_info": {
                "version": self.PROJECT_VERSION,
                "created_date": now.isoformat(),
                "last_modified": now.isoformat(),
                "plugin_version": self.PLUGIN_VERSION
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
            "measurements_data": saved_measurements or {},
            "statistics": {
                "total_profiles": 0,
                "measured_profiles": len(saved_measurements) if saved_measurements else 0,
                "completion_percentage": 0
            }
        }
        
        logger.debug(f"Datos de proyecto creados para {wall_name}")
        return project_data
    
    def save_project(self, 
                     wall_name: str,
                     dem_path: Optional[str],
                     ecw_path: Optional[str],
                     saved_measurements: Optional[Dict[str, Any]],
                     operation_mode: str,
                     auto_width_detection: bool,
                     parent_widget: Optional[QWidget] = None) -> Tuple[bool, Optional[str]]:
        """
        Guarda proyecto en archivo JSON.
        
        Args:
            wall_name: Nombre del muro
            dem_path: Ruta al archivo DEM
            ecw_path: Ruta al archivo ECW
            saved_measurements: Mediciones guardadas
            operation_mode: Modo de operación
            auto_width_detection: Estado de detección automática
            parent_widget: Widget padre para diálogos
            
        Returns:
            Tupla (éxito, ruta del archivo)
        """
        try:
            file_dialog = QFileDialog()
            file_dialog.setAcceptMode(QFileDialog.AcceptSave)
            file_dialog.setNameFilter(f"Proyectos Revanchas LT (*{self.PROJECT_EXTENSION})")
            file_dialog.setDefaultSuffix(self.PROJECT_EXTENSION[1:])
            
            # Nombre sugerido
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M')
            suggested_name = f"Proyecto_{wall_name}_{timestamp}"
            file_dialog.selectFile(suggested_name)
            
            if file_dialog.exec_() == QFileDialog.Accepted:
                file_path = file_dialog.selectedFiles()[0]
                
                # Crear datos del proyecto
                project_data = self.create_project_data(
                    wall_name, dem_path, ecw_path, saved_measurements,
                    operation_mode, auto_width_detection
                )
                
                # Actualizar estadísticas
                if saved_measurements:
                    project_data["statistics"]["measured_profiles"] = len(saved_measurements)
                
                # Guardar archivo JSON
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(project_data, f, indent=4, ensure_ascii=False)
                
                self.current_project_path = file_path
                self.project_data = project_data
                self._is_modified = False
                
                logger.info(f"Proyecto guardado: {file_path}")
                
                # Mensaje de éxito
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
            logger.error(f"Error guardando proyecto: {e}")
            QMessageBox.critical(
                parent_widget,
                "Error al Guardar",
                f"No se pudo guardar el proyecto:\n{str(e)}"
            )
            return False, None
    
    def load_project(self, 
                     parent_widget: Optional[QWidget] = None) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Carga proyecto desde archivo JSON.
        
        Args:
            parent_widget: Widget padre para diálogos
            
        Returns:
            Tupla (éxito, datos del proyecto)
        """
        try:
            file_dialog = QFileDialog()
            file_dialog.setAcceptMode(QFileDialog.AcceptOpen)
            file_dialog.setNameFilter(f"Proyectos Revanchas LT (*{self.PROJECT_EXTENSION})")
            
            if file_dialog.exec_() == QFileDialog.Accepted:
                file_path = file_dialog.selectedFiles()[0]
                
                logger.info(f"Cargando proyecto: {file_path}")
                
                # Leer archivo JSON
                with open(file_path, 'r', encoding='utf-8') as f:
                    project_data = json.load(f)
                
                # Validar estructura
                if not self._validate_project_data(project_data):
                    QMessageBox.warning(
                        parent_widget,
                        "Archivo Inválido",
                        "El archivo seleccionado no es un proyecto válido de Revanchas LT."
                    )
                    return False, None
                
                # Verificar archivos existentes
                missing_files = self._check_missing_files(project_data)
                
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
                self._is_modified = False
                
                # Actualizar fecha de modificación
                project_data["project_info"]["last_modified"] = datetime.datetime.now().isoformat()
                
                # Mostrar información
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
                
                logger.info(f"Proyecto cargado exitosamente: {project_data['project_settings']['wall_name']}")
                
                return True, project_data
            
            return False, None
            
        except Exception as e:
            logger.error(f"Error cargando proyecto: {e}")
            QMessageBox.critical(
                parent_widget,
                "Error al Cargar",
                f"No se pudo cargar el proyecto:\n{str(e)}"
            )
            return False, None
    
    def save_project_quick(self) -> bool:
        """
        Guarda rápidamente el proyecto actual (sin diálogo).
        
        Returns:
            True si el guardado fue exitoso
        """
        if not self.current_project_path or not self.project_data:
            logger.warning("No hay proyecto actual para guardar")
            return False
        
        try:
            self.project_data["project_info"]["last_modified"] = datetime.datetime.now().isoformat()
            
            with open(self.current_project_path, 'w', encoding='utf-8') as f:
                json.dump(self.project_data, f, indent=4, ensure_ascii=False)
            
            self._is_modified = False
            logger.info(f"Proyecto guardado rápidamente: {self.current_project_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error en guardado rápido: {e}")
            return False
    
    def _validate_project_data(self, project_data: Dict[str, Any]) -> bool:
        """
        Valida estructura de datos del proyecto.
        
        Args:
            project_data: Datos a validar
            
        Returns:
            True si la estructura es válida
        """
        try:
            required_keys = ["project_info", "project_settings", "file_paths", "measurements_data"]
            for key in required_keys:
                if key not in project_data:
                    logger.warning(f"Falta clave requerida: {key}")
                    return False
            
            if "version" not in project_data["project_info"]:
                logger.warning("Falta versión en project_info")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validando proyecto: {e}")
            return False
    
    def _check_missing_files(self, project_data: Dict[str, Any]) -> List[str]:
        """
        Verifica archivos faltantes.
        
        Args:
            project_data: Datos del proyecto
            
        Returns:
            Lista de archivos faltantes
        """
        missing_files: List[str] = []
        
        dem_path = project_data.get("file_paths", {}).get("dem_path")
        ecw_path = project_data.get("file_paths", {}).get("ecw_path")
        
        if dem_path and not os.path.exists(dem_path):
            missing_files.append(f"DEM: {dem_path}")
        
        if ecw_path and not os.path.exists(ecw_path):
            missing_files.append(f"ECW: {ecw_path}")
        
        return missing_files
    
    def update_measurements(self, measurements: Dict[str, Any]) -> None:
        """
        Actualiza mediciones en el proyecto actual.
        
        Args:
            measurements: Nuevas mediciones
        """
        if self.project_data:
            self.project_data["measurements_data"] = measurements
            self.project_data["statistics"]["measured_profiles"] = len(measurements)
            self._is_modified = True
            logger.debug(f"Mediciones actualizadas: {len(measurements)} perfiles")
    
    def get_recent_projects(self, max_projects: int = 5) -> List[Dict[str, Any]]:
        """
        Obtiene lista de proyectos recientes.
        
        Args:
            max_projects: Número máximo de proyectos
            
        Returns:
            Lista de proyectos recientes
        """
        # TODO: Implementar persistencia de proyectos recientes
        return []
    
    def auto_save_project(self) -> bool:
        """
        Guarda automáticamente el proyecto actual.
        
        Returns:
            True si el auto-guardado fue exitoso
        """
        if self._is_modified and self.current_project_path:
            return self.save_project_quick()
        return False
    
    @property
    def is_modified(self) -> bool:
        """Indica si el proyecto tiene cambios sin guardar."""
        return self._is_modified
    
    @property
    def has_project(self) -> bool:
        """Indica si hay un proyecto cargado."""
        return bool(self.project_data)
    
    def get_project_summary(self) -> Optional[Dict[str, Any]]:
        """
        Obtiene resumen del proyecto actual.
        
        Returns:
            Diccionario con resumen o None
        """
        if not self.project_data:
            return None
        
        return {
            'wall_name': self.project_data.get('project_settings', {}).get('wall_name'),
            'file_path': self.current_project_path,
            'measured_profiles': self.project_data.get('statistics', {}).get('measured_profiles', 0),
            'operation_mode': self.project_data.get('project_settings', {}).get('operation_mode'),
            'is_modified': self._is_modified
        }