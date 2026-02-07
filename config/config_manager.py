# -*- coding: utf-8 -*-
"""
Config Manager Module - Revanchas LT Plugin
Gestiona la carga y acceso a configuración desde archivos JSON

Este módulo proporciona acceso centralizado a la configuración del plugin,
permitiendo externalizar datos que antes estaban hardcodeados.
"""

import os
import json
from typing import Dict, Any, Optional, List

from .settings import get_plugin_dir, get_config_dir


class ConfigManager:
    """
    Gestor de configuración centralizado.
    
    Carga configuración desde archivos JSON y proporciona acceso
    estructurado a los datos de configuración del plugin.
    
    Attributes:
        config: Diccionario con configuración cargada
        walls_config: Configuración específica de muros
    """
    
    _instance = None  # Singleton instance
    
    def __new__(cls):
        """Implementa patrón Singleton para configuración global."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Inicializa el gestor de configuración."""
        if self._initialized:
            return
        
        self.config: Dict[str, Any] = {}
        self.walls_config: Dict[str, Any] = {}
        self._config_loaded = False
        
        # Cargar configuración automáticamente
        self.load_config()
        self._initialized = True
    
    def load_config(self) -> bool:
        """
        Carga la configuración desde archivos JSON.
        
        Returns:
            True si la carga fue exitosa, False en caso contrario
        """
        try:
            config_path = os.path.join(get_config_dir(), 'walls.json')
            
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                
                self.walls_config = self.config.get('walls', {})
                self._config_loaded = True
                print(f"✅ Configuración cargada desde: {config_path}")
                return True
            else:
                print(f"⚠️ Archivo de configuración no encontrado: {config_path}")
                self._use_default_config()
                return False
                
        except json.JSONDecodeError as e:
            print(f"❌ Error al parsear configuración JSON: {e}")
            self._use_default_config()
            return False
        except Exception as e:
            print(f"❌ Error al cargar configuración: {e}")
            self._use_default_config()
            return False
    
    def _use_default_config(self) -> None:
        """Establece configuración por defecto si no se puede cargar el archivo."""
        self.config = {
            "version": "1.0",
            "walls": {},
            "profile_settings": {
                "width": 140.0,
                "resolution": 0.1,
                "default_view_range": 40.0,
                "max_view_range": 70.0
            }
        }
        self.walls_config = {}
    
    @property
    def is_loaded(self) -> bool:
        """Indica si la configuración fue cargada correctamente."""
        return self._config_loaded
    
    def get_wall_names(self) -> List[str]:
        """
        Obtiene lista de nombres internos de muros disponibles.
        
        Returns:
            Lista de nombres internos ['Muro 1', 'Muro 2', 'Muro 3']
        """
        return list(self.walls_config.keys())
    
    def get_wall_display_name(self, internal_name: str) -> str:
        """
        Obtiene el nombre de display para un muro.
        
        Args:
            internal_name: Nombre interno del muro (ej: "Muro 1")
            
        Returns:
            Nombre de display (ej: "Muro Principal")
        """
        wall = self.walls_config.get(internal_name, {})
        return wall.get('display_name', internal_name)
    
    def get_wall_config(self, wall_name: str) -> Dict[str, Any]:
        """
        Obtiene configuración completa de un muro.
        
        Args:
            wall_name: Nombre interno del muro
            
        Returns:
            Diccionario con configuración del muro
        """
        return self.walls_config.get(wall_name, {})
    
    def get_wall_alignment_type(self, wall_name: str) -> str:
        """
        Obtiene el tipo de alineación de un muro.
        
        Args:
            wall_name: Nombre interno del muro
            
        Returns:
            'straight' o 'curved'
        """
        wall = self.walls_config.get(wall_name, {})
        return wall.get('alignment_type', 'straight')
    
    def get_wall_start_point(self, wall_name: str) -> Optional[Dict[str, float]]:
        """
        Obtiene coordenadas del punto inicial de un muro.
        
        Args:
            wall_name: Nombre interno del muro
            
        Returns:
            Dict con {x, y} o None
        """
        wall = self.walls_config.get(wall_name, {})
        return wall.get('start_point')
    
    def get_wall_end_point(self, wall_name: str) -> Optional[Dict[str, float]]:
        """
        Obtiene coordenadas del punto final de un muro.
        
        Args:
            wall_name: Nombre interno del muro
            
        Returns:
            Dict con {x, y} o None
        """
        wall = self.walls_config.get(wall_name, {})
        return wall.get('end_point')
    
    def get_wall_total_length(self, wall_name: str) -> float:
        """
        Obtiene longitud total de un muro.
        
        Args:
            wall_name: Nombre interno del muro
            
        Returns:
            Longitud en metros
        """
        wall = self.walls_config.get(wall_name, {})
        return wall.get('total_length', 0.0)
    
    def get_wall_interval(self, wall_name: str) -> float:
        """
        Obtiene intervalo entre estaciones de un muro.
        
        Args:
            wall_name: Nombre interno del muro
            
        Returns:
            Intervalo en metros (default: 20.0)
        """
        wall = self.walls_config.get(wall_name, {})
        return wall.get('interval', 20.0)
    
    def get_wall_display_range(self, wall_name: str) -> Dict[str, int]:
        """
        Obtiene rango de visualización por defecto para un muro.
        
        Args:
            wall_name: Nombre interno del muro
            
        Returns:
            Dict con {left, right} en metros
        """
        wall = self.walls_config.get(wall_name, {})
        default_range = {'left': -40, 'right': 40}
        return wall.get('display_range', default_range)
    
    def get_profile_settings(self) -> Dict[str, Any]:
        """
        Obtiene configuración de perfiles.
        
        Returns:
            Dict con settings de perfiles
        """
        return self.config.get('profile_settings', {
            'width': 140.0,
            'resolution': 0.1,
            'default_view_range': 40.0,
            'max_view_range': 70.0
        })
    
    def get_dem_settings(self) -> Dict[str, Any]:
        """
        Obtiene configuración de DEM.
        
        Returns:
            Dict con settings de DEM
        """
        return self.config.get('dem_settings', {
            'default_nodata': -9999.0,
            'coverage_buffer': 50.0,
            'supported_extensions': ['.asc', '.tif', '.tiff']
        })
    
    def get_visualization_settings(self) -> Dict[str, Any]:
        """
        Obtiene configuración de visualización.
        
        Returns:
            Dict con colores, tamaños de marcadores, etc.
        """
        return self.config.get('visualization', {})
    
    def get_color(self, color_name: str) -> str:
        """
        Obtiene un color de la configuración de visualización.
        
        Args:
            color_name: Nombre del color (ej: 'terrain', 'lama', 'crown')
            
        Returns:
            Color en formato hex
        """
        viz = self.get_visualization_settings()
        colors = viz.get('colors', {})
        
        default_colors = {
            'terrain': '#8B4513',
            'terrain_fill': '#D2B48C',
            'lama': '#FFD700',
            'lama_line': '#FFA500',
            'crown': '#00FF00',
            'width_line': '#FF00FF',
            'reference': '#0000FF',
            'centerline': '#FF0000'
        }
        
        return colors.get(color_name, default_colors.get(color_name, '#000000'))
    
    def reload_config(self) -> bool:
        """
        Recarga la configuración desde disco.
        
        Returns:
            True si la recarga fue exitosa
        """
        self._config_loaded = False
        return self.load_config()


# Instancia global para acceso fácil
_config_manager = None


def get_config() -> ConfigManager:
    """
    Obtiene la instancia singleton del ConfigManager.
    
    Returns:
        Instancia de ConfigManager
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager
