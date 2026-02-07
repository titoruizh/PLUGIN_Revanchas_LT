# -*- coding: utf-8 -*-
"""
Validators Module - Revanchas LT Plugin
Funciones de validación centralizadas

Este módulo consolida la lógica de validación dispersa en el código,
evitando duplicación y facilitando mantenimiento.
"""

import os
import re
from typing import Dict, Any, Optional, Tuple, List

try:
    from ..config.settings import DEMSettings
except ImportError:
    # Fallback si no se puede importar settings
    class DEMSettings:
        COVERAGE_BUFFER = 50.0


def validate_file_exists(file_path: str) -> Tuple[bool, str]:
    """
    Valida que un archivo exista en el sistema de archivos.
    
    Args:
        file_path: Ruta al archivo a validar
        
    Returns:
        Tuple (es_válido, mensaje_error)
    """
    if not file_path:
        return False, "No se especificó ruta de archivo"
    
    if not os.path.exists(file_path):
        return False, f"Archivo no encontrado: {file_path}"
    
    if not os.path.isfile(file_path):
        return False, f"La ruta no es un archivo: {file_path}"
    
    return True, ""


def validate_file_extension(file_path: str, allowed_extensions: List[str]) -> Tuple[bool, str]:
    """
    Valida que un archivo tenga una extensión permitida.
    
    Args:
        file_path: Ruta al archivo
        allowed_extensions: Lista de extensiones permitidas (ej: ['.asc', '.tif'])
        
    Returns:
        Tuple (es_válido, mensaje_error)
    """
    if not file_path:
        return False, "No se especificó ruta de archivo"
    
    _, ext = os.path.splitext(file_path)
    ext_lower = ext.lower()
    
    if ext_lower not in [e.lower() for e in allowed_extensions]:
        return False, f"Extensión no soportada: {ext}. Permitidas: {', '.join(allowed_extensions)}"
    
    return True, ""


def validate_dem_coverage(
    dem_bounds: Dict[str, float], 
    alignment_bounds: Dict[str, float],
    buffer: float = None
) -> Dict[str, Any]:
    """
    Valida que un DEM cubra completamente una alineación.
    
    Args:
        dem_bounds: Diccionario con xmin, xmax, ymin, ymax del DEM
        alignment_bounds: Diccionario con xmin, xmax, ymin, ymax de la alineación
        buffer: Buffer adicional en metros (default: DEMSettings.COVERAGE_BUFFER)
        
    Returns:
        Diccionario con:
        - coverage_ok: bool indicando si hay cobertura
        - dem_bounds: bounds del DEM
        - alignment_bounds: bounds de la alineación (con buffer)
        - missing: qué bordes faltan cobertura
    """
    if buffer is None:
        buffer = DEMSettings.COVERAGE_BUFFER
    
    # Aplicar buffer a la alineación
    req_xmin = alignment_bounds['xmin'] - buffer
    req_xmax = alignment_bounds['xmax'] + buffer
    req_ymin = alignment_bounds['ymin'] - buffer
    req_ymax = alignment_bounds['ymax'] + buffer
    
    # Verificar cobertura
    missing = []
    
    if dem_bounds['xmin'] > req_xmin:
        missing.append(f"Oeste (falta {dem_bounds['xmin'] - req_xmin:.1f}m)")
    
    if dem_bounds['xmax'] < req_xmax:
        missing.append(f"Este (falta {req_xmax - dem_bounds['xmax']:.1f}m)")
    
    if dem_bounds['ymin'] > req_ymin:
        missing.append(f"Sur (falta {dem_bounds['ymin'] - req_ymin:.1f}m)")
    
    if dem_bounds['ymax'] < req_ymax:
        missing.append(f"Norte (falta {req_ymax - dem_bounds['ymax']:.1f}m)")
    
    return {
        'coverage_ok': len(missing) == 0,
        'dem_bounds': dem_bounds,
        'alignment_bounds': {
            'xmin': req_xmin,
            'xmax': req_xmax,
            'ymin': req_ymin,
            'ymax': req_ymax
        },
        'missing': missing
    }


def validate_pk_format(pk: str) -> Tuple[bool, str, Optional[float]]:
    """
    Valida formato de PK (progresiva kilométrica).
    
    Formatos válidos:
    - "0+000" (PK 0)
    - "1+234" (PK 1234m)
    - "12+345.67" (PK 12345.67m)
    
    Args:
        pk: String con el PK
        
    Returns:
        Tuple (es_válido, mensaje_error, valor_decimal)
    """
    if not pk:
        return False, "PK vacío", None
    
    # Patrón: número+número con decimales opcionales
    pattern = r'^(\d+)\+(\d{3}(?:\.\d+)?)$'
    match = re.match(pattern, pk)
    
    if not match:
        return False, f"Formato de PK inválido: {pk}. Esperado: X+XXX o X+XXX.XX", None
    
    km = int(match.group(1))
    m = float(match.group(2))
    decimal_value = km * 1000 + m
    
    return True, "", decimal_value


