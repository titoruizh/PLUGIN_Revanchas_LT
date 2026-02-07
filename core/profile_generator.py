# -*- coding: utf-8 -*-
"""
Profile Generator Module - Revanchas LT Plugin
Genera perfiles topográficos a lo largo de alineaciones

Refactorizado con type hints y logging estructurado.
"""

import math
import csv
from typing import Dict, List, Optional, Any, Callable, Tuple

# Importar logging del plugin
try:
    from ..utils.logging_config import get_logger
except ImportError:
    get_logger = lambda x: __import__('logging').getLogger(x)

logger = get_logger(__name__)

# Importar numpy con manejo de errores
try:
    import numpy as np
    try:
        test_array = np.array([1, 2, 3])
        try:
            _ = hasattr(np, '_ARRAY_API')
        except AttributeError as ae:
            if '_ARRAY_API' in str(ae):
                logger.warning(f"NumPy _ARRAY_API error: {ae}")
                raise ae
        HAS_NUMPY = True
        logger.debug("NumPy funcionando correctamente")
    except (AttributeError, ImportError, Exception) as e:
        logger.warning(f"NumPy con problemas: {e}")
        HAS_NUMPY = False
        np = None
except ImportError:
    HAS_NUMPY = False
    np = None

from .dem_processor import DEMProcessor
from .alignment_data import AlignmentData


# Constantes por defecto
DEFAULT_PROFILE_WIDTH: float = 140.0  # metros (±70m)
DEFAULT_RESOLUTION: float = 0.1       # metros entre puntos
NODATA_VALUE: float = -9999.0


