# -*- coding: utf-8 -*-
"""
Export Manager Module - Revanchas LT Plugin
Gestiona la exportación de mediciones a CSV y otros formatos

Este módulo fue extraído de profile_viewer_dialog.py para mejorar
la modularidad y mantenibilidad del código.
"""

import csv
import os
from typing import Dict, List, Any, Optional

from qgis.PyQt.QtWidgets import (QDialog, QFileDialog, QMessageBox, 
                                  QProgressDialog, QApplication)


class ExportManager:
    """
    Gestiona la exportación de mediciones de perfiles a archivos CSV.
    
    Attributes:
        operation_mode: Modo de operación actual ("revancha" o "ancho_proyectado")
        profiles_data: Lista de datos de perfiles
        saved_measurements: Diccionario con mediciones guardadas por PK
    """
    
    # Configuración de exportación
    CSV_ENCODING = 'utf-8'
    DECIMAL_PRECISION = 3
    
    def __init__(self, 
                 profiles_data: List[Dict[str, Any]], 
                 saved_measurements: Dict[str, Any],
                 operation_mode: str = "revancha"):
        """
        Inicializa el gestor de exportación.
        
        Args:
            profiles_data: Lista de diccionarios con datos de perfiles
            saved_measurements: Diccionario {pk: mediciones}
            operation_mode: "revancha" o "ancho_proyectado"
        """
        self.profiles_data = profiles_data
        self.saved_measurements = saved_measurements
        self.operation_mode = operation_mode
    
    def export_to_csv(self, parent_widget: Optional[QDialog] = None) -> Optional[str]:
        """
        Exporta las mediciones a un archivo CSV con diálogo de selección.
        
        Args:
            parent_widget: Widget padre para los diálogos
            
        Returns:
            Ruta del archivo exportado o None si se canceló
        """
        try:
            # Determinar nombre de archivo sugerido
            default_name = self._get_default_filename()
            
            # Diálogo de selección de archivo
            file_path, _ = QFileDialog.getSaveFileName(
                parent_widget,
                "Guardar Mediciones CSV",
                default_name,
                "CSV Files (*.csv);;All Files (*)"
            )
            
            if not file_path:
                return None  # Usuario canceló
            
            # Asegurar extensión .csv
            if not file_path.lower().endswith('.csv'):
                file_path += '.csv'
            
            # Preparar y exportar datos
            export_data = self._prepare_export_data(parent_widget)
            
            if export_data is None:
                return None  # Usuario canceló durante preparación
            
            # Escribir archivo
            self._write_csv(file_path, export_data)
            
            # Mostrar resumen
            self._show_export_summary(parent_widget, file_path, export_data)
            
            return file_path
            
        except Exception as e:
            if parent_widget:
                QMessageBox.critical(
                    parent_widget,
                    "❌ Error de Exportación",
                    f"No se pudo exportar las mediciones:\n\n{str(e)}"
                )
            return None
    
    def _get_default_filename(self) -> str:
        """Genera nombre de archivo por defecto basado en el modo de operación."""
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
        
        if self.operation_mode == "ancho_proyectado":
            return f"AnchoProyectado_{timestamp}.csv"
        return f"Revanchas_{timestamp}.csv"
    
    def _prepare_export_data(self, parent_widget: Optional[QDialog] = None) -> Optional[List[Dict]]:
        """
        Prepara los datos para exportación con barra de progreso.
        
        Returns:
            Lista de diccionarios con datos de exportación o None si se canceló
        """
        export_data = []
        total_profiles = len(self.profiles_data)
        
        # Crear diálogo de progreso
        progress = QProgressDialog(
            "Preparando datos de exportación...", 
            "Cancelar", 
            0, 100, 
            parent_widget
        )
        progress.setWindowTitle("Exportando Mediciones")
        progress.setMinimumDuration(0)
        progress.show()
        
        try:
            for i, profile in enumerate(self.profiles_data):
                pk = profile.get('pk', f"PK{i}")
                
                if self.operation_mode == "ancho_proyectado":
                    row_data = self._prepare_ancho_proyectado_row(pk, profile)
                else:
                    row_data = self._prepare_revancha_row(pk, profile)
                
                export_data.append(row_data)
                
                # Actualizar progreso
                progress_percent = int((i + 1) / total_profiles * 85)
                progress.setValue(progress_percent)
                QApplication.processEvents()
                
                if progress.wasCanceled():
                    return None
            
            progress.setValue(100)
            progress.close()
            
            return export_data
            
        finally:
            if progress:
                progress.close()
    
    def _prepare_revancha_row(self, pk: str, profile: Dict) -> Dict:
        """Prepara una fila de datos en modo Revancha."""
        row_data = {
            'PK': pk,
            'Cota_Coronamiento': None,
            'Revancha': None,
            'Lama': None,
            'Ancho': None
        }
        
        if pk in self.saved_measurements:
            measurements = self.saved_measurements[pk]
            
            # Cota de coronamiento
            if 'crown' in measurements:
                row_data['Cota_Coronamiento'] = measurements['crown'].get('y')
            
            # LAMA
            if 'lama_modified' in measurements:
                row_data['Lama'] = measurements['lama_modified'].get('y')
            elif profile.get('lama_points'):
                for lama in profile['lama_points']:
                    if lama.get('elevation_dem') is not None:
                        row_data['Lama'] = lama['elevation_dem']
                        break
            
            # Revancha (diferencia entre coronamiento y LAMA)
            if row_data['Cota_Coronamiento'] is not None and row_data['Lama'] is not None:
                row_data['Revancha'] = row_data['Cota_Coronamiento'] - row_data['Lama']
            
            # Ancho
            if 'width' in measurements:
                row_data['Ancho'] = measurements['width'].get('distance')
        
        return row_data
    
    def _prepare_ancho_proyectado_row(self, pk: str, profile: Dict) -> Dict:
        """Prepara una fila de datos en modo Ancho Proyectado."""
        row_data = {
            'PK': pk,
            'Ancho_Proyectado': None
        }
        
        if pk in self.saved_measurements:
            measurements = self.saved_measurements[pk]
            
            if 'width' in measurements:
                row_data['Ancho_Proyectado'] = measurements['width'].get('distance')
        
        return row_data
    
    def _write_csv(self, file_path: str, export_data: List[Dict]) -> None:
        """
        Escribe los datos a un archivo CSV.
        
        Args:
            file_path: Ruta del archivo de salida
            export_data: Lista de diccionarios con datos a exportar
        """
        if not export_data:
            return
        
        # Determinar campos según modo de operación
        if self.operation_mode == "ancho_proyectado":
            fieldnames = ['PK', 'Ancho_Proyectado']
        else:
            fieldnames = ['PK', 'Cota_Coronamiento', 'Revancha', 'Lama', 'Ancho']
        
        with open(file_path, 'w', newline='', encoding=self.CSV_ENCODING) as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for row_data in export_data:
                formatted_row = self._format_row(row_data, fieldnames)
                writer.writerow(formatted_row)
    
    def _format_row(self, row_data: Dict, fieldnames: List[str]) -> Dict:
        """Formatea una fila para escritura CSV."""
        formatted_row = {}
        
        for key in fieldnames:
            value = row_data.get(key)
            
            if value is None:
                formatted_row[key] = ''
            elif isinstance(value, float):
                formatted_row[key] = f"{value:.{self.DECIMAL_PRECISION}f}"
            else:
                formatted_row[key] = value
        
        return formatted_row
    
    def _show_export_summary(self, parent_widget: Optional[QDialog], 
                             file_path: str, export_data: List[Dict]) -> None:
        """Muestra un resumen de la exportación al usuario."""
        if not parent_widget:
            return
        
        total_rows = len(export_data)
        
        if self.operation_mode == "ancho_proyectado":
            rows_with_data = sum(1 for row in export_data 
                               if row.get('Ancho_Proyectado') is not None)
            
            QMessageBox.information(
                parent_widget,
                "✅ Exportación Exitosa",
                f"Mediciones de Ancho Proyectado exportadas a:\n{file_path}\n\n"
                f"📊 Resumen:\n"
                f"• Total de perfiles: {total_rows}\n"
                f"• Con Ancho Proyectado: {rows_with_data}"
            )
        else:
            rows_with_crown = sum(1 for row in export_data 
                                if row.get('Cota_Coronamiento') is not None)
            rows_with_width = sum(1 for row in export_data 
                                if row.get('Ancho') is not None)
            rows_with_lama = sum(1 for row in export_data 
                               if row.get('Lama') is not None)
            rows_with_revancha = sum(1 for row in export_data 
                                   if row.get('Revancha') is not None)
            
            QMessageBox.information(
                parent_widget,
                "✅ Exportación Exitosa",
                f"Mediciones exportadas correctamente a:\n{file_path}\n\n"
                f"📊 Resumen:\n"
                f"• Total de perfiles: {total_rows}\n"
                f"• Con Cota Coronamiento: {rows_with_crown}\n"
                f"• Con Ancho: {rows_with_width}\n"
                f"• Con LAMA: {rows_with_lama}\n"
                f"• Con Revancha: {rows_with_revancha}"
            )
