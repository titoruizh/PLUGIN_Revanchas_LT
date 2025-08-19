# -*- coding: utf-8 -*-
"""
Lama Points Module
Manages lama points data from CSV files
"""

import os
import math


class LamaPointsManager:
    """Class to manage lama points for retaining walls from CSV files"""
    
    def __init__(self):
        self.lama_points = {}
        print("🚀 Inicializando LamaPointsManager (CSV mode)...")
        self.load_lama_points()
        
    def load_lama_points(self):
        """Load lama points from CSV files in data directory"""
        print("🔍 Loading lama points from CSV...")
        
        data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'lama_points')
        print(f"🔍 Looking for CSV files in: {data_dir}")
        
        # Check if directory exists
        if not os.path.exists(data_dir):
            print(f"⚠️ Directory does not exist: {data_dir}")
            print("   Creating directory...")
            try:
                os.makedirs(data_dir, exist_ok=True)
            except Exception as e:
                print(f"❌ Could not create directory: {e}")
        
        # Load Muro 1 lama points from CSV
        muro1_csv_file = os.path.join(data_dir, 'muro1_lama_points.csv')
        
        if os.path.exists(muro1_csv_file):
            print(f"✅ CSV file found: {muro1_csv_file}")
            self.lama_points['Muro 1'] = self._load_csv_file(muro1_csv_file)
            print(f"✅ Loaded {len(self.lama_points['Muro 1'])} lama points from CSV")
        else:
            print(f"⚠️ Lama points CSV file not found: {muro1_csv_file}")
            self.lama_points['Muro 1'] = []
    
    def _load_csv_file(self, file_path):
        """Load lama points from CSV file (Perfil,X,Y format)"""
        lama_points = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as csvfile:
                lines = csvfile.readlines()
                
                for line_num, line in enumerate(lines, 1):
                    line = line.strip()
                    
                    # Skip empty lines, comments or header
                    if not line or line.startswith('#') or line.startswith('Perfil'):
                        continue
                    
                    try:
                        # Parse Perfil,X,Y coordinates
                        parts = line.split(',')
                        if len(parts) >= 3:
                            perfil_number = int(parts[0].strip())
                            x_utm = float(parts[1].strip())
                            y_utm = float(parts[2].strip())
                            
                            lama_point = {
                                'pk': f"LAMA_{perfil_number:03d}",
                                'perfil_number': perfil_number,  # 🆕 NUEVO: número de perfil directo
                                'x_utm': x_utm,
                                'y_utm': y_utm,
                                'description': f'Punto Lama Perfil {perfil_number}',
                                'station_number': perfil_number - 1,  # 0-indexed
                                'elevation_dem': None
                            }
                            lama_points.append(lama_point)
                            print(f"  📍 Perfil {perfil_number}: X={x_utm:.3f}, Y={y_utm:.3f}")
                            
                    except (ValueError, IndexError) as e:
                        print(f"  ⚠️ Error parsing line {line_num}: {line} - {e}")
                        continue
                        
        except Exception as e:
            print(f"❌ Error loading CSV file: {str(e)}")
            return []
            
        print(f"✅ Successfully loaded {len(lama_points)} lama points from CSV")
        return lama_points
    
    def get_lama_points(self, wall_name):
        """Get lama points for specified wall"""
        return self.lama_points.get(wall_name, [])
    
    def extract_elevations_from_dem(self, wall_name, dem_processor, dem_data):
        """Extract elevations for lama points from DEM data"""
        if wall_name not in self.lama_points:
            print(f"❌ No lama points found for wall: {wall_name}")
            return
        
        points_updated = 0
        points_failed = 0
        
        print(f"\n🔍 Extracting elevations for {len(self.lama_points[wall_name])} lama points...")
        print(f"🗺️ DEM bounds: X({dem_data['info']['xmin']:.1f} - {dem_data['info']['xmax']:.1f}), Y({dem_data['info']['ymin']:.1f} - {dem_data['info']['ymax']:.1f})")
        
        for i, lama_point in enumerate(self.lama_points[wall_name]):
            x, y = lama_point['x_utm'], lama_point['y_utm']
            
            # Check if point is within DEM bounds
            within_bounds = (
                dem_data['info']['xmin'] <= x <= dem_data['info']['xmax'] and
                dem_data['info']['ymin'] <= y <= dem_data['info']['ymax']
            )
            
            print(f"  📍 Lama {i+1} ({lama_point['pk']}): X={x:.3f}, Y={y:.3f}")
            print(f"      Within DEM bounds: {within_bounds}")
            
            if not within_bounds:
                print(f"      ❌ Outside DEM coverage")
                lama_point['elevation_dem'] = None
                points_failed += 1
                continue
            
            try:
                # Extract elevation from DEM at lama point coordinates
                elevation = dem_processor.get_elevation_at_point(x, y, dem_data)
                
                print(f"      Extracted elevation: {elevation}")
                
                if elevation != dem_data['header'].get('nodata_value', -9999):
                    lama_point['elevation_dem'] = elevation
                    points_updated += 1
                    print(f"      ✅ SUCCESS: Z={elevation:.2f}m")
                else:
                    lama_point['elevation_dem'] = None
                    points_failed += 1
                    print(f"      ❌ NODATA value returned")
                    
            except Exception as e:
                print(f"      ❌ Error extracting elevation: {str(e)}")
                lama_point['elevation_dem'] = None
                points_failed += 1
        
        print(f"✅ Updated elevations: {points_updated} success, {points_failed} failed")
    
    def find_lama_by_profile_number(self, profile, lama_points):
        """Find lama point by direct profile number assignment (1:1 relationship)"""
        profile_lama_points = []
        
        # Get profile info
        profile_pk = profile['pk']
        profile_pk_decimal = profile['pk_decimal']
        
        # 🎯 CÁLCULO DIRECTO: número de perfil basado en PK
        # PK 0+000 = Perfil 1, PK 0+020 = Perfil 2, etc.
        profile_number = int(profile_pk_decimal / 20) + 1
        
        print(f"🔍 Profile {profile_pk} → Profile Number {profile_number}")
        
        # 🎯 BÚSQUEDA DIRECTA por número de perfil
        for lama_point in lama_points:
            if lama_point['elevation_dem'] is None:
                continue
                
            if lama_point['perfil_number'] == profile_number:
                # 🎯 FOUND! Calculate offset from profile centerline
                profile_x = profile['centerline_x']
                profile_y = profile['centerline_y']
                bearing_rad = math.radians(profile['bearing'])
                
                # Vector from profile center to lama point
                dx = lama_point['x_utm'] - profile_x
                dy = lama_point['y_utm'] - profile_y
                
                # Calculate distance
                distance = math.sqrt(dx*dx + dy*dy)
                
                # Calculate perpendicular offset (cross-direction distance)
                perp_bearing = bearing_rad + math.pi / 2
                offset = dx * math.cos(perp_bearing) + dy * math.sin(perp_bearing)
                
                profile_lama_point = {
                    'pk': lama_point['pk'],
                    'perfil_number': profile_number,
                    'x_utm': lama_point['x_utm'],
                    'y_utm': lama_point['y_utm'],
                    'elevation': lama_point['elevation_dem'],
                    'offset_from_centerline': offset,
                    'distance_to_profile': distance,
                    'description': lama_point['description']
                }
                
                profile_lama_points.append(profile_lama_point)
                print(f"  ✅ FOUND {lama_point['pk']}: offset={offset:.1f}m, distance={distance:.1f}m")
                break  # Solo debe haber 1 lama por perfil
        
        if len(profile_lama_points) == 0:
            print(f"  ❌ No lama point found for Profile {profile_number}")
        
        return profile_lama_points