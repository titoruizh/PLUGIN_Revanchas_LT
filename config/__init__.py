# -*- coding: utf-8 -*-
"""
Config Package - Revanchas LT Plugin
Configuración centralizada del plugin

Este paquete contiene:
- settings.py: Constantes y configuración estática
- config_manager.py: Gestor de configuración dinámica desde JSON
- walls.json: Datos de configuración de muros
"""

from .settings import (
    PLUGIN_NAME,
    PLUGIN_VERSION,
    PROFILE_WIDTH,
    PROFILE_RESOLUTION,
    DEM_NODATA_VALUE,
    get_plugin_dir,
    get_config_dir
)

from .config_manager import ConfigManager, get_config

__all__ = [
    'PLUGIN_NAME',
    'PLUGIN_VERSION',
    'PROFILE_WIDTH',
    'PROFILE_RESOLUTION',
    'DEM_NODATA_VALUE',
    'get_plugin_dir',
    'get_config_dir',
    'ConfigManager',
    'get_config'
]