class ProfileGenerator:
    """
    Clase para generar perfiles topográficos.
    
    Genera perfiles de alta resolución a lo largo de alineaciones,
    incluyendo puntos LAMA y estadísticas de elevación.
    """
    
    def __init__(self):
        """Inicializa el generador de perfiles."""
        self.dem_processor = DEMProcessor()
        self.alignment_data = AlignmentData()
        
        logger.debug("ProfileGenerator inicializado")
    
    def generate_profiles(self, 
                         dem_data: Dict[str, Any], 
                         alignment: Dict[str, Any], 
                         progress_callback: Optional[Callable[[float], None]] = None, 
                         resolution: float = DEFAULT_RESOLUTION, 
                         wall_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Genera todos los perfiles para una alineación.
        
        Args:
            dem_data: Datos DEM cargados
            alignment: Datos de alineación
            progress_callback: Función de callback para progreso (0.0-1.0)
            resolution: Resolución en metros
            wall_name: Nombre del muro para puntos LAMA
            
        Returns:
            Lista de perfiles generados
        """
        from .lama_points import LamaPointsManager
        
        profiles: List[Dict[str, Any]] = []
        total_stations = len(alignment['stations'])
        
        logger.info(
            f"Generando {total_stations} perfiles para {alignment.get('name', 'N/A')} "
            f"(resolución: {resolution}m)"
        )
        
        # Inicializar gestor de puntos LAMA
        lama_manager = None
        wall_lama_points: List[Dict[str, Any]] = []
        
        if wall_name:
            try:
                lama_manager = LamaPointsManager()
                lama_manager.extract_elevations_from_dem(
                    wall_name, self.dem_processor, dem_data
                )
                wall_lama_points = lama_manager.get_lama_points(wall_name)
                logger.info(f"Encontrados {len(wall_lama_points)} puntos LAMA para {wall_name}")
            except Exception as e:
                logger.warning(f"Error cargando puntos LAMA: {e}")
                wall_lama_points = []
        
        nodata = dem_data['header'].get('nodata_value', NODATA_VALUE)
        
        for i, station in enumerate(alignment['stations']):
            if progress_callback:
                progress = i / total_stations
                progress_callback(progress)
            
            # Generar puntos de sección transversal
            cross_section_points = self.alignment_data.get_cross_section_points(
                station, width=DEFAULT_PROFILE_WIDTH, resolution=resolution
            )
            
            elevations: List[float] = []
            distances: List[float] = []
            coordinates: List[Tuple[float, float]] = []
            
            for point in cross_section_points:
                x, y, offset = point
                elevation = self.dem_processor.get_elevation_at_point(x, y, dem_data)
                
                elevations.append(elevation)
                distances.append(offset)
                coordinates.append((x, y))
            
            profile = {
                'station': station,
                'pk': station['pk'],
                'pk_decimal': station['pk_decimal'],
                'centerline_x': station['x'],
                'centerline_y': station['y'],
                'bearing': station['bearing'],
                'distances': distances,
                'elevations': elevations,
                'coordinates': coordinates,
                'width': DEFAULT_PROFILE_WIDTH,
                'resolution': resolution,
                'total_points': len(distances),
                'valid_points': len([e for e in elevations if e != nodata])
            }
            
            # Agregar puntos LAMA al perfil
            if wall_lama_points and lama_manager:
                profile_lama_points = lama_manager.find_lama_by_profile_number(
                    profile, wall_lama_points
                )
                profile['lama_points'] = profile_lama_points
            else:
                profile['lama_points'] = []
            
            # Calcular estadísticas de elevación
            self._calculate_elevation_stats(profile, nodata)
            
            profiles.append(profile)
        
        if progress_callback:
            progress_callback(1.0)
        
        logger.info(f"Generados {len(profiles)} perfiles exitosamente")
        
        return profiles
    
    def generate_single_profile(self, 
                                dem_data: Dict[str, Any], 
                                station: Dict[str, Any], 
                                width: float = DEFAULT_PROFILE_WIDTH, 
                                resolution: float = DEFAULT_RESOLUTION) -> Dict[str, Any]:
        """
        Genera un único perfil de alta resolución.
        
        Args:
            dem_data: Datos DEM cargados
            station: Datos de estación
            width: Ancho total del perfil en metros
            resolution: Resolución en metros
            
        Returns:
            Diccionario con datos del perfil
        """
        cross_section_points = self.alignment_data.get_cross_section_points(
            station, width=width, resolution=resolution
        )
        
        elevations: List[float] = []
        distances: List[float] = []
        coordinates: List[Tuple[float, float]] = []
        nodata = dem_data['header'].get('nodata_value', NODATA_VALUE)
        
        for point in cross_section_points:
            x, y, offset = point
            elevation = self.dem_processor.get_elevation_at_point(x, y, dem_data)
            elevations.append(elevation)
            distances.append(offset)
            coordinates.append((x, y))
        
        profile = {
            'station': station,
            'pk': station['pk'],
            'pk_decimal': station['pk_decimal'],
            'centerline_x': station['x'],
            'centerline_y': station['y'],
            'bearing': station['bearing'],
            'distances': distances,
            'elevations': elevations,
            'coordinates': coordinates,
            'width': width,
            'resolution': resolution,
            'total_points': len(distances),
            'valid_points': len([e for e in elevations if e != nodata])
        }
        
        self._calculate_elevation_stats(profile, nodata)
        
        logger.debug(
            f"Perfil generado: {station['pk']} "
            f"({profile['valid_points']}/{profile['total_points']} puntos válidos)"
        )
        
        return profile
    
    def _calculate_elevation_stats(self, 
                                    profile: Dict[str, Any], 
                                    nodata: float = NODATA_VALUE) -> None:
        """
        Calcula estadísticas de elevación para un perfil.
        
        Args:
            profile: Diccionario del perfil (se modifica in-place)
            nodata: Valor NODATA a filtrar
        """
        valid_elevations = [e for e in profile['elevations'] if e != nodata]
        
        if valid_elevations:
            profile['min_elevation'] = min(valid_elevations)
            profile['max_elevation'] = max(valid_elevations)
            profile['avg_elevation'] = sum(valid_elevations) / len(valid_elevations)
            profile['elevation_range'] = profile['max_elevation'] - profile['min_elevation']
        else:
            profile['min_elevation'] = None
            profile['max_elevation'] = None
            profile['avg_elevation'] = None
            profile['elevation_range'] = None
    
    def export_profiles_to_csv(self, 
                               profiles: List[Dict[str, Any]], 
                               output_path: str) -> None:
        """
        Exporta datos de perfiles a archivo CSV.
        
        Args:
            profiles: Lista de datos de perfiles
            output_path: Ruta del archivo CSV de salida
        """
        logger.info(f"Exportando {len(profiles)} perfiles a {output_path}")
        
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Escribir header
            writer.writerow([
                'PK', 'Station_X', 'Station_Y', 'Bearing', 
                'Offset', 'Elevation', 'Distance_From_Start'
            ])
            
            # Escribir datos
            rows_written = 0
            for profile in profiles:
                pk = profile['pk']
                station_x = profile['centerline_x']
                station_y = profile['centerline_y']
                bearing = profile['bearing']
                
                for i, (distance, elevation, coords) in enumerate(zip(
                    profile['distances'], 
                    profile['elevations'], 
                    profile['coordinates']
                )):
                    writer.writerow([
                        pk, station_x, station_y, bearing,
                        distance, elevation, profile['pk_decimal']
                    ])
                    rows_written += 1
        
        logger.info(f"Exportadas {rows_written} filas a CSV")
    
    def create_profile_visualization_data(self, 
                                          profile: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Crea estructura de datos para visualización con matplotlib.
        
        Args:
            profile: Diccionario de datos del perfil
            
        Returns:
            Diccionario con datos x, y para plotting o None si no hay datos válidos
        """
        valid_indices: List[int] = []
        
        # Encontrar puntos de elevación válidos
        for i, elevation in enumerate(profile['elevations']):
            if elevation != NODATA_VALUE:
                valid_indices.append(i)
        
        if not valid_indices:
            logger.warning(f"Perfil {profile['pk']} no tiene elevaciones válidas")
            return None
        
        # Extraer datos válidos
        distances = [profile['distances'][i] for i in valid_indices]
        elevations = [profile['elevations'][i] for i in valid_indices]
        
        return {
            'distances': distances,
            'elevations': elevations,
            'pk': profile['pk'],
            'centerline_elevation': profile.get('avg_elevation', 0),
            'title': f"Perfil Topográfico - {profile['pk']}",
            'xlabel': 'Distancia desde Eje (m)',
            'ylabel': 'Elevación (m)'
        }
    
    def get_profile_summary(self, profiles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Obtiene un resumen estadístico de todos los perfiles.
        
        Args:
            profiles: Lista de perfiles
            
        Returns:
            Diccionario con estadísticas
        """
        if not profiles:
            return {}
        
        all_valid_elevations: List[float] = []
        total_points = 0
        valid_points = 0
        
        for profile in profiles:
            total_points += profile.get('total_points', 0)
            valid_points += profile.get('valid_points', 0)
            
            if profile.get('min_elevation') is not None:
                all_valid_elevations.append(profile['min_elevation'])
            if profile.get('max_elevation') is not None:
                all_valid_elevations.append(profile['max_elevation'])
        
        return {
            'num_profiles': len(profiles),
            'total_points': total_points,
            'valid_points': valid_points,
            'coverage_percent': (valid_points / total_points * 100) if total_points > 0 else 0,
            'min_elevation': min(all_valid_elevations) if all_valid_elevations else None,
            'max_elevation': max(all_valid_elevations) if all_valid_elevations else None,
            'start_pk': profiles[0]['pk'],
            'end_pk': profiles[-1]['pk']
        }