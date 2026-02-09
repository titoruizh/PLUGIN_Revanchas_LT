# -*- coding: utf-8 -*-
import os
import csv
from collections import defaultdict

class GeomembraneManager:
    """
    Gestor de datos de elevación de geomembrana desde CSV.
    Soporta nombres: Principal, Oeste, Este.
    Permite agregar (append) datos faltantes sin sobrescribir.
    """
    
    def __init__(self, plugin_dir):
        self.plugin_dir = plugin_dir
        self.base_dir = os.path.join(plugin_dir, "INFO BASE REPORTE")
        if not os.path.exists(self.base_dir):
            try: os.makedirs(self.base_dir, exist_ok=True)
            except: pass
            
        self.csv_path = os.path.join(self.base_dir, "geomembrana_bases.csv")
        self.data = defaultdict(dict) # { "MP": { "0+100": 2500.5 } }
        self._load_data()
        
    def _normalize_wall_code(self, wall_name):
        """Conversión interna a MP/MO/ME para lógica."""
        w = wall_name.upper()
        if "OESTE" in w or "MURO 2" in w: return "MO"
        if "ESTE" in w or "MURO 3" in w: return "ME"
        # "Principal" or "Muro 1" -> MP
        return "MP" 

    def get_display_name(self, wall_name):
        """Conversión para escribir en CSV (Principal/Oeste/Este)."""
        code = self._normalize_wall_code(wall_name)
        if code == "MO": return "Oeste"
        if code == "ME": return "Este"
        return "Principal"

    def _load_data(self):
        """Recarga datos del CSV."""
        self.data = defaultdict(dict)
        if not os.path.exists(self.csv_path):
            return
            
        try:
            with open(self.csv_path, 'r', encoding='utf-8') as f:
                # Detect delimiter
                line1 = f.readline()
                delimiter = ';' if ';' in line1 else ','
                f.seek(0)
                
                reader = csv.reader(f, delimiter=delimiter)
                header = next(reader, None)
                for row in reader:
                    if len(row) < 3: continue
                    wall_raw = row[0].strip()
                    wall_code = self._normalize_wall_code(wall_raw)
                    pk = row[1].strip()
                    try:
                        cota = float(row[2].strip().replace(',', '.'))
                        self.data[wall_code][pk] = cota
                    except: continue
        except Exception as e:
            print(f"Error cargando geomembrana: {e}")

    def ensure_data(self, wall_name, pks):
        """
        Verifica si los PKs del muro dado existen en la base de datos.
        Si faltan, los AGREGA al final del archivo CSV.
        Retorna True si se agregaron datos (requiere reload/aviso).
        """
        self._load_data() # Asegurar estado fresco
        
        # Filter blacklist PKS
        # User requested to remove specific invalid PKs like 690
        pks = [pk for pk in pks if str(pk) not in ['0+690', '690']]
        
        wall_code = self._normalize_wall_code(wall_name)
        display_name = self.get_display_name(wall_name)
        
        start_new_file = not os.path.exists(self.csv_path)
        
        missing_pks = []
        if wall_code not in self.data:
            missing_pks = pks
        else:
            existing = self.data[wall_code]
            for pk in pks:
                if str(pk) not in existing:
                    missing_pks.append(pk)
                    
        if not missing_pks and not start_new_file:
            return False # Nada que hacer
            
        # Sort missing PKs
        try:
            sorted_pks = sorted(missing_pks, key=lambda x: float(str(x).replace('+', '')))
        except:
            sorted_pks = missing_pks

        mode = 'a' if os.path.exists(self.csv_path) else 'w'
        try:
            with open(self.csv_path, mode, newline='', encoding='utf-8') as f:
                # Force semicolon for consistency if appending? Or use detected?
                # If creating new, use semicolon as user prefers it.
                # If appending, check delimiter.
                delimiter = ';' 
                if mode == 'a':
                    with open(self.csv_path, 'r', encoding='utf-8') as fr:
                        line1 = fr.readline()
                        if ',' in line1 and ';' not in line1: delimiter = ','
                
                writer = csv.writer(f, delimiter=delimiter)
                if mode == 'w':
                    writer.writerow(["Muro", "PK", "Cota_Geomembrana"])
                
                for pk in sorted_pks:
                    writer.writerow([display_name, pk, "0.00"])
            
            # Reload to include new placeholders
            self._load_data()
            return True
            
        except Exception as e:
            print(f"Error escribiendo geomembrana: {e}")
            return False

    def get_elevation(self, wall_name, pk):
        wall_code = self._normalize_wall_code(wall_name)
        return self.data[wall_code].get(str(pk))

    def get_all_data(self, wall_name):
        """Retorna diccionario {pk: elevation} para el muro dado."""
        if not self.data:
            self._load_data()
        
        wall_code = self._normalize_wall_code(wall_name)
        return self.data.get(wall_code, {})
