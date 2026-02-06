# -*- coding: utf-8 -*-
"""
Colors Module - Revanchas LT Plugin
Paleta de colores para temas modernos

Colores inspirados en Tailwind CSS y Material Design.
"""

from typing import Dict


class ColorPalette:
    """Paleta de colores base para temas."""
    
    # Slate (grises azulados)
    SLATE_50 = "#f8fafc"
    SLATE_100 = "#f1f5f9"
    SLATE_200 = "#e2e8f0"
    SLATE_300 = "#cbd5e1"
    SLATE_400 = "#94a3b8"
    SLATE_500 = "#64748b"
    SLATE_600 = "#475569"
    SLATE_700 = "#334155"
    SLATE_800 = "#1e293b"
    SLATE_900 = "#0f172a"
    SLATE_950 = "#020617"
    
    # Blue (azul primario)
    BLUE_50 = "#eff6ff"
    BLUE_100 = "#dbeafe"
    BLUE_200 = "#bfdbfe"
    BLUE_300 = "#93c5fd"
    BLUE_400 = "#60a5fa"
    BLUE_500 = "#3b82f6"
    BLUE_600 = "#2563eb"
    BLUE_700 = "#1d4ed8"
    BLUE_800 = "#1e40af"
    BLUE_900 = "#1e3a8a"
    
    # Green (éxito)
    GREEN_50 = "#f0fdf4"
    GREEN_400 = "#4ade80"
    GREEN_500 = "#22c55e"
    GREEN_600 = "#16a34a"
    
    # Yellow/Amber (advertencia)
    AMBER_50 = "#fffbeb"
    AMBER_400 = "#fbbf24"
    AMBER_500 = "#f59e0b"
    AMBER_600 = "#d97706"
    
    # Red (error)
    RED_50 = "#fef2f2"
    RED_400 = "#f87171"
    RED_500 = "#ef4444"
    RED_600 = "#dc2626"
    
    # Cyan (info)
    CYAN_400 = "#22d3ee"
    CYAN_500 = "#06b6d4"
    CYAN_600 = "#0891b2"


class DarkTheme:
    """Tema oscuro profesional estilo VS Code/Material."""
    
    # Fondos
    BG_PRIMARY = ColorPalette.SLATE_900      # #0f172a
    BG_SECONDARY = ColorPalette.SLATE_800    # #1e293b
    BG_TERTIARY = ColorPalette.SLATE_700     # #334155
    BG_HOVER = ColorPalette.SLATE_600        # #475569
    BG_INPUT = ColorPalette.SLATE_800        # #1e293b
    
    # Texto
    TEXT_PRIMARY = ColorPalette.SLATE_50     # #f8fafc
    TEXT_SECONDARY = ColorPalette.SLATE_400  # #94a3b8
    TEXT_MUTED = ColorPalette.SLATE_500      # #64748b
    TEXT_DISABLED = ColorPalette.SLATE_600   # #475569
    
    # Bordes
    BORDER = ColorPalette.SLATE_600          # #475569
    BORDER_FOCUS = ColorPalette.BLUE_500     # #3b82f6
    BORDER_LIGHT = ColorPalette.SLATE_700    # #334155
    
    # Accent (azul)
    ACCENT = ColorPalette.BLUE_500           # #3b82f6
    ACCENT_HOVER = ColorPalette.BLUE_400     # #60a5fa
    ACCENT_PRESSED = ColorPalette.BLUE_600   # #2563eb
    ACCENT_LIGHT = ColorPalette.BLUE_900     # #1e3a8a
    
    # Estados
    SUCCESS = ColorPalette.GREEN_500         # #22c55e
    SUCCESS_LIGHT = ColorPalette.GREEN_50    # #f0fdf4
    WARNING = ColorPalette.AMBER_500         # #f59e0b
    WARNING_LIGHT = ColorPalette.AMBER_50    # #fffbeb
    ERROR = ColorPalette.RED_500             # #ef4444
    ERROR_LIGHT = ColorPalette.RED_50        # #fef2f2
    INFO = ColorPalette.CYAN_500             # #06b6d4
    
    # Especiales
    SHADOW = "rgba(0, 0, 0, 0.3)"
    OVERLAY = "rgba(0, 0, 0, 0.5)"
    
    @classmethod
    def as_dict(cls) -> Dict[str, str]:
        """Retorna los colores como diccionario."""
        return {
            'bg_primary': cls.BG_PRIMARY,
            'bg_secondary': cls.BG_SECONDARY,
            'bg_tertiary': cls.BG_TERTIARY,
            'bg_hover': cls.BG_HOVER,
            'bg_input': cls.BG_INPUT,
            'text_primary': cls.TEXT_PRIMARY,
            'text_secondary': cls.TEXT_SECONDARY,
            'text_muted': cls.TEXT_MUTED,
            'text_disabled': cls.TEXT_DISABLED,
            'border': cls.BORDER,
            'border_focus': cls.BORDER_FOCUS,
            'border_light': cls.BORDER_LIGHT,
            'accent': cls.ACCENT,
            'accent_hover': cls.ACCENT_HOVER,
            'accent_pressed': cls.ACCENT_PRESSED,
            'success': cls.SUCCESS,
            'warning': cls.WARNING,
            'error': cls.ERROR,
            'info': cls.INFO,
        }


