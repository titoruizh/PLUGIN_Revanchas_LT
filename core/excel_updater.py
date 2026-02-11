# -*- coding: utf-8 -*-
import os
import shutil
import datetime
import openpyxl
from openpyxl.chart import Reference

class ExcelUpdater:
    """
    Handles updating of the Excel template with new measurement data.
    Preserves existing formulas and formatting.
    """

    # Configuration for Muro Principal (MP)
    # PK at Column A (1-based index = 1)
    # Rows 13 to 85
    WALL_CONFIG = {
        "Muro Principal": {
            "sheet_name": "REV_MP", # User specified
            "rows_range": (13, 85),
            "pk_col_idx": 9, # Column I (9) based on screenshot (0+000.00 is in Col I)
            
            # Source (Current) -> Target (Previous)
            "shift_map": [
                # (Source Letter, Target Letter)
                ("C", "Q"), # Coronamiento (Value) -> Previous Crow (Static)
                ("F", "O"), # Lama (Value) -> Previous Lama (Static)
                ("E", "M"), # Revancha (Formula Result) -> Previous Rev (Static)
            ],
            
            # Data to write (New Values) -> Target Column
            "write_map": {
                "crown": "C", # Cota Coronamiento
                "lama": "F",  # Cota Lama
                "width": "H", # Ancho
                # Revancha is calculated by Excel formula in E, do not write
            },
            
            "date_cell": "F6",
            "chart_name_contains": "Gráfico 1", # To identify the chart
            "chart_title_prefix": "Coronamiento vs Lama MP "
        },
        
        "Muro Oeste": {
            "sheet_name": "Hoja1",
            "rows_range": (10, 45),
            "pk_col_idx": 9, # Column I (9)
            
            # Source (Current) -> Target (Previous)
            "shift_map": [
                ("B", "Q"), # Coronamiento
                ("F", "O"), # Lama
                ("E", "M"), # Revancha
            ],
            
            # Data to write (New Values) -> Target Column
            "write_map": {
                "crown": "B", # Cota Coronamiento
                "lama": "F",  # Cota Lama
                "width": "H", # Ancho
            },
            
            "date_cell": "F6",
            "chart_name_contains": "Gráfico 8", 
            "chart_title_prefix": "Coronamiento vs Lama MO "
        },

        "Muro Este": {
            "sheet_name": "Hoja1",
            "rows_range": (13, 41),
            "pk_col_idx": 9, # Column I (9)
            
            # Source (Current) -> Target (Previous)
            "shift_map": [
                ("C", "Q"), # Coronamiento
                ("F", "O"), # Lama
                ("E", "M"), # Revancha
            ],
            
            # Data to write (New Values) -> Target Column
            "write_map": {
                "crown": "C", # Cota Coronamiento
                "lama": "F",  # Cota Lama
                "width": "H", # Ancho
            },
            
            "date_cell": "F6",
            "chart_name_contains": "Gráfico 1", 
            "chart_title_prefix": "Coronamiento vs Lama ME "
        }
    }

    def __init__(self, excel_path):
        self.excel_path = excel_path

    def update_wall_data(self, wall_name, measurements_data, dem_filename):
        """
        Main method to update the Excel file.
        :param wall_name: Name of the wall (e.g. "Muro Principal")
        :param measurements_data: List of dicts with measurements [{'pk':..., 'crown':..., 'lama':..., 'width':...}]
        :param dem_filename: Filename of the DEM to extract date
        :return: (bool, message)
        """
        try:
            if not os.path.exists(self.excel_path):
                return False, f"El archivo Excel no existe: {self.excel_path}"

            # 1. Load Workbook (Formulas) - To Write
            wb = openpyxl.load_workbook(self.excel_path, data_only=False)
            
            # 1b. Load Workbook (Values) - To Read Shifting Data
            # We need this to get the calculated result of formulas (like Revancha)
            wb_values = openpyxl.load_workbook(self.excel_path, data_only=True)
            
            # 2. Get Configuration
            # Normalize wall name / Handle aliases
            target_key = None
            wall_lower = wall_name.lower()
            
            if "muro 1" in wall_lower or "principal" in wall_lower:
                target_key = "Muro Principal"
            elif "muro 2" in wall_lower or "oeste" in wall_lower or "mo" in wall_lower:
                target_key = "Muro Oeste"
            elif "muro 3" in wall_lower or "este" in wall_lower or "me" in wall_lower:
                target_key = "Muro Este"
                
            config = self.WALL_CONFIG.get(target_key)
            
            if not config:
                # Fallback to fuzzy match
                for key in self.WALL_CONFIG:
                    if key.lower() in wall_lower:
                        config = self.WALL_CONFIG[key]
                        break
            
            if not config:
                return False, f"No hay configuración definida para el muro: {wall_name} (Normalizado: {target_key})"

            # 3. Get Sheet
            # Try to find sheet by name
            sheet = None
            sheet_values = None
            
            # Explicit config check first
            if config["sheet_name"] in wb.sheetnames:
                 sheet = wb[config["sheet_name"]]
                 sheet_values = wb_values[config["sheet_name"]]
            else:
                # Fallback search strategy
                search_terms = ["rev_mp", "rev", "muro principal", "muro 1", "mp", "principal"]
                found_sheet_name = None
                
                # Check each sheet name against search terms
                # Prioritize EXACT matches first? No, case insensitive contains
                for term in search_terms:
                    for sname in wb.sheetnames:
                        if term in sname.lower():
                            found_sheet_name = sname
                            break
                    if found_sheet_name:
                        break
                
                if found_sheet_name:
                    sheet = wb[found_sheet_name]
                    sheet_values = wb_values[found_sheet_name]
                else:
                    # List available sheets for error message
                    available = ", ".join(wb.sheetnames)
                    return False, f"No se encontró hoja para '{wall_name}'. Busqué: {search_terms}. Hojas disponibles: [{available}]"

            print(f"   📂 Usando hoja: {sheet.title}")

            # 4. Extract Date from DEM Filename
            # Format: DEM_MP_250101 -> 01/01/2025
            date_str = self._extract_date_from_filename(dem_filename)
            print(f"   📅 Fecha extraída: {date_str}")

            # 5. Shift Data (Current -> Previous)
            # Read from sheet_values (calculated), Write to sheet (formulas preserved where needed)
            self._shift_data(sheet, sheet_values, config)

            # 6. Write New Data
            # Pass sheet_values to read PKs reliably
            self._write_new_data(sheet, sheet_values, config, measurements_data)

            # 7. Update Date Cell
            # Format: dd-mm-yyyy
            self._update_date_cell(sheet, config, date_str)

            # 8. Update Chart Title
            self._update_chart_title(sheet, config, date_str)
            
            # Close value workbook
            wb_values.close()

            # 9. Save
            # Create backup first?
            backup_path = self.excel_path.replace(".xlsx", "_backup.xlsx")
            shutil.copy2(self.excel_path, backup_path)
            
            wb.save(self.excel_path)
            return True, f"Datos exportados exitosamente.\nFecha: {date_str}\nBackup creado: {os.path.basename(backup_path)}"

        except Exception as e:
            import traceback
            traceback.print_exc()
            return False, str(e)

    def _extract_date_from_filename(self, filename):
        """
        Extract date from format *_YYMMDD*
        Example: DEM_MP_250101 -> 01/01/2025
        """
        try:
            # Remove extension
            name = os.path.splitext(os.path.basename(filename))[0]
            parts = name.split('_')
            
            # Look for 6 digit part
            date_part = None
            for part in parts:
                if len(part) == 6 and part.isdigit():
                    date_part = part
                    break
            
            if date_part:
                yy = int(date_part[0:2])
                mm = int(date_part[2:4])
                dd = int(date_part[4:6])
                
                # Assume 20xx
                full_year = 2000 + yy
                return f"{dd:02d}-{mm:02d}-{full_year}"
            
            return datetime.datetime.now().strftime("%d-%m-%Y")
        except:
            return datetime.datetime.now().strftime("%d-%m-%Y")

    def _shift_data(self, sheet_target, sheet_source, config):
        """
        Move data from Current columns to Previous columns.
        Read from Source (Values), Write to Target (Static).
        """
        start_row, end_row = config["rows_range"]
        
        for src_col_output, tgt_col_output in config["shift_map"]:
            # Iterate rows
            for row in range(start_row, end_row + 1):
                # Read from Source (Values)
                src_cell = f"{src_col_output}{row}"
                tgt_cell = f"{tgt_col_output}{row}"
                
                val = sheet_source[src_cell].value
                
                # Write to Target (Previous)
                # Ensure we write values, not formulas
                if val is not None:
                     sheet_target[tgt_cell].value = val

    def _write_new_data(self, sheet, sheet_values, config, measurements):
        """
        Write new measurements matching PK.
        Uses sheet_values to read PK reliably.
        """
        start_row, end_row = config["rows_range"]
        pk_col_idx = config["pk_col_idx"]
        
        # Create a lookup map for measurements: PK -> Data
        # Use robust normalization
        meas_map = {}
        print("   🔍 Procesando mediciones de la App:")
        for m in measurements:
            pk_raw = m.get('PK')
            pk_val = self._normalize_pk(pk_raw)
            if pk_val is not None:
                meas_map[pk_val] = m
                print(f"      OK: '{pk_raw}' -> {pk_val:.2f}")
            else:
                print(f"      ERR: No se pudo normalizar PK '{pk_raw}'")

        print(f"   📊 Total mediciones válidas para exportar: {len(meas_map)}")

        # Iterate rows in Excel to find PKs and write data
        count_updated = 0
        for row in range(start_row, end_row + 1):
            # Read PK from Excel (VALUES sheet to handle formulas/formatting)
            # Column I is index 9
            pk_cell = sheet_values.cell(row=row, column=pk_col_idx)
            pk_raw = pk_cell.value
            
            pk_float = self._normalize_pk(pk_raw)
            
            if pk_float is not None:
                # Find closest PK in measurements
                # Tolerance 0.1m (10cm)
                found_data = None
                for m_pk, m_data in meas_map.items():
                    if abs(m_pk - pk_float) < 0.15: # 15cm tolerance just in case
                        found_data = m_data
                        break
                
                if found_data:
                    count_updated += 1
                    # Write Crown
                    if "crown" in config["write_map"] and found_data.get('Cota_Coronamiento') is not None:
                        col_letter = config["write_map"]["crown"]
                        sheet[f"{col_letter}{row}"].value = float(found_data['Cota_Coronamiento'])
                        
                    # Write Lama
                    if "lama" in config["write_map"] and found_data.get('Lama') is not None:
                        col_letter = config["write_map"]["lama"]
                        sheet[f"{col_letter}{row}"].value = float(found_data['Lama'])
                        
                    # Write Width
                    if "width" in config["write_map"] and found_data.get('Ancho') is not None:
                        col_letter = config["write_map"]["width"]
                        sheet[f"{col_letter}{row}"].value = float(found_data['Ancho'])
                    
                    print(f"      MATCH: Row {row} (PK {pk_float:.2f}) updated")

        print(f"   ✅ Filas actualizadas en Excel: {count_updated}")

    def _normalize_pk(self, value):
        """
        Convert various PK formats to float distance (meters).
        - 120.5 -> 120.5
        - "120.5" -> 120.5
        - "0+120.5" -> 120.5
        - "1+200" -> 1200.0
        """
        if value is None:
            return None
            
        try:
            # If already float/int
            if isinstance(value, (int, float)):
                return float(value)
            
            s = str(value).strip().replace(',', '.')
            
            if '+' in s:
                parts = s.split('+')
                if len(parts) == 2:
                    km = float(parts[0])
                    m = float(parts[1])
                    return km * 1000.0 + m
            
            return float(s)
        except:
            return None

    def _update_date_cell(self, sheet, config, date_str):
        if "date_cell" in config:
            sheet[config["date_cell"]].value = date_str

    def _update_chart_title(self, sheet, config, date_str):
        if "chart_name_contains" not in config:
            return
            
        print(f"   📊 Intentando actualizar título de gráfico...")
        try:
             # Iterate all charts
             count = 0
             for chart in sheet._charts:
                 # Try to force set title
                 new_title = config["chart_title_prefix"] + date_str
                 
                 # Debug info
                 try:
                     old_title = "Unknown"
                     if chart.title:
                         if hasattr(chart.title, "tx") and hasattr(chart.title.tx, "rich"):
                             old_title = "RichText"
                         elif hasattr(chart.title, "text"):
                             old_title = chart.title.text
                         else:
                             old_title = str(chart.title)
                     print(f"      Chart found. Old Title: {old_title}")
                 except:
                     pass

                 try:
                     # 1. Direct assignment (Best for simple titles)
                     chart.title = new_title
                     print(f"      ✅ Título actualizado a: {new_title}")
                     count += 1
                 except Exception as e:
                     print(f"      ⚠️ Falló asignación directa: {e}")
                     # 2. Try to navigate object if it exists?
                     # Openpyxl handling of titles is inconsistent across versions/chart types
                     pass
             
             if count == 0:
                 print("   ⚠️ No se encontraron gráficos iterables en sheet._charts")
                 
        except Exception as e:
            print(f"   ⚠️ Error general actualizando gráfico: {e}")
