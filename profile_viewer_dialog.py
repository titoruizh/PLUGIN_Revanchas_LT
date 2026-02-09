
import os
from qgis.PyQt.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                                 QLabel, QSlider, QGroupBox, QMessageBox,
                                 QFileDialog, QProgressDialog, QApplication, QSpinBox, QShortcut)
from qgis.PyQt.QtCore import Qt, QTimer
from qgis.PyQt.QtXml import QDomDocument
from qgis.PyQt.QtGui import QFont, QKeySequence
from qgis.core import (QgsApplication, QgsProject, QgsRasterLayer, QgsPointXY, QgsRectangle,
                       QgsPrintLayout, QgsLayoutExporter, QgsLayoutItemHtml, 
                       QgsLayoutItemPicture, QgsLayoutSize, QgsUnitTypes, QgsLayoutPoint, QgsReadWriteContext)

def diagnose_libraries():
    """Diagnose library versions for debugging compatibility issues"""
    print("🔍 DIAGNÓSTICO DE LIBRERÍAS:")
    
    # Check NumPy
    try:
        import numpy as np
        print(f"  ✅ NumPy version: {np.__version__}")
        
        # Test _ARRAY_API availability (this is what's causing the error)
        try:
            if hasattr(np, '_ARRAY_API'):
                print(f"    ✅ _ARRAY_API disponible")
            else:
                print(f"    ⚠️ _ARRAY_API no encontrado")
        except AttributeError as ae:
            print(f"    ❌ Error accediendo _ARRAY_API: {ae}")
        
        # Test basic numpy functionality
        try:
            test_array = np.array([1, 2, 3])
            print(f"    ✅ Funcionalidad básica de NumPy OK")
        except Exception as ne:
            print(f"    ❌ Error en funcionalidad básica de NumPy: {ne}")
            
    except Exception as e:
        print(f"  ❌ NumPy error general: {e}")
    
    # Check Matplotlib
    try:
        import matplotlib
        print(f"  ✅ Matplotlib version: {matplotlib.__version__}")
    except Exception as e:
        print(f"  ❌ Matplotlib error: {e}")
    
    # Check backend availability
    try:
        from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT
        print(f"    ✅ NavigationToolbar2QT (qt5agg) disponible")
    except Exception:
        print(f"    ⚠️ NavigationToolbar2QT (qt5agg) no disponible")
        try:
            from matplotlib.backends.backend_qtagg import NavigationToolbar2QT
            print(f"    ✅ NavigationToolbar2QT (qtagg) disponible")
        except Exception:
            print(f"    ❌ NavigationToolbar2QT no disponible en ningún backend")

try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    
    # Handle different versions of matplotlib NavigationToolbar
    try:
        from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
    except ImportError:
        try:
            from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
        except ImportError:
            try:
                from matplotlib.backends.backend_qt import NavigationToolbar2QT as NavigationToolbar
            except ImportError:
                # Fallback for very old versions
                from matplotlib.backends.backend_qt5agg import NavigationToolbar2QTAgg as NavigationToolbar
    
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    # Create dummy NavigationToolbar class
    class NavigationToolbar:
        def __init__(self, *args, **kwargs):
            pass


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
        
        # 🆕 Controles de rango de visualización
        self.addSeparator()
        
        # Label para rango
        range_label = QLabel("  Rango (m):")
        range_label.setStyleSheet("font-weight: bold; padding: 5px;")
        self.addWidget(range_label)
        
        # SpinBox para límite izquierdo (negativo)
        self.addWidget(QLabel(" Izq:"))
        self.left_limit_spin = QSpinBox()
        self.left_limit_spin.setMinimum(-70)
        self.left_limit_spin.setMaximum(0)
        self.left_limit_spin.setValue(-40)
        self.left_limit_spin.setSuffix("m")
        self.left_limit_spin.setToolTip("Límite izquierdo del perfil (-70 a 0)")
        self.left_limit_spin.valueChanged.connect(self.on_range_changed)
        self.addWidget(self.left_limit_spin)
        
        # SpinBox para límite derecho (positivo)
        self.addWidget(QLabel(" Der:"))
        self.right_limit_spin = QSpinBox()
        self.right_limit_spin.setMinimum(0)
        self.right_limit_spin.setMaximum(70)
        self.right_limit_spin.setValue(40)
        self.right_limit_spin.setSuffix("m")
        self.right_limit_spin.setToolTip("Límite derecho del perfil (0 a 70)")
        self.right_limit_spin.valueChanged.connect(self.on_range_changed)
        self.addWidget(self.right_limit_spin)
        
        # Botón para aplicar rango
        apply_range_btn = QPushButton("✓")
        apply_range_btn.setMaximumWidth(30)
        apply_range_btn.setToolTip("Aplicar rango personalizado")
        apply_range_btn.clicked.connect(self.apply_custom_range)
        self.addWidget(apply_range_btn)
        
        self.addSeparator()
        
        # 🆕 Botón para activar/desactivar leyenda
        self.legend_btn = QPushButton("📋 Leyenda")
        self.legend_btn.setCheckable(True)
        self.legend_btn.setChecked(False)  # Desactivada por defecto
        self.legend_btn.setToolTip("Activar/Desactivar leyenda")
        self.legend_btn.clicked.connect(self.toggle_legend)
        self.addWidget(self.legend_btn)
        
        self.addSeparator()
        
        # Add simple zoom level indicator (no coordinates)
        self.zoom_label = QLabel("Zoom: 100%")
        self.zoom_label.setStyleSheet("color: #333; font-weight: bold; padding: 5px;")
        self.addWidget(self.zoom_label)
        
        # Connect to zoom events - Compatible con matplotlib >= 3.5
        # Usar ax.callbacks en lugar de canvas.mpl_connect para xlim_changed
        self.profile_viewer.ax.callbacks.connect('xlim_changed', self.on_zoom_changed)
    
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
    
    def on_range_changed(self):
        """Handler cuando cambian los spinboxes de rango"""
        # Actualizar el tooltip del botón de extensión con el nuevo rango
        left = self.left_limit_spin.value()
        right = self.right_limit_spin.value()
        # No hacer nada aquí, solo actualizar cuando se presione el botón
    
    def apply_custom_range(self):
        """Aplicar el rango personalizado al perfil"""
        left = self.left_limit_spin.value()
        right = self.right_limit_spin.value()
        
        # Validar que el rango sea válido
        if left >= right:
            QMessageBox.warning(self, "Rango inválido", 
                              "El límite izquierdo debe ser menor que el derecho")
            return
        
        # Actualizar el rango personalizado en el profile_viewer
        self.profile_viewer.custom_range_left = left
        self.profile_viewer.custom_range_right = right
        
        # Redibujar el perfil con el nuevo rango
        self.profile_viewer.update_profile_display()
    
    def toggle_legend(self):
        """Activar/desactivar la visualización de la leyenda"""
        self.profile_viewer.show_legend = self.legend_btn.isChecked()
        self.profile_viewer.update_profile_display()
        self.profile_viewer.update_profile_display()
        
        # Zoom a la extensión completa del nuevo rango
        self.zoom_to_profile_extent()


