# -*- coding: utf-8 -*-
"""
Settings Module - Revanchas LT Plugin
Constantes y configuración centralizada

Este módulo centraliza todos los parámetros configurables del plugin,
evitando valores hardcodeados dispersos en el código.
"""

from typing import Dict, Any
import os


# =============================================================================
# PLUGIN INFO
# =============================================================================

PLUGIN_NAME = "Revanchas LT"
PLUGIN_VERSION = "2.0.0"
PLUGIN_AUTHOR = "Las Tortolas Project"
PLUGIN_EMAIL = "support@lastortolas.com"


# =============================================================================
# PROFILE GENERATION SETTINGS
# =============================================================================

class ProfileSettings:
    """Configuración para generación de perfiles topográficos"""
    
    # Ancho total del perfil en metros (±70m desde el eje = 140m total)
    PROFILE_WIDTH: float = 140.0
    
    # Resolución de muestreo en metros (distancia entre puntos)
    PROFILE_RESOLUTION: float = 0.1
    
    # Intervalo entre perfiles en metros
    PROFILE_INTERVAL: float = 20.0
    
    # Rango de visualización por defecto (±40m)
    DEFAULT_VIEW_RANGE: float = 40.0
    
    # Rango máximo de visualización (±70m)
    MAX_VIEW_RANGE: float = 70.0


# =============================================================================
# DEM SETTINGS
# =============================================================================

class DEMSettings:
    """Configuración para procesamiento de DEM"""
    
    # Valor NODATA por defecto para archivos ASC
    DEFAULT_NODATA: float = -9999.0
    
    # Buffer en metros para validación de cobertura
    COVERAGE_BUFFER: float = 50.0
    
    # Extensiones de archivo soportadas
    SUPPORTED_EXTENSIONS = ['.asc', '.tif', '.tiff']


# =============================================================================
# VISUALIZATION SETTINGS
# =============================================================================

class VisualizationSettings:
    """Configuración de visualización"""
    
    # Colores para elementos del perfil (formato matplotlib)
    COLOR_TERRAIN = '#8B4513'          # Marrón - terreno natural
    COLOR_TERRAIN_FILL = '#D2B48C'     # Beige claro - relleno terreno
    COLOR_LAMA = '#FFD700'             # Amarillo - punto LAMA
    COLOR_LAMA_LINE = '#FFA500'        # Naranja - línea LAMA
    COLOR_CROWN = '#00FF00'            # Verde - coronamiento
    COLOR_WIDTH_LINE = '#FF00FF'       # Magenta - línea de ancho
    COLOR_REFERENCE = '#0000FF'        # Azul - línea referencia
    COLOR_CENTERLINE = '#FF0000'       # Rojo - eje de alineación
    
    # Tamaño de marcadores
    MARKER_SIZE_SMALL = 6
    MARKER_SIZE_MEDIUM = 10
    MARKER_SIZE_LARGE = 14
    
    # Grosor de líneas
    LINE_WIDTH_THIN = 1.0
    LINE_WIDTH_NORMAL = 2.0
    LINE_WIDTH_THICK = 3.0
    
    # Configuración de la grilla
    GRID_ALPHA = 0.3
    GRID_STYLE = '--'


# =============================================================================
# MEASUREMENT SETTINGS
# =============================================================================

class MeasurementSettings:
    """Configuración para herramientas de medición"""
    
    # Radio de búsqueda para snap a terreno (en metros)
    SNAP_RADIUS: float = 2.0
    
    # Tolerancia para detección de intersecciones
    INTERSECTION_TOLERANCE: float = 0.5
    
    # Modos de operación disponibles
    MODE_REVANCHA = "measurement"
    MODE_ANCHO_PROYECTADO = "ancho_proyectado"


# =============================================================================
# PROJECT MANAGER SETTINGS
# =============================================================================

class ProjectSettings:
    """Configuración del gestor de proyectos"""
    
    # Extensión de archivos de proyecto
    PROJECT_EXTENSION = ".rvlt"
    
    # Versión del formato de proyecto
    PROJECT_FORMAT_VERSION = "1.0"
    
    # Número máximo de proyectos recientes
    MAX_RECENT_PROJECTS = 10


# =============================================================================
# WALL CONFIGURATION
# =============================================================================

# Mapeo de nombres internos a nombres de display
WALL_DISPLAY_NAMES: Dict[str, str] = {
    "Muro 1": "Muro Principal",
    "Muro 2": "Muro Oeste", 
    "Muro 3": "Muro Este"
}

# Mapeo inverso
WALL_INTERNAL_NAMES: Dict[str, str] = {v: k for k, v in WALL_DISPLAY_NAMES.items()}


# =============================================================================
# FILE PATHS
# =============================================================================

def get_plugin_dir() -> str:
    """Obtiene el directorio raíz del plugin"""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_data_dir() -> str:
    """Obtiene el directorio de datos del plugin"""
    return os.path.join(get_plugin_dir(), 'data')


def get_lama_points_dir() -> str:
    """Obtiene el directorio de puntos LAMA"""
    return os.path.join(get_data_dir(), 'lama_points')


def get_config_dir() -> str:
    """Obtiene el directorio de configuración"""
    return os.path.join(get_plugin_dir(), 'config')


# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================

class LoggingSettings:
    """Configuración de logging"""
    
    # Nivel de log por defecto
    DEFAULT_LEVEL = "INFO"
    
    # Formato de mensajes
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Prefijos para mensajes especiales
    PREFIX_SUCCESS = "✅"
    PREFIX_ERROR = "❌"
    PREFIX_WARNING = "⚠️"
    PREFIX_INFO = "ℹ️"
    PREFIX_DEBUG = "🔍"


# =============================================================================
# EXPORT SETTINGS
# =============================================================================

class ExportSettings:
    """Configuración para exportación de datos"""
    
    # Delimitador CSV
    CSV_DELIMITER = ","
    
    # Encoding por defecto
    DEFAULT_ENCODING = "utf-8"
    
    # Precisión decimal para coordenadas
    COORD_PRECISION = 3
    
    # Precisión decimal para elevaciones
    ELEVATION_PRECISION = 3
