# -*- coding: utf-8 -*-
"""
Profile Viewer Package - Revanchas LT Plugin
Módulos del visualizador interactivo de perfiles

Este paquete contiene los componentes modularizados del visualizador:
- viewer_dialog: Diálogo principal (orquestador) - PENDIENTE
- profile_canvas: Renderizado matplotlib ✅
- measurement_controller: Lógica de medición ✅
- navigation_controller: Navegación entre perfiles ✅
- export_manager: Exportación de datos ✅
"""

# Módulos nuevos ya extraídos
from .export_manager import ExportManager
from .navigation_controller import NavigationController, ProfileInfo
from .measurement_controller import (
    MeasurementController, 
    MeasurementMode, 
    OperationMode,
    ProfileMeasurements,
    WidthMeasurement,
    MeasurementPoint
)
from .profile_canvas import ProfileCanvas, ProfileRenderConfig

# Por ahora exportamos desde el archivo legacy
# Se irá migrando gradualmente
from ...profile_viewer_dialog import InteractiveProfileViewer

__all__ = [
    'InteractiveProfileViewer', 
    'ExportManager',
    'NavigationController',
    'ProfileInfo',
    'MeasurementController',
    'MeasurementMode',
    'OperationMode',
    'ProfileMeasurements',
    'WidthMeasurement',
    'MeasurementPoint',
    'ProfileCanvas',
    'ProfileRenderConfig'
]



