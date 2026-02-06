# -*- coding: utf-8 -*-
"""
Modern Widgets - Revanchas LT Plugin
Widgets personalizados con estilos modernos

Incluye:
- ModernButton: Botón con gradientes y efectos
- ModernCard: Panel con sombra
- ModernInput: Input estilizado
- StatusBadge: Badge de estado
"""

from typing import Optional

from qgis.PyQt.QtWidgets import (
    QPushButton, QFrame, QLabel, QLineEdit, QVBoxLayout,
    QHBoxLayout, QGraphicsDropShadowEffect, QSizePolicy
)
from qgis.PyQt.QtCore import Qt, QSize, pyqtSignal
from qgis.PyQt.QtGui import QColor, QFont, QIcon


class ModernButton(QPushButton):
    """
    Botón moderno con estilos predefinidos.
    
    Variantes:
    - primary: Azul gradient (default)
    - secondary: Gris con borde
    - success: Verde gradient
    - danger: Rojo gradient
    - ghost: Transparente con hover
    
    Uso:
        btn = ModernButton("Guardar", variant="success")
        btn = ModernButton("Eliminar", variant="danger", icon=QIcon("trash.svg"))
    """
    
    VARIANTS = {
        'primary': """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3b82f6, stop:1 #2563eb);
                border: none;
                border-radius: 8px;
                color: white;
                padding: 12px 24px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #60a5fa, stop:1 #3b82f6);
            }
            QPushButton:pressed {
                background: #1d4ed8;
            }
            QPushButton:disabled {
                background: #334155;
                color: #64748b;
            }
        """,
        'secondary': """
            QPushButton {
                background: #1e293b;
                border: 1px solid #475569;
                border-radius: 8px;
                color: #f8fafc;
                padding: 12px 24px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background: #334155;
                border-color: #60a5fa;
            }
            QPushButton:pressed {
                background: #475569;
            }
        """,
        'success': """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #22c55e, stop:1 #16a34a);
                border: none;
                border-radius: 8px;
                color: white;
                padding: 12px 24px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4ade80, stop:1 #22c55e);
            }
            QPushButton:pressed {
                background: #15803d;
            }
        """,
        'danger': """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ef4444, stop:1 #dc2626);
                border: none;
                border-radius: 8px;
                color: white;
                padding: 12px 24px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f87171, stop:1 #ef4444);
            }
            QPushButton:pressed {
                background: #b91c1c;
            }
        """,
        'ghost': """
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 8px;
                color: #94a3b8;
                padding: 12px 24px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background: #334155;
                color: #f8fafc;
            }
            QPushButton:pressed {
                background: #475569;
            }
        """,
        'warning': """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f59e0b, stop:1 #d97706);
                border: none;
                border-radius: 8px;
                color: white;
                padding: 12px 24px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #fbbf24, stop:1 #f59e0b);
            }
            QPushButton:pressed {
                background: #b45309;
            }
        """,
    }
    
    def __init__(self, text: str = "", 
                 variant: str = "primary",
                 icon: Optional[QIcon] = None,
                 parent=None):
        super().__init__(text, parent)
        
        self.variant = variant
        self._apply_variant(variant)
        
        if icon:
            self.setIcon(icon)
            self.setIconSize(QSize(20, 20))
        
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(44)
    
    def _apply_variant(self, variant: str) -> None:
        """Aplica el estilo de la variante."""
        style = self.VARIANTS.get(variant, self.VARIANTS['primary'])
        self.setStyleSheet(style)
    
    def set_variant(self, variant: str) -> None:
        """Cambia la variante del botón."""
        self.variant = variant
        self._apply_variant(variant)


class ModernCard(QFrame):
    """
    Card/Panel moderno con sombra y bordes redondeados.
    
    Uso:
        card = ModernCard()
        card.set_title("Configuración")
        card.layout().addWidget(content)
    """
    
    def __init__(self, parent=None, title: str = None):
        super().__init__(parent)
        
        self._setup_style()
        self._setup_layout()
        self._add_shadow()
        
        if title:
            self.set_title(title)
    
    def _setup_style(self) -> None:
        """Configura el estilo del card."""
        self.setStyleSheet("""
            ModernCard {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 12px;
            }
        """)
    
    def _setup_layout(self) -> None:
        """Configura el layout interno."""
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(20, 20, 20, 20)
        self._layout.setSpacing(16)
        
        self._title_label = None
    
    def _add_shadow(self) -> None:
        """Agrega efecto de sombra."""
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 60))
        self.setGraphicsEffect(shadow)
    
    def set_title(self, title: str) -> None:
        """Establece el título del card."""
        if self._title_label is None:
            self._title_label = QLabel()
            self._title_label.setStyleSheet("""
                QLabel {
                    color: #f8fafc;
                    font-size: 16px;
                    font-weight: bold;
                    margin-bottom: 8px;
                }
            """)
            self._layout.insertWidget(0, self._title_label)
        
        self._title_label.setText(title)
    
    def add_widget(self, widget) -> None:
        """Agrega un widget al card."""
        self._layout.addWidget(widget)
    
    def add_layout(self, layout) -> None:
        """Agrega un layout al card."""
        self._layout.addLayout(layout)


