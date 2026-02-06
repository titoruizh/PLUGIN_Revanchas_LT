# -*- coding: utf-8 -*-
"""
DEM Processor Module - Revanchas LT Plugin
Maneja la carga y procesamiento de archivos ASCII Grid (.asc)

Refactorizado con type hints y logging estructurado.
"""

import os
from typing import Dict, List, Optional, Any, Tuple, Union

# Importar logging del plugin
try:
    from ..utils.logging_config import get_logger
except ImportError:
    get_logger = lambda x: __import__('logging').getLogger(x)

logger = get_logger(__name__)

# Importar numpy con manejo de errores
try:
    import numpy as np
    # Verificar que numpy funciona correctamente
    try:
        test_array = np.array([1, 2, 3])
        try:
            _ = hasattr(np, '_ARRAY_API')
        except AttributeError as ae:
            if '_ARRAY_API' in str(ae):
                logger.warning(f"NumPy _ARRAY_API error detectado: {ae}")
                raise ae
        HAS_NUMPY = True
        logger.debug("NumPy funcionando correctamente")
    except (AttributeError, ImportError, Exception) as e:
        logger.warning(f"NumPy disponible pero con problemas: {e}")
        HAS_NUMPY = False
        np = None
except ImportError:
    HAS_NUMPY = False
    np = None
    logger.warning("NumPy no disponible, usando fallback")


# Fallback sin numpy
if not HAS_NUMPY:
    class NumpyFallback:
        """Implementación básica de operaciones numpy para fallback."""
        
        @staticmethod
        def array(data: List) -> List:
            return data
        
        @staticmethod
        def zeros(shape: Union[int, Tuple[int, int]]) -> List:
            if isinstance(shape, tuple) and len(shape) == 2:
                return [[0.0 for _ in range(shape[1])] for _ in range(shape[0])]
            return [0.0] * shape
    
    np = NumpyFallback()


