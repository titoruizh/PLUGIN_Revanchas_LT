# -*- coding: utf-8 -*-
"""
Theme Manager - Revanchas LT Plugin
Gestor centralizado de temas para la interfaz de usuario

Uso:
    from ui.themes import ThemeManager
    
    # Aplicar tema oscuro a toda la aplicación
    ThemeManager.apply_dark_theme(app)
    
    # Aplicar tema a un widget específico
    ThemeManager.apply_theme(dialog, 'dark')
    
    # Cambiar tema en runtime
    ThemeManager.toggle_theme(widget)
"""

import os
from typing import Optional, Literal
from enum import Enum

from qgis.PyQt.QtWidgets import QWidget, QApplication
from qgis.PyQt.QtCore import QFile, QTextStream
from qgis.PyQt.QtGui import QColor, QPalette

from .colors import DarkTheme, LightTheme, ColorPalette


class Theme(Enum):
    """Temas disponibles."""
    DARK = "dark"
    LIGHT = "light"
    SYSTEM = "system"


class ThemeManager:
    """
    Gestor de temas para el plugin.
    
    Proporciona métodos para aplicar, cambiar y gestionar
    temas visuales en la interfaz de usuario.
    """
    
    _current_theme: Theme = Theme.DARK
    _themes_dir: Optional[str] = None
    
    @classmethod
    def get_themes_dir(cls) -> str:
        """Obtiene el directorio de temas."""
        if cls._themes_dir is None:
            cls._themes_dir = os.path.dirname(os.path.abspath(__file__))
        return cls._themes_dir
    
    @classmethod
    def get_current_theme(cls) -> Theme:
        """Retorna el tema actual."""
        return cls._current_theme
    
    @classmethod
    def load_stylesheet(cls, theme: Theme) -> str:
        """
        Carga el archivo QSS para el tema especificado.
        
        Args:
            theme: Tema a cargar
            
        Returns:
            Contenido del stylesheet como string
        """
        if theme == Theme.SYSTEM:
            theme = cls._detect_system_theme()
        
        theme_file = f"{theme.value}_theme.qss"
        file_path = os.path.join(cls.get_themes_dir(), theme_file)
        
        if not os.path.exists(file_path):
            print(f"[ThemeManager] Archivo de tema no encontrado: {file_path}")
            return ""
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                stylesheet = f.read()
            return stylesheet
        except Exception as e:
            print(f"[ThemeManager] Error cargando tema: {e}")
            return ""
    
    @classmethod
    def apply_theme(cls, widget: QWidget, theme: Theme = Theme.DARK) -> None:
        """
        Aplica un tema a un widget específico.
        
        Args:
            widget: Widget al que aplicar el tema
            theme: Tema a aplicar
        """
        stylesheet = cls.load_stylesheet(theme)
        if stylesheet:
            widget.setStyleSheet(stylesheet)
            cls._current_theme = theme
            print(f"[ThemeManager] Tema '{theme.value}' aplicado a {widget.__class__.__name__}")
    
    @classmethod
    def apply_dark_theme(cls, widget: QWidget) -> None:
        """Aplica el tema oscuro."""
        cls.apply_theme(widget, Theme.DARK)
    
    @classmethod
    def apply_light_theme(cls, widget: QWidget) -> None:
        """Aplica el tema claro."""
        cls.apply_theme(widget, Theme.LIGHT)
    
    @classmethod
    def toggle_theme(cls, widget: QWidget) -> Theme:
        """
        Cambia entre tema oscuro y claro.
        
        Args:
            widget: Widget al que aplicar el cambio
            
        Returns:
            El nuevo tema aplicado
        """
        new_theme = Theme.LIGHT if cls._current_theme == Theme.DARK else Theme.DARK
        cls.apply_theme(widget, new_theme)
        return new_theme
    
    @classmethod
    def _detect_system_theme(cls) -> Theme:
        """
        Detecta el tema del sistema operativo.
        
        Returns:
            Theme.DARK o Theme.LIGHT basado en la configuración del sistema
        """
        try:
            # Intentar detectar tema del sistema via palette
            app = QApplication.instance()
            if app:
                palette = app.palette()
                bg_color = palette.color(QPalette.Window)
                # Si el fondo es más oscuro que claro, es tema oscuro
                luminance = (bg_color.red() * 0.299 + 
                           bg_color.green() * 0.587 + 
                           bg_color.blue() * 0.114)
                return Theme.DARK if luminance < 128 else Theme.LIGHT
        except Exception:
            pass
        
        # Por defecto retornar tema oscuro
        return Theme.DARK
    
    @classmethod
    def get_color(cls, color_name: str, theme: Optional[Theme] = None) -> str:
        """
        Obtiene un color del tema actual o especificado.
        
        Args:
            color_name: Nombre del color (ej: 'accent', 'bg_primary')
            theme: Tema del cual obtener el color
            
        Returns:
            Código de color hexadecimal
        """
        if theme is None:
            theme = cls._current_theme
        
        colors = DarkTheme.as_dict() if theme == Theme.DARK else LightTheme.as_dict()
        return colors.get(color_name, '#000000')
    
    @classmethod
    def get_qcolor(cls, color_name: str, theme: Optional[Theme] = None) -> QColor:
        """
        Obtiene un QColor del tema actual o especificado.
        
        Args:
            color_name: Nombre del color
            theme: Tema del cual obtener el color
            
        Returns:
            QColor del color especificado
        """
        hex_color = cls.get_color(color_name, theme)
        return QColor(hex_color)


