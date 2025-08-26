
import os
from qgis.PyQt.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                                 QLabel, QSlider, QGroupBox, QMessageBox,
                                 QFileDialog, QProgressDialog, QApplication)
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QFont
from qgis.core import QgsApplication

try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


class CustomNavigationToolbar(NavigationToolbar):
    """Custom navigation toolbar with essential topographic tools only"""
    
    def __init__(self, canvas, parent, profile_viewer):
        super().__init__(canvas, parent)
        self.profile_viewer = profile_viewer
        
        # Remove ALL unwanted buttons and keep only essential ones
        actions = self.actions()
        
        # Keep only: Home, Pan, Zoom
        wanted_actions = ['home', 'pan', 'zoom']
        
        # Remove all actions except the ones we want
        for action in actions:
            if hasattr(action, 'text') and action.text():
                action_text = action.text().lower()
                # Remove back, forward, configure, coordinates, etc.
                if not any(wanted in action_text for wanted in wanted_actions):
                    self.removeAction(action)
            elif hasattr(action, 'toolTip') and action.toolTip():
                tooltip_text = action.toolTip().lower()
                if 'back' in tooltip_text or 'forward' in tooltip_text or 'configure' in tooltip_text:
                    self.removeAction(action)
        
        # Add ONLY zoom extent button
        self.addSeparator()
        
        # Only Zoom to extent (fit profile in view)
        zoom_extent_action = self.addAction("🔍 Extensión")
        zoom_extent_action.triggered.connect(self.zoom_to_profile_extent)
        zoom_extent_action.setToolTip("Vista completa del perfil (-50m a +50m)")
        
        self.addSeparator()
        
        # Add simple zoom level indicator (no coordinates)
        self.zoom_label = QLabel("Zoom: 100%")
        self.zoom_label.setStyleSheet("color: #333; font-weight: bold; padding: 5px;")
        self.addWidget(self.zoom_label)
        
        # Connect to zoom events
        self.profile_viewer.canvas.mpl_connect('xlim_changed', self.on_zoom_changed)
    
    def zoom_to_profile_extent(self):
        """Zoom to full profile extent with wall-specific ranges"""
        ax = self.profile_viewer.ax
        profile = self.profile_viewer.profiles_data[self.profile_viewer.current_profile_index]
        
        # 🆕 OBTENER RANGO ESPECÍFICO DEL MURO
        x_min, x_max = self.profile_viewer.get_wall_display_range(profile)
        
        # Get valid elevations for Y-axis
        distances = profile.get('distances', [])
        elevations = profile.get('elevations', [])
        valid_data = [(d, e) for d, e in zip(distances, elevations) 
                    if e != -9999 and x_min <= d <= x_max]  # 🔧 USAR RANGO DINÁMICO
        
        if valid_data:
            valid_distances, valid_elevations = zip(*valid_data)
            
            # Include reference lines if they exist
            current_pk = profile['pk']
            crown_elevation = None
            if current_pk in self.profile_viewer.saved_measurements and 'crown' in self.profile_viewer.saved_measurements[current_pk]:
                crown_elevation = self.profile_viewer.saved_measurements[current_pk]['crown']['y']
            elif self.profile_viewer.current_crown_point:
                crown_elevation = self.profile_viewer.current_crown_point[1]
            
            y_values = list(valid_elevations)
            if crown_elevation is not None:
                y_values.extend([crown_elevation, crown_elevation - 1.0])
            
            margin_y = (max(y_values) - min(y_values)) * 0.05
            
            # 🆕 USAR RANGOS DINÁMICOS
            ax.set_xlim(x_min, x_max)
            ax.set_ylim(min(y_values) - margin_y, max(y_values) + margin_y)
            self.profile_viewer.canvas.draw()
            self.update_zoom_label()
    
    def on_zoom_changed(self, ax):
        """Update zoom level indicator when zoom changes"""
        self.update_zoom_label()
    
    def update_zoom_label(self):
        """Update zoom level percentage with dynamic width"""
        ax = self.profile_viewer.ax
        profile = self.profile_viewer.profiles_data[self.profile_viewer.current_profile_index]
        
        # 🆕 OBTENER ANCHO DINÁMICO
        x_min, x_max = self.profile_viewer.get_wall_display_range(profile)
        full_width = x_max - x_min  # Ancho dinámico según el muro
        
        xlim = ax.get_xlim()
        current_width = xlim[1] - xlim[0]
        
        zoom_percentage = (full_width / current_width) * 100
        
        self.zoom_label.setText(f"Zoom: {zoom_percentage:.0f}%")


