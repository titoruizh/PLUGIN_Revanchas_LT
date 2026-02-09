# -*- coding: utf-8 -*-
"""
Data Exporter Module
====================
Handles exporting measurement data to CSV and other formats.

This module was extracted from profile_viewer_dialog.py for better modularity.
"""

import os
import csv
from typing import Dict, List, Optional, Any

import logging
logger = logging.getLogger(__name__)


class DataExporter:
    """
    Handles exporting measurement data to various formats (CSV, etc.).
    
    Attributes:
        operation_mode: Current operation mode ('revancha' or 'ancho_proyectado').
    """
    
    def __init__(self, operation_mode: str = "revancha"):
        """
        Initialize the DataExporter.
        
        Args:
            operation_mode: Current operation mode.
        """
        self.operation_mode = operation_mode
    
    def write_measurements_csv(self, file_path: str, export_data: List[Dict]) -> bool:
        """
        Write measurements data to CSV file.
        
        Args:
            file_path: Path to the output CSV file.
            export_data: List of dictionaries with measurement data.
            
        Returns:
            True if export was successful, False otherwise.
        """
        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                if self.operation_mode == "ancho_proyectado":
                    # Columns for Ancho Proyectado
                    fieldnames = ['PK', 'Ancho_Proyectado']
                else:
                    # Columns for Revancha (original)
                    fieldnames = ['PK', 'Cota_Coronamiento', 'Revancha', 'Lama', 'Ancho']
                
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                # Write header
                writer.writeheader()
                
                # Write data
                for row_data in export_data:
                    # Format null values as empty strings
                    formatted_row = {}
                    for key in fieldnames:
                        value = row_data.get(key)
                        if value is None:
                            formatted_row[key] = ''
                        elif isinstance(value, float):
                            formatted_row[key] = f"{value:.3f}"  # 3 decimals
                        else:
                            formatted_row[key] = value
                    
                    writer.writerow(formatted_row)
            
            logger.info(f"CSV exported successfully to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error writing CSV: {e}")
            return False
    
    def prepare_export_data(self, profiles_data: List[Dict], 
                           saved_measurements: Dict) -> List[Dict]:
        """
        Prepare measurement data for export based on operation mode.
        
        Args:
            profiles_data: List of profile data dictionaries.
            saved_measurements: Dictionary of saved measurements by PK.
            
        Returns:
            List of dictionaries ready for export.
        """
        export_data = []
        
        for profile in profiles_data:
            pk = profile.get('pk', profile.get('PK', ''))
            pk_str = str(pk)
            measurements = saved_measurements.get(pk_str, {})
            
            if self.operation_mode == "ancho_proyectado":
                # Ancho Proyectado mode
                ancho_proy = None
                if 'width' in measurements:
                    ancho_proy = measurements['width'].get('distance')
                
                export_data.append({
                    'PK': pk_str,
                    'Ancho_Proyectado': ancho_proy
                })
            else:
                # Revancha mode
                crown_y = None
                if 'crown' in measurements:
                    crown_y = measurements['crown'].get('y')
                
                lama_y = None
                if 'lama' in measurements:
                    lama_y = measurements['lama'].get('y')
                elif 'lama_selected' in measurements:
                    lama_y = measurements['lama_selected'].get('y')
                elif profile.get('lama_points'):
                    lama_y = profile['lama_points'][0]['elevation']
                
                revancha = None
                if crown_y is not None and lama_y is not None:
                    revancha = crown_y - lama_y
                
                width = None
                if 'width' in measurements:
                    width = measurements['width'].get('distance')
                
                export_data.append({
                    'PK': pk_str,
                    'Cota_Coronamiento': crown_y,
                    'Revancha': revancha,
                    'Lama': lama_y,
                    'Ancho': width
                })
        
        return export_data
    
    def get_export_statistics(self, export_data: List[Dict]) -> Dict[str, Any]:
        """
        Calculate statistics from export data for summary display.
        
        Args:
            export_data: List of export data dictionaries.
            
        Returns:
            Dictionary with statistics (counts, alerts, etc.).
        """
        stats = {
            'total_profiles': len(export_data),
            'profiles_with_data': 0,
            'revancha_alerts': 0,
            'width_alerts': 0
        }
        
        for row in export_data:
            if self.operation_mode == "ancho_proyectado":
                if row.get('Ancho_Proyectado') is not None:
                    stats['profiles_with_data'] += 1
                    if row['Ancho_Proyectado'] < 15.0:
                        stats['width_alerts'] += 1
            else:
                if row.get('Revancha') is not None:
                    stats['profiles_with_data'] += 1
                    if row['Revancha'] < 3.0:
                        stats['revancha_alerts'] += 1
                if row.get('Ancho') is not None and row['Ancho'] < 15.0:
                    stats['width_alerts'] += 1
        
        return stats