def validate_coordinates(x: float, y: float,
                         x_range: Optional[Tuple[float, float]] = None,
                         y_range: Optional[Tuple[float, float]] = None) -> Tuple[bool, str]:
    """
    Valida coordenadas.
    
    Args:
        x, y: Coordenadas a validar
        x_range: Rango válido para X (min, max)
        y_range: Rango válido para Y (min, max)
        
    Returns:
        Tuple (es_válido, mensaje_error)
    """
    # Verificar que sean números válidos
    try:
        float(x)
        float(y)
    except (TypeError, ValueError):
        return False, f"Coordenadas inválidas: ({x}, {y})"
    
    # Verificar rangos si se proporcionan
    if x_range:
        if not (x_range[0] <= x <= x_range[1]):
            return False, f"X={x} fuera de rango [{x_range[0]}, {x_range[1]}]"
    
    if y_range:
        if not (y_range[0] <= y <= y_range[1]):
            return False, f"Y={y} fuera de rango [{y_range[0]}, {y_range[1]}]"
    
    return True, ""


def validate_profile_data(profile: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Valida que un diccionario de perfil tenga los campos requeridos.
    
    Args:
        profile: Diccionario con datos del perfil
        
    Returns:
        Tuple (es_válido, mensaje_error)
    """
    required_fields = [
        'pk', 'pk_decimal', 'centerline_x', 'centerline_y',
        'distances', 'elevations'
    ]
    
    for field in required_fields:
        if field not in profile:
            return False, f"Campo requerido faltante: {field}"
    
    if len(profile['distances']) != len(profile['elevations']):
        return False, "Longitud de distances y elevations no coincide"
    
    if len(profile['distances']) == 0:
        return False, "Perfil sin datos de elevación"
    
    return True, ""


def validate_measurement_data(measurement: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Valida datos de medición.
    
    Args:
        measurement: Diccionario con datos de medición
        
    Returns:
        Tuple (es_válido, mensaje_error)
    """
    # Verificar que tenga al menos crown o width data
    has_crown = 'crown_x' in measurement and 'crown_y' in measurement
    has_width = 'width_left' in measurement or 'width_right' in measurement
    has_reference = 'reference_y' in measurement
    
    if not has_crown and not has_reference:
        return False, "Medición sin punto de referencia (crown o reference_y)"
    
    return True, ""


def validate_project_file(project_data: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Valida estructura de archivo de proyecto .rvlt
    
    Args:
        project_data: Diccionario con datos del proyecto
        
    Returns:
        Tuple (es_válido, mensaje_error)
    """
    required_sections = ['project_info', 'project_settings', 'file_paths', 'measurements_data']
    
    for section in required_sections:
        if section not in project_data:
            return False, f"Sección requerida faltante: {section}"
    
    if 'version' not in project_data.get('project_info', {}):
        return False, "Versión del proyecto no especificada"
    
    if 'wall_name' not in project_data.get('project_settings', {}):
        return False, "Nombre del muro no especificado"
    
    return True, ""


def validate_elevation_data(elevations: List[float], 
                            nodata_value: float = -9999.0) -> Dict[str, Any]:
    """
    Valida datos de elevación.
    
    Args:
        elevations: Lista de elevaciones
        nodata_value: Valor que indica sin datos
        
    Returns:
        Diccionario con estadísticas de validez
    """
    if not elevations:
        return {
            'valid': False,
            'total_count': 0,
            'valid_count': 0,
            'nodata_count': 0,
            'valid_percentage': 0.0
        }
    
    valid_elevations = [e for e in elevations if e != nodata_value]
    nodata_count = len(elevations) - len(valid_elevations)
    valid_percentage = (len(valid_elevations) / len(elevations)) * 100
    
    return {
        'valid': len(valid_elevations) > 0,
        'total_count': len(elevations),
        'valid_count': len(valid_elevations),
        'nodata_count': nodata_count,
        'valid_percentage': valid_percentage,
        'min_elevation': min(valid_elevations) if valid_elevations else None,
        'max_elevation': max(valid_elevations) if valid_elevations else None
    }


def validate_wall_name(wall_name: str, 
                       valid_names: Optional[List[str]] = None) -> Tuple[bool, str]:
    """
    Valida nombre de muro.
    
    Args:
        wall_name: Nombre del muro
        valid_names: Lista de nombres válidos (opcional)
        
    Returns:
        Tuple (es_válido, mensaje_error)
    """
    if not wall_name:
        return False, "Nombre de muro vacío"
    
    if not wall_name.strip():
        return False, "Nombre de muro contiene solo espacios"
    
    if valid_names and wall_name not in valid_names:
        return False, f"Muro desconocido: {wall_name}. Válidos: {', '.join(valid_names)}"
    
    return True, ""