class InteractiveProfileViewer(QDialog):
    """Interactive profile viewer with navigation and measurement tools"""
    
    def __init__(self, profiles_data, parent=None):
        super().__init__(parent)
        self.profiles_data = profiles_data
        self.current_profile_index = 0
        self.measurement_mode = None
        
        # Separate measurements per PK
        self.saved_measurements = {}  # PK -> {crown: {x, y}, width: {p1, p2, distance}}
        
        # Current temporary measurements (reset when changing PK)
        self.current_crown_point = None
        self.current_width_points = []
        
        # Auto-detection parameters
        self.auto_width_detection = True
        self.pretil_height_threshold = 0.5  # metros - diferencia mínima para detectar pretil
        self.search_step = 0.5  # metros - paso de búsqueda
        
        # Initialize key state BEFORE UI creation
        self._key_A_pressed = False
        
        self.setWindowTitle("Visualizador Interactivo de Perfiles")
        self.setModal(True)
        self.resize(1200, 800)
        
        if HAS_MATPLOTLIB:
            self.init_ui()
            # Setup keyboard events AFTER UI is fully created
            self.setup_keyboard_events()
        else:
            self.init_no_matplotlib()
        
        # AHORA es seguro acceder a self.canvas:
        self._key_A_pressed = False
        self.canvas.setFocusPolicy(Qt.StrongFocus)
        self.canvas.setFocus()
        self.canvas.mpl_connect('key_press_event', self.on_key_press)
        self.canvas.mpl_connect('key_release_event', self.on_key_release)

    def setup_keyboard_events(self):
        """Setup keyboard event handling after UI is created"""
        self.canvas.setFocusPolicy(Qt.StrongFocus)
        self.canvas.mpl_connect('key_press_event', self.on_key_press)
        self.canvas.mpl_connect('key_release_event', self.on_key_release)
        
        # Ensure canvas gets focus immediately
        self.canvas.setFocus()

    def on_key_press(self, event):
        """Handle key press events"""
        if event.key == 'a':
            self._key_A_pressed = True
            # Visual feedback when A is pressed during width measurement
            if self.measurement_mode == 'width':
                self.auto_status.setText("🎯 SNAP AUTOMÁTICO ACTIVO - Haz clic para intersección con terreno")
                self.auto_status.setStyleSheet("color: red; font-style: italic; font-weight: bold;")

    def on_key_release(self, event):
        """Handle key release events"""
        if event.key == 'a':
            self._key_A_pressed = False
            # Restore normal status when A is released
            if self.measurement_mode == 'width':
                self.auto_status.setText("Herramienta Ancho activa - Presiona 'A' para auto-snap")
                self.auto_status.setStyleSheet("color: purple; font-style: italic; font-weight: bold;")

    def on_mouse_scroll(self, event):
        """Handle mouse wheel zoom - UPDATED for new range"""
        if not event.inaxes:
            return
        
        # Get current axis limits
        ax = self.ax
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()
        
        # Current zoom level (100% = full extent -50 to +50 = 100m width)
        current_width = xlim[1] - xlim[0]
        x_min, x_max = self.get_wall_display_range()
        full_width = x_max - x_min  # Ancho dinámico según el muro
        current_zoom = (full_width / current_width) * 100
        
        # LIMIT ZOOM OUT - No permitir zoom out más allá del 100%
        if event.button == 'down' and current_zoom <= 100:
            return
        
        # Zoom factor
        zoom_factor = 0.85 if event.button == 'up' else 1.18
        
        # Center calculation
        current_center_x = (xlim[0] + xlim[1]) / 2
        current_center_y = (ylim[0] + ylim[1]) / 2
        
        x_center = event.xdata * 0.2 + current_center_x * 0.8
        y_center = event.ydata * 0.2 + current_center_y * 0.8
        
        if x_center is None or y_center is None:
            return
        
        # Calculate new limits
        x_width = (xlim[1] - xlim[0]) * zoom_factor
        y_height = (ylim[1] - ylim[0]) * zoom_factor
        
        new_xlim = [x_center - x_width/2, x_center + x_width/2]
        new_ylim = [y_center - y_height/2, y_center + y_height/2]
        
        # CONSTRAIN X-AXIS TO PROFILE BOUNDS (-50 to +50)
        if new_xlim[0] < x_min:
            new_xlim = [x_min, x_min + x_width]
        if new_xlim[1] > x_max:
            new_xlim = [x_max - x_width, x_max]
        
        # DOUBLE CHECK: No permitir zoom out más allá de extensión completa
        if new_xlim[1] - new_xlim[0] > full_width:
            # Forzar a zoom extensión completa
            new_xlim = [x_min, x_max]
            # Mantener Y proporcional
            profile = self.profiles_data[self.current_profile_index]
            distances = profile.get('distances', [])
            elevations = profile.get('elevations', [])
            valid_data = [(d, e) for d, e in zip(distances, elevations) if e != -9999 and x_min <= d <= x_max]
            
            if valid_data:
                _, valid_elevations = zip(*valid_data)
                
                # Include reference lines if they exist
                current_pk = profile['pk']
                crown_elevation = None
                if current_pk in self.saved_measurements and 'crown' in self.saved_measurements[current_pk]:
                    crown_elevation = self.saved_measurements[current_pk]['crown']['y']
                elif self.current_crown_point:
                    crown_elevation = self.current_crown_point[1]
                
                y_values = list(valid_elevations)
                if crown_elevation is not None:
                    y_values.extend([crown_elevation, crown_elevation - 1.0])
                
                margin_y = (max(y_values) - min(y_values)) * 0.05
                new_ylim = [min(y_values) - margin_y, max(y_values) + margin_y]
        
        # Apply new limits
        ax.set_xlim(new_xlim)
        ax.set_ylim(new_ylim)
        
        # Update display
        self.canvas.draw()
        if hasattr(self, 'toolbar'):
            self.toolbar.update_zoom_label()

    def get_wall_display_range(self, profile=None):
        if not profile:
            profile = self.profiles_data[self.current_profile_index]
        
        # Usar alignment_type si está disponible (más confiable)
        station = profile.get('station', {})
        alignment_type = station.get('alignment_type', None)
        
        if alignment_type == 'curved':
            return (-20, 40)  # Muro 2: rango especial
        
        # Si no, fallback a coordenadas (por compatibilidad)
        if 'centerline_x' in profile and 'centerline_y' in profile:
            x = profile['centerline_x']
            y = profile['centerline_y']
            if 336193 <= x <= 336328 and 6332549 <= y <= 6333195:
                return (-20, 40)
        
        # Default para Muro 1 y 3
        return (-40, 20)

    def detect_wall_name(self, profile):
        """Detecta el nombre del muro para mostrar en el título"""
        if 'centerline_x' in profile and 'centerline_y' in profile:
            x = profile['centerline_x']
            y = profile['centerline_y']
            
            if 336688 <= x <= 337997 and 6334170 <= y <= 6334753:
                return "Muro Principal"
            elif 336193 <= x <= 336328 and 6332549 <= y <= 6333195:
                return "Muro Oeste"
            elif 339816 <= x <= 340114 and 6333743 <= y <= 6334206:
                return "Muro Este"
        return None
    
    def init_matplotlib(self):
        """Initialize matplotlib components with navigation toolbar"""
        self.figure = Figure(figsize=(14, 8))
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        
        # Custom navigation toolbar with topographic tools
        self.toolbar = CustomNavigationToolbar(self.canvas, self, self)
        
        # Enable matplotlib interactions
        self.canvas.mpl_connect('button_press_event', self.on_canvas_click)
        
        # Enable mouse wheel zoom
        self.canvas.mpl_connect('scroll_event', self.on_mouse_scroll)
        
        layout = QVBoxLayout()
        
        # Add toolbar ABOVE canvas
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas, stretch=1)
        
        self.setLayout(layout)
    
    def init_ui(self):
        """Initialize the user interface with zoom controls"""
        layout = QVBoxLayout()
        
        # Matplotlib canvas with toolbar
        self.figure = Figure(figsize=(14, 8))
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        
        # Custom navigation toolbar
        self.toolbar = CustomNavigationToolbar(self.canvas, self, self)
        
        # Enable matplotlib interactions
        self.canvas.mpl_connect('button_press_event', self.on_canvas_click)
        self.canvas.mpl_connect('scroll_event', self.on_mouse_scroll)
        
        # Control panels
        control_panel = self.create_control_panel()
        measurement_panel = self.create_measurement_panel()
        info_panel = self.create_info_panel()
        
        # Layout assembly with toolbar
        layout.addWidget(control_panel)
        layout.addWidget(self.toolbar)  # Navigation toolbar
        layout.addWidget(self.canvas, stretch=1)
        
        bottom_layout = QHBoxLayout()
        bottom_layout.addWidget(measurement_panel)
        bottom_layout.addWidget(info_panel)
        layout.addLayout(bottom_layout)
        
        self.setLayout(layout)
        
        # Initialize with first profile
        if self.profiles_data:
            self.update_profile_display()
            # Set initial zoom to full extent
            self.toolbar.zoom_to_profile_extent()
    
    def create_control_panel(self):
        """Create navigation control panel"""
        group = QGroupBox("🧭 Navegación de Perfiles")
        layout = QHBoxLayout()
        
        # Previous/Next buttons
        self.prev_btn = QPushButton("◀ Anterior")
        self.next_btn = QPushButton("Siguiente ▶")
        self.prev_btn.clicked.connect(self.prev_profile)
        self.next_btn.clicked.connect(self.next_profile)
        
        # PK slider
        self.pk_slider = QSlider(Qt.Horizontal)
        self.pk_slider.setMinimum(0)
        self.pk_slider.setMaximum(len(self.profiles_data) - 1)
        self.pk_slider.setValue(0)
        self.pk_slider.valueChanged.connect(self.on_slider_changed)
        
        # Current PK label
        self.current_pk_label = QLabel("PK 0+000")
        self.current_pk_label.setFont(QFont("Arial", 12, QFont.Bold))
        
        # Profile counter
        self.profile_counter = QLabel(f"1 / {len(self.profiles_data)}")
        
        layout.addWidget(self.prev_btn)
        layout.addWidget(self.pk_slider, stretch=1)
        layout.addWidget(self.next_btn)
        layout.addWidget(self.current_pk_label)
        layout.addWidget(self.profile_counter)
        
        group.setLayout(layout)
        return group
    
    def create_measurement_panel(self):
        """Create measurement tools panel"""
        group = QGroupBox("🔧 Herramientas de Medición")
        layout = QVBoxLayout()
        
        # Measurement mode buttons (PRIMERA FILA)
        btn_layout1 = QHBoxLayout()
        
        self.crown_btn = QPushButton("📍 Cota Coronamiento")
        self.width_btn = QPushButton("📏 Medir Ancho")
        self.lama_btn = QPushButton("🟡 Modificar LAMA")
        self.clear_btn = QPushButton("🗑️ Limpiar")
        
        self.crown_btn.setCheckable(True)
        self.width_btn.setCheckable(True)
        self.lama_btn.setCheckable(True)
        
        self.crown_btn.clicked.connect(lambda: self.set_measurement_mode('crown'))
        self.width_btn.clicked.connect(lambda: self.set_measurement_mode('width'))
        self.lama_btn.clicked.connect(lambda: self.set_measurement_mode('lama'))
        self.clear_btn.clicked.connect(self.clear_current_measurements)
        
        btn_layout1.addWidget(self.crown_btn)
        btn_layout1.addWidget(self.width_btn)
        btn_layout1.addWidget(self.lama_btn)
        btn_layout1.addWidget(self.clear_btn)
        
        # Auto-detection toggle (SEGUNDA FILA)
        btn_layout2 = QHBoxLayout()
        self.auto_detect_btn = QPushButton("🤖 Auto-Detección: ON")
        self.auto_detect_btn.setCheckable(True)
        self.auto_detect_btn.setChecked(True)
        self.auto_detect_btn.clicked.connect(self.toggle_auto_detection)
        btn_layout2.addWidget(self.auto_detect_btn)
        
        # BOTÓN DE EXPORTACIÓN (TERCERA FILA)
        btn_layout3 = QHBoxLayout()
        self.export_btn = QPushButton("📊 Exportar Mediciones CSV")
        self.export_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 8px;")
        self.export_btn.clicked.connect(self.export_measurements_to_csv)
        btn_layout3.addWidget(self.export_btn)
        
        # Measurement results
        self.crown_result = QLabel("Cota Coronamiento: --")
        self.width_result = QLabel("Ancho medido: --")
        self.lama_result = QLabel("Cota LAMA: --")
        self.revancha_result = QLabel("Revancha: --")
        
        # Auto-detection status
        self.auto_status = QLabel("Auto-detección activada")
        self.auto_status.setStyleSheet("color: green; font-style: italic;")
        
        # Assembly
        layout.addLayout(btn_layout1)
        layout.addLayout(btn_layout2)
        layout.addLayout(btn_layout3)
        layout.addWidget(self.crown_result)
        layout.addWidget(self.width_result)
        layout.addWidget(self.lama_result)
        layout.addWidget(self.revancha_result)
        layout.addWidget(self.auto_status)
        
        group.setLayout(layout)
        return group
        
    def create_info_panel(self):
        """Create profile information panel"""
        group = QGroupBox("ℹ️ Información del Perfil")
        layout = QVBoxLayout()
        
        self.info_pk = QLabel("PK: --")
        self.info_coords = QLabel("Coordenadas: --")
        self.info_elevation_range = QLabel("Rango elevación: --")
        self.info_valid_points = QLabel("Puntos válidos: --")
        
        layout.addWidget(self.info_pk)
        layout.addWidget(self.info_coords)
        layout.addWidget(self.info_elevation_range)
        layout.addWidget(self.info_valid_points)
        
        group.setLayout(layout)
        return group
    
    def toggle_auto_detection(self):
        """Toggle automatic width detection"""
        self.auto_width_detection = self.auto_detect_btn.isChecked()
        
        if self.auto_width_detection:
            self.auto_detect_btn.setText("🤖 Auto-Detección: ON")
            self.auto_status.setText("Auto-detección activada")
            self.auto_status.setStyleSheet("color: green; font-style: italic;")
        else:
            self.auto_detect_btn.setText("🤖 Auto-Detección: OFF")
            self.auto_status.setText("Modo manual activado")
            self.auto_status.setStyleSheet("color: orange; font-style: italic;")
    
    def set_measurement_mode(self, mode):
        """Set measurement mode and ensure canvas has focus"""
        if mode == 'crown':
            self.measurement_mode = 'crown'
            self.crown_btn.setChecked(True)
            self.width_btn.setChecked(False)
            self.lama_btn.setChecked(False)
        elif mode == 'width':
            self.measurement_mode = 'width' 
            self.width_btn.setChecked(True)
            self.crown_btn.setChecked(False)
            self.lama_btn.setChecked(False)
            self.current_width_points = []  # Reset width measurement
        elif mode == 'lama':
            self.measurement_mode = 'lama'
            self.lama_btn.setChecked(True)
            self.crown_btn.setChecked(False)
            self.width_btn.setChecked(False)
        
        self.canvas.setCursor(Qt.CrossCursor)
        
        # CRITICAL: Ensure canvas has focus when entering measurement mode
        self.canvas.setFocus()
        
        # Add visual indicator that canvas is ready for keyboard input
        if mode == 'width':
            self.auto_status.setText("Herramienta Ancho activa - Presiona 'A' para auto-snap")
            self.auto_status.setStyleSheet("color: purple; font-style: italic; font-weight: bold;")
    
    def clear_current_measurements(self):
        """Clear measurements ONLY for current PK including reference line"""
        current_pk = self.profiles_data[self.current_profile_index]['pk']
        
        # Remove saved measurements for this PK
        if current_pk in self.saved_measurements:
            del self.saved_measurements[current_pk]
        
        # Clear current temporary measurements
        self.current_crown_point = None
        self.current_width_points = []
        
        # Reset UI
        self.measurement_mode = None
        self.crown_btn.setChecked(False)
        self.width_btn.setChecked(False)
        self.lama_btn.setChecked(False)
        self.crown_result.setText("Cota Coronamiento: --")
        self.width_result.setText("Ancho medido: --")
        self.lama_result.setText("Cota LAMA: --")
        self.revancha_result.setText("Revancha: --")
        self.canvas.setCursor(Qt.ArrowCursor)
        
        # This will remove the reference line too since crown is cleared
        self.update_profile_display()
    
    def find_nearest_terrain_point(self, x_click):
        """ONLY snap to horizontal reference line for width measurements"""
        current_pk = self.profiles_data[self.current_profile_index]['pk']
        
        # ONLY REFERENCE LINE SNAP - No terrain snap for width measurements
        crown_elevation = None
        if current_pk in self.saved_measurements and 'crown' in self.saved_measurements[current_pk]:
            crown_elevation = self.saved_measurements[current_pk]['crown']['y']
        elif self.current_crown_point:
            crown_elevation = self.current_crown_point[1]
        
        # Return point on reference line or None
        if crown_elevation is not None:
            # Ensure click is within reasonable range (-50 to +50)
            if -50 <= x_click <= 50:
                return (x_click, crown_elevation)  # Exact X click, crown Y
        
        # NO TERRAIN SNAP - Return None if no reference line
        return None
    
    def find_terrain_snap_point(self, x_click):
        """Find closest point ONLY on terrain natural (for crown and lama)"""
        profile = self.profiles_data[self.current_profile_index]
        distances = profile.get('distances', [])
        elevations = profile.get('elevations', [])
        
        # Filter valid terrain data points
        valid_terrain_data = [(d, e) for d, e in zip(distances, elevations) if e != -9999]
        
        if not valid_terrain_data:
            return None
        
        # Find closest point on terrain
        min_diff = float('inf')
        closest_point = None
        
        for distance, elevation in valid_terrain_data:
            diff = abs(distance - x_click)
            if diff < min_diff:
                min_diff = diff
                closest_point = (distance, elevation)
        
        return closest_point
    
    def detect_road_width_automatically(self, crown_x, crown_y):
        """IMPROVED: Auto-detect full road width with better algorithm"""
        profile = self.profiles_data[self.current_profile_index]
        distances = profile.get('distances', [])
        elevations = profile.get('elevations', [])
        
        # Filter valid data points and sort by distance
        valid_data = [(d, e) for d, e in zip(distances, elevations) if e != -9999]
        valid_data.sort(key=lambda x: x[0])  # Sort by distance
        
        if len(valid_data) < 20:  # Need enough points
            print(f"❌ Not enough data points: {len(valid_data)}")
            return None, None
        
        print(f"🔍 Auto-detecting from {len(valid_data)} points, crown at X={crown_x:.2f}")
        
        # DEBUG - Add this line
        self.debug_profile_data(crown_x, crown_y)
        
        # Find left and right boundaries using simpler approach
        left_boundary = self.find_boundary_simple(valid_data, crown_x, crown_y, 'left')
        right_boundary = self.find_boundary_simple(valid_data, crown_x, crown_y, 'right')
        
        if left_boundary and right_boundary:
            print(f"✅ Detected boundaries: Left={left_boundary[0]:.2f}, Right={right_boundary[0]:.2f}")
            return left_boundary, right_boundary
        else:
            print("❌ Could not find boundaries")
            return None, None
        
    def find_boundary_simple(self, valid_data, crown_x, crown_y, direction):
        """Find boundary by exact horizontal line intersection at crown elevation"""
        
        # Get points in the search direction
        if direction == 'left':
            search_points = [(d, e) for d, e in valid_data if d < crown_x]
            search_points.sort(key=lambda x: x[0], reverse=True)  # Nearest to furthest
        else:
            search_points = [(d, e) for d, e in valid_data if d > crown_x]  
            search_points.sort(key=lambda x: x[0])  # Nearest to furthest
        
        if len(search_points) < 10:
            print(f"  ❌ Not enough points in {direction} direction: {len(search_points)}")
            return None
        
        print(f"  🔍 Searching {direction}: {len(search_points)} points")
        print(f"  🎯 Target elevation (EXACT): {crown_y:.3f}m")
        
        # Find intersections by interpolation between adjacent points
        intersections = []
        
        for i in range(len(search_points) - 1):
            p1_x, p1_y = search_points[i]
            p2_x, p2_y = search_points[i + 1]
            
            # Check if crown elevation is between these two points
            if (p1_y <= crown_y <= p2_y) or (p2_y <= crown_y <= p1_y):
                # Linear interpolation to find exact X coordinate
                if abs(p2_y - p1_y) > 0.001:  # Avoid division by zero
                    # Calculate exact X where line crosses crown_y
                    ratio = (crown_y - p1_y) / (p2_y - p1_y)
                    intersection_x = p1_x + ratio * (p2_x - p1_x)
                    
                    intersections.append((intersection_x, crown_y))
                    print(f"    ✅ EXACT intersection at X={intersection_x:.2f}, Y={crown_y:.3f}")
                else:
                    # Points are at same elevation, use the furthest one
                    furthest_x = p2_x if abs(p2_x) > abs(p1_x) else p1_x
                    intersections.append((furthest_x, crown_y))
                    print(f"    ✅ Same elevation at X={furthest_x:.2f}, Y={crown_y:.3f}")
        
        if not intersections:
            print(f"    ❌ No exact intersections found at elevation {crown_y:.3f}m")
            return None
        
        # Return the furthest intersection (extended boundary)
        if direction == 'left':
            # For left, get the most negative X (furthest left)
            furthest = min(intersections, key=lambda x: x[0])
        else:
            # For right, get the most positive X (furthest right) 
            furthest = max(intersections, key=lambda x: x[0])
        
        print(f"    ✅ Selected boundary at X={furthest[0]:.2f}, Y={furthest[1]:.3f}")
        return furthest
    
    def debug_profile_data(self, crown_x, crown_y):
        """🐛 Debug function to see what data we have"""
        profile = self.profiles_data[self.current_profile_index]
        distances = profile.get('distances', [])
        elevations = profile.get('elevations', [])
        
        valid_data = [(d, e) for d, e in zip(distances, elevations) if e != -9999]
        
        print(f"\n🐛 DEBUG INFO:")
        print(f"Total points: {len(valid_data)}")
        print(f"Distance range: {min(d for d,e in valid_data):.1f} to {max(d for d,e in valid_data):.1f}")
        print(f"Elevation range: {min(e for d,e in valid_data):.1f} to {max(e for d,e in valid_data):.1f}")
        print(f"Crown position: X={crown_x:.2f}, Y={crown_y:.2f}")
        
        # Show points near crown elevation
        tolerance = 0.5
        near_crown = [(d, e) for d, e in valid_data if abs(e - crown_y) <= tolerance]
        print(f"Points near crown elevation (±{tolerance}m): {len(near_crown)}")
        
        if near_crown:
            print(f"Near crown sample: {near_crown[:10]}")  # First 10 points
    
    
    def on_canvas_click(self, event):
        """Handle canvas click - ensure focus is maintained"""
        if not event.inaxes or not self.measurement_mode:
            return
        
        # Ensure canvas maintains focus after click
        self.canvas.setFocus()
        
        # Rest of the method remains the same as the fixed version...
        x_click = event.xdata
        current_pk = self.profiles_data[self.current_profile_index]['pk']
        
        if self.measurement_mode == 'crown' or self.measurement_mode == 'lama':
            # Crown and LAMA use TERRAIN snap
            terrain_point = self.find_terrain_snap_point(x_click)
            if not terrain_point:
                return
            snap_x, snap_y = terrain_point
            
        elif self.measurement_mode == 'width':
            # Width measurements: Check if A key is pressed for auto-snap
            crown_elevation = None
            crown_x = 0
            
            # Get crown reference data
            if current_pk in self.saved_measurements and 'crown' in self.saved_measurements[current_pk]:
                crown_elevation = self.saved_measurements[current_pk]['crown']['y']
                crown_x = self.saved_measurements[current_pk]['crown']['x']
            elif self.current_crown_point:
                crown_elevation = self.current_crown_point[1]
                crown_x = self.current_crown_point[0]
            
            if crown_elevation is None:
                from qgis.PyQt.QtWidgets import QMessageBox
                QMessageBox.information(
                    self,
                    "Referencia requerida",
                    "Debe definir una Cota Coronamiento antes de medir el ancho.\n"
                    "El ancho se puede medir sobre la línea de referencia o con snap automático (tecla A)."
                )
                return
            
            # Determine snap behavior based on A key
            if self._key_A_pressed:
                # AUTO-SNAP: Find intersection of crown elevation with terrain
                direction = 'left' if x_click < crown_x else 'right'
                profile = self.profiles_data[self.current_profile_index]
                distances = profile.get('distances', [])
                elevations = profile.get('elevations', [])
                valid_data = [(d, e) for d, e in zip(distances, elevations) if e != -9999]
                boundary = self.find_boundary_simple(valid_data, crown_x, crown_elevation, direction)
                
                if boundary:
                    snap_x, snap_y = boundary
                else:
                    # Fallback to manual reference line if auto-snap fails
                    snap_x, snap_y = (x_click, crown_elevation)
            else:
                # MANUAL SNAP: Use reference line (original behavior)
                snap_x, snap_y = (x_click, crown_elevation)
                
        else:
            return
        
        # Process the measurement based on mode
        if self.measurement_mode == 'crown':
            # Save crown point for current PK
            self.current_crown_point = (snap_x, snap_y)
            
            # Update saved measurements
            if current_pk not in self.saved_measurements:
                self.saved_measurements[current_pk] = {}
            self.saved_measurements[current_pk]['crown'] = {
                'x': snap_x,
                'y': snap_y
            }
            
            self.crown_result.setText(f"Cota Coronamiento: {snap_y:.2f} m")
            
            # Auto-detection for width (unchanged from original)
            if self.auto_width_detection:
                self.auto_status.setText("🔍 Detectando ancho automáticamente...")
                self.auto_status.setStyleSheet("color: blue; font-style: italic;")
                
                left_boundary, right_boundary = self.detect_road_width_automatically(snap_x, snap_y)
                
                if left_boundary and right_boundary:
                    # Automatically set width measurement
                    self.current_width_points = [left_boundary, right_boundary]
                    
                    # Calculate width
                    width = abs(right_boundary[0] - left_boundary[0])
                    
                    # Save auto-detected measurement
                    self.saved_measurements[current_pk]['width'] = {
                        'p1': left_boundary,
                        'p2': right_boundary,
                        'distance': width,
                        'auto_detected': True
                    }
                    
                    self.width_result.setText(f"Ancho auto-detectado: {width:.2f} m")
                    self.auto_status.setText("✅ Ancho detectado automáticamente")
                    self.auto_status.setStyleSheet("color: green; font-style: italic;")
                    
                    self.set_measurement_mode('width')
                    
                else:
                    self.auto_status.setText("⚠️ No se pudo detectar automáticamente")
                    self.auto_status.setStyleSheet("color: orange; font-style: italic;")
            
        elif self.measurement_mode == 'width':
            # Add point to width measurement
            self.current_width_points.append((snap_x, snap_y))
            
            if len(self.current_width_points) == 1:
                # Show feedback for first point
                snap_type = "Auto-snap" if self._key_A_pressed else "Ref"
                self.width_result.setText(f"Punto 1: X={snap_x:.1f}m, Y={snap_y:.2f}m ({snap_type})")
                
            elif len(self.current_width_points) == 2:
                # Calculate width between two points
                p1 = self.current_width_points[0]
                p2 = self.current_width_points[1]
                width = abs(p2[0] - p1[0])
                
                # Save measurement for current PK
                if current_pk not in self.saved_measurements:
                    self.saved_measurements[current_pk] = {}
                self.saved_measurements[current_pk]['width'] = {
                    'p1': p1,
                    'p2': p2,
                    'distance': width,
                    'auto_detected': False
                }
                
                self.width_result.setText(f"Ancho medido: {width:.2f} m (manual)")
                self.auto_status.setText("✏️ Medición manual completada")
                self.auto_status.setStyleSheet("color: blue; font-style: italic;")
                
                # Reset for next measurement
                self.current_width_points = []
        
        elif self.measurement_mode == 'lama':
            # LAMA measurement on terrain
            if current_pk not in self.saved_measurements:
                self.saved_measurements[current_pk] = {}
            self.saved_measurements[current_pk]['lama'] = {
                'x': snap_x,
                'y': snap_y
            }
            
            self.lama_result.setText(f"Cota LAMA: {snap_y:.2f} m (manual)")
        
        # Update the display
        self.update_profile_display()
    
    def update_revancha_calculation(self):
        """Calculate and update Revancha value (Crown - LAMA)"""
        current_pk = self.profiles_data[self.current_profile_index]['pk']
        
        # Get current profile lama points (automatic)
        profile = self.profiles_data[self.current_profile_index]
        auto_lama_points = profile.get('lama_points', [])
        
        # Check for manual LAMA override
        manual_lama = None
        if current_pk in self.saved_measurements and 'lama' in self.saved_measurements[current_pk]:
            manual_lama = self.saved_measurements[current_pk]['lama']
        
        # Get LAMA elevation (manual takes priority)
        lama_elevation = None
        if manual_lama:
            lama_elevation = manual_lama['y']
            lama_source = "manual"
        elif auto_lama_points:
            lama_elevation = auto_lama_points[0]['elevation']
            lama_source = "auto"
        
        # Get Crown elevation - 🔧 CORREGIR AQUÍ
        crown_elevation = None
        if current_pk in self.saved_measurements and 'crown' in self.saved_measurements[current_pk]:
            crown_elevation = self.saved_measurements[current_pk]['crown']['y']
        elif self.current_crown_point:  # 🆕 TAMBIÉN USAR CROWN TEMPORAL
            crown_elevation = self.current_crown_point[1]
        
        # Calculate Revancha
        if crown_elevation is not None and lama_elevation is not None:
            revancha = crown_elevation - lama_elevation
            self.revancha_result.setText(f"Revancha: {revancha:.2f} m")
            
            # Update LAMA display
            self.lama_result.setText(f"Cota LAMA: {lama_elevation:.2f} m ({lama_source})")
        else:
            # 🔧 MEJORAR MENSAJE DE ERROR
            missing_parts = []
            if crown_elevation is None:
                missing_parts.append("coronamiento")
            if lama_elevation is None:
                missing_parts.append("lama")
            
            self.revancha_result.setText(f"Revancha: -- (falta {', '.join(missing_parts)})")
            
            # Still show LAMA if available
            if lama_elevation is not None:
                self.lama_result.setText(f"Cota LAMA: {lama_elevation:.2f} m ({lama_source})")
            else:
                self.lama_result.setText("Cota LAMA: --")
    
    def prev_profile(self):
        """Navigate to previous profile"""
        if self.current_profile_index > 0:
            self.current_profile_index -= 1
            self.pk_slider.setValue(self.current_profile_index)
            self.load_profile_measurements()  # Load measurements for new PK
            self.update_profile_display()
    
    def next_profile(self):
        """Navigate to next profile"""
        if self.current_profile_index < len(self.profiles_data) - 1:
            self.current_profile_index += 1
            self.pk_slider.setValue(self.current_profile_index)
            self.load_profile_measurements()  # Load measurements for new PK
            self.update_profile_display()
    
    def on_slider_changed(self, value):
        """Handle slider position change"""
        if value != self.current_profile_index:
            self.current_profile_index = value
            self.load_profile_measurements()  # Load measurements for new PK
            self.update_profile_display()
    
    def load_profile_measurements(self):
        """🔧 Load measurements specific to current PK including LAMA and Revancha"""
        current_pk = self.profiles_data[self.current_profile_index]['pk']
        
        # Clear current temporary measurements
        self.current_crown_point = None
        self.current_width_points = []
        
        # Load saved measurements for this PK
        if current_pk in self.saved_measurements:
            measurements = self.saved_measurements[current_pk]
            
            # Load crown measurement - 🔧 SIN (X: value)
            if 'crown' in measurements:
                crown_data = measurements['crown']
                self.current_crown_point = (crown_data['x'], crown_data['y'])
                self.crown_result.setText(f"Cota Coronamiento: {crown_data['y']:.2f} m")  # 🔧 QUITADO (X: ...)
            else:
                self.crown_result.setText("Cota Coronamiento: --")
            
            # Load width measurement - 🔧 MEJORAR LABELS
            if 'width' in measurements:
                width_data = measurements['width']
                auto_detected = width_data.get('auto_detected', False)
                
                if auto_detected:
                    self.width_result.setText(f"Ancho medido: {width_data['distance']:.2f} m (auto-detectado)")
                else:
                    self.width_result.setText(f"Ancho medido: {width_data['distance']:.2f} m (manual)")
                
                # Update status
                if auto_detected:
                    self.auto_status.setText("✅ Ancho detectado automáticamente")
                    self.auto_status.setStyleSheet("color: green; font-style: italic;")
                else:
                    self.auto_status.setText("✏️ Medición manual")
                    self.auto_status.setStyleSheet("color: blue; font-style: italic;")
            else:
                self.width_result.setText("Ancho medido: --")
                self.auto_status.setText("Auto-detección activada" if self.auto_width_detection else "Modo manual activado")
                self.auto_status.setStyleSheet("color: green; font-style: italic;" if self.auto_width_detection else "color: orange; font-style: italic;")
                
        else:
            # No measurements for this PK
            self.crown_result.setText("Cota Coronamiento: --")
            self.width_result.setText("Ancho medido: --")
            self.auto_status.setText("Auto-detección activada" if self.auto_width_detection else "Modo manual activado")
            self.auto_status.setStyleSheet("color: green; font-style: italic;" if self.auto_width_detection else "color: orange; font-style: italic;")
        
        # 🆕 Update LAMA and Revancha (always recalculate)
        self.update_revancha_calculation()
    
    def update_profile_display(self):
        """Update the profile visualization including LAMA points and reference lines"""
        if not self.profiles_data:
            return
        
        profile = self.profiles_data[self.current_profile_index]
        current_pk = profile.get('pk', 'Unknown')
        # 🆕 OBTENER RANGOS ESPECÍFICOS DEL MURO
        x_min, x_max = self.get_wall_display_range(profile)
        # Clear and plot
        self.ax.clear()
        
        # Extract data
        distances = profile.get('distances', [])
        elevations = profile.get('elevations', [])
        
        # Filter valid data
        valid_data = [(d, e) for d, e in zip(distances, elevations) if e != -9999]
        
        if not valid_data:
            self.ax.text(0.5, 0.5, 'No hay datos válidos', 
                        ha='center', va='center', transform=self.ax.transAxes)
            return
        
        valid_distances, valid_elevations = zip(*valid_data)
        
        # 🎨 Plot the profile with FINER LINE and MORE DETAIL
        self.ax.plot(valid_distances, valid_elevations, 'b-', linewidth=1.2,
                    label='Terreno Natural', alpha=0.9)
        
        # Fill with reduced opacity to see terrain detail better
        self.ax.fill_between(valid_distances, valid_elevations,
                        min(valid_elevations) - 2, alpha=0.15, color='brown',
                        label='Terreno')
        
        # 📍 Mark centerline
        self.ax.axvline(x=0, color='red', linestyle='--', linewidth=1.8, alpha=0.8, 
                    label='Eje de Alineación')
        
        # 🆕 REFERENCE LINES - Draw BEFORE measurements for better layering
        crown_elevation = None
        if current_pk in self.saved_measurements and 'crown' in self.saved_measurements[current_pk]:
            crown_elevation = self.saved_measurements[current_pk]['crown']['y']
        elif self.current_crown_point:
            crown_elevation = self.current_crown_point[1]
        
        if crown_elevation is not None:
            x_range = [x_min, x_max]  # Usar rangos específicos del muro
            
            # 🔥 MAIN REFERENCE LINE - MÁS INTENSA
            y_ref = [crown_elevation, crown_elevation]
            self.ax.plot(x_range, y_ref, '--', color='orange', linewidth=2.5, 
                        alpha=1.0, label=f'Ref. Coronamiento: {crown_elevation:.2f}m',
                        zorder=3)
            
            # 🆕 AUXILIARY LINE - 1 metro debajo, MÁS TENUE
            aux_elevation = crown_elevation - 1.0  # 1 metro abajo
            y_aux = [aux_elevation, aux_elevation]
            self.ax.plot(x_range, y_aux, ':', color='gray', linewidth=1.5, 
                        alpha=0.6, label=f'Auxiliar (-1m): {aux_elevation:.2f}m',
                        zorder=2)
        
        # 📏 Show SAVED measurements for current PK
        if current_pk in self.saved_measurements:
            measurements = self.saved_measurements[current_pk]
            
            # Crown point
            if 'crown' in measurements:
                crown_data = measurements['crown']
                self.ax.plot(crown_data['x'], crown_data['y'], 'ro', markersize=10, 
                        label=f'Cota Coronamiento: {crown_data["y"]:.2f}m', zorder=4)
            
            # Width measurement with auto-detection indicator
            if 'width' in measurements:
                width_data = measurements['width']
                p1, p2 = width_data['p1'], width_data['p2']
                auto_detected = width_data.get('auto_detected', False)
                
                # Different colors for auto vs manual
                color = 'lime' if auto_detected else 'magenta'
                marker_size = 10 if auto_detected else 8
                line_style = '-' if auto_detected else '--'
                label_prefix = 'Auto' if auto_detected else 'Manual'
                
                # Draw points and line
                self.ax.plot([p1[0], p2[0]], [p1[1], p2[1]], 'o', color=color, markersize=marker_size, zorder=4)
                self.ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color=color, linestyle=line_style, 
                        linewidth=2.5, alpha=0.9, label=f'{label_prefix}: {width_data["distance"]:.2f}m', zorder=4)
            
            # Manual LAMA point (overrides automatic)
            if 'lama' in measurements:
                lama_data = measurements['lama']
                self.ax.plot(lama_data['x'], lama_data['y'], 'o', color='orange', markersize=12,
                        markeredgecolor='red', markeredgewidth=2, 
                        label=f'LAMA Manual: {lama_data["y"]:.2f}m', zorder=4)
        
        # Show automatic LAMA points (only if no manual override)
        if current_pk not in self.saved_measurements or 'lama' not in self.saved_measurements[current_pk]:
            lama_points = profile.get('lama_points', [])
            if lama_points:
                for lama_point in lama_points:
                    self.ax.plot(lama_point['offset_from_centerline'], lama_point['elevation'], 
                                'o', color='yellow', markersize=10, markeredgecolor='brown',
                                markeredgewidth=2, label=f'LAMA Auto: {lama_point["elevation"]:.2f}m', zorder=4)
        
        # 🎯 Show current temporary measurements
        if self.current_crown_point:
            self.ax.plot(self.current_crown_point[0], self.current_crown_point[1], 'go', 
                        markersize=12, alpha=0.8, label='Cota (temp)', zorder=5)
        
        if len(self.current_width_points) == 1:
            self.ax.plot(self.current_width_points[0][0], self.current_width_points[0][1], 
                        'yo', markersize=10, label='Punto 1', zorder=5)
        
        # 🎨 Formatting with MORE DETAIL
        self.ax.grid(True, alpha=0.3, linestyle=':', linewidth=0.6)
        
        # Add minor grid for more precision
        self.ax.minorticks_on()
        self.ax.grid(which='minor', alpha=0.15, linestyle=':', linewidth=0.4)
        
        self.ax.set_xlabel('Distancia desde Eje (m)', fontsize=12)
        self.ax.set_ylabel('Elevación (m)', fontsize=12)
        self.ax.set_title(f'Perfil Topográfico - {current_pk}', fontsize=14, fontweight='bold')
        self.ax.legend(loc='upper right', fontsize=9)
        
        # 🎯 Focus on relevant area (-40 to +20)
        self.ax.set_xlim(x_min, x_max)
        
        if valid_elevations:
            # Filter elevations within the display range for better Y scaling
            relevant_elevations = [e for d, e in valid_data if x_min <= d <= x_max]
            
            # 🆕 Include both crown elevation and auxiliary line in Y-axis scaling
            if crown_elevation is not None:
                relevant_elevations.append(crown_elevation)
                relevant_elevations.append(crown_elevation - 1.0)  # Auxiliary line
            
            if relevant_elevations:
                margin = (max(relevant_elevations) - min(relevant_elevations)) * 0.08
                self.ax.set_ylim(min(relevant_elevations) - margin, 
                            max(relevant_elevations) + margin)
            else:
                # Fallback to all elevations
                margin = (max(valid_elevations) - min(valid_elevations)) * 0.08
                self.ax.set_ylim(min(valid_elevations) - margin, 
                            max(valid_elevations) + margin)
        
        # Update UI labels
        self.current_pk_label.setText(f"{current_pk}")
        self.profile_counter.setText(f"{self.current_profile_index + 1} / {len(self.profiles_data)}")
        
        # Update info panel
        self.info_pk.setText(f"PK: {current_pk}")
        self.info_coords.setText(f"Coordenadas: X={profile.get('centerline_x', 0):.1f}, Y={profile.get('centerline_y', 0):.1f}")
        
        if valid_elevations:
            # Show elevation range for the visible area only
            relevant_elevations = [e for d, e in valid_data if -40 <= d <= 20]
            if relevant_elevations:
                self.info_elevation_range.setText(f"Rango elevación: {min(relevant_elevations):.2f} - {max(relevant_elevations):.2f} m")
            else:
                self.info_elevation_range.setText(f"Rango elevación: {min(valid_elevations):.2f} - {max(valid_elevations):.2f} m")
        
        # Update info with LAMA info (single value, not range)
        lama_points = profile.get('lama_points', [])
        if lama_points:
            lama_elevation = lama_points[0]['elevation']
            lama_info = f"LAMA: {lama_elevation:.2f}m"
        else:
            lama_info = "Sin LAMA"
        
        # Check for manual LAMA override
        if current_pk in self.saved_measurements and 'lama' in self.saved_measurements[current_pk]:
            manual_lama = self.saved_measurements[current_pk]['lama']
            lama_info = f"LAMA: {manual_lama['y']:.2f}m (manual)"
        
        visible_points = len([d for d, e in valid_data if -40 <= d <= 20])
        
        # 🆕 Add reference lines info if exists
        ref_info = ""
        if crown_elevation is not None:
            ref_info = f" | Ref: {crown_elevation:.2f}m | Aux: {crown_elevation-1.0:.2f}m"
        
        self.info_valid_points.setText(f"Puntos válidos: {len(valid_data)} | Visibles: {visible_points} | {lama_info}{ref_info}")
        
        # Refresh canvas
        self.figure.tight_layout()
        self.canvas.draw()

    def export_measurements_to_csv(self):
        """Export all measurements from all profiles to CSV file"""
        try:
            from qgis.PyQt.QtWidgets import QFileDialog, QMessageBox
            
            # 🎯 DIÁLOGO SIMPLE - TÚ ELIGES EL NOMBRE COMPLETO
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Exportar Mediciones a CSV",
                "mediciones_perfiles.csv",  # 🔧 NOMBRE SIMPLE POR DEFECTO
                "CSV files (*.csv);;All files (*.*)"
            )
            
            if not file_path:
                return  # Usuario canceló
            
            # Mostrar progreso
            progress = QProgressDialog("Recopilando mediciones de todos los perfiles...", "Cancelar", 0, 100, self)
            progress.setWindowModality(Qt.WindowModal)
            progress.show()
            
            QApplication.processEvents()
            
            # Recopilar datos de todos los perfiles
            export_data = []
            total_profiles = len(self.profiles_data)
            
            progress.setLabelText("Procesando mediciones...")
            progress.setValue(10)
            QApplication.processEvents()
            
            for i, profile in enumerate(self.profiles_data):
                pk = profile['pk']
                
                # Obtener datos automáticos (LAMA siempre disponible)
                auto_lama_points = profile.get('lama_points', [])
                auto_lama_elevation = auto_lama_points[0]['elevation'] if auto_lama_points else None
                
                # Obtener mediciones manuales guardadas
                measurements = self.saved_measurements.get(pk, {})
                
                # COTA CORONAMIENTO
                crown_elevation = None
                if 'crown' in measurements:
                    crown_elevation = measurements['crown']['y']
                
                # ANCHO
                width_value = None
                if 'width' in measurements:
                    width_value = measurements['width']['distance']
                
                # LAMA (manual tiene prioridad)
                lama_elevation = None
                if 'lama' in measurements:
                    lama_elevation = measurements['lama']['y']  # Manual
                elif auto_lama_elevation is not None:
                    lama_elevation = auto_lama_elevation  # Automática
                
                # REVANCHA (calcular si tenemos ambos valores)
                revancha_value = None
                if crown_elevation is not None and lama_elevation is not None:
                    revancha_value = crown_elevation - lama_elevation
                
                # 🎯 CREAR FILA SOLO CON LAS COLUMNAS QUE QUIERES
                row_data = {
                    'PK': pk,
                    'Cota_Coronamiento': crown_elevation,
                    'Revancha': revancha_value,
                    'Lama': lama_elevation,
                    'Ancho': width_value
                }
                
                export_data.append(row_data)
                
                # Actualizar progreso
                progress_percent = 10 + int((i / total_profiles) * 70)
                progress.setValue(progress_percent)
                QApplication.processEvents()
                
                if progress.wasCanceled():
                    return
            
            # Escribir CSV
            progress.setLabelText("Escribiendo archivo CSV...")
            progress.setValue(85)
            QApplication.processEvents()
            
            self.write_measurements_csv(file_path, export_data)
            
            progress.setValue(100)
            progress.close()
            
            # Calcular estadísticas para mostrar al usuario
            total_rows = len(export_data)
            rows_with_crown = sum(1 for row in export_data if row['Cota_Coronamiento'] is not None)
            rows_with_width = sum(1 for row in export_data if row['Ancho'] is not None)
            rows_with_lama = sum(1 for row in export_data if row['Lama'] is not None)
            rows_with_revancha = sum(1 for row in export_data if row['Revancha'] is not None)
            
            # Mensaje de éxito
            QMessageBox.information(
                self,
                "✅ Exportación Exitosa",
                f"Mediciones exportadas correctamente a:\n{file_path}\n\n"
                f"📊 Resumen:\n"
                f"• Total de perfiles: {total_rows}\n"
                f"• Con Cota Coronamiento: {rows_with_crown}\n"
                f"• Con Ancho: {rows_with_width}\n"
                f"• Con LAMA: {rows_with_lama}\n"
                f"• Con Revancha: {rows_with_revancha}"
            )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "❌ Error de Exportación",
                f"No se pudo exportar las mediciones:\n\n{str(e)}"
            )

    def write_measurements_csv(self, file_path, export_data):
        """Write measurements data to CSV file"""
        import csv
        
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            # 🎯 SOLO LAS COLUMNAS QUE QUIERES (sin PK_Decimal)
            fieldnames = ['PK', 'Cota_Coronamiento', 'Revancha', 'Lama', 'Ancho']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            # Escribir cabecera
            writer.writeheader()
            
            # Escribir datos
            for row_data in export_data:
                # Formatear valores nulos como cadenas vacías
                formatted_row = {}
                for key in fieldnames:  # Solo las columnas que queremos
                    value = row_data.get(key)
                    if value is None:
                        formatted_row[key] = ''
                    elif isinstance(value, float):
                        formatted_row[key] = f"{value:.3f}"  # 3 decimales
                    else:
                        formatted_row[key] = value
                
                writer.writerow(formatted_row)
