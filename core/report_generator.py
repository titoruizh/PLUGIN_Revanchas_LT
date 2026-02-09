# -*- coding: utf-8 -*-
"""
Report Generator Module
=======================
Generates PDF reports with longitudinal charts and measurement tables.

This module was extracted from profile_viewer_dialog.py for better modularity.
"""

import os
import math
import tempfile
from typing import Dict, List, Optional, Tuple, Any

try:
    from matplotlib.figure import Figure
except ImportError:
    Figure = None

from qgis.core import (
    QgsProject,
    QgsPrintLayout,
    QgsLayoutExporter,
    QgsLayoutItemPicture,
    QgsLayoutItemHtml,
    QgsLayoutFrame,
    QgsLayoutSize,
    QgsLayoutPoint,
    QgsUnitTypes,
    QgsReadWriteContext
)
from qgis.PyQt.QtXml import QDomDocument
from qgis.PyQt.QtWidgets import QApplication, QMessageBox

import logging
logger = logging.getLogger(__name__)

# Import Manager for Chart Data
try:
    from .geomembrane_manager import GeomembraneManager
except ImportError:
    GeomembraneManager = None


class ReportGenerator:
    """
    Handles PDF report generation with charts, tables, and alert screenshots.
    
    Attributes:
        plugin_dir: Path to the plugin directory for locating templates.
        profiles_data: List of profile dictionaries with elevation data.
        saved_measurements: Dictionary of measurements keyed by PK.
        operation_mode: Current operation mode ('revancha' or 'ancho_proyectado').
    """
    
    def __init__(self, plugin_dir: str, profiles_data: List[Dict], 
                 saved_measurements: Dict, operation_mode: str = "revancha"):
        """
        Initialize the ReportGenerator.
        
        Args:
            plugin_dir: Path to the plugin directory.
            profiles_data: List of profile data dictionaries.
            saved_measurements: Dictionary of saved measurements by PK.
            operation_mode: Current operation mode.
        """
        self.plugin_dir = plugin_dir
        self.profiles_data = profiles_data
        self.saved_measurements = saved_measurements
        self.operation_mode = operation_mode
        self.template_path = os.path.join(plugin_dir, 'report_template.qpt')
    
    @staticmethod
    def parse_pk(pk_str: str) -> float:
        """
        Convert PK string (e.g., '0+100') to float value.
        
        Args:
            pk_str: PK string in format 'X+XXX' or numeric.
            
        Returns:
            Float representation of the PK value.
        """
        try:
            if '+' in str(pk_str):
                parts = str(pk_str).split('+')
                return float(parts[0]) * 1000 + float(parts[1])
            return float(pk_str)
        except (ValueError, TypeError):
            return 0.0
    
    def generate_longitudinal_chart(self, output_path: str) -> bool:
        """
        Generate longitudinal profile chart (Crown & Lama) and save as image.
        
        Args:
            output_path: File path to save the chart image.
            
        Returns:
            True if chart was generated successfully, False otherwise.
        """
        # Matplotlib check
        if Figure is None:
            logger.error("Matplotlib not available for chart generation")
            return False
            
        try:
            # Define normalization helper
            def normalize_pk_key(val):
                try:
                    # Use existing parse_pk to get float
                    v = self.parse_pk(str(val))
                    # Format as simple 0+000 (standard for matching)
                    km = int(v // 1000)
                    m = int(v % 1000)
                    return f"{km}+{m:03d}"
                except:
                    return str(val).strip()

            # 🆕 Load Geomembrane Data for Trend Line
            geo_data = {}
            if GeomembraneManager and self.profiles_data:
                try:
                    # Get wall name from first profile (propagated from fix)
                    wall_name = self.profiles_data[0].get('wall_name', "Muro 1")
                    geo_mgr = GeomembraneManager(self.plugin_dir)
                    # Load data for this wall
                    raw_data = geo_mgr.get_all_data(wall_name)
                    
                    # Create NORMALIZED lookup {pk_norm: elevation}
                    # We normalize keys from CSV to ensure match with measurements
                    geo_data = {}
                    for k, v in raw_data.items():
                        norm_key = normalize_pk_key(k)
                        geo_data[norm_key] = v
                        
                    logger.info(f"Loaded {len(geo_data)} geomembrane points for chart ({wall_name})")
                    if geo_data:
                        logger.info(f"Sample normalized keys: {list(geo_data.keys())[:3]}")
                except Exception as e:
                    logger.error(f"Error loading geomembrane for chart: {e}")
            
            # Initialize data container (Fixed: was deleted accidentally)
            data_points = []
            
            for pk, measurements in self.saved_measurements.items():
                # Crown
                crown_y = None
                if 'crown' in measurements:
                    crown_y = measurements['crown']['y']
                
                # Lama
                lama_y = None
                if 'lama' in measurements:
                    lama_y = measurements['lama']['y']
                elif 'lama_selected' in measurements:
                    lama_y = measurements['lama_selected']['y']
                else:
                    # Try to find auto lama from profile data
                    for p in self.profiles_data:
                        if str(p.get('pk')) == str(pk) or str(p.get('PK')) == str(pk):
                            if p.get('lama_points'):
                                lama_y = p['lama_points'][0]['elevation']
                            break
                
                pk_float = self.parse_pk(str(pk))
                
                # Get Geo value with NORMALIZED key
                pk_norm = normalize_pk_key(pk)
                geo_y = geo_data.get(pk_norm)
                
                # Partial fallback if exact normalized match fails (e.g. integer vs float)
                if geo_y is None:
                    # Try with float representation string if normalized failed?
                    pass
                
                data_points.append({
                    'pk_str': str(pk),
                    'pk_val': pk_float,
                    'crown': crown_y,
                    'lama': lama_y,
                    'geo': geo_y
                })
            
            # Sort by PK
            data_points.sort(key=lambda x: x['pk_val'])
            
            if not data_points:
                return False
            
            # 2. Prepare plot data
            valid_crowns = [(d['pk_val'], d['crown']) for d in data_points if d['crown'] is not None]
            valid_lamas = [(d['pk_val'], d['lama']) for d in data_points if d['lama'] is not None]
            valid_geos = [(d['pk_val'], d['geo']) for d in data_points if d['geo'] is not None]
            
            # DEBUG: Diagnostic Popup if Geodata missing or not matched
            if not valid_geos:
                wall_code = geo_mgr._normalize_wall_code(wall_name) if GeomembraneManager else "None"
                
                # Case 1: No data found for this wall in CSV
                if len(geo_data) == 0:
                    available_walls = list(geo_mgr.data.keys()) if geo_mgr and hasattr(geo_mgr, 'data') else []
                    msg = (f"DEBUG GEOMEMBRANA:\n"
                           f"Perfil: '{wall_name}' (Code: {wall_code})\n"
                           f"NO se encontraron datos para este muro en el CSV.\n\n"
                   f"Muros detectados en CSV: {available_walls}\n"
                           f"Asegúrese de que el CSV tenga filas para '{wall_name}' (o su alias 'Oeste'/'Este').")
                    logger.warning(msg)

                # Case 2: Data exists but no match
                elif len(geo_data) > 0:
                    sample_csv = list(geo_data.keys())[0] if geo_data else "None"
                    sample_meas = list(self.saved_measurements.keys())[0] if self.saved_measurements else "None"
                    if sample_meas != "None":
                        sample_meas = normalize_pk_key(sample_meas)
                        
                    msg = (f"DEBUG GEOMEMBRANA (MISMATCH):\n"
                           f"Muro Profile: '{wall_name}'\n"
                           f"Puntos CSV Cargados: {len(geo_data)}\n"
                           f"Puntos Matched: 0\n"
                           f"Ejemplo Key CSV (Norm): '{sample_csv}'\n"
                           f"Ejemplo Key Medición (Norm): '{sample_meas}'")
                    logger.warning(msg)
            
            # 3. Create Figure
            fig = Figure(figsize=(20, 8), dpi=100)
            ax = fig.add_subplot(111)
            
            # Plot Crown (Red)
            if valid_crowns:
                vx, vy = zip(*valid_crowns)
                ax.plot(vx, vy, 'o-', color='red', linewidth=2, markersize=6, label='Coronamiento')
            
            # Plot Lama (Green)
            if valid_lamas:
                vx, vy = zip(*valid_lamas)
                ax.plot(vx, vy, 'o-', color='green', linewidth=2, markersize=6, label='Lama')

            # 🆕 Plot Geomembrane (Blue Trend Line)
            if valid_geos:
                vx, vy = zip(*valid_geos)
                # Use dashed line for trend
                ax.plot(vx, vy, '--', color='blue', linewidth=2, label='Geomembrana')
            
            # Styling
            ax.set_title("Perfil Longitudinal (Tendencia)", fontsize=16, fontweight='bold', pad=20)
            ax.set_xlabel("PK (Progresiva)", fontsize=12)
            ax.set_ylabel("Elevación (m)", fontsize=12)
            ax.grid(True, which='both', linestyle='--', alpha=0.7)
            ax.minorticks_on()
            ax.grid(which='minor', linestyle=':', alpha=0.3)
            ax.legend(loc='best', fontsize=12)
            
            fig.tight_layout()
            fig.savefig(output_path)
            return True
            
        except Exception as e:
            logger.error(f"Error generating longitudinal chart: {e}")
            return False
    
    def generate_detail_html_table(self) -> str:
        """
        Generate HTML for Table 1: Detailed Measurements.
        
        Returns:
            HTML string for the detailed measurements table.
        """
        # CSS Style (Blue Header)
        style = """
        <style>
            table { border-collapse: collapse; width: 100%; font-family: Arial, sans-serif; font-size: 10px; }
            th { background-color: #2b579a; color: white; padding: 6px; border: 1px solid #ddd; text-align: left; }
            td { padding: 5px; border: 1px solid #ddd; text-align: left; }
            tr:nth-child(even) { background-color: #f8f9fa; }
            .alert { color: red; font-weight: bold; }
        </style>
        """
        
        html = [style, "<table>"]
        
        # Headers
        headers = ["Sector", "PK", "Coronamiento", "Revancha", "Lama", "Ancho", "Geomembrana", "Dist. G-L", "Dist. G-C"]
        html.append("<thead><tr>")
        for h in headers:
            html.append(f"<th>{h}</th>")
        html.append("</tr></thead>")
        
        html.append("<tbody>")
        
        # Data Rows (Sorted by PK)
        sorted_profiles = sorted(self.profiles_data, key=lambda x: self.parse_pk(str(x.get('pk', '0'))))
        
        for profile in sorted_profiles:
            pk = str(profile.get('pk', ''))
            measurements = self.saved_measurements.get(pk, {})
            
            # 1. Values
            crown_val = measurements.get('crown', {}).get('y')
            lama_val = measurements.get('lama', {}).get('y')
            # Auto lama fallback
            if lama_val is None and profile.get('lama_points'):
                lama_val = profile['lama_points'][0]['elevation']
            
            revancha_val = None
            if crown_val is not None and lama_val is not None:
                revancha_val = crown_val - lama_val
            
            width_val = measurements.get('width', {}).get('distance')
            
            # Geomembrane placeholders
            geomembrane_val = 0.00
            dist_gl_val = 0.00
            dist_gc_val = 0.00
            
            # 2. Formatting & Alerts
            sector_txt = "Sector 1"  # Default
            pk_txt = pk
            
            coronamiento_txt = f"{crown_val:.3f}" if crown_val is not None else "-"
            
            revancha_cls = "alert" if (revancha_val is not None and revancha_val < 3.0) else ""
            revancha_txt = f"{revancha_val:.3f}" if revancha_val is not None else "-"
            if revancha_cls:
                revancha_txt = f"<span class='{revancha_cls}'>{revancha_txt}</span>"
            
            lama_txt = f"{lama_val:.3f}" if lama_val is not None else "-"
            
            ancho_cls = "alert" if (width_val is not None and width_val < 15.0) else ""
            ancho_txt = f"{width_val:.3f}" if width_val is not None else "-"
            if ancho_cls:
                ancho_txt = f"<span class='{ancho_cls}'>{ancho_txt}</span>"
            
            # Placeholders
            geo_txt = "0.000"
            dgl_txt = "0.000"
            dgc_txt = "0.000"
            
            # Row Construction
            html.append("<tr>")
            html.append(f"<td>{sector_txt}</td>")
            html.append(f"<td>{pk_txt}</td>")
            html.append(f"<td>{coronamiento_txt}</td>")
            html.append(f"<td>{revancha_txt}</td>")
            html.append(f"<td>{lama_txt}</td>")
            html.append(f"<td>{ancho_txt}</td>")
            html.append(f"<td>{geo_txt}</td>")
            html.append(f"<td>{dgl_txt}</td>")
            html.append(f"<td>{dgc_txt}</td>")
            html.append("</tr>")
        
        html.append("</tbody></table>")
        return "".join(html)
    
    def generate_summary_html_table(self) -> str:
        """
        Generate HTML for Table 2: Summary Measurements (Min/Max by Sector).
        
        Returns:
            HTML string for the summary table.
        """
        # Find Min/Max
        min_rev, max_rev = (None, None), (None, None)  # (Value, PK)
        min_ancho, max_ancho = (None, None), (None, None)
        min_crown, max_crown = (None, None), (None, None)
        
        for profile in self.profiles_data:
            pk = str(profile.get('pk', ''))
            measurements = self.saved_measurements.get(pk, {})
            
            # Revancha
            crown_val = measurements.get('crown', {}).get('y')
            lama_val = measurements.get('lama', {}).get('y')
            if lama_val is None and profile.get('lama_points'):
                lama_val = profile['lama_points'][0]['elevation']
            
            revancha_val = None
            if crown_val is not None and lama_val is not None:
                revancha_val = crown_val - lama_val
                
                if min_rev[0] is None or revancha_val < min_rev[0]:
                    min_rev = (revancha_val, pk)
                if max_rev[0] is None or revancha_val > max_rev[0]:
                    max_rev = (revancha_val, pk)
            
            # Ancho
            width_val = measurements.get('width', {}).get('distance')
            if width_val is not None:
                if min_ancho[0] is None or width_val < min_ancho[0]:
                    min_ancho = (width_val, pk)
                if max_ancho[0] is None or width_val > max_ancho[0]:
                    max_ancho = (width_val, pk)
            
            # Crown
            if crown_val is not None:
                if min_crown[0] is None or crown_val < min_crown[0]:
                    min_crown = (crown_val, pk)
                if max_crown[0] is None or crown_val > max_crown[0]:
                    max_crown = (crown_val, pk)
        
        # Construct HTML
        style = """
        <style>
            .summary-table { border-collapse: collapse; width: 100%; font-family: Arial, sans-serif; font-size: 10px; margin-top: 20px; }
            .summary-table th { background-color: #1a428a; color: white; padding: 8px; border: 1px solid #ddd; text-align: center; }
            .summary-table td { padding: 8px; border: 1px solid #ddd; text-align: center; }
            .summary-table tr:nth-child(even) { background-color: #f8f9fa; }
            .sub-header { background-color: #2b579a; font-size: 9px; }
            .sector-col { font-weight: bold; color: #2b579a; }
        </style>
        """
        
        html = [style, "<table class='summary-table'>"]
        
        # Main Headers
        html.append("<thead>")
        html.append("<tr>")
        html.append("<th rowspan='2' style='vertical-align: middle;'>SECTOR</th>")
        html.append("<th colspan='2'>REVANCHA</th>")
        html.append("<th colspan='2'>ANCHO</th>")
        html.append("<th colspan='2'>CORONAMIENTO</th>")
        html.append("</tr>")
        
        # Sub Headers
        html.append("<tr class='sub-header'>")
        for _ in range(3):
            html.append("<th>MIN (PK)</th>")
            html.append("<th>MAX (PK)</th>")
        html.append("</tr>")
        html.append("</thead>")
        
        html.append("<tbody>")
        
        def fmt(val_tuple):
            val, pk = val_tuple
            if val is None:
                return "-"
            return f"{val:.3f} ({pk})"
        
        html.append("<tr>")
        html.append("<td class='sector-col'>Sector 1</td>")
        
        html.append(f"<td>{fmt(min_rev)}</td>")
        html.append(f"<td>{fmt(max_rev)}</td>")
        
        html.append(f"<td>{fmt(min_ancho)}</td>")
        html.append(f"<td>{fmt(max_ancho)}</td>")
        
        html.append(f"<td>{fmt(min_crown)}</td>")
        html.append(f"<td>{fmt(max_crown)}</td>")
        
        html.append("</tr>")
        html.append("</tbody></table>")
        
        return "".join(html)
    
    def detect_alert_profiles(self) -> List[str]:
        """
        Detect profiles that have alerts (Revancha < 3 or Width < 15).
        
        Returns:
            List of PK strings for profiles with alerts.
        """
        alert_profiles = []
        
        for profile in self.profiles_data:
            pk = str(profile.get('pk', ''))
            measurements = self.saved_measurements.get(pk, {})
            
            # Check Revancha < 3
            crown_val = measurements.get('crown', {}).get('y')
            lama_val = measurements.get('lama', {}).get('y')
            if lama_val is None and profile.get('lama_points'):
                lama_val = profile['lama_points'][0]['elevation']
            
            revancha_alert = False
            if crown_val is not None and lama_val is not None:
                if (crown_val - lama_val) < 3.0:
                    revancha_alert = True
            
            # Check Width < 15
            width_val = measurements.get('width', {}).get('distance')
            width_alert = False
            if width_val is not None and width_val < 15.0:
                width_alert = True
            
            if revancha_alert or width_alert:
                alert_profiles.append(pk)
        
        return alert_profiles
    
    def load_template(self, layout: QgsPrintLayout) -> bool:
        """
        Load the QPT template into the given layout.
        
        Args:
            layout: QgsPrintLayout instance to load template into.
            
        Returns:
            True if template loaded successfully, False otherwise.
        """
        if not os.path.exists(self.template_path):
            logger.error(f"Template not found: {self.template_path}")
            return False
        
        try:
            with open(self.template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
                doc = QDomDocument()
                doc.setContent(template_content)
                layout.loadFromTemplate(doc, QgsReadWriteContext())
            return True
        except Exception as e:
            logger.error(f"Error loading template: {e}")
            return False
