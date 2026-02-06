# -*- coding: utf-8 -*-
"""
Navigation Controller Module - Revanchas LT Plugin
Gestiona la navegación entre perfiles topográficos

Este módulo fue extraído de profile_viewer_dialog.py para mejorar
la modularidad y mantenibilidad del código.
"""

from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass

from qgis.PyQt.QtWidgets import (QWidget, QSlider, QPushButton, QLabel, 
                                  QHBoxLayout, QVBoxLayout, QGroupBox)
from qgis.PyQt.QtCore import Qt, pyqtSignal, QObject
from qgis.PyQt.QtGui import QFont


@dataclass
class ProfileInfo:
    """Información básica de un perfil para navegación."""
    index: int
    pk: str
    pk_decimal: float
    wall_name: Optional[str] = None


class NavigationController(QObject):
    """
    Controla la navegación entre perfiles topográficos.
    
    Emite señales cuando el perfil actual cambia, permitiendo
    que otros componentes reaccionen al cambio.
    
    Signals:
        profile_changed: Emitido cuando cambia el perfil actual
        range_changed: Emitido cuando cambia el rango de visualización
    """
    
    profile_changed = pyqtSignal(int, str)  # (index, pk)
    range_changed = pyqtSignal(int, int)    # (left, right)
    
    # Constantes
    DEFAULT_RANGE_LEFT = -40
    DEFAULT_RANGE_RIGHT = 40
    MAX_RANGE = 70
    MIN_RANGE = 10
    
    def __init__(self, profiles_data: List[Dict[str, Any]], parent: Optional[QWidget] = None):
        """
        Inicializa el controlador de navegación.
        
        Args:
            profiles_data: Lista de diccionarios con datos de perfiles
            parent: Widget padre opcional
        """
        super().__init__(parent)
        
        self.profiles_data = profiles_data
        self.current_index = 0
        
        # Rango de visualización personalizado
        self.range_left = self.DEFAULT_RANGE_LEFT
        self.range_right = self.DEFAULT_RANGE_RIGHT
        
        # Referencias a widgets (se configuran al crear el panel)
        self.slider: Optional[QSlider] = None
        self.pk_label: Optional[QLabel] = None
        self.counter_label: Optional[QLabel] = None
        self.prev_btn: Optional[QPushButton] = None
        self.next_btn: Optional[QPushButton] = None
    
    @property
    def current_profile(self) -> Optional[Dict[str, Any]]:
        """Obtiene el perfil actual."""
        if 0 <= self.current_index < len(self.profiles_data):
            return self.profiles_data[self.current_index]
        return None
    
    @property
    def current_pk(self) -> str:
        """Obtiene el PK del perfil actual."""
        profile = self.current_profile
        if profile:
            return profile.get('pk', profile.get('PK', f'?+???'))
        return '?+???'
    
    @property
    def total_profiles(self) -> int:
        """Número total de perfiles disponibles."""
        return len(self.profiles_data)
    
    @property
    def display_range(self) -> tuple:
        """Obtiene el rango de visualización actual (left, right)."""
        return (self.range_left, self.range_right)
    
    def navigate_to(self, index: int) -> bool:
        """
        Navega a un perfil específico por índice.
        
        Args:
            index: Índice del perfil destino (0-based)
            
        Returns:
            True si la navegación fue exitosa
        """
        if not 0 <= index < len(self.profiles_data):
            return False
        
        if index != self.current_index:
            self.current_index = index
            self._update_ui()
            self.profile_changed.emit(index, self.current_pk)
        
        return True
    
    def navigate_to_pk(self, pk: str) -> bool:
        """
        Navega a un perfil por su PK.
        
        Args:
            pk: PK del perfil (ej: "0+000", "1+434")
            
        Returns:
            True si se encontró y navegó al perfil
        """
        for i, profile in enumerate(self.profiles_data):
            profile_pk = profile.get('pk', profile.get('PK', ''))
            if profile_pk == pk:
                return self.navigate_to(i)
        return False
    
    def next_profile(self) -> bool:
        """
        Navega al siguiente perfil.
        
        Returns:
            True si había un siguiente perfil
        """
        if self.current_index < len(self.profiles_data) - 1:
            return self.navigate_to(self.current_index + 1)
        return False
    
    def prev_profile(self) -> bool:
        """
        Navega al perfil anterior.
        
        Returns:
            True si había un perfil anterior
        """
        if self.current_index > 0:
            return self.navigate_to(self.current_index - 1)
        return False
    
    def first_profile(self) -> bool:
        """Navega al primer perfil."""
        return self.navigate_to(0)
    
    def last_profile(self) -> bool:
        """Navega al último perfil."""
        return self.navigate_to(len(self.profiles_data) - 1)
    
    def set_display_range(self, left: int, right: int) -> bool:
        """
        Establece el rango de visualización.
        
        Args:
            left: Límite izquierdo (negativo, ej: -40)
            right: Límite derecho (positivo, ej: 40)
            
        Returns:
            True si el rango es válido y fue aplicado
        """
        # Validar rango
        if left >= right:
            return False
        
        if left < -self.MAX_RANGE or right > self.MAX_RANGE:
            return False
        
        if abs(right - left) < self.MIN_RANGE:
            return False
        
        self.range_left = left
        self.range_right = right
        self.range_changed.emit(left, right)
        
        return True
    
    def reset_range(self) -> None:
        """Restaura el rango de visualización por defecto."""
        self.set_display_range(self.DEFAULT_RANGE_LEFT, self.DEFAULT_RANGE_RIGHT)
    
    def get_profile_info(self, index: Optional[int] = None) -> Optional[ProfileInfo]:
        """
        Obtiene información de un perfil.
        
        Args:
            index: Índice del perfil (None = actual)
            
        Returns:
            ProfileInfo con datos del perfil
        """
        if index is None:
            index = self.current_index
        
        if not 0 <= index < len(self.profiles_data):
            return None
        
        profile = self.profiles_data[index]
        pk = profile.get('pk', profile.get('PK', '?+???'))
        pk_decimal = profile.get('pk_decimal', 0.0)
        
        # Detectar nombre del muro
        wall_name = self._detect_wall_name(profile)
        
        return ProfileInfo(
            index=index,
            pk=pk,
            pk_decimal=pk_decimal,
            wall_name=wall_name
        )
    
    def _detect_wall_name(self, profile: Dict[str, Any]) -> Optional[str]:
        """Detecta el nombre del muro basado en coordenadas."""
        if 'centerline_x' not in profile or 'centerline_y' not in profile:
            return None
        
        x = profile['centerline_x']
        y = profile['centerline_y']
        
        # Rangos aproximados para cada muro
        if 336688 <= x <= 337997 and 6334170 <= y <= 6334753:
            return "Muro Principal"
        elif 336193 <= x <= 336328 and 6332549 <= y <= 6333195:
            return "Muro Oeste"
        elif 339816 <= x <= 340114 and 6333743 <= y <= 6334206:
            return "Muro Este"
        
        return None
    
    def _update_ui(self) -> None:
        """Actualiza los widgets de UI con el estado actual."""
        if self.slider is not None:
            self.slider.blockSignals(True)
            self.slider.setValue(self.current_index)
            self.slider.blockSignals(False)
        
        if self.pk_label is not None:
            self.pk_label.setText(f"PK {self.current_pk}")
        
        if self.counter_label is not None:
            self.counter_label.setText(f"{self.current_index + 1} / {len(self.profiles_data)}")
        
        if self.prev_btn is not None:
            self.prev_btn.setEnabled(self.current_index > 0)
        
        if self.next_btn is not None:
            self.next_btn.setEnabled(self.current_index < len(self.profiles_data) - 1)
    
    def _on_slider_changed(self, value: int) -> None:
        """Handler para cambio del slider."""
        self.navigate_to(value)
    
    def _on_prev_clicked(self) -> None:
        """Handler para botón anterior."""
        self.prev_profile()
    
    def _on_next_clicked(self) -> None:
        """Handler para botón siguiente."""
        self.next_profile()
    
    def create_navigation_widget(self) -> QWidget:
        """
        Crea y retorna un widget con controles de navegación.
        
        Returns:
            QWidget con slider, botones y etiquetas de navegación
        """
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Botón anterior
        self.prev_btn = QPushButton("◀ Anterior")
        self.prev_btn.clicked.connect(self._on_prev_clicked)
        
        # Slider
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(len(self.profiles_data) - 1)
        self.slider.setValue(self.current_index)
        self.slider.valueChanged.connect(self._on_slider_changed)
        
        # Botón siguiente
        self.next_btn = QPushButton("Siguiente ▶")
        self.next_btn.clicked.connect(self._on_next_clicked)
        
        # Etiqueta PK
        self.pk_label = QLabel(f"PK {self.current_pk}")
        self.pk_label.setFont(QFont("Arial", 12, QFont.Bold))
        
        # Contador
        self.counter_label = QLabel(f"{self.current_index + 1} / {len(self.profiles_data)}")
        
        # Ensamblar
        layout.addWidget(self.prev_btn)
        layout.addWidget(self.slider, stretch=1)
        layout.addWidget(self.next_btn)
        layout.addWidget(self.pk_label)
        layout.addWidget(self.counter_label)
        
        # Actualizar estado inicial
        self._update_ui()
        
        return widget
    
    def connect_external_slider(self, slider: QSlider) -> None:
        """
        Conecta un slider externo al controlador.
        
        Args:
            slider: QSlider a conectar
        """
        self.slider = slider
        slider.setMinimum(0)
        slider.setMaximum(len(self.profiles_data) - 1)
        slider.setValue(self.current_index)
        slider.valueChanged.connect(self._on_slider_changed)
    
    def sync_with_ortho_viewer(self, ortho_viewer) -> None:
        """
        Sincroniza la navegación con el visualizador de ortomosaico.
        
        Args:
            ortho_viewer: Instancia de OrthomosaicViewer
        """
        def update_ortho():
            profile = self.current_profile
            if profile and ortho_viewer:
                x = profile.get('centerline_x')
                y = profile.get('centerline_y')
                if x and y:
                    ortho_viewer.update_location(x, y, self.current_pk)
        
        self.profile_changed.connect(lambda idx, pk: update_ortho())
