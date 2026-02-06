# -*- coding: utf-8 -*-
"""
Custom Navigation Toolbar - Revanchas LT Plugin
Barra de herramientas personalizada para navegación de perfiles topográficos

Este módulo fue extraído de profile_viewer_dialog.py para mejorar
la modularidad y mantenibilidad del código.
"""

from qgis.PyQt.QtWidgets import (QPushButton, QLabel, QSpinBox, QMessageBox)

# Importar matplotlib con manejo de errores
try:
    from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
    HAS_MATPLOTLIB = True
except ImportError:
    try:
        from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
        HAS_MATPLOTLIB = True
    except ImportError:
        HAS_MATPLOTLIB = False
        # Crear clase dummy si matplotlib no está disponible
        class NavigationToolbar:
            def __init__(self, *args, **kwargs):
                pass


class CustomNavigationToolbar(NavigationToolbar):
    """
    Barra de herramientas de navegación personalizada con funciones topográficas.
    
    Características:
    - Botones básicos: Home, Pan, Zoom
    - Control de rango de visualización (izquierdo/derecho)
    - Toggle de leyenda
    - Indicador de porcentaje de zoom
    """
    
    def __init__(self, canvas, parent, profile_viewer):
        """
        Inicializa la barra de herramientas personalizada.
        
        Args:
            canvas: Canvas de matplotlib
            parent: Widget padre
            profile_viewer: Referencia al InteractiveProfileViewer
        """
        super().__init__(canvas, parent)
        self.profile_viewer = profile_viewer
        
        # Limpiar botones no deseados
        self._remove_unwanted_buttons()
        
        # Agregar botón de extensión
        self._add_extent_button()
        
        # Agregar controles de rango
        self._add_range_controls()
        
        # Agregar toggle de leyenda
        self._add_legend_toggle()
        
        # Agregar indicador de zoom
        self._add_zoom_indicator()
    
    def _remove_unwanted_buttons(self):
        """Elimina botones no necesarios de la barra de herramientas."""
        wanted_actions = ['home', 'pan', 'zoom']
        
        for action in self.actions():
            if hasattr(action, 'text') and action.text():
                action_text = action.text().lower()
                if not any(wanted in action_text for wanted in wanted_actions):
                    self.removeAction(action)
            elif hasattr(action, 'toolTip') and action.toolTip():
                tooltip_text = action.toolTip().lower()
                if 'back' in tooltip_text or 'forward' in tooltip_text or 'configure' in tooltip_text:
                    self.removeAction(action)
    
    def _add_extent_button(self):
        """Agrega botón de zoom a extensión completa."""
        self.addSeparator()
        
        zoom_extent_action = self.addAction("🔍 Extensión")
        zoom_extent_action.triggered.connect(self.zoom_to_profile_extent)
        zoom_extent_action.setToolTip("Vista completa del perfil (-50m a +50m)")
    
    def _add_range_controls(self):
        """Agrega controles de rango de visualización."""
        self.addSeparator()
        
        # Label
        range_label = QLabel("  Rango (m):")
        range_label.setStyleSheet("font-weight: bold; padding: 5px;")
        self.addWidget(range_label)
        
        # SpinBox izquierdo
        self.addWidget(QLabel(" Izq:"))
        self.left_limit_spin = QSpinBox()
        self.left_limit_spin.setMinimum(-70)
        self.left_limit_spin.setMaximum(0)
        self.left_limit_spin.setValue(-40)
        self.left_limit_spin.setSuffix("m")
        self.left_limit_spin.setToolTip("Límite izquierdo del perfil (-70 a 0)")
        self.left_limit_spin.valueChanged.connect(self.on_range_changed)
        self.addWidget(self.left_limit_spin)
        
        # SpinBox derecho
        self.addWidget(QLabel(" Der:"))
        self.right_limit_spin = QSpinBox()
        self.right_limit_spin.setMinimum(0)
        self.right_limit_spin.setMaximum(70)
        self.right_limit_spin.setValue(40)
        self.right_limit_spin.setSuffix("m")
        self.right_limit_spin.setToolTip("Límite derecho del perfil (0 a 70)")
        self.right_limit_spin.valueChanged.connect(self.on_range_changed)
        self.addWidget(self.right_limit_spin)
        
        # Botón aplicar
        apply_range_btn = QPushButton("✓")
        apply_range_btn.setMaximumWidth(30)
        apply_range_btn.setToolTip("Aplicar rango personalizado")
        apply_range_btn.clicked.connect(self.apply_custom_range)
        self.addWidget(apply_range_btn)
    
    def _add_legend_toggle(self):
        """Agrega botón toggle de leyenda."""
        self.addSeparator()
        
        self.legend_btn = QPushButton("📋 Leyenda")
        self.legend_btn.setCheckable(True)
        self.legend_btn.setChecked(False)
        self.legend_btn.setToolTip("Activar/Desactivar leyenda")
        self.legend_btn.clicked.connect(self.toggle_legend)
        self.addWidget(self.legend_btn)
    
    def _add_zoom_indicator(self):
        """Agrega indicador de nivel de zoom."""
        self.addSeparator()
        
        self.zoom_label = QLabel("Zoom: 100%")
        self.zoom_label.setStyleSheet("color: #333; font-weight: bold; padding: 5px;")
        self.addWidget(self.zoom_label)
        
        # Conectar a eventos de zoom
        self.profile_viewer.canvas.mpl_connect('xlim_changed', self.on_zoom_changed)
    
    def zoom_to_profile_extent(self):
        """Zoom a la extensión completa del perfil."""
        ax = self.profile_viewer.ax
        profile = self.profile_viewer.profiles_data[self.profile_viewer.current_profile_index]
        
        # Obtener rango específico del muro
        x_min, x_max = self.profile_viewer.get_wall_display_range(profile)
        
        # Obtener elevaciones válidas para eje Y
        distances = profile.get('distances', [])
        elevations = profile.get('elevations', [])
        valid_data = [(d, e) for d, e in zip(distances, elevations) 
                      if e != -9999 and x_min <= d <= x_max]
        
        if valid_data:
            valid_distances, valid_elevations = zip(*valid_data)
            
            # Incluir líneas de referencia si existen
            current_pk = profile['pk']
            crown_elevation = None
            if current_pk in self.profile_viewer.saved_measurements:
                crown_data = self.profile_viewer.saved_measurements[current_pk].get('crown')
                if crown_data:
                    crown_elevation = crown_data.get('y')
            elif self.profile_viewer.current_crown_point:
                crown_elevation = self.profile_viewer.current_crown_point[1]
            
            y_values = list(valid_elevations)
            if crown_elevation is not None:
                y_values.extend([crown_elevation, crown_elevation - 1.0])
            
            margin_y = (max(y_values) - min(y_values)) * 0.05
            
            # Aplicar rangos
            ax.set_xlim(x_min, x_max)
            ax.set_ylim(min(y_values) - margin_y, max(y_values) + margin_y)
            self.profile_viewer.canvas.draw()
            self.update_zoom_label()
    
    def on_zoom_changed(self, ax):
        """Actualiza indicador de zoom cuando cambia el nivel de zoom."""
        self.update_zoom_label()
    
    def update_zoom_label(self):
        """Actualiza el porcentaje de zoom."""
        ax = self.profile_viewer.ax
        profile = self.profile_viewer.profiles_data[self.profile_viewer.current_profile_index]
        
        x_min, x_max = self.profile_viewer.get_wall_display_range(profile)
        full_width = x_max - x_min
        
        xlim = ax.get_xlim()
        current_width = xlim[1] - xlim[0]
        
        zoom_percentage = (full_width / current_width) * 100
        self.zoom_label.setText(f"Zoom: {zoom_percentage:.0f}%")
    
    def on_range_changed(self):
        """Handler cuando cambian los spinboxes de rango."""
        pass  # No hacer nada, esperar al botón aplicar
    
    def apply_custom_range(self):
        """Aplica el rango personalizado al perfil."""
        left = self.left_limit_spin.value()
        right = self.right_limit_spin.value()
        
        if left >= right:
            QMessageBox.warning(
                self, 
                "Rango inválido",
                "El límite izquierdo debe ser menor que el derecho"
            )
            return
        
        # Actualizar rango personalizado
        self.profile_viewer.custom_range_left = left
        self.profile_viewer.custom_range_right = right
        
        # Redibujar perfil
        self.profile_viewer.update_profile_display()
        
        # Zoom a extensión completa del nuevo rango
        self.zoom_to_profile_extent()
    
    def toggle_legend(self):
        """Activa/desactiva la visualización de la leyenda."""
        self.profile_viewer.show_legend = self.legend_btn.isChecked()
        self.profile_viewer.update_profile_display()