class DEMProcessor:
    """
    Clase para operaciones con archivos DEM.
    
    Maneja la carga de archivos ASCII Grid (.asc), extracción de
    elevaciones y operaciones de interpolación bilineal.
    """
    
    NODATA_DEFAULT: float = -9999.0
    HEADER_LINES: int = 6
    
    def __init__(self):
        """Inicializa el procesador DEM."""
        self.dem_data: Optional[Any] = None
        self.header: Optional[Dict[str, Any]] = None
        self._file_path: Optional[str] = None
        
        logger.debug("DEMProcessor inicializado")
    
    def get_dem_info(self, file_path: str) -> Dict[str, Any]:
        """
        Obtiene información básica de un archivo DEM sin cargarlo completamente.
        
        Args:
            file_path: Ruta al archivo DEM
            
        Returns:
            Diccionario con información del DEM
            
        Raises:
            FileNotFoundError: Si el archivo no existe
        """
        if not os.path.exists(file_path):
            logger.error(f"Archivo DEM no encontrado: {file_path}")
            raise FileNotFoundError(f"DEM file not found: {file_path}")
        
        header = self._read_header(file_path)
        
        info = {
            'cols': header['ncols'],
            'rows': header['nrows'],
            'xmin': header['xllcorner'],
            'ymin': header['yllcorner'],
            'xmax': header['xllcorner'] + header['ncols'] * header['cellsize'],
            'ymax': header['yllcorner'] + header['nrows'] * header['cellsize'],
            'cellsize': header['cellsize'],
            'nodata': header.get('nodata_value', self.NODATA_DEFAULT)
        }
        
        logger.debug(
            f"DEM info: {info['cols']}x{info['rows']}, "
            f"cellsize={info['cellsize']}, "
            f"extent=({info['xmin']:.2f}, {info['ymin']:.2f}) - "
            f"({info['xmax']:.2f}, {info['ymax']:.2f})"
        )
        
        return info
    
    def load_dem(self, file_path: str) -> Dict[str, Any]:
        """
        Carga DEM desde archivo ASCII Grid.
        
        Args:
            file_path: Ruta al archivo DEM
            
        Returns:
            Diccionario con datos, header e información del DEM
            
        Raises:
            FileNotFoundError: Si el archivo no existe
        """
        if not os.path.exists(file_path):
            logger.error(f"Archivo DEM no encontrado: {file_path}")
            raise FileNotFoundError(f"DEM file not found: {file_path}")
        
        self._file_path = file_path
        
        # Leer header
        self.header = self._read_header(file_path)
        
        # Leer datos
        data: List[List[float]] = []
        
        logger.info(f"Cargando DEM: {os.path.basename(file_path)}")
        
        with open(file_path, 'r') as f:
            # Saltar header
            for _ in range(self.HEADER_LINES):
                f.readline()
            
            # Leer datos
            for line in f:
                row = [float(val) for val in line.strip().split()]
                data.append(row)
        
        if HAS_NUMPY:
            self.dem_data = np.array(data)
        else:
            self.dem_data = data
        
        logger.info(
            f"DEM cargado: {self.header['nrows']} filas x "
            f"{self.header['ncols']} columnas"
        )
        
        return {
            'data': self.dem_data,
            'header': self.header,
            'info': self.get_dem_info(file_path)
        }
    
    def _read_header(self, file_path: str) -> Dict[str, Any]:
        """
        Lee el header del archivo ASC.
        
        Args:
            file_path: Ruta al archivo
            
        Returns:
            Diccionario con parámetros del header
        """
        header: Dict[str, Any] = {}
        
        with open(file_path, 'r') as f:
            header['ncols'] = int(f.readline().strip().split()[1])
            header['nrows'] = int(f.readline().strip().split()[1])
            header['xllcorner'] = float(f.readline().strip().split()[1])
            header['yllcorner'] = float(f.readline().strip().split()[1])
            header['cellsize'] = float(f.readline().strip().split()[1])
            
            # NODATA_value es opcional
            next_line = f.readline().strip().split()
            if next_line[0].lower().startswith('nodata'):
                header['nodata_value'] = float(next_line[1])
            else:
                header['nodata_value'] = self.NODATA_DEFAULT
        
        return header
    
    def get_elevation_at_point(self, 
                                x: float, 
                                y: float, 
                                dem_data: Optional[Dict[str, Any]] = None) -> float:
        """
        Obtiene elevación en un punto usando interpolación bilineal.
        
        Args:
            x: Coordenada X (Este)
            y: Coordenada Y (Norte)
            dem_data: Datos DEM opcionales (usa self.dem_data si None)
            
        Returns:
            Elevación interpolada o NODATA si fuera de rango
            
        Raises:
            ValueError: Si no hay datos DEM cargados
        """
        if dem_data is None:
            data = self.dem_data
            header = self.header
        else:
            header = dem_data['header']
            data = dem_data['data']
        
        if data is None or header is None:
            logger.error("No hay datos DEM cargados")
            raise ValueError("No DEM data loaded")
        
        nodata = header.get('nodata_value', self.NODATA_DEFAULT)
        
        # Convertir coordenadas mundo a coordenadas grid
        col = (x - header['xllcorner']) / header['cellsize']
        row = (header['yllcorner'] + header['nrows'] * header['cellsize'] - y) / header['cellsize']
        
        # Verificar límites
        if col < 0 or col >= header['ncols'] - 1 or row < 0 or row >= header['nrows'] - 1:
            return nodata
        
        # Interpolación bilineal
        col_int = int(col)
        row_int = int(row)
        
        # Obtener los cuatro puntos circundantes
        if HAS_NUMPY:
            z11 = data[row_int, col_int]
            z12 = data[row_int, col_int + 1]
            z21 = data[row_int + 1, col_int]
            z22 = data[row_int + 1, col_int + 1]
        else:
            z11 = data[row_int][col_int]
            z12 = data[row_int][col_int + 1]
            z21 = data[row_int + 1][col_int]
            z22 = data[row_int + 1][col_int + 1]
        
        # Verificar valores NODATA
        if any(z == nodata for z in [z11, z12, z21, z22]):
            return nodata
        
        # Interpolar
        dx = col - col_int
        dy = row - row_int
        
        z1 = z11 * (1 - dx) + z12 * dx
        z2 = z21 * (1 - dx) + z22 * dx
        z = z1 * (1 - dy) + z2 * dy
        
        return float(z)
    
    def extract_profile_elevations(self, 
                                    profile_points: List[Tuple[float, float, float]],
                                    dem_data: Optional[Dict[str, Any]] = None) -> List[float]:
        """
        Extrae elevaciones a lo largo de una línea de perfil.
        
        Args:
            profile_points: Lista de puntos (x, y, offset)
            dem_data: Datos DEM opcionales
            
        Returns:
            Lista de elevaciones
        """
        elevations: List[float] = []
        
        for point in profile_points:
            elevation = self.get_elevation_at_point(point[0], point[1], dem_data)
            elevations.append(elevation)
        
        logger.debug(
            f"Extraídas {len(elevations)} elevaciones, "
            f"rango: {min(elevations):.2f} - {max(elevations):.2f}"
        )
        
        return elevations
    
    def is_point_in_dem(self, x: float, y: float) -> bool:
        """
        Verifica si un punto está dentro del extent del DEM.
        
        Args:
            x: Coordenada X
            y: Coordenada Y
            
        Returns:
            True si el punto está dentro del DEM
        """
        if self.header is None:
            return False
        
        xmin = self.header['xllcorner']
        ymin = self.header['yllcorner']
        xmax = xmin + self.header['ncols'] * self.header['cellsize']
        ymax = ymin + self.header['nrows'] * self.header['cellsize']
        
        return xmin <= x <= xmax and ymin <= y <= ymax
    
    def get_extent(self) -> Optional[Tuple[float, float, float, float]]:
        """
        Obtiene el extent del DEM cargado.
        
        Returns:
            Tupla (xmin, ymin, xmax, ymax) o None si no hay DEM
        """
        if self.header is None:
            return None
        
        xmin = self.header['xllcorner']
        ymin = self.header['yllcorner']
        xmax = xmin + self.header['ncols'] * self.header['cellsize']
        ymax = ymin + self.header['nrows'] * self.header['cellsize']
        
        return (xmin, ymin, xmax, ymax)
    
    @property
    def cellsize(self) -> Optional[float]:
        """Obtiene el tamaño de celda del DEM."""
        if self.header:
            return self.header.get('cellsize')
        return None
    
    @property
    def nodata_value(self) -> float:
        """Obtiene el valor NODATA del DEM."""
        if self.header:
            return self.header.get('nodata_value', self.NODATA_DEFAULT)
        return self.NODATA_DEFAULT