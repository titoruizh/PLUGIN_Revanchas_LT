# -*- coding: utf-8 -*-
"""
DEM Validator Module - Revanchas LT Plugin
Valida si el DEM cubre las coordenadas de alineación

Refactorizado con type hints y logging estructurado.
"""

from typing import Dict, Any, List, Optional

# Importar logging del plugin
try:
    from ..utils.logging_config import get_logger
except ImportError:
    get_logger = lambda x: __import__('logging').getLogger(x)

logger = get_logger(__name__)


# Constantes
DEFAULT_BUFFER: float = 50.0  # metros (margen de seguridad para secciones de 80m)


class DEMValidator:
    """
    Valida la cobertura del DEM para datos de alineación.
    
    Proporciona métodos estáticos para validar que el DEM
    cubra completamente el área de la alineación incluyendo
    el ancho de las secciones transversales.
    """
    
    @staticmethod
    def validate_dem_coverage(dem_info: Dict[str, Any], 
                              alignment: Dict[str, Any],
                              buffer: float = DEFAULT_BUFFER) -> Dict[str, Any]:
        """
        Valida que el DEM cubra el área de alineación.
        
        Args:
            dem_info: Información de extent del DEM
            alignment: Datos de alineación con estaciones
            buffer: Buffer adicional en metros
            
        Returns:
            Diccionario con resultados de validación
        """
        stations = alignment.get('stations', [])
        
        if not stations:
            logger.warning("Alineación sin estaciones para validar")
            return {
                'coverage_ok': False,
                'error': 'No hay estaciones en la alineación'
            }
        
        # Obtener límites de la alineación
        x_coords: List[float] = [station['x'] for station in stations]
        y_coords: List[float] = [station['y'] for station in stations]
        
        align_xmin, align_xmax = min(x_coords), max(x_coords)
        align_ymin, align_ymax = min(y_coords), max(y_coords)
        
        # Agregar buffer para secciones transversales
        align_xmin -= buffer
        align_xmax += buffer
        align_ymin -= buffer
        align_ymax += buffer
        
        # Verificar cobertura
        dem_xmin = dem_info.get('xmin', 0)
        dem_xmax = dem_info.get('xmax', 0)
        dem_ymin = dem_info.get('ymin', 0)
        dem_ymax = dem_info.get('ymax', 0)
        
        coverage_ok = (
            align_xmin >= dem_xmin and align_xmax <= dem_xmax and
            align_ymin >= dem_ymin and align_ymax <= dem_ymax
        )
        
        # Calcular déficit de cobertura
        x_deficit_min = max(0, dem_xmin - align_xmin)
        x_deficit_max = max(0, align_xmax - dem_xmax)
        y_deficit_min = max(0, dem_ymin - align_ymin)
        y_deficit_max = max(0, align_ymax - dem_ymax)
        
        result = {
            'coverage_ok': coverage_ok,
            'alignment_bounds': {
                'xmin': align_xmin, 'xmax': align_xmax,
                'ymin': align_ymin, 'ymax': align_ymax
            },
            'dem_bounds': {
                'xmin': dem_xmin, 'xmax': dem_xmax,
                'ymin': dem_ymin, 'ymax': dem_ymax
            },
            'missing_coverage': {
                'x_deficit': x_deficit_min + x_deficit_max,
                'y_deficit': y_deficit_min + y_deficit_max,
                'x_deficit_min': x_deficit_min,
                'x_deficit_max': x_deficit_max,
                'y_deficit_min': y_deficit_min,
                'y_deficit_max': y_deficit_max
            },
            'buffer_used': buffer,
            'stations_count': len(stations)
        }
        
        if coverage_ok:
            logger.info(
                f"DEM cubre alineación: {len(stations)} estaciones dentro del extent"
            )
        else:
            logger.warning(
                f"DEM no cubre completamente la alineación: "
                f"déficit X={result['missing_coverage']['x_deficit']:.1f}m, "
                f"Y={result['missing_coverage']['y_deficit']:.1f}m"
            )
        
        return result
    
    @staticmethod
    def calculate_coverage_percentage(dem_info: Dict[str, Any], 
                                      alignment: Dict[str, Any]) -> float:
        """
        Calcula el porcentaje de cobertura del DEM sobre la alineación.
        
        Args:
            dem_info: Información de extent del DEM
            alignment: Datos de alineación
            
        Returns:
            Porcentaje de cobertura (0-100)
        """
        stations = alignment.get('stations', [])
        
        if not stations:
            return 0.0
        
        dem_xmin = dem_info.get('xmin', 0)
        dem_xmax = dem_info.get('xmax', 0)
        dem_ymin = dem_info.get('ymin', 0)
        dem_ymax = dem_info.get('ymax', 0)
        
        covered = 0
        
        for station in stations:
            x, y = station['x'], station['y']
            if dem_xmin <= x <= dem_xmax and dem_ymin <= y <= dem_ymax:
                covered += 1
        
        percentage = (covered / len(stations)) * 100 if stations else 0.0
        
        logger.debug(f"Cobertura: {covered}/{len(stations)} estaciones ({percentage:.1f}%)")
        
        return percentage
    
    @staticmethod  
    def get_uncovered_stations(dem_info: Dict[str, Any], 
                               alignment: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Obtiene lista de estaciones no cubiertas por el DEM.
        
        Args:
            dem_info: Información de extent del DEM
            alignment: Datos de alineación
            
        Returns:
            Lista de estaciones fuera de cobertura
        """
        stations = alignment.get('stations', [])
        uncovered: List[Dict[str, Any]] = []
        
        dem_xmin = dem_info.get('xmin', 0)
        dem_xmax = dem_info.get('xmax', 0)
        dem_ymin = dem_info.get('ymin', 0)
        dem_ymax = dem_info.get('ymax', 0)
        
        for station in stations:
            x, y = station['x'], station['y']
            if not (dem_xmin <= x <= dem_xmax and dem_ymin <= y <= dem_ymax):
                uncovered.append({
                    'pk': station.get('pk'),
                    'x': x,
                    'y': y,
                    'reason': DEMValidator._get_uncovered_reason(
                        x, y, dem_xmin, dem_xmax, dem_ymin, dem_ymax
                    )
                })
        
        if uncovered:
            logger.warning(f"{len(uncovered)} estaciones fuera de cobertura DEM")
        
        return uncovered
    
    @staticmethod
    def _get_uncovered_reason(x: float, y: float,
                              dem_xmin: float, dem_xmax: float,
                              dem_ymin: float, dem_ymax: float) -> str:
        """
        Obtiene razón por la que un punto está fuera de cobertura.
        
        Args:
            x, y: Coordenadas del punto
            dem_*: Límites del DEM
            
        Returns:
            Descripción de la razón
        """
        reasons = []
        
        if x < dem_xmin:
            reasons.append(f"X<DEM_min ({x:.1f} < {dem_xmin:.1f})")
        if x > dem_xmax:
            reasons.append(f"X>DEM_max ({x:.1f} > {dem_xmax:.1f})")
        if y < dem_ymin:
            reasons.append(f"Y<DEM_min ({y:.1f} < {dem_ymin:.1f})")
        if y > dem_ymax:
            reasons.append(f"Y>DEM_max ({y:.1f} > {dem_ymax:.1f})")
        
        return ", ".join(reasons) if reasons else "Desconocido"
    
    @staticmethod
    def validate_dem_quality(dem_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valida la calidad general del DEM.
        
        Args:
            dem_info: Información del DEM
            
        Returns:
            Diccionario con resultados de calidad
        """
        cellsize = dem_info.get('cellsize', 0)
        nrows = dem_info.get('nrows', 0)
        ncols = dem_info.get('ncols', 0)
        
        # Evaluar resolución
        if cellsize <= 0.5:
            resolution_quality = 'Excelente'
        elif cellsize <= 1.0:
            resolution_quality = 'Buena'
        elif cellsize <= 2.0:
            resolution_quality = 'Aceptable'
        else:
            resolution_quality = 'Baja'
        
        # Calcular área de cobertura
        width = dem_info.get('xmax', 0) - dem_info.get('xmin', 0)
        height = dem_info.get('ymax', 0) - dem_info.get('ymin', 0)
        area_km2 = (width * height) / 1_000_000
        
        result = {
            'cellsize': cellsize,
            'resolution_quality': resolution_quality,
            'dimensions': f"{ncols}x{nrows}",
            'total_cells': ncols * nrows,
            'coverage_width': width,
            'coverage_height': height,
            'coverage_area_km2': area_km2
        }
        
        logger.debug(
            f"Calidad DEM: {resolution_quality}, "
            f"resolución {cellsize}m, área {area_km2:.2f}km²"
        )
        
        return result