class InteractiveProfileViewer(QDialog):
    """Interactive profile viewer with navigation and measurement tools"""
    
    def __init__(self, profiles_data, parent=None, ecw_file_path=None):
        super().__init__(parent)
        
        # Run diagnostic to help debug library issues
        diagnose_libraries()
        
        self.profiles_data = profiles_data
        self.current_profile_index = 0
        self.measurement_mode = None
        self.ecw_file_path = ecw_file_path  # Store ECW file path
        
        # Separate measurements per PK
        self.saved_measurements = {}  # PK -> {crown: {x, y}, width: {p1, p2, distance}}
        
        # Current temporary measurements (reset when changing PK)
        self.current_crown_point = None
        self.current_width_points = []
        
        # Auto-detection parameters
        self.auto_width_detection = True
        self.pretil_height_threshold = 0.5  # metros - diferencia mínima para detectar pretil
        self.search_step = 0.5  # metros - paso de búsqueda
        
        # 🆕 Custom range parameters (user-configurable)
        self.custom_range_left = -40  # Default: -40m
        self.custom_range_right = 40  # Default: +40m
        
        # 🆕 Legend visibility control (desactivada por defecto)
        self.show_legend = False
        
        # Initialize key state BEFORE UI creation
        self._key_A_pressed = False
        
        # 🆕 MODO DE OPERACIÓN: "revancha" o "ancho_proyectado"
        self.operation_mode = "revancha"  # Modo por defecto
        
        # 🆕 Referencia al visualizador de ortomosaico (si está abierto)
        self.ortho_viewer = None
        
        self.setWindowTitle("Visualizador Interactivo de Perfiles")
        self.setModal(True)
        self.resize(1200, 800)
        
        # Verify matplotlib functionality before proceeding
        matplotlib_working = False
        if HAS_MATPLOTLIB:
            try:
                # Test if NavigationToolbar is properly imported and functional
                test_fig = Figure(figsize=(1, 1))
                test_canvas = FigureCanvas(test_fig)
                test_toolbar = NavigationToolbar(test_canvas, self)
                matplotlib_working = True
                print("✅ Matplotlib y NavigationToolbar funcionando correctamente")
            except Exception as e:
                print(f"⚠️ Error al inicializar matplotlib/NavigationToolbar: {e}")
                matplotlib_working = False
        
        if matplotlib_working:
            self.init_ui()
            # Setup keyboard events AFTER UI is fully created
            self.setup_keyboard_events()
        else:
            self.init_no_matplotlib()
        
        # AHORA es seguro acceder a self.canvas SOLO si matplotlib funciona:
        self._key_A_pressed = False
        if matplotlib_working and hasattr(self, 'canvas'):
            self.canvas.setFocusPolicy(Qt.StrongFocus)
            self.canvas.setFocus()
            self.canvas.mpl_connect('key_press_event', self.on_key_press)
            self.canvas.mpl_connect('key_release_event', self.on_key_release)

    def setup_keyboard_events(self):
        """Setup keyboard event handling after UI is created"""
        self.canvas.setFocusPolicy(Qt.StrongFocus)
        self.canvas.mpl_connect('key_press_event', self.on_key_press)
        self.canvas.mpl_connect('key_release_event', self.on_key_release)
        
        # Add global shortcuts for measurement buttons (Z, X, C)
        self.shortcut_lama = QShortcut(QKeySequence("Z"), self)
        self.shortcut_crown = QShortcut(QKeySequence("X"), self)
        self.shortcut_width = QShortcut(QKeySequence("C"), self)
        
        self.shortcut_lama.activated.connect(lambda: self.lama_btn.click())
        self.shortcut_crown.activated.connect(lambda: self.crown_btn.click())
        self.shortcut_width.activated.connect(lambda: self.width_btn.click())
        
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
        
        # 🆕 USAR RANGO PERSONALIZADO del usuario
        return (self.custom_range_left, self.custom_range_right)

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
    
    def init_no_matplotlib(self):
        """Initialize widget when matplotlib is not available or has problems"""
        layout = QVBoxLayout()
        
        # Create informative message
        message = QLabel()
        message.setText(
            "<h2>🚧 Error de Compatibilidad de Librerías</h2>"
            "<p><b>Error detectado: AttributeError '_ARRAY_API not found'</b></p>"
            "<p>Este error indica incompatibilidad entre versiones de NumPy y otras librerías.</p>"
            "<p><b>Soluciones (en orden de recomendación):</b></p>"
            "<ol>"
            "<li><b>Actualizar NumPy:</b><br>"
            "<code>pip install --upgrade numpy>=1.21.0</code></li>"
            "<li><b>Reinstalar NumPy y Matplotlib:</b><br>"
            "<code>pip uninstall numpy matplotlib</code><br>"
            "<code>pip install numpy matplotlib</code></li>"
            "<li><b>Para QGIS con conda:</b><br>"
            "<code>conda update numpy matplotlib</code></li>"
            "</ol>"
            "<p><b>Nota:</b> Los perfiles se generaron correctamente. Solo la interfaz gráfica está afectada.</p>"
            "<p><i>Esta ventana se cerrará automáticamente en 10 segundos.</i></p>"
        )
        message.setWordWrap(True)
        message.setStyleSheet(
            "QLabel { "
            "padding: 20px; "
            "background-color: #fff3cd; "
            "border: 2px solid #ffeaa7; "
            "border-radius: 10px; "
            "color: #856404; "
            "}"
        )
        
        layout.addWidget(message)
        self.setLayout(layout)
        
        # Auto-close after showing the message
        QTimer.singleShot(10000, self.close)  # Close after 10 seconds
    
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
            # 🆕 Initialize UI for default operation mode
            self.update_ui_for_operation_mode()
            self.sync_range_controls()  # 🆕 Sync range controls on init
            self.update_profile_display()
            # Set initial zoom to full extent
            self.toolbar.zoom_to_profile_extent()
    
    def create_control_panel(self):
        """Create navigation control panel with operation mode toggle"""
        group = QGroupBox("🧭 Navegación de Perfiles")
        layout = QVBoxLayout()  # Cambiar a vertical para incluir el toggle
        
        # 🆕 TOGGLE DE MODO DE OPERACIÓN (PRIMERA FILA)
        mode_layout = QHBoxLayout()
        mode_label = QLabel("Modo de Operación:")
        mode_label.setFont(QFont("Arial", 10, QFont.Bold))
        
        self.mode_toggle_btn = QPushButton("🔧 REVANCHA")
        self.mode_toggle_btn.setCheckable(True)
        self.mode_toggle_btn.setChecked(False)  # False = Revancha, True = Ancho Proyectado
        self.mode_toggle_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3; 
                color: white; 
                font-weight: bold; 
                padding: 8px 16px; 
                border-radius: 5px; 
                border: 2px solid #1976D2;
            }
            QPushButton:checked {
                background-color: #FF9800; 
                border: 2px solid #F57C00;
            }
        """)
        self.mode_toggle_btn.clicked.connect(self.toggle_operation_mode)
        
        # Botón de Visualización de Ortomosaico
        self.view_ortho_btn = QPushButton("🌎 Visualiza Ortomosaico")
        self.view_ortho_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50; 
                color: white; 
                font-weight: bold; 
                padding: 8px 16px; 
                border-radius: 5px; 
                border: 2px solid #388E3C;
            }
            QPushButton:hover {
                background-color: #388E3C;
            }
        """)
        self.view_ortho_btn.clicked.connect(self.show_orthomosaic)
        
        # Solo mostrar botón de ortomosaico si tenemos el archivo
        if self.ecw_file_path:
            self.view_ortho_btn.setEnabled(True)
            self.view_ortho_btn.setToolTip("Ver ortomosaico en esta ubicación")
        else:
            self.view_ortho_btn.setEnabled(False)
            self.view_ortho_btn.setToolTip("No hay ortomosaico disponible")
        
        mode_layout.addWidget(mode_label)
        mode_layout.addWidget(self.mode_toggle_btn)
        mode_layout.addWidget(self.view_ortho_btn)
        mode_layout.addStretch()
        
        # NAVEGACIÓN (SEGUNDA FILA)
        nav_layout = QHBoxLayout()
        
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
        
        nav_layout.addWidget(self.prev_btn)
        nav_layout.addWidget(self.pk_slider, stretch=1)
        nav_layout.addWidget(self.next_btn)
        nav_layout.addWidget(self.current_pk_label)
        nav_layout.addWidget(self.profile_counter)
        
        # Ensamblar layout
        layout.addLayout(mode_layout)
        layout.addLayout(nav_layout)
        
        group.setLayout(layout)
        return group
    
    def create_measurement_panel(self):
        """Create measurement tools panel"""
        group = QGroupBox("🔧 Herramientas de Medición")
        layout = QVBoxLayout()
        
        # Measurement mode buttons (PRIMERA FILA)
        btn_layout1 = QHBoxLayout()
        
        self.lama_btn = QPushButton("🟡 Modificar LAMA (Z)")
        self.crown_btn = QPushButton("📍 Cota Coronamiento (X)")
        self.width_btn = QPushButton("📏 Medir Ancho (C)")
        self.clear_btn = QPushButton("🗑️ Limpiar")
        
        self.crown_btn.setCheckable(True)
        self.width_btn.setCheckable(True)
        self.lama_btn.setCheckable(True)
        
        self.crown_btn.clicked.connect(lambda: self.set_measurement_mode('crown'))
        self.width_btn.clicked.connect(lambda: self.set_measurement_mode('width'))
        self.lama_btn.clicked.connect(lambda: self.set_measurement_mode('lama'))
        self.clear_btn.clicked.connect(self.clear_current_measurements)
        
        btn_layout1.addWidget(self.lama_btn)
        btn_layout1.addWidget(self.crown_btn)
        btn_layout1.addWidget(self.width_btn)
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
        self.export_btn = QPushButton("📊 Exportar Mediciones")
        self.export_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 8px;")
        self.export_btn.clicked.connect(self.export_measurements_to_csv)
        btn_layout3.addWidget(self.export_btn)
        
        self.export_pdf_btn = QPushButton("📄 Generar Reporte PDF")
        self.export_pdf_btn.setStyleSheet("background-color: #d32f2f; color: white; font-weight: bold; padding: 8px;")
        self.export_pdf_btn.clicked.connect(self.export_pdf_report)
        self.export_pdf_btn.clicked.connect(self.export_pdf_report)
        btn_layout3.addWidget(self.export_pdf_btn)
        
        # 🆕 BOTÓN DE DESARROLLO (SOLO PARA DEV)
        self.dev_map_btn = QPushButton("🛠️ Generar Mapa (Dev)")
        self.dev_map_btn.setStyleSheet("background-color: #607D8B; color: white; border: 1px dashed white;")
        self.dev_map_btn.setToolTip("Generar solo la imagen del mapa para pruebas")
        self.dev_map_btn.clicked.connect(self.generate_dev_map)
        btn_layout3.addWidget(self.dev_map_btn)
        
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
    
    def toggle_operation_mode(self):
        """🆕 Toggle between Revancha and Ancho Proyectado modes"""
        if self.mode_toggle_btn.isChecked():
            # Cambiar a modo Ancho Proyectado
            self.operation_mode = "ancho_proyectado"
            self.mode_toggle_btn.setText("📐 ANCHO PROYECTADO")
        else:
            # Cambiar a modo Revancha
            self.operation_mode = "revancha"
            self.mode_toggle_btn.setText("🔧 REVANCHA")
        
        # Reset current measurement mode when switching operation modes
        self.measurement_mode = None
        self.crown_btn.setChecked(False)
        self.width_btn.setChecked(False)
        self.lama_btn.setChecked(False)
        self.canvas.setCursor(Qt.ArrowCursor)
        
        # Update the UI to reflect new mode
        self.update_ui_for_operation_mode()
        self.update_profile_display()
        
        # Show feedback to user
        mode_name = "Ancho Proyectado" if self.operation_mode == "ancho_proyectado" else "Revancha"
        self.auto_status.setText(f"🔄 Cambiado a modo: {mode_name}")
        self.auto_status.setStyleSheet("color: blue; font-weight: bold;")
    
    def update_ui_for_operation_mode(self):
        """🆕 Update UI elements based on current operation mode"""
        current_pk = self.profiles_data[self.current_profile_index]['pk']
        
        if self.operation_mode == "ancho_proyectado":
            # Modo Ancho Proyectado: Solo mostrar Ancho
            self.crown_result.setText("Cota Lama: --")  # Cambiar label
            self.width_result.setText("Ancho Proyectado: --")
            self.lama_result.setText("")  # Ocultar
            self.revancha_result.setText("")  # Ocultar
            
            # Cambiar texto de botones
            self.crown_btn.setText("📍 Seleccionar Lama")
            self.width_btn.setText("📏 Medir Ancho Proyectado")
            self.lama_btn.setVisible(False)  # Ocultar botón LAMA manual
            
        else:
            # Modo Revancha: UI original
            self.crown_result.setText("Cota Coronamiento: --")
            self.width_result.setText("Ancho medido: --")
            self.lama_result.setText("Cota LAMA: --")
            self.revancha_result.setText("Revancha: --")
            
            # Restaurar texto de botones
            self.crown_btn.setText("📍 Cota Coronamiento")
            self.width_btn.setText("📏 Medir Ancho")
            self.lama_btn.setVisible(True)  # Mostrar botón LAMA manual
            self.lama_btn.setText("🟡 Modificar LAMA")
        
        # Recargar mediciones para el PK actual
        self.load_profile_measurements()
    
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
        
        # Clear labels based on operation mode
        if self.operation_mode == "ancho_proyectado":
            self.crown_result.setText("Cota Lama: --")
            self.width_result.setText("Ancho Proyectado: --")
            self.lama_result.setText("")
            self.revancha_result.setText("")
        else:
            self.crown_result.setText("Cota Coronamiento: --")
            self.width_result.setText("Ancho medido: --")
            self.lama_result.setText("Cota LAMA: --")
            self.revancha_result.setText("Revancha: --")
            
        self.canvas.setCursor(Qt.ArrowCursor)
        
        # This will remove the reference line too since crown is cleared
        self.update_profile_display()
    
    def find_nearest_terrain_point(self, x_click):
        """Find nearest point - different logic for each mode"""
        current_pk = self.profiles_data[self.current_profile_index]['pk']
        
        if self.operation_mode == "ancho_proyectado":
            # En modo Ancho Proyectado, buscar intersección con línea +3m si existe
            lama_elevation = None
            if current_pk in self.saved_measurements and 'lama_selected' in self.saved_measurements[current_pk]:
                lama_elevation = self.saved_measurements[current_pk]['lama_selected']['y'] + 3.0
            elif self.current_crown_point:
                lama_elevation = self.current_crown_point[1] + 3.0
                
            if lama_elevation is not None:
                # Use improved snap for reference line
                return self.find_reference_line_snap_point(x_click, lama_elevation)
            else:
                # No reference line, use terrain snap
                return self.find_terrain_snap_point(x_click)
                
        else:
            # Modo Revancha: ONLY snap to horizontal reference line for width measurements
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
        print(f"🔧 DEBUG: detect_road_width_automatically called with crown_x={crown_x}, crown_y={crown_y}")
        print(f"🔧 DEBUG: Current operation mode: {self.operation_mode}")
        
        profile = self.profiles_data[self.current_profile_index]
        distances = profile.get('distances', [])
        elevations = profile.get('elevations', [])
        
        # Filter valid data points and sort by distance
        valid_data = [(d, e) for d, e in zip(distances, elevations) if e != -9999]
        valid_data.sort(key=lambda x: x[0])  # Sort by distance
        
        print(f"🔧 DEBUG: Valid data points: {len(valid_data)}")
        
        if len(valid_data) < 20:  # Need enough points
            print(f"❌ Not enough data points: {len(valid_data)}")
            return None, None
        
        print(f"🔍 Auto-detecting from {len(valid_data)} points, crown at X={crown_x:.2f}")
        
        # 🆕 USAR DIFERENTES ALGORITMOS SEGÚN EL MODO
        if self.operation_mode == "ancho_proyectado":
            return self.detect_ancho_proyectado_boundaries(valid_data, crown_x, crown_y)
        else:
            # Lógica original para modo Revancha
            return self.detect_revancha_boundaries(valid_data, crown_x, crown_y)
    
    def detect_ancho_proyectado_boundaries(self, valid_data, reference_x, reference_y):
        """🆕 Nueva lógica para Ancho Proyectado: buscar TODAS las intersecciones"""
        print(f"🎯 ANCHO PROYECTADO: Buscando intersecciones a elevación {reference_y:.3f}m")
        
        # Buscar TODAS las intersecciones con la línea horizontal de referencia
        all_intersections = []
        
        for i in range(len(valid_data) - 1):
            p1_x, p1_y = valid_data[i]
            p2_x, p2_y = valid_data[i + 1]
            
            # Check if reference elevation is between these two points
            if (p1_y <= reference_y <= p2_y) or (p2_y <= reference_y <= p1_y):
                # Linear interpolation to find exact X coordinate
                if abs(p2_y - p1_y) > 0.001:  # Avoid division by zero
                    ratio = (reference_y - p1_y) / (p2_y - p1_y)
                    intersection_x = p1_x + ratio * (p2_x - p1_x)
                    all_intersections.append((intersection_x, reference_y))
                    print(f"  ✅ Intersección encontrada en X={intersection_x:.2f}")
        
        if len(all_intersections) < 2:
            print(f"  ❌ Se necesitan al menos 2 intersecciones, encontradas: {len(all_intersections)}")
            return None, None
        
        print(f"  🔍 Total intersecciones encontradas: {len(all_intersections)}")
        
        # Encontrar la más cercana y más lejana al punto de referencia
        distances_to_ref = [(abs(x - reference_x), (x, y)) for x, y in all_intersections]
        distances_to_ref.sort(key=lambda x: x[0])  # Sort by distance to reference
        
        closest = distances_to_ref[0][1]  # Más cercana
        furthest = distances_to_ref[-1][1]  # Más lejana
        
        print(f"  ✅ Boundary más cercana: X={closest[0]:.2f} (distancia: {distances_to_ref[0][0]:.2f}m)")
        print(f"  ✅ Boundary más lejana: X={furthest[0]:.2f} (distancia: {distances_to_ref[-1][0]:.2f}m)")
        
        return closest, furthest
    
    def detect_revancha_boundaries(self, valid_data, crown_x, crown_y):
        """🔧 Lógica original para modo Revancha (izquierda/derecha)"""
        print(f"🎯 REVANCHA: Buscando boundaries izquierda/derecha desde corona")
        
        # DEBUG - Add this line
        self.debug_profile_data(crown_x, crown_y)
        
        # Find left and right boundaries using original approach
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
            print(f"    🔍 Searching for closest point instead...")
            
            # Fallback: find closest point to target elevation
            closest_point = None
            min_elevation_diff = float('inf')
            
            for point_x, point_y in search_points:
                elevation_diff = abs(point_y - crown_y)
                if elevation_diff < min_elevation_diff:
                    min_elevation_diff = elevation_diff
                    closest_point = (point_x, point_y)
            
            if closest_point and min_elevation_diff < 1.0:  # Within 1 meter tolerance
                print(f"    ✅ Using closest point: X={closest_point[0]:.2f}, Y={closest_point[1]:.3f} (diff: {min_elevation_diff:.3f}m)")
                return closest_point
            else:
                print(f"    ❌ No suitable point found (closest diff: {min_elevation_diff:.3f}m)")
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
        
        # 🆕 LÓGICA ESPECÍFICA SEGÚN MODO DE OPERACIÓN
        if self.operation_mode == "ancho_proyectado":
            return self.handle_ancho_proyectado_click(x_click, current_pk)
        else:
            return self.handle_revancha_click(x_click, current_pk)
    
    def handle_revancha_click(self, x_click, current_pk):
        """🔧 Lógica original para modo Revancha"""
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
            
            # 🆕 Sincronizar medición con ortomosaico
            self.sync_measurements_to_orthomosaic()
            
            # 🔄 Actualizar cálculo de revancha inmediatamente
            self.update_revancha_calculation(current_pk)
            
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
                    
                    # 🔴 ALERT: Check width < 15m (HTML Styling)
                    width_str = f"{width:.2f}"
                    if width < 15.0:
                        width_str = f"<span style='color:red;'>{width_str}</span>"
                    
                    self.width_result.setText(f"Ancho auto-detectado: {width_str} m")
                    self.width_result.setStyleSheet("") # Reset style
                    
                    self.auto_status.setText("✅ Ancho detectado automáticamente")
                    self.auto_status.setStyleSheet("color: green; font-style: italic;")
                    
                    # 🆕 Sincronizar medición con ortomosaico
                    self.sync_measurements_to_orthomosaic()
                    
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
                
                self.current_width_points = []

                # 🔴 ALERT: Check width < 15m (HTML Styling)
                width_str = f"{width:.2f}"
                if width < 15.0:
                    width_str = f"<span style='color:red;'>{width_str}</span>"

                self.width_result.setText(f"Ancho medido: {width_str} m (manual)")
                self.width_result.setStyleSheet("") # Reset style
                
                self.auto_status.setText("✏️ Medición manual completada")
                self.auto_status.setStyleSheet("color: blue; font-style: italic;")
                
                # 🆕 Sincronizar medición con ortomosaico
                self.sync_measurements_to_orthomosaic()
                
                self.current_width_points = []

        
        elif self.measurement_mode == 'lama':
            # LAMA measurement on terrain
            if current_pk not in self.saved_measurements:
                self.saved_measurements[current_pk] = {}
            self.saved_measurements[current_pk]['lama'] = {
                'x': snap_x,
                'y': snap_y
            }
            
            # 🆕 Sincronizar medición con ortomosaico
            self.sync_measurements_to_orthomosaic()
            
            self.lama_result.setText(f"Cota LAMA: {snap_y:.2f} m (manual)")
            
            # 🔄 Actualizar cálculo de revancha inmediatamente
            self.update_revancha_calculation(current_pk)
        
        # Update the display
        self.update_profile_display()
    
    def handle_ancho_proyectado_click(self, x_click, current_pk):
        """🆕 Lógica específica para modo Ancho Proyectado"""
        
        if self.measurement_mode == 'crown':
            # En modo Ancho Proyectado, "crown" es realmente seleccionar la Lama
            terrain_point = self.find_terrain_snap_point(x_click)
            if not terrain_point:
                return
            snap_x, snap_y = terrain_point
            
            # Guardar como "lama_selected" en lugar de crown
            self.current_crown_point = (snap_x, snap_y)
            
            if current_pk not in self.saved_measurements:
                self.saved_measurements[current_pk] = {}
            self.saved_measurements[current_pk]['lama_selected'] = {
                'x': snap_x,
                'y': snap_y
            }
            
            self.crown_result.setText(f"Cota Lama: {snap_y:.2f} m")
            
            # 🆕 Sincronizar medición con ortomosaico
            self.sync_measurements_to_orthomosaic()
            
            # 🔄 Actualizar cálculo de revancha inmediatamente
            self.update_revancha_calculation(current_pk)
            
            # 🆕 Auto-detection: MISMA LÓGICA QUE REVANCHA pero en línea +3m
            print(f"🐛 DEBUG: auto_width_detection = {self.auto_width_detection}")
            if self.auto_width_detection:
                print(f"🐛 DEBUG: Iniciando auto-detección en Ancho Proyectado")
                print(f"🐛 DEBUG: Lama point = ({snap_x:.2f}, {snap_y:.2f})")
                
                self.auto_status.setText("🔍 Detectando ancho proyectado automáticamente...")
                self.auto_status.setStyleSheet("color: blue; font-style: italic;")
                
                reference_elevation = snap_y + 3.0  # 3 metros arriba de la lama
                print(f"🐛 DEBUG: Reference elevation +3m = {reference_elevation:.2f}")
                print(f"🐛 DEBUG: About to call detect_road_width_automatically with snap_x={snap_x:.2f}, reference_elevation={reference_elevation:.2f}")
                
                # 🎯 USAR LA MISMA FUNCIÓN ROBUSTA QUE REVANCHA
                left_boundary, right_boundary = self.detect_road_width_automatically(snap_x, reference_elevation)
                print(f"🐛 DEBUG: Boundaries returned = {left_boundary}, {right_boundary}")
                
                if left_boundary and right_boundary:
                    print("🐛 DEBUG: ✅ Auto-detección exitosa")
                    # Automatically set width measurement
                    self.current_width_points = [left_boundary, right_boundary]
                    
                    # Calculate width
                    width = abs(right_boundary[0] - left_boundary[0])
                    print(f"🐛 DEBUG: Width calculated = {width:.2f}m")
                    
                    # Save auto-detected measurement
                    self.saved_measurements[current_pk]['width'] = {
                        'p1': left_boundary,
                        'p2': right_boundary,
                        'distance': width,
                        'auto_detected': True,
                        'reference_elevation': reference_elevation
                    }
                    
                    # 🔴 ALERT: Check width < 15m (HTML Styling)
                    width_str = f"{width:.2f}"
                    if width < 15.0:
                        width_str = f"<span style='color:red;'>{width_str}</span>"
                    
                    self.width_result.setText(f"Ancho Proyectado auto: {width_str} m")
                    self.width_result.setStyleSheet("") # Reset style
                    
                    self.auto_status.setText("✅ Ancho proyectado detectado automáticamente")
                    self.auto_status.setStyleSheet("color: green; font-style: italic;")
                    
                    # 🆕 Sincronizar medición con ortomosaico
                    self.sync_measurements_to_orthomosaic()
                    
                    # 🆕 Actualizar cálculo de revancha inmediatamente
                    self.update_revancha_calculation(current_pk)
                    
                    # 🆕 ACTIVAR AUTOMÁTICAMENTE MODO WIDTH para permitir ajustes
                    self.set_measurement_mode('width')
                    
                else:
                    print("🐛 DEBUG: ❌ Auto-detección falló")
                    self.auto_status.setText("⚠️ No se pudo detectar ancho automáticamente")
                    self.auto_status.setStyleSheet("color: orange; font-style: italic;")
            else:
                print("🐛 DEBUG: Auto-width detection está DESACTIVADO")
                    
        elif self.measurement_mode == 'width':
            # En modo Ancho Proyectado, el width se mide sobre la línea de referencia (+3m)
            lama_elevation = None
            lama_x = 0
            
            # Obtener datos de lama seleccionada
            if current_pk in self.saved_measurements and 'lama_selected' in self.saved_measurements[current_pk]:
                lama_data = self.saved_measurements[current_pk]['lama_selected']
                lama_elevation = lama_data['y'] + 3.0  # 3 metros arriba
                lama_x = lama_data['x']
            elif self.current_crown_point:
                lama_elevation = self.current_crown_point[1] + 3.0  # 3 metros arriba
                lama_x = self.current_crown_point[0]
                
            if lama_elevation is None:
                from qgis.PyQt.QtWidgets import QMessageBox
                QMessageBox.information(
                    self,
                    "Lama requerida",
                    "Debe seleccionar un punto de Lama antes de medir el ancho proyectado.\n"
                    "El ancho se medirá 3 metros arriba de la cota Lama."
                )
                return
                
            # Determine snap behavior based on A key
            if self._key_A_pressed:
                # AUTO-SNAP: intersección con terreno a la altura de referencia
                # 🔧 MEJORAR SNAP: buscar en radio alrededor del click
                reference_snap_point = self.find_reference_line_snap_point(x_click, lama_elevation)
                
                if reference_snap_point:
                    snap_x, snap_y = reference_snap_point
                else:
                    snap_x, snap_y = (x_click, lama_elevation)
            else:
                # MANUAL SNAP: usar línea de referencia
                snap_x, snap_y = (x_click, lama_elevation)
                
            # Agregar punto a medición de ancho
            self.current_width_points.append((snap_x, snap_y))
            
            if len(self.current_width_points) == 1:
                snap_type = "Auto-snap" if self._key_A_pressed else "Ref"
                self.width_result.setText(f"Punto 1: X={snap_x:.1f}m, Y={snap_y:.2f}m ({snap_type})")
                
            elif len(self.current_width_points) == 2:
                p1 = self.current_width_points[0]
                p2 = self.current_width_points[1]
                width = abs(p2[0] - p1[0])
                
                if current_pk not in self.saved_measurements:
                    self.saved_measurements[current_pk] = {}
                self.saved_measurements[current_pk]['width'] = {
                    'p1': p1,
                    'p2': p2,
                    'distance': width,
                    'auto_detected': False,
                    'reference_elevation': lama_elevation
                }
                
                self.current_width_points = []

                # 🔴 ALERT: Check width < 15m (HTML Styling)
                width_str = f"{width:.2f}"
                if width < 15.0:
                    width_str = f"<span style='color:red;'>{width_str}</span>"
                
                self.width_result.setText(f"Ancho Proyectado: {width_str} m (manual)")
                self.width_result.setStyleSheet("") # Reset style
                
                self.auto_status.setText("✏️ Medición manual completada")
                self.auto_status.setStyleSheet("color: blue; font-style: italic;")
                
                # 🆕 Sincronizar medición con ortomosaico
                self.sync_measurements_to_orthomosaic()
                
                self.current_width_points = []
        
        # Update display
        self.update_profile_display()
    
    def find_reference_line_snap_point(self, x_click, reference_elevation):
        """🆕 Find snap point on reference line with terrain intersection in radius around click"""
        profile = self.profiles_data[self.current_profile_index]
        distances = profile.get('distances', [])
        elevations = profile.get('elevations', [])
        
        valid_data = [(d, e) for d, e in zip(distances, elevations) if e != -9999]
        if len(valid_data) < 10:
            return None
            
        # 🎯 BUSCAR EN RADIO ALREDEDOR DEL CLICK (similar a modo Revancha)
        search_radius = 5.0  # metros de radio de búsqueda
        
        # Filter points within search radius
        nearby_points = [(d, e) for d, e in valid_data 
                        if abs(d - x_click) <= search_radius]
        
        if not nearby_points:
            # If no points in radius, find closest intersection
            return self.find_closest_terrain_intersection(x_click, reference_elevation, valid_data)
        
        # Find intersections within the search radius
        intersections = []
        nearby_points.sort(key=lambda x: x[0])  # Sort by distance
        
        for i in range(len(nearby_points) - 1):
            p1_x, p1_y = nearby_points[i]
            p2_x, p2_y = nearby_points[i + 1]
            
            # Check if reference elevation is between these two points
            if (p1_y <= reference_elevation <= p2_y) or (p2_y <= reference_elevation <= p1_y):
                # Linear interpolation to find exact X coordinate
                if abs(p2_y - p1_y) > 0.001:  # Avoid division by zero
                    ratio = (reference_elevation - p1_y) / (p2_y - p1_y)
                    intersection_x = p1_x + ratio * (p2_x - p1_x)
                    
                    # Calculate distance from click point
                    distance_from_click = abs(intersection_x - x_click)
                    intersections.append((intersection_x, reference_elevation, distance_from_click))
        
        if intersections:
            # Return closest intersection to click point
            closest = min(intersections, key=lambda x: x[2])
            return (closest[0], closest[1])
        
        # Fallback: no intersections found, return point on reference line at click X
        return (x_click, reference_elevation)
    
    def find_closest_terrain_intersection(self, x_click, reference_elevation, valid_data):
        """🔧 Fallback function to find closest intersection when no points in radius"""
        intersections = []
        
        for i in range(len(valid_data) - 1):
            p1_x, p1_y = valid_data[i]
            p2_x, p2_y = valid_data[i + 1]
            
            # Check if reference elevation is between these two points
            if (p1_y <= reference_elevation <= p2_y) or (p2_y <= reference_elevation <= p1_y):
                if abs(p2_y - p1_y) > 0.001:
                    ratio = (reference_elevation - p1_y) / (p2_y - p1_y)
                    intersection_x = p1_x + ratio * (p2_x - p1_x)
                    distance_from_click = abs(intersection_x - x_click)
                    intersections.append((intersection_x, reference_elevation, distance_from_click))
        
        if intersections:
            closest = min(intersections, key=lambda x: x[2])
            return (closest[0], closest[1])
            
        return None

    # Implementación original de update_revancha_calculation fue reemplazada por una versión más completa más abajo
    
    def prev_profile(self):
        """Navigate to previous profile"""
        if self.current_profile_index > 0:
            self.current_profile_index -= 1
            self.pk_slider.setValue(self.current_profile_index)
            self.load_profile_measurements()  # Load measurements for new PK
            self.sync_range_controls()  # 🆕 Sync range spinboxes
            self.update_profile_display()
            # 🆕 Actualizar visualizador de ortomosaico si está abierto
            self.update_orthomosaic_view()
    
    def next_profile(self):
        """Navigate to next profile"""
        if self.current_profile_index < len(self.profiles_data) - 1:
            self.current_profile_index += 1
            self.pk_slider.setValue(self.current_profile_index)
            self.load_profile_measurements()  # Load measurements for new PK
            self.sync_range_controls()  # 🆕 Sync range spinboxes
            self.update_profile_display()
            # 🆕 Actualizar visualizador de ortomosaico si está abierto
            self.update_orthomosaic_view()
    
    def on_slider_changed(self, value):
        """Handle slider position change"""
        if value != self.current_profile_index:
            self.current_profile_index = value
            self.load_profile_measurements()  # Load measurements for new PK
            self.sync_range_controls()  # 🆕 Sync range spinboxes
            self.update_profile_display()
            # 🆕 Actualizar visualizador de ortomosaico si está abierto
            self.update_orthomosaic_view()
            
    def update_orthomosaic_view(self):
        """🆕 Actualiza la vista del ortomosaico si está abierto"""
        if self.ortho_viewer and hasattr(self.ortho_viewer, 'update_to_profile'):
            try:
                profile = self.profiles_data[self.current_profile_index]
                self.ortho_viewer.update_to_profile(profile)
                
                # 🆕 Sincronizar mediciones también
                self.sync_measurements_to_orthomosaic()
                
            except Exception as e:
                print(f"Error al actualizar ortomosaico: {str(e)}")
    
    def sync_range_controls(self):
        """🆕 Sincroniza los spinboxes de rango con los valores actuales"""
        if hasattr(self, 'toolbar') and hasattr(self.toolbar, 'left_limit_spin'):
            # Bloquear señales temporalmente para evitar bucles
            self.toolbar.left_limit_spin.blockSignals(True)
            self.toolbar.right_limit_spin.blockSignals(True)
            
            # Actualizar valores
            self.toolbar.left_limit_spin.setValue(int(self.custom_range_left))
            self.toolbar.right_limit_spin.setValue(int(self.custom_range_right))
            
            # Desbloquear señales
            self.toolbar.left_limit_spin.blockSignals(False)
            self.toolbar.right_limit_spin.blockSignals(False)
            
            # Actualizar tooltip del botón de extensión
            zoom_extent_actions = [a for a in self.toolbar.actions() if "Extensión" in a.text()]
            if zoom_extent_actions:
                zoom_extent_actions[0].setToolTip(
                    f"Vista completa del perfil ({self.custom_range_left}m a {self.custom_range_right}m)"
                )
    
    def sync_measurements_to_orthomosaic(self):
        """🆕 Sincroniza las mediciones actuales al ortomosaico"""
        if not self.ortho_viewer or not hasattr(self.ortho_viewer, 'update_measurements_display'):
            return
            
        try:
            # Get current PK with fallback for different naming conventions
            profile = self.profiles_data[self.current_profile_index]
            current_pk = profile.get('pk') or profile.get('PK')
            
            print(f"🔍 DEBUG - Syncing for PK: {current_pk} (profile index: {self.current_profile_index})")
            
            # Obtener mediciones guardadas para el PK actual
            measurements_data = {}
            if current_pk in self.saved_measurements:
                measurements_data = self.saved_measurements[current_pk].copy()
                print(f"🔍 DEBUG - Found saved measurements for {current_pk}: {list(measurements_data.keys())}")
            else:
                print(f"⚠️ DEBUG - No saved measurements found for PK {current_pk}")
                print(f"📊 DEBUG - Available PKs in saved_measurements: {list(self.saved_measurements.keys())}")
            
            # 🔧 CORREGIDO: Añadir puntos LAMA automáticos si no hay manuales
            profile = self.profiles_data[self.current_profile_index]
            auto_lama_points = profile.get('lama_points', [])
            
            # Si no hay LAMA manual ni lama_selected, usar LAMA automático
            if (auto_lama_points and 
                'lama' not in measurements_data and 
                'lama_selected' not in measurements_data):
                
                # Convertir LAMA automático a formato de medición
                lama_point = auto_lama_points[0]  # Usar el primer punto LAMA
                measurements_data['lama'] = {
                    'x': lama_point.get('offset_from_centerline', 0),  # Offset desde el eje
                    'y': lama_point['elevation']
                }
                print(f"DEBUG - LAMA automático agregado: x={lama_point.get('offset_from_centerline', 0):.2f}, y={lama_point['elevation']:.2f}")
            
            # Añadir mediciones temporales SOLO si no hay guardadas
            # Esto evita que las temporales sobrescriban las guardadas al navegar
            if self.current_crown_point and 'crown' not in measurements_data:
                measurements_data['crown'] = {
                    'x': self.current_crown_point[0],
                    'y': self.current_crown_point[1]
                }
            
            if len(self.current_width_points) >= 2 and 'width' not in measurements_data:
                measurements_data['width'] = {
                    'p1': {'x': self.current_width_points[0][0], 'y': self.current_width_points[0][1]},
                    'p2': {'x': self.current_width_points[1][0], 'y': self.current_width_points[1][1]},
                    'distance': abs(self.current_width_points[1][0] - self.current_width_points[0][0])
                }
            
            # Enviar mediciones al ortomosaico
            self.ortho_viewer.update_measurements_display(measurements_data)
            print(f"DEBUG - Mediciones sincronizadas para PK {current_pk}: {list(measurements_data.keys())}")
            
            # 🔧 DEBUG TEMPORAL: Mostrar estructura completa
            if measurements_data:
                for key, value in measurements_data.items():
                    print(f"DEBUG - {key}: {value}")
            
        except Exception as e:
            print(f"ERROR al sincronizar mediciones: {str(e)}")
    
    def load_profile_measurements(self):
        """🔧 Load measurements specific to current PK including different modes"""
        current_pk = self.profiles_data[self.current_profile_index]['pk']
        
        # Clear current temporary measurements
        self.current_crown_point = None
        self.current_width_points = []
        
        # Load saved measurements for this PK
        if current_pk in self.saved_measurements:
            measurements = self.saved_measurements[current_pk]
            
            if self.operation_mode == "ancho_proyectado":
                # Modo Ancho Proyectado
                if 'lama_selected' in measurements:
                    lama_data = measurements['lama_selected']
                    self.current_crown_point = (lama_data['x'], lama_data['y'])
                    self.crown_result.setText(f"Cota Lama: {lama_data['y']:.2f} m")
                else:
                    self.crown_result.setText("Cota Lama: --")
                
                # Load width measurement
                if 'width' in measurements:
                    width_data = measurements['width']
                    auto_detected = width_data.get('auto_detected', False)
                    width_val = width_data['distance']
                    
                    # 🔴 ALERT: Check width < 15m (HTML Styling)
                    width_str = f"{width_val:.2f}"
                    if width_val < 15.0:
                        width_str = f"<span style='color:red;'>{width_str}</span>"
                    
                    if auto_detected:
                        self.width_result.setText(f"Ancho Proyectado: {width_str} m (auto)")
                        self.auto_status.setText("✅ Ancho proyectado calculado (+3m)")
                        self.auto_status.setStyleSheet("color: green; font-style: italic;")
                    else:
                        self.width_result.setText(f"Ancho Proyectado: {width_str} m (manual)")
                        self.auto_status.setText("✏️ Medición manual")
                        self.auto_status.setStyleSheet("color: blue; font-style: italic;")
                    
                    # Reset stylesheet just in case
                    self.width_result.setStyleSheet("")

                else:
                    self.width_result.setText("Ancho Proyectado: --")
                    self.width_result.setStyleSheet("")
                    self.auto_status.setText("Auto-detección activada" if self.auto_width_detection else "Modo manual activado")
                    self.auto_status.setStyleSheet("color: green; font-style: italic;" if self.auto_width_detection else "color: orange; font-style: italic;")
                    
            else:
                # Modo Revancha (lógica original)
                if 'crown' in measurements:
                    crown_data = measurements['crown']
                    self.current_crown_point = (crown_data['x'], crown_data['y'])
                    self.crown_result.setText(f"Cota Coronamiento: {crown_data['y']:.2f} m")
                else:
                    self.crown_result.setText("Cota Coronamiento: --")
                
                # Load width measurement
                if 'width' in measurements:
                    width_data = measurements['width']
                    auto_detected = width_data.get('auto_detected', False)
                    width_val = width_data['distance']
                    
                    # 🔴 ALERT: Check width < 15m (HTML Styling)
                    width_str = f"{width_val:.2f}"
                    if width_val < 15.0:
                        width_str = f"<span style='color:red;'>{width_str}</span>"
                    
                    if auto_detected:
                        self.width_result.setText(f"Ancho medido: {width_str} m (auto-detectado)")
                    else:
                        self.width_result.setText(f"Ancho medido: {width_str} m (manual)")
                    
                    if auto_detected:
                        self.auto_status.setText("✅ Ancho detectado automáticamente")
                        self.auto_status.setStyleSheet("color: green; font-style: italic;")
                    else:
                        self.auto_status.setText("✏️ Medición manual")
                        self.auto_status.setStyleSheet("color: blue; font-style: italic;")
                    
                    # Reset stylesheet just in case
                    self.width_result.setStyleSheet("")

                else:
                    self.width_result.setText("Ancho medido: --")
                    self.width_result.setStyleSheet("")
                    self.auto_status.setText("Auto-detección activada" if self.auto_width_detection else "Modo manual activado")
                    self.auto_status.setStyleSheet("color: green; font-style: italic;" if self.auto_width_detection else "color: orange; font-style: italic;")
                    
        else:
            # No measurements for this PK
            if self.operation_mode == "ancho_proyectado":
                self.crown_result.setText("Cota Lama: --")
                self.width_result.setText("Ancho Proyectado: --")
                self.width_result.setStyleSheet("")  # Reset style
            else:
                self.crown_result.setText("Cota Coronamiento: --")
                self.width_result.setText("Ancho medido: --")
                self.width_result.setStyleSheet("")  # Reset style
                
            self.auto_status.setText("Auto-detección activada" if self.auto_width_detection else "Modo manual activado")
            self.auto_status.setStyleSheet("color: green; font-style: italic;" if self.auto_width_detection else "color: orange; font-style: italic;")
        
        # 🆕 Update LAMA and Revancha (only in Revancha mode)
        if self.operation_mode == "revancha":
            self.update_revancha_calculation()
            
        # 🆕 Sincronizar mediciones cargadas con ortomosaico
        self.sync_measurements_to_orthomosaic()
    
    def update_revancha_calculation(self, current_pk=None):
        """
        Actualiza los cálculos de revancha basados en los datos actuales
        sin necesidad de navegar entre PKs.
        
        Esta función se llamará después de cada modificación de crown o LAMA.
        """
        if current_pk is None:
            if hasattr(self, 'profiles_data') and hasattr(self, 'current_profile_index'):
                profile = self.profiles_data[self.current_profile_index]
                current_pk = profile.get('PK') or profile.get('pk')
            else:
                return
        
        # Get LAMA point - check saved first, then auto LAMA
        manual_lama = None
        if current_pk in self.saved_measurements and 'lama' in self.saved_measurements[current_pk]:
            manual_lama = self.saved_measurements[current_pk]['lama']
        
        # Get auto LAMA points if available
        auto_lama_points = None
        if hasattr(self, 'profiles_data') and hasattr(self, 'current_profile_index'):
            profile = self.profiles_data[self.current_profile_index]
            auto_lama_points = profile.get('lama_points', [])
        
        # Get LAMA elevation (manual takes priority)
        lama_elevation = None
        if manual_lama:
            lama_elevation = manual_lama['y']
            lama_source = "manual"
        elif auto_lama_points:
            lama_elevation = auto_lama_points[0]['elevation']
            lama_source = "auto"
        
        # Get Crown elevation
        crown_elevation = None
        if current_pk in self.saved_measurements and 'crown' in self.saved_measurements[current_pk]:
            crown_elevation = self.saved_measurements[current_pk]['crown']['y']
        elif hasattr(self, 'current_crown_point') and self.current_crown_point:
            crown_elevation = self.current_crown_point[1]
        
        # Calculate Revancha
        if crown_elevation is not None and lama_elevation is not None:
            revancha = crown_elevation - lama_elevation
            
            # 🔴 ALERT: Check Revancha < 3m (HTML Styling)
            revancha_str = f"{revancha:.2f}"
            if revancha < 3.0:
                revancha_str = f"<span style='color:red;'>{revancha_str}</span>"
            
            self.revancha_result.setText(f"Revancha: {revancha_str} m")
            self.revancha_result.setStyleSheet("") # Reset style
            
            # Update LAMA display
            self.lama_result.setText(f"Cota LAMA: {lama_elevation:.2f} m ({lama_source})")
            
            print(f"✅ Revancha calculada: {revancha:.2f}m (crown: {crown_elevation:.2f}m, lama: {lama_elevation:.2f}m)")
            return revancha
        else:
            # Show what's missing
            missing_parts = []
            if crown_elevation is None:
                missing_parts.append("coronamiento")
            if lama_elevation is None:
                missing_parts.append("lama")
            
            self.revancha_result.setText(f"Revancha: -- (falta {', '.join(missing_parts)})")
            self.revancha_result.setStyleSheet("")  # Reset style
            
            # Still show LAMA if available
            if lama_elevation is not None:
                self.lama_result.setText(f"Cota LAMA: {lama_elevation:.2f} m ({lama_source})")
            else:
                self.lama_result.setText("Cota LAMA: --")
            
            return None
    
    def update_profile_display(self, export_mode=False):
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
        
        # 🔧 CRITICAL FIX: Filter data to display range FIRST
        # This ensures we only plot what's visible and prevents "empty" appearance
        print(f"📊 DEBUG - Total points: {len(distances)}, Range: {x_min} to {x_max}")
        
        # Filter valid data within the display range
        valid_data = [(d, e) for d, e in zip(distances, elevations) 
                      if e != -9999 and x_min <= d <= x_max]
        
        print(f"📊 DEBUG - Points in range: {len(valid_data)}")
        
        if not valid_data:
            self.ax.text(0.5, 0.5, f'No hay datos válidos en el rango {x_min}m a {x_max}m', 
                        ha='center', va='center', transform=self.ax.transAxes)
            self.canvas.draw()
            return
        
        valid_distances, valid_elevations = zip(*valid_data)
        
        # 🆕 Plot Previous Terrain (Background)
        previous_elevations = profile.get('previous_elevations', [])
        if previous_elevations and len(previous_elevations) == len(distances):
            # Filter valid previous data
            valid_prev_data = [(d, pe) for d, pe in zip(distances, previous_elevations) 
                             if pe != -9999 and x_min <= d <= x_max]
            
            if valid_prev_data:
                prev_d, prev_e = zip(*valid_prev_data)
                self.ax.plot(prev_d, prev_e, '--', color='gray', linewidth=1.0, 
                           alpha=0.6, label='Terreno Anterior', zorder=0)

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
        
        # 🆕 REFERENCE LINES - Different logic based on operation mode
        if self.operation_mode == "ancho_proyectado":
            # Modo Ancho Proyectado: Línea en lama, línea +2m (visual) y línea +3m (medición)
            lama_elevation = None
            
            # Get lama point (selected manually)
            if current_pk in self.saved_measurements and 'lama_selected' in self.saved_measurements[current_pk]:
                lama_elevation = self.saved_measurements[current_pk]['lama_selected']['y']
            elif self.current_crown_point:
                lama_elevation = self.current_crown_point[1]
                
            if lama_elevation is not None:
                x_range = [x_min, x_max]
                
                # Línea en la lama (visual reference)
                y_lama = [lama_elevation, lama_elevation]
                self.ax.plot(x_range, y_lama, ':', color='yellow', linewidth=2.0, 
                            alpha=0.8, label=f'Lama: {lama_elevation:.2f}m', zorder=2)
                
                # 🆕 Línea de ayuda visual (+2m) - MÁS TENUE
                visual_elevation = lama_elevation + 2.0
                y_visual = [visual_elevation, visual_elevation]
                self.ax.plot(x_range, y_visual, ':', color='gray', linewidth=1.0, 
                            alpha=0.4, label=f'Visual +2m: {visual_elevation:.2f}m', zorder=1)
                
                # Línea de referencia 3m arriba (para medición)
                reference_elevation = lama_elevation + 3.0
                y_ref = [reference_elevation, reference_elevation]
                self.ax.plot(x_range, y_ref, '--', color='orange', linewidth=2.5, 
                            alpha=1.0, label=f'Ref. +3m: {reference_elevation:.2f}m', zorder=3)
        else:
            # Modo Revancha: Línea de coronamiento y auxiliar
            crown_elevation = None
            if current_pk in self.saved_measurements and 'crown' in self.saved_measurements[current_pk]:
                crown_elevation = self.saved_measurements[current_pk]['crown']['y']
            elif self.current_crown_point:
                crown_elevation = self.current_crown_point[1]
            
            if crown_elevation is not None:
                x_range = [x_min, x_max]
                
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
        
        # 📏 Show SAVED measurements for current PK - Different based on mode
        if current_pk in self.saved_measurements:
            measurements = self.saved_measurements[current_pk]
            
            if self.operation_mode == "ancho_proyectado":
                # Modo Ancho Proyectado
                if 'lama_selected' in measurements:
                    lama_data = measurements['lama_selected']
                    self.ax.plot(lama_data['x'], lama_data['y'], 'o', color='yellow', markersize=12,
                            markeredgecolor='orange', markeredgewidth=2, 
                            label=f'Lama Seleccionada: {lama_data["y"]:.2f}m', zorder=4)
                
                # Width measurement
                if 'width' in measurements:
                    width_data = measurements['width']
                    p1, p2 = width_data['p1'], width_data['p2']
                    auto_detected = width_data.get('auto_detected', False)
                    
                    color = 'lime' if (auto_detected or export_mode) else 'magenta'
                    marker_size = 10 if auto_detected else 8
                    line_style = '-' if auto_detected else '--'
                    label_prefix = 'Auto' if auto_detected else 'Manual'
                    
                    self.ax.plot([p1[0], p2[0]], [p1[1], p2[1]], 'o', color=color, markersize=marker_size, zorder=4)
                    self.ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color=color, linestyle=line_style, 
                            linewidth=2.5, alpha=0.9, label=f'Ancho {label_prefix}: {width_data["distance"]:.2f}m', zorder=4)
            else:
                # Modo Revancha (lógica original)
                if 'crown' in measurements:
                    crown_data = measurements['crown']
                    self.ax.plot(crown_data['x'], crown_data['y'], 'ro', markersize=10, 
                            label=f'Cota Coronamiento: {crown_data["y"]:.2f}m', zorder=4)
                
                # Width measurement with auto-detection indicator
                if 'width' in measurements:
                    width_data = measurements['width']
                    p1, p2 = width_data['p1'], width_data['p2']
                    auto_detected = width_data.get('auto_detected', False)
                    
                    color = 'lime' if (auto_detected or export_mode) else 'magenta'
                    marker_size = 10 if auto_detected else 8
                    line_style = '-' if auto_detected else '--'
                    label_prefix = 'Auto' if auto_detected else 'Manual'
                    
                    self.ax.plot([p1[0], p2[0]], [p1[1], p2[1]], 'o', color=color, markersize=marker_size, zorder=4)
                    self.ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color=color, linestyle=line_style, 
                            linewidth=2.5, alpha=0.9, label=f'{label_prefix}: {width_data["distance"]:.2f}m', zorder=4)
                
                # Manual LAMA point (overrides automatic)
                if 'lama' in measurements:
                    lama_data = measurements['lama']
                    self.ax.plot(lama_data['x'], lama_data['y'], 'o', color='orange', markersize=12,
                            markeredgecolor='red', markeredgewidth=2, 
                            label=f'LAMA Manual: {lama_data["y"]:.2f}m', zorder=4)
        
        # Show automatic LAMA points (only in Revancha mode and if no manual override)
        if (self.operation_mode == "revancha" and 
            (current_pk not in self.saved_measurements or 'lama' not in self.saved_measurements[current_pk])):
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
        
        # 🆕 Mostrar leyenda solo si está activada
        if self.show_legend and not export_mode:
            self.ax.legend(loc='upper right', fontsize=9)
        elif export_mode:
            # 📸 LEYENDA DETALLADA PARA PANTALLAZOS
            from matplotlib.lines import Line2D
            custom_handles = []
            
            # 1. Cota Coronamiento / Lama
            crown_val = None
            if self.operation_mode == "ancho_proyectado":
                if current_pk in self.saved_measurements and 'lama_selected' in self.saved_measurements[current_pk]:
                    crown_val = self.saved_measurements[current_pk]['lama_selected']['y']
                    custom_handles.append(Line2D([0], [0], marker='o', color='w', markerfacecolor='yellow', 
                                              markersize=10, label=f'Lama: {crown_val:.2f}m'))
            else:
                 if current_pk in self.saved_measurements and 'crown' in self.saved_measurements[current_pk]:
                    crown_val = self.saved_measurements[current_pk]['crown']['y']
                    custom_handles.append(Line2D([0], [0], marker='o', color='w', markerfacecolor='darkgreen', 
                                              markersize=10, label=f'Cota Coronamiento: {crown_val:.2f}m'))

            # 2. LAMA (solo revancha)
            lama_val = None
            if self.operation_mode == "revancha":
                if current_pk in self.saved_measurements and 'lama' in self.saved_measurements[current_pk]:
                    lama_val = self.saved_measurements[current_pk]['lama']['y']
                elif 'lama_points' in profile and profile['lama_points']:
                    lama_val = profile['lama_points'][0]['elevation']
                
                if lama_val is not None:
                     custom_handles.append(Line2D([0], [0], marker='o', color='w', markerfacecolor='yellow', 
                                              markersize=10, markeredgecolor='brown', label=f'LAMA: {lama_val:.2f}m'))

            # 3. Revancha
            if crown_val is not None and lama_val is not None:
                revancha = crown_val - lama_val
                
                # Formato con color rojo si es menor a 3m
                if revancha < 3.0:
                    label_text = r"Revancha: $\mathdefault{\color{red}{" + f"{revancha:.2f}" + r"}}$ m"
                else:
                    label_text = f"Revancha: {revancha:.2f}m"
                    
                custom_handles.append(Line2D([0], [0], color='none', label=label_text))

            # 4. Ancho
            width_val = None
            if current_pk in self.saved_measurements and 'width' in self.saved_measurements[current_pk]:
                width_val = self.saved_measurements[current_pk]['width']['distance']
                
                # Formato con color rojo si es menor a 15m
                if width_val < 15.0:
                    label_text = r"Ancho: $\mathdefault{\color{red}{" + f"{width_val:.2f}" + r"}}$ m"
                else:
                    label_text = f"Ancho: {width_val:.2f}m"
                    
                custom_handles.append(Line2D([0], [0], color='lime', linewidth=2, label=label_text))
            
            self.ax.legend(handles=custom_handles, loc='upper right', framealpha=0.9, fontsize=10)
        else:
            # Remover leyenda si existe
            legend = self.ax.get_legend()
            if legend:
                legend.remove()
        
        # 🎯 Focus on relevant area with custom range
        self.ax.set_xlim(x_min, x_max)
        
        if valid_elevations:
            # valid_data already filtered to display range, so use all elevations
            relevant_elevations = list(valid_elevations)
            
            # 🆕 Include reference elevations in Y-axis scaling based on mode
            reference_elevation = None
            if self.operation_mode == "ancho_proyectado":
                # Get lama elevation for Ancho Proyectado
                if current_pk in self.saved_measurements and 'lama_selected' in self.saved_measurements[current_pk]:
                    reference_elevation = self.saved_measurements[current_pk]['lama_selected']['y']
                elif self.current_crown_point:
                    reference_elevation = self.current_crown_point[1]
                    
                if reference_elevation is not None:
                    relevant_elevations.append(reference_elevation)  # Lama line
                    relevant_elevations.append(reference_elevation + 2.0)  # +2m visual line
                    relevant_elevations.append(reference_elevation + 3.0)  # +3m reference line
            else:
                # Get crown elevation for Revancha mode
                if current_pk in self.saved_measurements and 'crown' in self.saved_measurements[current_pk]:
                    reference_elevation = self.saved_measurements[current_pk]['crown']['y']
                elif self.current_crown_point:
                    reference_elevation = self.current_crown_point[1]
                    
                if reference_elevation is not None:
                    relevant_elevations.append(reference_elevation)  # Crown line
                    relevant_elevations.append(reference_elevation - 1.0)  # Auxiliary line
            
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
            # valid_data already filtered, so use all elevations for range
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
        
        # valid_data already filtered to range, so count all
        visible_points = len(valid_data)
        
        # 🆕 Add reference lines info based on operation mode
        ref_info = ""
        if self.operation_mode == "ancho_proyectado":
            # Modo Ancho Proyectado: mostrar info de líneas Lama
            lama_elevation = None
            if current_pk in self.saved_measurements and 'lama_selected' in self.saved_measurements[current_pk]:
                lama_elevation = self.saved_measurements[current_pk]['lama_selected']['y']
            elif self.current_crown_point:
                lama_elevation = self.current_crown_point[1]
                
            if lama_elevation is not None:
                ref_info = f" | Lama: {lama_elevation:.2f}m | +2m: {lama_elevation+2.0:.2f}m | +3m: {lama_elevation+3.0:.2f}m"
        else:
            # Modo Revancha: mostrar info de líneas de coronamiento
            crown_elevation = None
            if current_pk in self.saved_measurements and 'crown' in self.saved_measurements[current_pk]:
                crown_elevation = self.saved_measurements[current_pk]['crown']['y']
            elif self.current_crown_point:
                crown_elevation = self.current_crown_point[1]
                
            if crown_elevation is not None:
                ref_info = f" | Ref: {crown_elevation:.2f}m | Aux: {crown_elevation-1.0:.2f}m"
        
        self.info_valid_points.setText(f"Puntos válidos: {len(valid_data)} | Visibles: {visible_points} | {lama_info}{ref_info}")
        
        # Refresh canvas
        self.figure.tight_layout()
        self.canvas.draw()

    def export_measurements_to_csv(self):
        """Export all measurements from all profiles to CSV file and screenshots for alerts"""
        try:
            from qgis.PyQt.QtWidgets import QFileDialog, QMessageBox
            import os
            
            # 🎯 NOMBRE DINÁMICO SEGÚN MODO
            mode_name = "ancho_proyectado" if self.operation_mode == "ancho_proyectado" else "revanchas"
            default_filename = f"mediciones_{mode_name}.csv"
            
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                f"Exportar Mediciones", # Renamed from Exportar Mediciones CSV
                default_filename,
                "CSV files (*.csv);;All files (*.*)"
            )
            
            if not file_path:
                return  # Usuario canceló
            
            # Crear carpeta de perfiles si no existe
            profiles_dir = os.path.join(os.path.dirname(file_path), "Perfiles")
            if not os.path.exists(profiles_dir):
                try:
                    os.makedirs(profiles_dir)
                except Exception as e:
                    print(f"Error creando carpeta Perfiles: {e}")
            
            # Mostrar progreso
            progress = QProgressDialog("Recopilando mediciones y generando pantallazos...", "Cancelar", 0, 100, self)
            progress.setWindowModality(Qt.WindowModal)
            progress.show()
            
            QApplication.processEvents()
            
            # Guardar el índice actual para restaurarlo al final
            original_profile_index = self.current_profile_index
            
            # Recopilar datos de todos los perfiles
            export_data = []
            total_profiles = len(self.profiles_data)
            
            progress.setLabelText("Procesando mediciones...")
            progress.setValue(0)
            QApplication.processEvents()
            
            screenshots_taken = 0
            
            for i, profile in enumerate(self.profiles_data):
                pk = profile['pk']
                
                # Obtener mediciones guardadas
                measurements = self.saved_measurements.get(pk, {})
                
                should_take_screenshot = False
                
                if self.operation_mode == "ancho_proyectado":
                    # Modo Ancho Proyectado: Solo PK y Ancho
                    width_val = measurements.get('width', {}).get('distance', None)
                    row_data = {
                        'PK': pk,
                        'Ancho_Proyectado': width_val
                    }
                    
                    # Check alert
                    if width_val is not None and width_val < 15.0:
                        should_take_screenshot = True
                        
                else:
                    # Modo Revancha
                    # Obtener datos automáticos (LAMA siempre disponible)
                    auto_lama_points = profile.get('lama_points', [])
                    auto_lama_elevation = auto_lama_points[0]['elevation'] if auto_lama_points else None
                    
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
                    
                    row_data = {
                        'PK': pk,
                        'Cota_Coronamiento': crown_elevation,
                        'Revancha': revancha_value,
                        'Lama': lama_elevation,
                        'Ancho': width_value
                    }
                    
                    # Check alerts
                    if (revancha_value is not None and revancha_value < 3.0) or \
                       (width_value is not None and width_value < 15.0):
                        should_take_screenshot = True
                
                export_data.append(row_data)
                
                # 📸 GENERAR PANTALLAZO SI HAY ALERTA
                if should_take_screenshot:
                    try:
                        # Cambiar al perfil
                        self.current_profile_index = i
                        self.update_profile_display(export_mode=True)
                        QApplication.processEvents() # Permitir redibujado de UI
                        
                        # Generar nombre de archivo
                        safe_pk = str(pk).replace('.', '_')
                        filename = f"Perfil_PK_{safe_pk}"
                        if self.operation_mode == "revancha":
                            if row_data.get('Revancha') is not None and row_data['Revancha'] < 3.0:
                                filename += f"_Revancha_{row_data['Revancha']:.2f}"
                        
                        if width_val := (row_data.get('Ancho') or row_data.get('Ancho_Proyectado')):
                            if width_val < 15.0:
                                filename += f"_Ancho_{width_val:.2f}"
                                
                        filename += ".png"
                        full_screenshot_path = os.path.join(profiles_dir, filename)
                        
                        # Guardar la figura actual
                        self.figure.savefig(full_screenshot_path, dpi=100, bbox_inches='tight')
                        screenshots_taken += 1
                        
                    except Exception as e:
                        print(f"Error generando pantallazo para PK {pk}: {e}")
                
                # Actualizar progreso
                progress_percent = int((i / total_profiles) * 90)
                progress.setValue(progress_percent)
                QApplication.processEvents()
                
                if progress.wasCanceled():
                    break
            
            # Restaurar vista original
            if self.current_profile_index != original_profile_index:
                self.current_profile_index = original_profile_index
                self.update_profile_display()
            
            # Escribir CSV
            if not progress.wasCanceled():
                progress.setLabelText("Escribiendo archivo CSV...")
                progress.setValue(95)
                QApplication.processEvents()
                
                self.write_measurements_csv(file_path, export_data)
                
                progress.setValue(100)
                progress.close()
                
                # Calcular estadísticas para mostrar al usuario
                total_rows = len(export_data)
                
                msg = f"Mediciones exportadas correctamente a:\n{file_path}\n"
                
                if screenshots_taken > 0:
                    msg += f"\n📸 Se generaron {screenshots_taken} pantallazos de perfiles con alertas en:\n{profiles_dir}\n"
                
                msg += f"\n📊 Resumen:\n• Total de perfiles: {total_rows}\n"
                
                if self.operation_mode == "ancho_proyectado":
                    rows_with_ancho = sum(1 for row in export_data if row['Ancho_Proyectado'] is not None)
                    msg += f"• Con Ancho Proyectado: {rows_with_ancho}"
                else:
                    rows_with_revancha = sum(1 for row in export_data if row['Revancha'] is not None)
                    msg += f"• Con Revancha: {rows_with_revancha}"
                    
                QMessageBox.information(self, "✅ Exportación Exitosa", msg)
            else:
                progress.close()
            
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
            if self.operation_mode == "ancho_proyectado":
                # Columnas para Ancho Proyectado
                fieldnames = ['PK', 'Ancho_Proyectado']
            else:
                # Columnas para Revancha (original)
                fieldnames = ['PK', 'Cota_Coronamiento', 'Revancha', 'Lama', 'Ancho']
                
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            # Escribir cabecera
            writer.writeheader()
            
            # Escribir datos
            for row_data in export_data:
                # Formatear valores nulos como cadenas vacías
                formatted_row = {}
                for key in fieldnames:
                    value = row_data.get(key)
                    if value is None:
                        formatted_row[key] = ''
                    elif isinstance(value, float):
                        formatted_row[key] = f"{value:.3f}"  # 3 decimales
                    else:
                        formatted_row[key] = value
                
                writer.writerow(formatted_row)
                
    def show_orthomosaic(self):
        """Mostrar ortomosaico en una ventana separada en la ubicación exacta del perfil actual"""
        # Si ya hay un visualizador abierto, mostrarle y traerle al frente
        if self.ortho_viewer and hasattr(self.ortho_viewer, 'isVisible'):
            if self.ortho_viewer.isVisible():
                self.ortho_viewer.activateWindow()  # Trae la ventana al frente
                self.ortho_viewer.raise_()  # Asegura que esté por encima
                return
        
        if not self.ecw_file_path:
            QMessageBox.warning(
                self,
                "Ortomosaico no disponible",
                "No hay un archivo de ortomosaico cargado.\n\n" +
                "Para usar esta función, vuelva a la ventana principal y seleccione un archivo ECW."
            )
            return
            
        try:
            print(f"\n======= INICIANDO VISUALIZACIÓN DE ORTOMOSAICO =======")
            # Obtener el perfil actual
            profile = self.profiles_data[self.current_profile_index]
            current_pk = profile['pk']
            print(f"Perfil actual: PK {current_pk}")
            
            # Obtener coordenadas del centro del perfil
            if 'centerline_x' not in profile or 'centerline_y' not in profile:
                QMessageBox.warning(
                    self,
                    "Error de coordenadas",
                    f"No se encontraron coordenadas para el perfil {current_pk}."
                )
                return
                
            x_coord = profile['centerline_x']
            y_coord = profile['centerline_y']
            print(f"Coordenadas del perfil: X={x_coord:.2f}, Y={y_coord:.2f}")
            
            # Obtener el ángulo de dirección (bearing) para el cálculo de la perpendicular
            bearing = None
            
            # 🔧 MEJORADO: Obtener bearing_tangent para curvas si está disponible
            if 'station' in profile:
                station_data = profile['station']
                
                # Verificar si estamos en una curva y usar bearing_tangent si está disponible
                if 'alignment_type' in station_data and station_data['alignment_type'] == 'curved':
                    if 'bearing_tangent' in station_data:
                        bearing = station_data['bearing_tangent']
                        print(f"🔄 Usando bearing tangente para curva: {bearing:.2f}° [PK {current_pk}]")
                    else:
                        # Intentar calcular un bearing aproximado basado en puntos adyacentes
                        print(f"⚠️ No se encontró bearing_tangent para curva en PK {current_pk}")
                
                # Si no encontramos un bearing específico para curva, usar el bearing normal
                if bearing is None and 'bearing' in station_data:
                    bearing = station_data['bearing']
                    print(f"📏 Usando bearing normal del station: {bearing:.2f}°")
            
            # Si aún no tenemos bearing, intentar obtenerlo directamente del profile
            if bearing is None and 'bearing' in profile:
                bearing = profile['bearing']
                print(f"📏 Usando bearing del perfil: {bearing:.2f}°")
                
            # Log si no encontramos bearing
            if bearing is None:
                print("⚠️ ADVERTENCIA: No se encontró bearing en el perfil, se usará valor por defecto")
                    
            # Usar nuestra nueva clase de visualizador de ortomosaico
            from .orthomosaic_viewer import OrthomosaicViewer
            
            print(f"Creando visualizador con ECW: {self.ecw_file_path}")
            print(f"Parámetros: X={x_coord:.2f}, Y={y_coord:.2f}, PK={current_pk}, Bearing={bearing}")
            
            # 🆕 Crear la ventana del visualizador de forma NO MODAL
            self.ortho_viewer = OrthomosaicViewer(
                self.ecw_file_path, 
                x_coord, 
                y_coord, 
                current_pk,
                self,  # Parent es este visualizador de perfiles
                bearing
            )
            
            # Actualizar título para mostrar que es una ventana sincronizada
            self.ortho_viewer.setWindowTitle(f"Visualizador de Ortomosaico - Perfil {current_pk} [Sincronizado]")
            
            # 🆕 Conectar señal de cierre para limpiar referencia
            self.ortho_viewer.destroyed.connect(self.on_ortho_viewer_closed)
            
            # 🆕 Mostrar de forma no modal para permitir interacción con ambas ventanas
            self.ortho_viewer.show()
                
        except ImportError as ie:
            QMessageBox.critical(
                self,
                "Error - Módulo no encontrado",
                f"No se pudo cargar el visualizador de ortomosaico.\n\n"
                f"Asegúrese de que el archivo 'orthomosaic_viewer.py' esté en la carpeta del plugin.\n\n"
                f"Error técnico: {str(ie)}"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Error al mostrar el ortomosaico: {str(e)}"
            )
            
    def on_ortho_viewer_closed(self):
        """🆕 Limpia la referencia al visualizador cuando se cierra"""
        print("Visualizador de ortomosaico cerrado")
    
    # 🆕 PROJECT MANAGEMENT METHODS
    
    def get_all_measurements(self):
        """Get all measurements for project saving"""
        return {
            'saved_measurements': self.saved_measurements,
            'current_temp_crown': getattr(self, 'current_temp_crown', None),
            'current_temp_width': getattr(self, 'current_temp_width', None),
            'current_temp_lama': getattr(self, 'current_temp_lama', None),
            'lama_points_data': getattr(self, 'lama_points_data', {}),
            'current_pk': getattr(self, 'current_pk', None),
            'measurement_mode': getattr(self, 'measurement_mode', 'crown'),
            'operation_mode': getattr(self, 'operation_mode', 'measurement'),
            'auto_detection_enabled': getattr(self, 'auto_detection_enabled', False)
        }
    
    def restore_measurements(self, measurements_data):
        """Restore measurements from project data"""
        try:
            if not measurements_data:
                print("No measurements data to restore")
                return
            
            # Handle different measurement data formats
            if 'saved_measurements' in measurements_data:
                # New format: measurements in saved_measurements structure
                self.saved_measurements = measurements_data.get('saved_measurements', {})
                
                # Restore current temporary measurements
                self.current_temp_crown = measurements_data.get('current_temp_crown')
                self.current_temp_width = measurements_data.get('current_temp_width')
                self.current_temp_lama = measurements_data.get('current_temp_lama')
                
                # Restore LAMA points data
                if 'lama_points_data' in measurements_data:
                    self.lama_points_data = measurements_data['lama_points_data']
                
                # Restore UI state
                if 'measurement_mode' in measurements_data:
                    self.measurement_mode = measurements_data['measurement_mode']
                    self.set_measurement_mode(self.measurement_mode)
                
                if 'operation_mode' in measurements_data:
                    self.operation_mode = measurements_data['operation_mode']
                    self.update_ui_for_operation_mode()
                
                if 'auto_detection_enabled' in measurements_data:
                    self.auto_detection_enabled = measurements_data['auto_detection_enabled']
                    if hasattr(self, 'auto_detection_btn'):
                        self.auto_detection_btn.setChecked(self.auto_detection_enabled)
                
                # If we have a current PK, restore to that profile
                if 'current_pk' in measurements_data and measurements_data['current_pk']:
                    target_pk = measurements_data['current_pk']
                    # Find and set the correct profile
                    for i, profile in enumerate(self.profiles_data):
                        if profile.get('PK') == target_pk:
                            if hasattr(self, 'profile_combo'):
                                self.profile_combo.setCurrentIndex(i)
                            self.current_pk = target_pk
                            break
            else:
                # Legacy format: measurements directly as PK keys
                self.saved_measurements = {}
                first_pk_with_measurements = None
                
                # Convert direct PK format to saved_measurements format
                for pk, measurement_data in measurements_data.items():
                    if isinstance(measurement_data, dict) and ('crown' in measurement_data or 'width' in measurement_data):
                        self.saved_measurements[pk] = measurement_data
                        if first_pk_with_measurements is None:
                            first_pk_with_measurements = pk
                        
                        # Detailed debug info
                        crown_info = f"Crown: ({measurement_data['crown']['x']:.2f}, {measurement_data['crown']['y']:.2f})" if 'crown' in measurement_data else "No Crown"
                        width_info = f"Width: {measurement_data['width']['distance']:.2f}m" if 'width' in measurement_data else "No Width"
                        print(f"📏 Restored measurement for PK {pk}: {crown_info}, {width_info}")
                
                print(f"🗂️ Total measurements restored: {len(self.saved_measurements)}")
                print(f"📋 PKs with measurements: {list(self.saved_measurements.keys())}")
                
                # Set the first PK with measurements as current
                if first_pk_with_measurements and hasattr(self, 'profiles_data'):
                    for i, profile in enumerate(self.profiles_data):
                        profile_pk = profile.get('PK') or profile.get('pk')
                        if profile_pk == first_pk_with_measurements:
                            if hasattr(self, 'profile_combo'):
                                self.profile_combo.setCurrentIndex(i)
                                self.current_profile_index = i
                            self.current_pk = first_pk_with_measurements
                            print(f"🎯 Set initial PK to {first_pk_with_measurements} (index {i})")
                            break
                    else:
                        print(f"⚠️ Could not find profile for PK {first_pk_with_measurements} in profiles_data")
                        if hasattr(self, 'profiles_data') and self.profiles_data:
                            available_pks = [p.get('PK') or p.get('pk') for p in self.profiles_data]
                            print(f"📊 Available profile PKs: {available_pks}")
                else:
                    print(f"⚠️ No PKs with measurements found or no profiles_data available")
            
            # Refresh display
            self.update_profile_display()
            
            # Sync measurements to orthomosaic if it exists
            self.sync_measurements_to_orthomosaic()
            
            print(f"✅ Mediciones restauradas: {len(self.saved_measurements)} perfiles con datos")
            
        except Exception as e:
            print(f"❌ Error al restaurar mediciones: {str(e)}")
            import traceback
            traceback.print_exc()

    def parse_pk(self, pk_str):
        """Helper to convert PK string (e.g., '0+100') to float"""
        try:
            if '+' in pk_str:
                parts = pk_str.split('+')
                return float(parts[0]) * 1000 + float(parts[1])
            return float(pk_str)
        except:
            return 0.0

    def generate_longitudinal_chart(self, output_path):
        """Generate longitudinal profile chart (Crown & Lama) and save as image"""
        try:
            # 1. Extract and sort data
            data_points = []
            
            for pk, measurements in self.saved_measurements.items():
                # Crown
                crown_y = None
                if 'crown' in measurements:
                    crown_y = measurements['crown']['y']
                elif 'lama_selected' in measurements and self.operation_mode == "ancho_proyectado":
                    # In Ancho Mode, "Crown" concept might be the reference lama
                    # But user asked for trends. Let's stick to what we have.
                    pass
                
                # Lama
                lama_y = None
                if 'lama' in measurements:
                    lama_y = measurements['lama']['y']
                elif 'lama_selected' in measurements:
                     lama_y = measurements['lama_selected']['y']
                else: 
                     # Try to find auto lama from profile data
                     for p in self.profiles_data:
                         if str(p.get('pk')) == str(pk) or str(p.get('PK')) == str(pk):
                             if p.get('lama_points'):
                                 lama_y = p['lama_points'][0]['elevation']
                             break
                
                pk_float = self.parse_pk(str(pk))
                    
                data_points.append({
                    'pk_str': str(pk),
                    'pk_val': pk_float,
                    'crown': crown_y,
                    'lama': lama_y
                })
            
            # Sort by PK
            data_points.sort(key=lambda x: x['pk_val'])
            
            if not data_points:
                return False
                
            # 2. Prepare plot data
            # Filter for plotting lines (avoid gaps if desired, or keep them)
            # We want connected lines, so we filter valid points for each series INDEPENDENTLY
            
            valid_crowns = [(d['pk_val'], d['crown']) for d in data_points if d['crown'] is not None]
            valid_lamas = [(d['pk_val'], d['lama']) for d in data_points if d['lama'] is not None]

            # 3. Create Figure
            fig = Figure(figsize=(20, 8), dpi=100)
            ax = fig.add_subplot(111)
            
            # Plot Crown (Red)
            if valid_crowns:
                vx, vy = zip(*valid_crowns)
                ax.plot(vx, vy, 'o-', color='red', linewidth=2, markersize=6, label='Coronamiento')
                
            # Plot Lama (Green)
            if valid_lamas:
                vx, vy = zip(*valid_lamas)
                ax.plot(vx, vy, 'o-', color='green', linewidth=2, markersize=6, label='Lama')
                
            # Styling
            ax.set_title("Perfil Longitudinal (Tendencia)", fontsize=16, fontweight='bold', pad=20)
            ax.set_xlabel("PK (Progresiva)", fontsize=12)
            ax.set_ylabel("Elevación (m)", fontsize=12)
            ax.grid(True, which='both', linestyle='--', alpha=0.7)
            ax.minorticks_on()
            ax.grid(which='minor', linestyle=':', alpha=0.3)
            ax.legend(loc='best', fontsize=12)
            
            # X Ticks formatting
            # If standard PKs, just use auto. If special strings, might need custom
            # For now let matplotlib handle numeric X axis
            
            # Tight layout
            fig.tight_layout()
            
            # Save
            fig.savefig(output_path)
            return True
            
        except Exception as e:
            print(f"Error generating longitudinal chart: {e}")
            return False

    def generate_detail_html_table(self):
        """Generate HTML for Table 1: Detailed Measurements"""
        
        # CSS Style (Blue Header)
        style = """
        <style>
            table { border-collapse: collapse; width: 100%; font-family: Arial, sans-serif; font-size: 10px; }
            th { background-color: #2b579a; color: white; padding: 6px; border: 1px solid #ddd; text-align: left; }
            td { padding: 5px; border: 1px solid #ddd; text-align: left; }
            tr:nth-child(even) { background-color: #f8f9fa; }
            .alert { color: red; font-weight: bold; }
            .geomembrane-col { background-color: #f0f0f0; color: #555; } /* Placeholder visual cue? Optional */
        </style>
        """
        
        html = [style, "<table>"]
        
        # Headers
        headers = ["Sector", "PK", "Coronamiento", "Revancha", "Lama", "Ancho", "Geomembrana", "Dist. G-L", "Dist. G-C"]
        html.append("<thead><tr>")
        for h in headers:
            html.append(f"<th>{h}</th>")
        html.append("</tr></thead>")
        
        html.append("<tbody>")
        
        # Data Rows (Sorted by PK)
        # We assume self.profiles_data contains all PKs, we merge with saved measurements
        sorted_profiles = sorted(self.profiles_data, key=lambda x: self.parse_pk(str(x.get('pk', '0'))))
        
        for profile in sorted_profiles:
            pk = str(profile.get('pk', ''))
            measurements = self.saved_measurements.get(pk, {})
            
            # 1. Values
            crown_val = measurements.get('crown', {}).get('y')
            lama_val = measurements.get('lama', {}).get('y')
            # Auto lama fallback
            if lama_val is None and profile.get('lama_points'):
                lama_val = profile['lama_points'][0]['elevation']
                
            revancha_val = None
            if crown_val is not None and lama_val is not None:
                revancha_val = crown_val - lama_val
                
            width_val = measurements.get('width', {}).get('distance')
            
            # Geomembrane placeholders
            geomembrane_val = 0.00
            dist_gl_val = 0.00
            dist_gc_val = 0.00
            
            # 2. Formatting & Alerts
            sector_txt = "Sector 1" # Default
            pk_txt = pk
            
            coronamiento_txt = f"{crown_val:.3f}" if crown_val is not None else "-"
            
            revancha_cls = "alert" if (revancha_val is not None and revancha_val < 3.0) else ""
            revancha_txt = f"{revancha_val:.3f}" if revancha_val is not None else "-"
            if revancha_cls: revancha_txt = f"<span class='{revancha_cls}'>{revancha_txt}</span>"
            
            lama_txt = f"{lama_val:.3f}" if lama_val is not None else "-"
            
            ancho_cls = "alert" if (width_val is not None and width_val < 15.0) else ""
            ancho_txt = f"{width_val:.3f}" if width_val is not None else "-"
            if ancho_cls: ancho_txt = f"<span class='{ancho_cls}'>{ancho_txt}</span>"
            
            # Placeholders
            geo_txt = "0.000"
            dgl_txt = "0.000"
            dgc_txt = "0.000"
            
            # Row Construction
            html.append(f"<tr>")
            html.append(f"<td>{sector_txt}</td>")
            html.append(f"<td>{pk_txt}</td>")
            html.append(f"<td>{coronamiento_txt}</td>")
            html.append(f"<td>{revancha_txt}</td>")
            html.append(f"<td>{lama_txt}</td>")
            html.append(f"<td>{ancho_txt}</td>")
            html.append(f"<td>{geo_txt}</td>")
            html.append(f"<td>{dgl_txt}</td>")
            html.append(f"<td>{dgc_txt}</td>")
            html.append(f"</tr>")
            
        html.append("</tbody></table>")
        return "".join(html)

    def generate_summary_html_table(self):
        """Generate HTML for Table 2: Summary Measurements"""
        
        # Structure to hold aggregated data
        # Since we only have "Sector 1", we just calculate min/max for all data
        # If we had multiple sectors, we'd dict Key=Sector -> values
        
        # Find Min/Max
        min_rev, max_rev = (None, None), (None, None) # (Value, PK)
        min_ancho, max_ancho = (None, None), (None, None)
        min_crown, max_crown = (None, None), (None, None)
        
        for profile in self.profiles_data:
            pk = str(profile.get('pk', ''))
            measurements = self.saved_measurements.get(pk, {})
            
            # Revancha
            crown_val = measurements.get('crown', {}).get('y')
            lama_val = measurements.get('lama', {}).get('y')
            if lama_val is None and profile.get('lama_points'):
                lama_val = profile['lama_points'][0]['elevation']
            
            revancha_val = None
            if crown_val is not None and lama_val is not None:
                revancha_val = crown_val - lama_val
                
                # Check Min
                if min_rev[0] is None or revancha_val < min_rev[0]:
                    min_rev = (revancha_val, pk)
                # Check Max
                if max_rev[0] is None or revancha_val > max_rev[0]:
                    max_rev = (revancha_val, pk)
            
            # Ancho
            width_val = measurements.get('width', {}).get('distance')
            if width_val is not None:
                if min_ancho[0] is None or width_val < min_ancho[0]:
                    min_ancho = (width_val, pk)
                if max_ancho[0] is None or width_val > max_ancho[0]:
                    max_ancho = (width_val, pk)
                    
            # Crown
            if crown_val is not None:
                if min_crown[0] is None or crown_val < min_crown[0]:
                    min_crown = (crown_val, pk)
                if max_crown[0] is None or crown_val > max_crown[0]:
                    max_crown = (crown_val, pk)
                    
        # Construct HTML
        style = """
        <style>
            .summary-table { border-collapse: collapse; width: 100%; font-family: Arial, sans-serif; font-size: 10px; margin-top: 20px; }
            .summary-table th { background-color: #1a428a; color: white; padding: 8px; border: 1px solid #ddd; text-align: center; }
            .summary-table td { padding: 8px; border: 1px solid #ddd; text-align: center; }
            .summary-table tr:nth-child(even) { background-color: #f8f9fa; }
            .sub-header { background-color: #2b579a; font-size: 9px; }
            .sector-col { font-weight: bold; color: #2b579a; }
        </style>
        """
        
        html = [style, "<table class='summary-table'>"]
        
        # Main Headers
        html.append("<thead>")
        html.append("<tr>")
        html.append("<th rowspan='2' style='vertical-align: middle;'>SECTOR</th>")
        html.append("<th colspan='2'>REVANCHA</th>")
        html.append("<th colspan='2'>ANCHO</th>")
        html.append("<th colspan='2'>CORONAMIENTO</th>")
        html.append("</tr>")
        
        # Sub Headers
        html.append("<tr class='sub-header'>")
        for _ in range(3): # Repeated 3 times
            html.append("<th>MIN (PK)</th>")
            html.append("<th>MAX (PK)</th>")
        html.append("</tr>")
        html.append("</thead>")
        
        html.append("<tbody>")
        
        # Data Row (Sector 1)
        def fmt(val_tuple):
            val, pk = val_tuple
            if val is None: return "-"
            return f"{val:.3f} ({pk})"
            
        html.append("<tr>")
        html.append("<td class='sector-col'>Sector 1</td>")
        
        html.append(f"<td>{fmt(min_rev)}</td>")
        html.append(f"<td>{fmt(max_rev)}</td>")
        
        html.append(f"<td>{fmt(min_ancho)}</td>")
        html.append(f"<td>{fmt(max_ancho)}</td>")
        
        html.append(f"<td>{fmt(min_crown)}</td>")
        html.append(f"<td>{fmt(max_crown)}</td>")
        
        html.append("</tr>")
        html.append("</tbody></table>")
        
        return "".join(html)

    def export_pdf_report(self):
        """Generate PDF report using QPT Template and Dynamic Screenshots"""
        try:
            # 1. Validation: Check if Previous DEM is loaded
            has_previous_dem = False
            if self.profiles_data and len(self.profiles_data) > 0:
                # Check first profile for previous elevations
                if 'previous_elevations' in self.profiles_data[0] and self.profiles_data[0]['previous_elevations']:
                    has_previous_dem = True
            
            if not has_previous_dem:
                QMessageBox.warning(
                    self, 
                    "Requisito Faltante", 
                    "⚠️ Para generar el Reporte PDF, es OBLIGATORIO haber cargado un 'DEM Anterior'.\n\n"
                    "El reporte requiere comparar el terreno actual con el anterior.\n"
                    "Por favor, cargue un DEM de referencia en la pantalla principal y vuelva a generar los perfiles."
                )
                return

            # 2. Ask for output file
            filename, _ = QFileDialog.getSaveFileName(self, "Guardar Reporte PDF", "Reporte_Mediciones.pdf", "PDF Files (*.pdf)")
            if not filename:
                return

            # 3. Generate Assets (Chart & Tables)
            import tempfile
            temp_dir = tempfile.gettempdir()
            chart_path = os.path.join(temp_dir, "temp_profile_chart.png")
            
            if not self.generate_longitudinal_chart(chart_path):
                QMessageBox.warning(self, "Aviso", "No se pudo generar el gráfico longitudinal.")

            html_detail = self.generate_detail_html_table()
            html_summary = self.generate_summary_html_table()
            
            # 4. Load Template
            project = QgsProject.instance()
            layout = QgsPrintLayout(project)
            layout.initializeDefaults()
            
            # Find template path
            plugin_dir = os.path.dirname(__file__)
            template_path = os.path.join(plugin_dir, 'report_template.qpt')
            
            if not os.path.exists(template_path):
                # Create default if missing (fallback to simple code or error)
                QMessageBox.critical(self, "Error", f"No se encontró la plantilla: {template_path}")
                return
            
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
                doc = QDomDocument()
                doc.setContent(template_content)
                layout.loadFromTemplate(doc, QgsReadWriteContext())
            
            # 5. Inject Content into Template Items
            # Chart
            chart_item = layout.itemById('chart')
            if chart_item and isinstance(chart_item, QgsLayoutItemPicture):
                chart_item.setPicturePath(chart_path)
            
            # Summary Table (Fix: Handle Frames for HTML)
            summary_frame = layout.itemById('summary_table')
            if summary_frame and isinstance(summary_frame, QgsLayoutFrame):
                summary_mf = summary_frame.multiFrame()
                if isinstance(summary_mf, QgsLayoutItemHtml):
                    summary_mf.setHtml(html_summary)
                    summary_mf.loadHtml()
                
            # Detail Table (Fix: Handle Frames for HTML)
            detail_frame = layout.itemById('detail_table')
            if detail_frame and isinstance(detail_frame, QgsLayoutFrame):
                detail_mf = detail_frame.multiFrame()
                if isinstance(detail_mf, QgsLayoutItemHtml):
                    detail_mf.setHtml(html_detail)
                    detail_mf.loadHtml()

            # 6. Dynamic Screenshots (Pages 2+)
            # Detect Alerts
            alert_profiles = []
            for profile in self.profiles_data:
                pk = str(profile.get('pk', ''))
                measurements = self.saved_measurements.get(pk, {})
                
                # Check Revancha < 3
                crown_val = measurements.get('crown', {}).get('y')
                lama_val = measurements.get('lama', {}).get('y')
                # Auto lama fallback
                if lama_val is None and profile.get('lama_points'):
                    lama_val = profile['lama_points'][0]['elevation']
                
                revancha_alert = False
                if crown_val is not None and lama_val is not None:
                    if (crown_val - lama_val) < 3.0:
                        revancha_alert = True
                        
                # Check Width < 15
                width_val = measurements.get('width', {}).get('distance')
                width_alert = False
                if width_val is not None and width_val < 15.0:
                    width_alert = True
                    
                if revancha_alert or width_alert:
                    alert_profiles.append(pk)
            
            if alert_profiles:
                # Add new pages for screenshots
                # Grid settings
                rows = 2
                cols = 2
                per_page = rows * cols
                
                # Current Y position tracking for new pages
                # We need to extend the layout
                # layout.pageCollection().extend(num_pages) matches existing page size
                
                import math
                num_pages_needed = math.ceil(len(alert_profiles) / per_page)
                
                for i in range(num_pages_needed):
                    page = layout.pageCollection().extend(1)[0] # Add 1 page
                    
                    # Add Title for this page (FIX: Use QgsLayoutFrame + QgsLayoutItemHtml)
                    title_mf = QgsLayoutItemHtml(layout)
                    title_mf.setHtml(f"<h2 style='font-family: Arial; color: #d32f2f;'>Perfiles con Alertas (Página {i+1})</h2>")
                    layout.addMultiFrame(title_mf)
                    
                    title_frame = QgsLayoutFrame(layout, title_mf)
                    title_frame.attemptResize(QgsLayoutSize(280, 15, QgsUnitTypes.LayoutMillimeters))
                    
                    # Calculate position: Page Height * (Original Pages + i) + Margin
                    # Default A4 Height is 210mm. Template is page 0. Extent adds to end.
                    # We need absolute position.
                    # Note: 'page' object has pos().y() but it might be easier to calculate
                    page_y_offset = (i + 1) * 297 # A4 Height is 297mm (Portrait) or 210mm (Landscape)?
                    # Asssuming A4 Landscape (297x210) based on width usage?
                    # Wait, QGIS layout coordinates are continuous.
                    # The template page size dictates the interval.
                    # Let's assume standard A4 Landscape (297mm width, 210mm height).
                    page_height = layout.pageCollection().page(0).pageSize().height()
                    page_y_offset = (i + 1) * page_height
                    
                    title_frame.attemptMove(QgsLayoutPoint(10, page_y_offset + 10, QgsUnitTypes.LayoutMillimeters))
                    layout.addLayoutItem(title_frame)
                    
                    # Add Screenshots
                    start_idx = i * per_page
                    end_idx = min(start_idx + per_page, len(alert_profiles))
                    
                    page_profiles = alert_profiles[start_idx:end_idx]
                    
                    for idx, pk in enumerate(page_profiles):
                        # Generate Screenshot
                        # 1. Switch profile
                        self.current_pk = pk
                        # Find index
                        for p_idx, p in enumerate(self.profiles_data):
                            if str(p.get('pk')) == pk:
                                self.current_profile_index = p_idx
                                break
                        self.update_profile_display()
                        QApplication.processEvents() # Ensure redraw
                        
                        # 2. Save Image
                        screenshot_path = os.path.join(temp_dir, f"alert_{pk.replace('+','_')}.png")
                        self.figure.savefig(screenshot_path)
                        
                        # 3. Add to layout
                        # Grid logic
                        row = idx // cols
                        col = idx % cols
                        
                        w = 130 # mm
                        h = 80  # mm
                        x = 10 + (col * 140)
                        y = 30 + (row * 90) + page_y_offset
                        
                        pic = QgsLayoutItemPicture(layout)
                        pic.setPicturePath(screenshot_path)
                        pic.attemptResize(QgsLayoutSize(w, h, QgsUnitTypes.LayoutMillimeters))
                        pic.attemptMove(QgsLayoutPoint(x, y, QgsUnitTypes.LayoutMillimeters))
                        layout.addLayoutItem(pic)
                        
                        # Label (FIX: Use QgsLayoutFrame + QgsLayoutItemHtml)
                        lbl_mf = QgsLayoutItemHtml(layout)
                        lbl_mf.setHtml(f"<h3 style='font-family: Arial;'>PK: {pk}</h3>")
                        layout.addMultiFrame(lbl_mf)
                        
                        lbl_frame = QgsLayoutFrame(layout, lbl_mf)
                        lbl_frame.attemptResize(QgsLayoutSize(w, 10, QgsUnitTypes.LayoutMillimeters))
                        lbl_frame.attemptMove(QgsLayoutPoint(x, y - 10, QgsUnitTypes.LayoutMillimeters))
                        layout.addLayoutItem(lbl_frame)


            # 7. Export
            exporter = QgsLayoutExporter(layout)
            result = exporter.exportToPdf(filename, QgsLayoutExporter.PdfExportSettings())
            
            if result == QgsLayoutExporter.Success:
                QMessageBox.information(self, "Éxito", f"Reporte PDF generado correctamente en:\n{filename}")
                try:
                    os.startfile(filename)
                except:
                    pass
            else:
                QMessageBox.critical(self, "Error", "Fallo al exportar el PDF.")
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"Error generando reporte: {str(e)}")

    def generate_dev_map(self):
        """🆕 Método DEV para probar generación de mapas rápidamente"""
        from .core.map_generator import MapGenerator
        
        try:
            # 1. Validar requisitos
            if not self.ecw_file_path or not os.path.exists(self.ecw_file_path):
                QMessageBox.warning(self, "Falta Ortomosaico", "Debe cargar un Ortomosaico (ECW/TIF) primero.")
                return
                
            has_previous_dem = False
            prev_dem_path = None
            
            # Recuperar path del DEM anterior desde el diálogo principal
            main_dialog = self.parent()
            if hasattr(main_dialog, 'previous_dem_file_path') and main_dialog.previous_dem_file_path:
                prev_dem_path = main_dialog.previous_dem_file_path
                has_previous_dem = True
            
            if not has_previous_dem:
                QMessageBox.warning(self, "Falta DEM Anterior", "Debe cargar un DEM Anterior en la ventana principal.")
                return
                
            # Current DEM Path
            current_dem_path = None
            if hasattr(main_dialog, 'dem_file_path') and main_dialog.dem_file_path:
                current_dem_path = main_dialog.dem_file_path
                
            if not current_dem_path:
                QMessageBox.warning(self, "Falta DEM Actual", "No se detectó el path del DEM actual.")
                return
                
            # 2. Pedir destino
            output_path, _ = QFileDialog.getSaveFileName(
                self, "Guardar Mapa de Prueba", "Mapa_Contexto_Dev.png", "Images (*.png *.jpg)"
            )
            
            if not output_path:
                return
                
            # 3. Llamar al generador
            plugin_dir = os.path.dirname(__file__)
            generator = MapGenerator(plugin_dir)
            
            wall_name = "Muro 1" # Default fallback
            if hasattr(main_dialog, 'selected_wall'):
                wall_name = main_dialog.selected_wall
            
            QApplication.setOverrideCursor(Qt.WaitCursor)
            
            success = generator.generate_map_image(
                wall_name,
                self.ecw_file_path,
                current_dem_path,
                prev_dem_path,
                output_path
            )
            
            QApplication.restoreOverrideCursor()
            
            if success:
                QMessageBox.information(self, "Éxito", f"Mapa generado en:\n{output_path}")
                try:
                    os.startfile(output_path)
                except:
                    pass
            else:
                QMessageBox.critical(self, "Error", "Falló la generación del mapa. Ver log/consola.")
                
        except Exception as e:
            QApplication.restoreOverrideCursor()
            QMessageBox.critical(self, "Error Crítico", str(e))
            import traceback
            traceback.print_exc()