class ModernStyleHelper:
    """
    Helper para aplicar estilos modernos adicionales.
    
    Proporciona métodos para efectos especiales como
    sombras, animaciones y transiciones.
    """
    
    @staticmethod
    def add_shadow(widget: QWidget, blur: int = 20, 
                   offset_x: int = 0, offset_y: int = 4,
                   color: Optional[QColor] = None) -> None:
        """
        Agrega efecto de sombra a un widget.
        
        Args:
            widget: Widget al que agregar sombra
            blur: Radio de blur de la sombra
            offset_x: Desplazamiento horizontal
            offset_y: Desplazamiento vertical
            color: Color de la sombra
        """
        from qgis.PyQt.QtWidgets import QGraphicsDropShadowEffect
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(blur)
        shadow.setOffset(offset_x, offset_y)
        
        if color is None:
            color = QColor(0, 0, 0, 60)
        shadow.setColor(color)
        
        widget.setGraphicsEffect(shadow)
    
    @staticmethod
    def set_rounded_corners(widget: QWidget, radius: int = 8) -> None:
        """
        Establece esquinas redondeadas en un widget.
        
        Args:
            widget: Widget a modificar
            radius: Radio de las esquinas en píxeles
        """
        widget.setStyleSheet(
            widget.styleSheet() + f"\nborder-radius: {radius}px;"
        )
    
    @staticmethod
    def make_button_primary(widget) -> None:
        """Aplica estilo de botón primario."""
        widget.setProperty("class", "primary")
        widget.style().unpolish(widget)
        widget.style().polish(widget)
    
    @staticmethod
    def make_button_secondary(widget) -> None:
        """Aplica estilo de botón secundario."""
        widget.setProperty("class", "secondary")
        widget.style().unpolish(widget)
        widget.style().polish(widget)
    
    @staticmethod
    def make_button_success(widget) -> None:
        """Aplica estilo de botón de éxito."""
        widget.setProperty("class", "success")
        widget.style().unpolish(widget)
        widget.style().polish(widget)
    
    @staticmethod
    def make_button_danger(widget) -> None:
        """Aplica estilo de botón de peligro."""
        widget.setProperty("class", "danger")
        widget.style().unpolish(widget)
        widget.style().polish(widget)


# Funciones de conveniencia
def apply_dark_theme(widget: QWidget) -> None:
    """Aplica tema oscuro al widget."""
    ThemeManager.apply_dark_theme(widget)


def apply_light_theme(widget: QWidget) -> None:
    """Aplica tema claro al widget."""
    ThemeManager.apply_light_theme(widget)


def toggle_theme(widget: QWidget) -> Theme:
    """Alterna entre temas."""
    return ThemeManager.toggle_theme(widget)


def get_current_theme() -> Theme:
    """Obtiene el tema actual."""
    return ThemeManager.get_current_theme()
