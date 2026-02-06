# -*- coding: utf-8 -*-
"""
Lama Points Module - Revanchas LT Plugin
Gestiona datos de puntos LAMA desde archivos CSV

Refactorizado con type hints y logging estructurado.
"""

import os
import math
from typing import Dict, List, Optional, Any

# Importar logging del plugin
try:
    from ..utils.logging_config import get_logger
except ImportError:
    get_logger = lambda x: __import__('logging').getLogger(x)

logger = get_logger(__name__)


# Constantes
NODATA_VALUE: float = -9999.0
PROFILE_INTERVAL: float = 20.0  # metros entre perfiles


class LamaPointsManager:
    """
    Clase para gestionar puntos LAMA de muros de contención.
    
    Carga puntos LAMA desde archivos CSV y extrae elevaciones
    desde datos DEM para cada punto.
    """
    
    def __init__(self):
        """Inicializa el gestor de puntos LAMA."""
        self.lama_points: Dict[str, List[Dict[str, Any]]] = {}
        
        logger.info("Inicializando LamaPointsManager")
        self.load_lama_points()
    
    def load_lama_points(self) -> None:
        """Carga puntos LAMA desde archivos CSV."""
        logger.debug("Cargando puntos LAMA desde CSV")
        
        # Directorio de datos
        data_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            'data', 
            'lama_points'
        )
        logger.debug(f"Directorio de datos: {data_dir}")
        
        # Cargar archivos para cada muro
        wall_files = {
            'Muro 1': 'muro1_lama_points.csv',
            'Muro 2': 'muro2_lama_points.csv',
            'Muro 3': 'muro3_lama_points.csv'
        }
        
        for wall_name, filename in wall_files.items():
            csv_path = os.path.join(data_dir, filename)
            if os.path.exists(csv_path):
                self.lama_points[wall_name] = self._load_csv_file(csv_path)
                logger.info(
                    f"{wall_name}: Cargados {len(self.lama_points[wall_name])} puntos LAMA"
                )
            else:
                self.lama_points[wall_name] = []
                logger.warning(f"{wall_name}: Archivo CSV no encontrado ({filename})")
    
    def _load_csv_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Carga puntos LAMA desde archivo CSV (formato Perfil,X,Y).
        
        Args:
            file_path: Ruta al archivo CSV
            
        Returns:
            Lista de diccionarios con datos de puntos LAMA
        """
        lama_points: List[Dict[str, Any]] = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as csvfile:
                lines = csvfile.readlines()
                
                for line_num, line in enumerate(lines, 1):
                    line = line.strip()
                    
                    # Saltar líneas vacías, comentarios o header
                    if not line or line.startswith('#') or line.startswith('Perfil'):
                        continue
                    
                    try:
                        # Parsear coordenadas Perfil,X,Y
                        parts = line.split(',')
                        if len(parts) >= 3:
                            perfil_number = int(parts[0].strip())
                            x_utm = float(parts[1].strip())
                            y_utm = float(parts[2].strip())
                            
                            lama_point = {
                                'pk': f"LAMA_{perfil_number:03d}",
                                'perfil_number': perfil_number,
                                'x_utm': x_utm,
                                'y_utm': y_utm,
                                'description': f'Punto Lama Perfil {perfil_number}',
                                'station_number': perfil_number - 1,  # 0-indexed
                                'elevation_dem': None
                            }
                            lama_points.append(lama_point)
                            
                            logger.debug(
                                f"Perfil {perfil_number}: X={x_utm:.3f}, Y={y_utm:.3f}"
                            )
                            
                    except (ValueError, IndexError) as e:
                        logger.warning(f"Error parseando línea {line_num}: {line} - {e}")
                        continue
                        
        except Exception as e:
            logger.error(f"Error cargando archivo CSV: {str(e)}")
            return []
        
        logger.debug(f"Cargados {len(lama_points)} puntos LAMA")
        return lama_points
    
    def get_lama_points(self, wall_name: str) -> List[Dict[str, Any]]:
        """
        Obtiene puntos LAMA para un muro específico.
        
        Args:
            wall_name: Nombre del muro
            
        Returns:
            Lista de puntos LAMA
        """
        return self.lama_points.get(wall_name, [])
    
    def extract_elevations_from_dem(self, 
                                     wall_name: str, 
                                     dem_processor: Any, 
                                     dem_data: Dict[str, Any]) -> None:
        """
        Extrae elevaciones para puntos LAMA desde datos DEM.
        
        Args:
            wall_name: Nombre del muro
            dem_processor: Instancia de DEMProcessor
            dem_data: Datos DEM cargados
        """
        if wall_name not in self.lama_points:
            logger.error(f"No hay puntos LAMA para: {wall_name}")
            return
        
        points_updated = 0
        points_failed = 0
        
        nodata = dem_data['header'].get('nodata_value', NODATA_VALUE)
        
        logger.info(
            f"Extrayendo elevaciones para {len(self.lama_points[wall_name])} "
            f"puntos LAMA de {wall_name}"
        )
        logger.debug(
            f"DEM bounds: X({dem_data['info']['xmin']:.1f} - "
            f"{dem_data['info']['xmax']:.1f}), "
            f"Y({dem_data['info']['ymin']:.1f} - "
            f"{dem_data['info']['ymax']:.1f})"
        )
        
        for i, lama_point in enumerate(self.lama_points[wall_name]):
            x, y = lama_point['x_utm'], lama_point['y_utm']
            
            # Verificar si el punto está dentro del DEM
            within_bounds = (
                dem_data['info']['xmin'] <= x <= dem_data['info']['xmax'] and
                dem_data['info']['ymin'] <= y <= dem_data['info']['ymax']
            )
            
            if not within_bounds:
                logger.debug(f"Lama {lama_point['pk']}: fuera de cobertura DEM")
                lama_point['elevation_dem'] = None
                points_failed += 1
                continue
            
            try:
                # Extraer elevación del DEM
                elevation = dem_processor.get_elevation_at_point(x, y, dem_data)
                
                if elevation != nodata:
                    lama_point['elevation_dem'] = elevation
                    points_updated += 1
                    logger.debug(
                        f"Lama {lama_point['pk']}: Z={elevation:.2f}m"
                    )
                else:
                    lama_point['elevation_dem'] = None
                    points_failed += 1
                    logger.debug(f"Lama {lama_point['pk']}: valor NODATA")
                    
            except Exception as e:
                logger.warning(f"Error extrayendo elevación para {lama_point['pk']}: {e}")
                lama_point['elevation_dem'] = None
                points_failed += 1
        
        logger.info(
            f"Elevaciones actualizadas: {points_updated} éxito, "
            f"{points_failed} fallidos"
        )
    
    def find_lama_by_profile_number(self, 
                                     profile: Dict[str, Any], 
                                     lama_points: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Encuentra punto LAMA por número de perfil directo (relación 1:1).
        
        Args:
            profile: Datos del perfil
            lama_points: Lista de puntos LAMA del muro
            
        Returns:
            Lista con punto LAMA encontrado (vacía si no hay)
        """
        profile_lama_points: List[Dict[str, Any]] = []
        
        # Calcular número de perfil basado en PK
        profile_pk_decimal = profile['pk_decimal']
        profile_number = int(profile_pk_decimal / PROFILE_INTERVAL) + 1
        
        logger.debug(f"Perfil {profile['pk']} → Número de perfil {profile_number}")
        
        # Búsqueda directa por número de perfil
        for lama_point in lama_points:
            if lama_point['elevation_dem'] is None:
                continue
            
            if lama_point['perfil_number'] == profile_number:
                # Calcular offset desde línea central del perfil
                profile_x = profile['centerline_x']
                profile_y = profile['centerline_y']
                bearing_rad = math.radians(profile['bearing'])
                
                # Vector desde centro del perfil a punto LAMA
                dx = lama_point['x_utm'] - profile_x
                dy = lama_point['y_utm'] - profile_y
                
                # Calcular distancia
                distance = math.sqrt(dx*dx + dy*dy)
                
                # Calcular offset perpendicular
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
                    'description': lama_point['description'],
                    # Nuevos campos útiles
                    'distance_from_centerline': offset,  # alias
                    'elevation_dem': lama_point['elevation_dem']
                }
                
                profile_lama_points.append(profile_lama_point)
                logger.debug(
                    f"Encontrado {lama_point['pk']}: offset={offset:.1f}m, "
                    f"distancia={distance:.1f}m"
                )
                break  # Solo debe haber 1 LAMA por perfil
        
        if not profile_lama_points:
            logger.debug(f"No hay punto LAMA para perfil {profile_number}")
        
        return profile_lama_points
    
    def get_all_lama_elevations(self, wall_name: str) -> List[Optional[float]]:
        """
        Obtiene todas las elevaciones LAMA de un muro.
        
        Args:
            wall_name: Nombre del muro
            
        Returns:
            Lista de elevaciones (None para puntos sin datos)
        """
        points = self.get_lama_points(wall_name)
        return [p.get('elevation_dem') for p in points]
    
    def get_lama_statistics(self, wall_name: str) -> Dict[str, Any]:
        """
        Obtiene estadísticas de puntos LAMA de un muro.
        
        Args:
            wall_name: Nombre del muro
            
        Returns:
            Diccionario con estadísticas
        """
        points = self.get_lama_points(wall_name)
        
        if not points:
            return {'total': 0, 'with_elevation': 0, 'coverage': 0}
        
        with_elevation = sum(1 for p in points if p.get('elevation_dem') is not None)
        elevations = [p['elevation_dem'] for p in points if p.get('elevation_dem') is not None]
        
        return {
            'total': len(points),
            'with_elevation': with_elevation,
            'coverage': (with_elevation / len(points) * 100) if points else 0,
            'min_elevation': min(elevations) if elevations else None,
            'max_elevation': max(elevations) if elevations else None,
            'avg_elevation': sum(elevations) / len(elevations) if elevations else None
        }