class LightTheme:
    """Tema claro profesional."""
    
    # Fondos
    BG_PRIMARY = "#ffffff"
    BG_SECONDARY = ColorPalette.SLATE_50     # #f8fafc
    BG_TERTIARY = ColorPalette.SLATE_100     # #f1f5f9
    BG_HOVER = ColorPalette.SLATE_200        # #e2e8f0
    BG_INPUT = "#ffffff"
    
    # Texto
    TEXT_PRIMARY = ColorPalette.SLATE_900    # #0f172a
    TEXT_SECONDARY = ColorPalette.SLATE_600  # #475569
    TEXT_MUTED = ColorPalette.SLATE_500      # #64748b
    TEXT_DISABLED = ColorPalette.SLATE_400   # #94a3b8
    
    # Bordes
    BORDER = ColorPalette.SLATE_300          # #cbd5e1
    BORDER_FOCUS = ColorPalette.BLUE_500     # #3b82f6
    BORDER_LIGHT = ColorPalette.SLATE_200    # #e2e8f0
    
    # Accent (azul)
    ACCENT = ColorPalette.BLUE_600           # #2563eb
    ACCENT_HOVER = ColorPalette.BLUE_500     # #3b82f6
    ACCENT_PRESSED = ColorPalette.BLUE_700   # #1d4ed8
    ACCENT_LIGHT = ColorPalette.BLUE_50      # #eff6ff
    
    # Estados
    SUCCESS = ColorPalette.GREEN_600         # #16a34a
    SUCCESS_LIGHT = ColorPalette.GREEN_50    # #f0fdf4
    WARNING = ColorPalette.AMBER_600         # #d97706
    WARNING_LIGHT = ColorPalette.AMBER_50    # #fffbeb
    ERROR = ColorPalette.RED_600             # #dc2626
    ERROR_LIGHT = ColorPalette.RED_50        # #fef2f2
    INFO = ColorPalette.CYAN_600             # #0891b2
    
    # Especiales
    SHADOW = "rgba(0, 0, 0, 0.1)"
    OVERLAY = "rgba(0, 0, 0, 0.3)"
    
    @classmethod
    def as_dict(cls) -> Dict[str, str]:
        """Retorna los colores como diccionario."""
        return {
            'bg_primary': cls.BG_PRIMARY,
            'bg_secondary': cls.BG_SECONDARY,
            'bg_tertiary': cls.BG_TERTIARY,
            'bg_hover': cls.BG_HOVER,
            'bg_input': cls.BG_INPUT,
            'text_primary': cls.TEXT_PRIMARY,
            'text_secondary': cls.TEXT_SECONDARY,
            'text_muted': cls.TEXT_MUTED,
            'text_disabled': cls.TEXT_DISABLED,
            'border': cls.BORDER,
            'border_focus': cls.BORDER_FOCUS,
            'border_light': cls.BORDER_LIGHT,
            'accent': cls.ACCENT,
            'accent_hover': cls.ACCENT_HOVER,
            'accent_pressed': cls.ACCENT_PRESSED,
            'success': cls.SUCCESS,
            'warning': cls.WARNING,
            'error': cls.ERROR,
            'info': cls.INFO,
        }


# Alias para acceso rápido
DARK = DarkTheme
LIGHT = LightTheme
