# -*- coding: utf-8 -*-
"""
Themes Package - Revanchas LT Plugin
Sistema de theming moderno para la interfaz de usuario

Este paquete contiene:
- theme_manager.py: Gestor centralizado de temas
- colors.py: Paleta de colores (Dark/Light)
- dark_theme.qss: Stylesheet tema oscuro
- light_theme.qss: Stylesheet tema claro

Uso básico:
    from ui.themes import ThemeManager, Theme
    
    # Aplicar tema oscuro
    ThemeManager.apply_dark_theme(my_dialog)
    
    # Alternar tema
    ThemeManager.toggle_theme(my_dialog)
    
    # Obtener color del tema actual
    accent_color = ThemeManager.get_color('accent')
"""

from .theme_manager import (
    ThemeManager,
    Theme,
    ModernStyleHelper,
    apply_dark_theme,
    apply_light_theme,
    toggle_theme,
    get_current_theme,
)

from .colors import (
    ColorPalette,
    DarkTheme,
    LightTheme,
    DARK,
    LIGHT,
)

__all__ = [
    # Theme Manager
    'ThemeManager',
    'Theme',
    'ModernStyleHelper',
    'apply_dark_theme',
    'apply_light_theme',
    'toggle_theme',
    'get_current_theme',
    # Colors
    'ColorPalette',
    'DarkTheme',
    'LightTheme',
    'DARK',
    'LIGHT',
]
