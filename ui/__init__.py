# -*- coding: utf-8 -*-
"""
UI Package - Revanchas LT Plugin
Capa de presentación del plugin

Este paquete contiene:
- dialogs/: Diálogos y ventanas del plugin
- widgets/: Widgets reutilizables
"""

# Importar widgets
from .widgets.custom_toolbar import CustomNavigationToolbar

# Importar componentes del visor de perfiles
from .dialogs.profile_viewer.export_manager import ExportManager
from .dialogs.profile_viewer.navigation_controller import NavigationController
from .dialogs.profile_viewer.measurement_controller import MeasurementController
from .dialogs.profile_viewer.profile_canvas import ProfileCanvas

__all__ = [
    'CustomNavigationToolbar',
    'ExportManager',
    'NavigationController',
    'MeasurementController',
    'ProfileCanvas',
]