class ModernInput(QLineEdit):
    """
    Input de texto moderno con estilo consistente.
    
    Uso:
        input = ModernInput(placeholder="Ingrese nombre...")
        input.set_error(True)  # Mostrar estado de error
    """
    
    def __init__(self, placeholder: str = "", parent=None):
        super().__init__(parent)
        
        self.setPlaceholderText(placeholder)
        self._apply_style()
        self._error_state = False
    
    def _apply_style(self) -> None:
        """Aplica el estilo del input."""
        self.setStyleSheet("""
            QLineEdit {
                background-color: #1e293b;
                border: 2px solid #334155;
                border-radius: 8px;
                padding: 12px 16px;
                color: #f8fafc;
                font-size: 14px;
                selection-background-color: #3b82f6;
            }
            QLineEdit:hover {
                border-color: #475569;
            }
            QLineEdit:focus {
                border-color: #3b82f6;
            }
            QLineEdit:disabled {
                background-color: #0f172a;
                color: #64748b;
                border-color: #1e293b;
            }
        """)
        self.setMinimumHeight(48)
    
    def set_error(self, error: bool) -> None:
        """Establece estado de error."""
        self._error_state = error
        if error:
            self.setStyleSheet(self.styleSheet().replace(
                "border-color: #3b82f6", "border-color: #ef4444"
            ))
        else:
            self._apply_style()


class StatusBadge(QLabel):
    """
    Badge de estado moderno.
    
    Variantes: success, warning, error, info, neutral
    
    Uso:
        badge = StatusBadge("Activo", variant="success")
    """
    
    VARIANTS = {
        'success': {'bg': '#166534', 'text': '#4ade80', 'border': '#22c55e'},
        'warning': {'bg': '#854d0e', 'text': '#fbbf24', 'border': '#f59e0b'},
        'error': {'bg': '#991b1b', 'text': '#f87171', 'border': '#ef4444'},
        'info': {'bg': '#164e63', 'text': '#22d3ee', 'border': '#06b6d4'},
        'neutral': {'bg': '#334155', 'text': '#94a3b8', 'border': '#475569'},
    }
    
    def __init__(self, text: str, variant: str = "neutral", parent=None):
        super().__init__(text, parent)
        
        self._apply_variant(variant)
        self.setAlignment(Qt.AlignCenter)
    
    def _apply_variant(self, variant: str) -> None:
        """Aplica el estilo de la variante."""
        colors = self.VARIANTS.get(variant, self.VARIANTS['neutral'])
        
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {colors['bg']};
                color: {colors['text']};
                border: 1px solid {colors['border']};
                border-radius: 12px;
                padding: 4px 12px;
                font-size: 12px;
                font-weight: bold;
            }}
        """)


class ModernDivider(QFrame):
    """
    Línea divisoria horizontal moderna.
    
    Uso:
        layout.addWidget(ModernDivider())
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setFrameShape(QFrame.HLine)
        self.setStyleSheet("""
            QFrame {
                background-color: #334155;
                max-height: 1px;
                border: none;
            }
        """)
        self.setFixedHeight(1)


class IconButton(QPushButton):
    """
    Botón de solo icono moderno.
    
    Uso:
        btn = IconButton(QIcon("settings.svg"))
    """
    
    def __init__(self, icon: QIcon, size: int = 36, parent=None):
        super().__init__(parent)
        
        self.setIcon(icon)
        self.setIconSize(QSize(size - 12, size - 12))
        self.setFixedSize(QSize(size, size))
        self.setCursor(Qt.PointingHandCursor)
        
        self.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #334155;
            }
            QPushButton:pressed {
                background-color: #475569;
            }
        """)
