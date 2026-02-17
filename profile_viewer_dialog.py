
import os
from qgis.PyQt.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                                 QLabel, QSlider, QGroupBox, QMessageBox,
                                 QFileDialog, QProgressDialog, QApplication, QSpinBox, QDoubleSpinBox, QShortcut)
from qgis.PyQt.QtCore import Qt, QTimer
from qgis.PyQt.QtXml import QDomDocument
from qgis.PyQt.QtGui import QFont, QKeySequence
from qgis.core import (QgsApplication, QgsProject, QgsRasterLayer, QgsPointXY, QgsRectangle,
                       QgsPrintLayout, QgsLayoutExporter, QgsLayoutItemHtml, QgsLayoutFrame,
                       QgsLayoutItemPicture, QgsLayoutSize, QgsUnitTypes, QgsLayoutPoint, QgsReadWriteContext,
                       QgsLayoutItemLabel)

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
    from matplotlib.offsetbox import AnchoredOffsetbox, TextArea, VPacker # 🆕 For multi-color legend
    
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
    
    def __init__(self, profiles_data, parent=None, ecw_file_path=None, excel_file_path=None, dem_path=None):
        super().__init__(parent)
        
        # Run diagnostic to help debug library issues
        diagnose_libraries()
        
        self.profiles_data = profiles_data
        self.current_profile_index = 0
        self.measurement_mode = None
        self.ecw_file_path = ecw_file_path  # Store ECW file path
        self.excel_file_path = excel_file_path  # 🆕 Store Excel template path
        self.dem_path = dem_path  # 🆕 Store DEM path for date extraction
        
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
        
        # 🆕 Navigation commands (S = Previous, D = Next)
        self.shortcut_prev = QShortcut(QKeySequence("S"), self)
        self.shortcut_next = QShortcut(QKeySequence("D"), self)
        
        self.shortcut_prev.activated.connect(lambda: self.prev_btn.click())
        self.shortcut_next.activated.connect(lambda: self.next_btn.click())
        
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
        btn_layout3.addWidget(self.export_pdf_btn)
        
        # 🆕 MAP SETTINGS (Min/Max overrides)
        map_settings_layout = QHBoxLayout()
        map_settings_layout.addWidget(QLabel("Mapa Min:"))
        self.map_min_spin = QDoubleSpinBox()
        self.map_min_spin.setRange(0.01, 10.0)
        self.map_min_spin.setSingleStep(0.05)
        self.map_min_spin.setValue(0.05)
        self.map_min_spin.setDecimals(2)
        self.map_min_spin.setToolTip("Valor mínimo para la escala de colores del mapa (Default: 0.05m)")
        map_settings_layout.addWidget(self.map_min_spin)
        
        map_settings_layout.addWidget(QLabel("Max:"))
        self.map_max_spin = QDoubleSpinBox()
        self.map_max_spin.setRange(0.0, 100.0)
        self.map_max_spin.setSingleStep(0.1)
        self.map_max_spin.setValue(0.0) # 0 = Auto
        self.map_max_spin.setDecimals(2)
        self.map_max_spin.setSpecialValueText("Auto")
        self.map_max_spin.setToolTip("Valor máximo para la escala de colores (0 = Auto)")
        map_settings_layout.addWidget(self.map_max_spin)
        
        # Add settings layout next to PDF button
        btn_layout3.addLayout(map_settings_layout)
        
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
        
        # 🆕 SMART ZOOM PARA PANTALLAZOS DE ALERTAS
        if export_mode:
            try:
                # Recopilar puntos de interés (X coordinates)
                interest_xs = []
                
                # 1. Puntos de LAMA
                if current_pk in self.saved_measurements:
                    if 'lama' in self.saved_measurements[current_pk]:
                        interest_xs.append(self.saved_measurements[current_pk]['lama']['x'])
                    elif 'lama_selected' in self.saved_measurements[current_pk]:
                        interest_xs.append(self.saved_measurements[current_pk]['lama_selected']['x'])
                
                # Fallback a LAMA automático si no hay manual
                if not interest_xs and profile.get('lama_points'):
                    interest_xs.append(profile['lama_points'][0]['offset_from_centerline'])
                
                # 2. Puntos de Coronamiento
                if current_pk in self.saved_measurements and 'crown' in self.saved_measurements[current_pk]:
                    interest_xs.append(self.saved_measurements[current_pk]['crown']['x'])
                elif self.current_crown_point:
                    interest_xs.append(self.current_crown_point[0])
                    
                # 3. Puntos de Ancho (Extremos)
                if current_pk in self.saved_measurements and 'width' in self.saved_measurements[current_pk]:
                    p1 = self.saved_measurements[current_pk]['width']['p1']
                    p2 = self.saved_measurements[current_pk]['width']['p2']
                    interest_xs.append(p1[0]) # p1 x
                    interest_xs.append(p2[0]) # p2 x
                    
                # Calcular nuevo rango si tenemos puntos de interés
                if interest_xs:
                    # Margen de 5 metros a cada lado
                    padding = 5.0
                    smart_min = min(interest_xs) - padding
                    smart_max = max(interest_xs) + padding
                    
                    # Asegurar un ancho mínimo de visualización (ej. 15m) para contexto
                    current_span = smart_max - smart_min
                    min_span = 15.0
                    if current_span < min_span:
                        diff = (min_span - current_span) / 2
                        smart_min -= diff
                        smart_max += diff
                    
                    # Aplicar límites (respetando los límites máximos del muro)
                    # No restringimos con x_min_wall/x_max_wall estrictamente por si el feature está fuera,
                    # pero es bueno no mostrar infinito. Usaremos los calculados.
                    x_min = smart_min
                    x_max = smart_max
                    print(f"🔎 Smart Zoom aplicado: {x_min:.2f}m a {x_max:.2f}m (Export Mode)")
                    
            except Exception as e:
                print(f"⚠️ Error calculando Smart Zoom: {e}. Usando rango por defecto.")
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
        
        # 🆕 Plot Previous Terrain (Background) - SOLO en modo interactivo
        if not export_mode:
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
        
        # 📍 Mark centerline - SOLO en modo interactivo
        if not export_mode:
            self.ax.axvline(x=0, color='red', linestyle='--', linewidth=1.8, alpha=0.8, 
                        label='Eje de Alineación')
        
        # 🆕 REFERENCE LINES - Different logic based on operation mode - SOLO en modo interactivo
        if not export_mode:
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
                    
                    # En export_mode, NO dibujar los puntos extremos, solo la línea
                    if not export_mode:
                        self.ax.plot([p1[0], p2[0]], [p1[1], p2[1]], 'o', color=color, markersize=marker_size, zorder=4)
                    self.ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color=color, linestyle=line_style, 
                            linewidth=2.5, alpha=0.9, label=f'Ancho {label_prefix}: {width_data["distance"]:.2f}m', zorder=4)
            else:
                # Modo Revancha (lógica original)
                # En export_mode, NO dibujar punto de coronamiento (rojo)
                if 'crown' in measurements and not export_mode:
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
                    
                    # En export_mode, NO dibujar los puntos extremos, solo la línea
                    if not export_mode:
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
        # EN EXPORT_MODE: Mostrar si no hay manual override
        if self.operation_mode == "revancha":
            if current_pk not in self.saved_measurements or 'lama' not in self.saved_measurements[current_pk]:
                lama_points = profile.get('lama_points', [])
                if lama_points:
                    for lama_point in lama_points:
                        # Dibujar siempre (incluso en export_mode)
                        self.ax.plot(lama_point['offset_from_centerline'], lama_point['elevation'], 
                                    'o', color='orange', markersize=12, markeredgecolor='red',
                                    markeredgewidth=2, label=f'LAMA Auto: {lama_point["elevation"]:.2f}m', zorder=4)
        
        # 🎯 Show current temporary measurements - NO en export_mode
        if not export_mode:
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
            # 📸 LEYENDA SIMPLIFICADA PARA PANTALLAZOS DE ALERTAS
            legend_lines = []
            
            # 1. Cota Coronamiento (línea verde)
            crown_val = None
            if current_pk in self.saved_measurements and 'crown' in self.saved_measurements[current_pk]:
                crown_val = self.saved_measurements[current_pk]['crown']['y']
                legend_lines.append(f"─ Cota Coronamiento: {crown_val:.2f} m")
            
            # 2. Cota Lama (punto naranja)
            lama_val = None
            if current_pk in self.saved_measurements:
                # Buscar lama en diferentes formatos según modo
                if 'lama' in self.saved_measurements[current_pk]:
                    lama_val = self.saved_measurements[current_pk]['lama']['y']
                elif 'lama_selected' in self.saved_measurements[current_pk]:
                    lama_val = self.saved_measurements[current_pk]['lama_selected']['y']
            
            # Fallback a lama automática
            if lama_val is None and 'lama_points' in profile and profile['lama_points']:
                lama_val = profile['lama_points'][0]['elevation']
            
            if lama_val is not None:
                legend_lines.append(f"● Cota Lama: {lama_val:.2f} m")
            
            # 3. Revancha (sin símbolo)
            if crown_val is not None and lama_val is not None:
                revancha_val = crown_val - lama_val
                legend_lines.append(f"  Revancha: {revancha_val:.2f} m")
            
            # 4. Ancho (línea verde)
            width_val = None
            if current_pk in self.saved_measurements and 'width' in self.saved_measurements[current_pk]:
                width_val = self.saved_measurements[current_pk]['width']['distance']
                legend_lines.append(f"─ Ancho: {width_val:.2f} m")
            
            # 🆕 CONSTRUIR LEYENDA MULTICOLOR (VPacker)
            try:
                pack_items = []
                
                # Header - REMOVED AS REQUESTED
                # pack_items.append(TextArea(f"Perfil: {current_pk}", textprops=dict(color='black', weight='bold', size=11, family='monospace')))
                
                # Cota Coronamiento
                if crown_val is not None:
                     pack_items.append(TextArea(f"─ Cota Coronamiento: {crown_val:.2f} m", textprops=dict(color='black', size=11, family='monospace')))

                # Cota Lama
                if lama_val is not None:
                    pack_items.append(TextArea(f"● Cota Lama: {lama_val:.2f} m", textprops=dict(color='black', size=11, family='monospace')))
                
                # Revancha (ROJO si < 3.0)
                if revancha_val is not None:
                    color = 'red' if revancha_val < 3.0 else 'black'
                    pack_items.append(TextArea(f"  Revancha: {revancha_val:.2f} m", textprops=dict(color=color, size=11, family='monospace')))
                
                # Ancho (ROJO si < 15.0)
                if width_val is not None:
                    color = 'red' if width_val < 15.0 else 'black'
                    pack_items.append(TextArea(f"─ Ancho: {width_val:.2f} m", textprops=dict(color=color, size=11, family='monospace')))
                
                # Empaquetar verticalmente alineado a la derecha
                vbox = VPacker(children=pack_items, align="right", pad=0, sep=4)
                
                # 🆕 Determinar posición según el muro seleccionado
                # Default: Muro Principal (Top-Right)
                # MO (Muro Oeste/2): Bottom-Right
                loc_param = 'upper right'
                bbox_param = (0.98, 0.98)
                valign_param = 'top'
                
                try:
                    # Intentar obtener nombre del muro desde el padre
                    wall_name = "Muro Principal" 
                    if self.parent() and hasattr(self.parent(), 'selected_wall') and self.parent().selected_wall:
                        wall_name = self.parent().selected_wall
                    
                    wall_lower = wall_name.lower()
                    if "oeste" in wall_lower or "mo" in wall_lower or "muro 2" in wall_lower:
                        # Muro Oeste -> Abajo Derecha
                        loc_param = 'lower right'
                        bbox_param = (0.98, 0.02)
                        valign_param = 'bottom'
                except:
                    pass

                # Crear caja anclada
                anchored_box = AnchoredOffsetbox(loc=loc_param, 
                                               child=vbox, 
                                               pad=0.5, 
                                               frameon=True, 
                                               bbox_to_anchor=bbox_param,
                                               bbox_transform=self.ax.transAxes, 
                                               borderpad=0.5)
                
                # Estilo del cuadro (igual al anterior)
                anchored_box.patch.set_boxstyle("round,pad=0.5,rounding_size=0.2")
                anchored_box.patch.set_facecolor("white")
                anchored_box.patch.set_alpha(0.9)
                anchored_box.patch.set_edgecolor("black")
                anchored_box.patch.set_linewidth(1.5)
                
                self.ax.add_artist(anchored_box)
                
            except Exception as e:
                print(f"⚠️ Error generando leyenda multicolor: {e}. Usando texto simple.")
                # Fallback a texto simple si falla VPacker
                if legend_lines:
                    legend_text = "\n".join(legend_lines)
                    self.ax.text(0.98, bbox_param[1], legend_text, # Use matching Y coord
                               transform=self.ax.transAxes,
                               fontsize=11,
                               verticalalignment=valign_param, # Use matching alignment
                               horizontalalignment='right',
                               bbox=dict(boxstyle='round', facecolor='white', alpha=0.9, edgecolor='black', linewidth=1.5),
                               family='monospace',
                               weight='bold')
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
            # 🎯 NOMBRE DINÁMICO SEGÚN MODO
            mode_name = "ancho_proyectado" if self.operation_mode == "ancho_proyectado" else "revanchas"
            default_filename = f"mediciones_{mode_name}.csv"
            
            is_excel_export = False
            file_path = None
            
            # 🆕 LOGIC: Check if Excel template is provided
            if self.excel_file_path and os.path.exists(self.excel_file_path):
                is_excel_export = True
                template_path = self.excel_file_path
                
                # Prompt for Save As, defaulting to template name
                default_save_name = os.path.basename(template_path)
                file_path, _ = QFileDialog.getSaveFileName(
                    self,
                    f"Guardar Excel como...", 
                    default_save_name,
                    "Excel Files (*.xlsx);;All files (*.*)"
                )
                
                if not file_path:
                    return # User cancelled
                    
                print(f"📊 Exportando a Excel: {file_path} (Template: {template_path})")
            else:
                # Standard CSV Export
                file_path, _ = QFileDialog.getSaveFileName(
                    self,
                    f"Exportar Mediciones", 
                    default_filename,
                    "CSV files (*.csv);;All files (*.*)"
                )
            
            if not file_path:
                return  # Usuario canceló
            
            # Mostrar progreso
            progress = QProgressDialog("Recopilando mediciones...", "Cancelar", 0, 100, self)
            progress.setWindowModality(Qt.WindowModal)
            progress.show()
            
            QApplication.processEvents()
            
            # Recopilar datos de todos los perfiles
            export_data = []
            total_profiles = len(self.profiles_data)
            
            progress.setLabelText("Procesando mediciones...")
            progress.setValue(0)
            QApplication.processEvents()
            
            for i, profile in enumerate(self.profiles_data):
                pk = profile['pk']
                
                # Obtener mediciones guardadas
                measurements = self.saved_measurements.get(pk, {})
                
                if self.operation_mode == "ancho_proyectado":
                    # Modo Ancho Proyectado: Solo PK y Ancho
                    width_val = measurements.get('width', {}).get('distance', None)
                    row_data = {
                        'PK': pk,
                        'Ancho_Proyectado': width_val
                    }
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
                
                export_data.append(row_data)
                
                # Actualizar progreso
                progress_percent = int((i / total_profiles) * 90)
                progress.setValue(progress_percent)
                QApplication.processEvents()
                
                if progress.wasCanceled():
                    break
            
            # Escribir CSV o Actualizar Excel
            if not progress.wasCanceled():
                progress.setLabelText("Guardando datos...")
                progress.setValue(95)
                QApplication.processEvents()
                
                if is_excel_export:
                    # 🆕 UPDATE EXCEL LOGIC
                    try:
                        from .core.excel_updater import ExcelUpdater
                        # Pass source template and destination path
                        updater = ExcelUpdater(file_path, template_path=template_path)
                        
                        # Detect wall name lookup
                        wall_name = "Muro Principal" # Default fallback
                        if self.parent() and hasattr(self.parent(), 'selected_wall') and self.parent().selected_wall:
                            wall_name = self.parent().selected_wall
                        
                        # Get DEM filename
                        dem_filename = os.path.basename(self.dem_path) if self.dem_path else "Unknown_DEM"
                        
                        # Update
                        success, msg = updater.update_wall_data(wall_name, export_data, dem_filename)
                        
                        progress.close()
                        
                        if success:
                             QMessageBox.information(self, "✅ Exportación Excel Exitosa", msg)
                        else:
                            QMessageBox.critical(self, "❌ Error Excel", f"Error actualizando Excel:\n{msg}")
                            
                    except Exception as e:
                        progress.close()
                        import traceback
                        traceback.print_exc()
                        QMessageBox.critical(self, "❌ Error Crítico", f"Error en módulo ExcelUpdater:\n{str(e)}")
                
                else:
                    # STANDARD CSV LOGIC
                    progress.setLabelText("Escribiendo archivo CSV...")
                    self.write_measurements_csv(file_path, export_data)
                    
                    progress.setValue(100)
                    progress.close()
                    
                    # Calcular estadísticas para mostrar al usuario
                    total_rows = len(export_data)
                    
                    msg = f"Mediciones exportadas correctamente a:\n{file_path}\n"
                    
                    msg += f"\n📊 Resumen:\n• Total de perfiles: {total_rows}\n"
                    
                    if self.operation_mode == "ancho_proyectado":
                        rows_with_ancho = sum(1 for row in export_data if row['Ancho_Proyectado'] is not None)
                        msg += f"• Con Ancho Proyectado: {rows_with_ancho}"
                    else:
                        rows_with_revancha = sum(1 for row in export_data if row['Revancha'] is not None)
                        msg += f"• Con Revancha: {rows_with_revancha}"
                        
                    QMessageBox.information(self, "✅ Exportación Exitosa", msg)
            

            
        except Exception as e:
            if 'progress' in locals():
                progress.close()
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

    def generate_detail_html_table(self, geo_manager=None, frame_height_mm=220):
        """
        Generate HTML for Table 1: Detailed Measurements (Single Column - Compact)
        
        Args:
            geo_manager: GeomembraneManager instance
            frame_height_mm: Altura del frame en mm (para cálculo de fill dinámico)
        """
        
        # 1. Prepare Data & Sorting
        sorted_profiles = sorted(self.profiles_data, key=lambda x: self.parse_pk(str(x.get('pk', '0'))))
        total_rows = len(sorted_profiles)
        
        # 🔍 DIAGNOSTICS: Show row count per wall
        wall_name = self.profiles_data[self.current_profile_index].get('wall_name', "Muro 1") if self.profiles_data else "Desconocido"
        print(f"\n📊 DIAGNÓSTICO TABLA DETAIL:")
        print(f"   Muro: {wall_name}")
        print(f"   Total Filas: {total_rows}")
        print(f"   Frame Height: {frame_height_mm}mm")
        
        # 2. NUEVO: Cálculo Dinámico para LLENAR el Frame exactamente
        # Convertir mm a px (aprox 3.78 px/mm en QGIS rendering)
        px_per_mm = 3.78
        frame_height_px = frame_height_mm * px_per_mm  # ej: 220mm = 831px
        
        # Reservar espacio para header (2 filas de encabezado)
        header_height_px = 30  # Aprox 2 filas de header con borders
        
        # Espacio disponible para las filas de datos
        available_height_px = frame_height_px - header_height_px
        
        # Calcular altura POR FILA para llenar exactamente el espacio
        row_height_px = available_height_px / total_rows
        
        # Determinar font-size base según cantidad de filas (legibilidad)
        if total_rows > 80:
            base_font_px = 6    # Mínimo para legibilidad
        elif total_rows > 60:
            base_font_px = 7
        elif total_rows > 40:
            base_font_px = 8
        elif total_rows > 25:
            base_font_px = 9
        else:
            base_font_px = 10
        
        # Calcular padding para llenar la altura de fila
        # row_height = font_size * line_height + (padding_top + padding_bottom) + border
        line_height = 1.2
        border_height = 2  # 1px arriba + 1px abajo
        content_height = base_font_px * line_height
        remaining_space = row_height_px - content_height - border_height
        padding_vertical_px = max(0, remaining_space / 2)  # Top + bottom
        
        # Convertir a valores CSS
        font_size = f"{base_font_px}px"
        padding_vertical = f"{padding_vertical_px:.1f}px"
        padding_horizontal = "2px"  # Fijo para no hacer muy ancho
        
        print(f"   🎨 Cálculo Fill Dinámico:")
        print(f"      • Altura Frame: {frame_height_mm}mm ({frame_height_px:.0f}px)")
        print(f"      • Espacio p/filas: {available_height_px:.0f}px")
        print(f"      • Altura por fila: {row_height_px:.1f}px")
        print(f"      • Font: {font_size}, Padding V: {padding_vertical}, Line-H: {line_height}")
        
        font_size_final = font_size
        padding_final = f"{padding_vertical} {padding_horizontal}"
        line_height_final = str(line_height)
             
        # 3. CSS Styles con Fill Dinámico + Colores por Rangos
        style = f"""
        <style>
            table {{ 
                border-collapse: collapse; 
                width: 100%; 
                height: 100%;
                font-family: Arial, sans-serif; 
                font-size: {font_size_final}; 
                line-height: {line_height_final};
            }}
            th {{ 
                background-color: #EF7F1A; 
                color: white; 
                padding: 3px {padding_horizontal}; 
                border: 1px solid #ddd; 
                text-align: center; 
                font-weight: bold; 
                white-space: nowrap; 
            }}
            td {{ 
                padding: {padding_final}; 
                border: 1px solid #ddd; 
                text-align: left; 
                white-space: nowrap; 
                line-height: {line_height_final};
                height: {row_height_px:.1f}px;
            }}
            tr {{ page-break-inside: auto; }}
            tbody tr:nth-child(even) {{ background-color: #f8f9fa; }}
            .geo-col {{ background-color: #f9f9f9; }}
            /* Colores por Rango - Revancha */
            .rev-green {{ color: #2e7d32; font-weight: bold; }}
            .rev-yellow {{ color: #f57f17; font-weight: bold; }}
            .rev-red {{ color: #c62828; font-weight: bold; }}
            /* Colores por Rango - Ancho */
            .ancho-green {{ color: #2e7d32; font-weight: bold; }}
            .ancho-yellow {{ color: #f57f17; font-weight: bold; }}
            .ancho-red {{ color: #c62828; font-weight: bold; }}
            /* Colores por Rango - Geomembrana */
            .geo-yellow {{ color: #f57f17; font-weight: bold; }}
            .geo-red {{ color: #c62828; font-weight: bold; }}
        </style>
        """
        
        html = [style, "<table>"]
        
        # Headers (Reverted to Full Names)
        headers = ["Sector", "PK", "Coronam.", "Revancha", "Lama", "Ancho", "Geomemb.", "D. G-L", "D. G-C"]
        html.append("<thead><tr>")
        for h in headers:
            html.append(f"<th>{h}</th>")
        html.append("</tr></thead>")
        
        html.append("<tbody>")
        
        # Import utilities
        from .core.sector_utils import get_sector_for_profile
        # Ensure wall_name for sector logic
        wall_name = self.profiles_data[self.current_profile_index].get('wall_name', "Muro 1")
        
        for profile in sorted_profiles:
            pk = str(profile.get('pk', ''))
            measurements = self.saved_measurements.get(pk, {})
            profile['wall_name'] = wall_name 
            
            # --- DATA EXTRACTION & FORMATTING ---
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
            
            # Geomembrane Logic
            geomembrane_val = None
            if geo_manager:
                geomembrane_val = geo_manager.get_elevation(wall_name, pk)
            
            # Formatting
            sector_txt = get_sector_for_profile(profile)
            pk_txt = pk
            
            coronamiento_txt = f"{crown_val:.3f}" if crown_val is not None else "-"
            
            # Revancha con colores por rango
            revancha_txt = "-"
            if revancha_val is not None:
                if revancha_val > 3.5:
                    revancha_txt = f"<span class='rev-green'>{revancha_val:.3f}</span>"
                elif revancha_val >= 3.0:
                    revancha_txt = f"<span class='rev-yellow'>{revancha_val:.3f}</span>"
                else:
                    revancha_txt = f"<span class='rev-red'>{revancha_val:.3f}</span>"
            
            lama_txt = f"{lama_val:.3f}" if lama_val is not None else "-"
            
            # Ancho con colores por rango
            ancho_txt = "-"
            if width_val is not None:
                if width_val > 18.0:
                    ancho_txt = f"<span class='ancho-green'>{width_val:.3f}</span>"
                elif width_val >= 15.0:
                    ancho_txt = f"<span class='ancho-yellow'>{width_val:.3f}</span>"
                else:
                    ancho_txt = f"<span class='ancho-red'>{width_val:.3f}</span>"
            
            # Geo columns con colores por rango
            geo_txt = "-"
            dgl_txt = "-"
            dgc_txt = "-"
            
            if geomembrane_val is not None:
                geo_txt = f"{geomembrane_val:.3f}"  # Sin color, valor de referencia
                
                # D. G-L (Geomembrana - Lama) con colores
                if lama_val is not None:
                    dgl_val = geomembrane_val - lama_val
                    if dgl_val > 1.0:
                        dgl_txt = f"{dgl_val:.3f}"  # Normal (negro)
                    elif dgl_val >= 0.5:
                        dgl_txt = f"<span class='geo-yellow'>{dgl_val:.3f}</span>"
                    else:
                        dgl_txt = f"<span class='geo-red'>{dgl_val:.3f}</span>"
                
                # D. G-C (Coronamiento - Geomembrana) con colores
                if crown_val is not None:
                    dgc_val = crown_val - geomembrane_val
                    if dgc_val > 1.0:
                        dgc_txt = f"{dgc_val:.3f}"  # Normal (negro)
                    elif dgc_val >= 0.5:
                        dgc_txt = f"<span class='geo-yellow'>{dgc_val:.3f}</span>"
                    else:
                        dgc_txt = f"<span class='geo-red'>{dgc_val:.3f}</span>"

            # Add Row
            html.append(f"<tr>")
            html.append(f"<td>{sector_txt}</td>")
            html.append(f"<td>{pk_txt}</td>")
            html.append(f"<td>{coronamiento_txt}</td>")
            html.append(f"<td>{revancha_txt}</td>")
            html.append(f"<td>{lama_txt}</td>")
            html.append(f"<td>{ancho_txt}</td>")
            html.append(f"<td class='geo-col'>{geo_txt}</td>")
            html.append(f"<td class='geo-col'>{dgl_txt}</td>")
            html.append(f"<td class='geo-col'>{dgc_txt}</td>")
            html.append(f"</tr>")
            
        html.append("</tbody></table>")
        return "".join(html)

    def diagnose_table_sizing(self):
        """
        🔍 HERRAMIENTA DE DIAGNÓSTICO: Analiza cuántas filas tiene cada muro
        y recomienda ajustes de tamaño para el layout QPT.
        
        Llámalo desde la consola Python de QGIS:
        >>> dialog.profile_viewer_dialog.diagnose_table_sizing()
        """
        if not self.profiles_data:
            print("⚠️ No hay datos de perfiles cargados para diagnosticar")
            return
        
        wall_name = self.profiles_data[self.current_profile_index].get('wall_name', "Desconocido")
        total_rows = len(self.profiles_data)
        
        # Calcular configuración sugerida
        if total_rows > 80:
            config = {"font": "4.5px", "padding": "0.5px", "line_height": "1.1", "frame_height": "220mm"}
        elif total_rows > 60:
            config = {"font": "5px", "padding": "1px", "line_height": "1.15", "frame_height": "210mm"}
        elif total_rows > 40:
            config = {"font": "6px", "padding": "2px", "line_height": "1.2", "frame_height": "190mm"}
        elif total_rows > 25:
            config = {"font": "6.5px", "padding": "2.5px", "line_height": "1.25", "frame_height": "170mm"}
        else:
            config = {"font": "7px", "padding": "3px", "line_height": "1.3", "frame_height": "150mm"}
        
        # Altura estimada por fila (aprox)
        row_height_mm = {
            "4.5px": 2.5,
            "5px": 2.8,
            "6px": 3.2,
            "6.5px": 3.5,
            "7px": 4.0
        }.get(config["font"], 3.5)
        
        estimated_height = total_rows * row_height_mm
        
        print("\n" + "="*70)
        print("🔍 DIAGNÓSTICO DE TABLA DETAIL - AJUSTE DE LAYOUT")
        print("="*70)
        print(f"📁 Muro: {wall_name}")
        print(f"📊 Total de Filas (Perfiles): {total_rows}")
        print(f"\n🎨 CONFIGURACIÓN CSS AUTOMÁTICA:")
        print(f"   • Font Size:    {config['font']}")
        print(f"   • Padding:      {config['padding']}")
        print(f"   • Line Height:  {config['line_height']}")
        print(f"\n📐 AJUSTE RECOMENDADO EN LAYOUT QPT:")
        print(f"   • Altura Estimada de Tabla: ~{estimated_height:.1f} mm")
        print(f"   • Frame 'detail_table' - Alto Sugerido: {config['frame_height']}")
        print(f"\n🛠️ PASOS PARA AJUSTAR EN QGIS:")
        print(f"   1. Abrir 'report_template.qpt' en el Layout Manager")
        print(f"   2. Seleccionar el Frame 'detail_table'")
        print(f"   3. En 'Propiedades del Elemento' → Posición y Tamaño")
        print(f"   4. Ajustar Alto (Height) a: {config['frame_height']}")
        print(f"   5. Si sigue desbordando, aumentar +10mm y probar de nuevo")
        print("="*70 + "\n")
        
        return {
            "wall_name": wall_name,
            "total_rows": total_rows,
            "config": config,
            "estimated_height_mm": estimated_height
        }

    def generate_summary_html_table(self, geo_manager=None):
        """Generate HTML for Table 2: Summary Measurements"""
        from .core.sector_utils import get_sector_for_profile
        
        # Structure to hold aggregated data per sector
        sectors_data = {}
        
        wall_name = self.profiles_data[self.current_profile_index].get('wall_name', "Muro 1")
        
        for profile in self.profiles_data:
            profile['wall_name'] = wall_name 
            pk = str(profile.get('pk', ''))
            measurements = self.saved_measurements.get(pk, {})
            
            # Determine Sector
            sector_name = get_sector_for_profile(profile)
            
            if sector_name not in sectors_data:
                sectors_data[sector_name] = {
                    'min_rev': [None, None], 'max_rev': [None, None],
                    'min_ancho': [None, None], 'max_ancho': [None, None],
                    'min_crown': [None, None], 'max_crown': [None, None]
                }
            
            stats = sectors_data[sector_name]
            
            # Revancha
            crown_val = measurements.get('crown', {}).get('y')
            lama_val = measurements.get('lama', {}).get('y')
            if lama_val is None and profile.get('lama_points'):
                lama_val = profile['lama_points'][0]['elevation']
            
            revancha_val = None
            if crown_val is not None and lama_val is not None:
                revancha_val = crown_val - lama_val
                
                # Check Min
                if stats['min_rev'][0] is None or revancha_val < stats['min_rev'][0]:
                    stats['min_rev'] = [revancha_val, pk]
                # Check Max
                if stats['max_rev'][0] is None or revancha_val > stats['max_rev'][0]:
                    stats['max_rev'] = [revancha_val, pk]
            
            # Ancho
            width_val = measurements.get('width', {}).get('distance')
            if width_val is not None:
                if stats['min_ancho'][0] is None or width_val < stats['min_ancho'][0]:
                    stats['min_ancho'] = [width_val, pk]
                if stats['max_ancho'][0] is None or width_val > stats['max_ancho'][0]:
                    stats['max_ancho'] = [width_val, pk]
                    
            # Crown
            if crown_val is not None:
                if stats['min_crown'][0] is None or crown_val < stats['min_crown'][0]:
                    stats['min_crown'] = [crown_val, pk]
                if stats['max_crown'][0] is None or crown_val > stats['max_crown'][0]:
                    stats['max_crown'] = [crown_val, pk]
                    
        # Construct HTML con colores por rango
        style = """
        <style>
            .summary-table { border-collapse: collapse; width: 100%; font-family: Arial, sans-serif; font-size: 7px; margin-top: 10px; }
            .summary-table th { background-color: #EF7F1A; color: white; padding: 3px; border: 1px solid #ddd; text-align: center; font-weight: bold; }
            .summary-table td { padding: 3px; border: 1px solid #ddd; text-align: center; }
            .summary-table tr:nth-child(even) { background-color: #f8f9fa; }
            .sub-header { background-color: #e6e6e6; font-size: 7px; }
            .sector-col { font-weight: bold; color: #2b579a; }
            /* Colores por Rango - Revancha */
            .rev-green { color: #2e7d32; font-weight: bold; }
            .rev-yellow { color: #f57f17; font-weight: bold; }
            .rev-red { color: #c62828; font-weight: bold; }
            /* Colores por Rango - Ancho */
            .ancho-green { color: #2e7d32; font-weight: bold; }
            .ancho-yellow { color: #f57f17; font-weight: bold; }
            .ancho-red { color: #c62828; font-weight: bold; }
        </style>
        """
        
        html = [style, "<table class='summary-table'>"]
        
        # Main Headers
        html.append("<thead>")
        html.append("<tr>")
        html.append("<th rowspan='2' style='vertical-align: middle;'>SECTOR</th>")
        html.append("<th colspan='2'>REVANCHA (m)</th>")
        html.append("<th colspan='2'>ANCHO (m)</th>")
        html.append("<th colspan='2'>CORONAMIENTO (m)</th>")
        html.append("</tr>")
        
        # Sub Headers
        html.append("<tr class='sub-header'>")
        for _ in range(3): # Repeated 3 times
            html.append("<th>MIN (PK)</th>")
            html.append("<th>MAX (PK)</th>")
        html.append("</tr>")
        html.append("</thead>")
        
        html.append("<tbody>")
        
        # Sort sectors
        def sort_key(s):
            # Try to extract number: "Sector 2" -> 2
            try: return int(''.join(filter(str.isdigit, s)))
            except: return s
            
        sorted_sector_names = sorted(sectors_data.keys(), key=sort_key)
        
        def fmt(val_list, value_type='normal'):
            """Formatea valor con PK, aplicando colores según tipo y rango"""
            val, pk = val_list
            if val is None: return "-"
            
            # Aplicar colores según tipo de valor
            if value_type == 'revancha':
                if val > 3.5:
                    return f"<span class='rev-green'>{val:.3f}</span> ({pk})"
                elif val >= 3.0:
                    return f"<span class='rev-yellow'>{val:.3f}</span> ({pk})"
                else:
                    return f"<span class='rev-red'>{val:.3f}</span> ({pk})"
            elif value_type == 'ancho':
                if val > 18.0:
                    return f"<span class='ancho-green'>{val:.3f}</span> ({pk})"
                elif val >= 15.0:
                    return f"<span class='ancho-yellow'>{val:.3f}</span> ({pk})"
                else:
                    return f"<span class='ancho-red'>{val:.3f}</span> ({pk})"
            else:
                return f"{val:.3f} ({pk})"

        for sec_name in sorted_sector_names:
            stats = sectors_data[sec_name]
            
            html.append("<tr>")
            html.append(f"<td class='sector-col'>{sec_name}</td>")
            
            html.append(f"<td>{fmt(stats['min_rev'], 'revancha')}</td>")
            html.append(f"<td>{fmt(stats['max_rev'], 'revancha')}</td>")
            
            html.append(f"<td>{fmt(stats['min_ancho'], 'ancho')}</td>")
            html.append(f"<td>{fmt(stats['max_ancho'], 'ancho')}</td>")
            
            html.append(f"<td>{fmt(stats['min_crown'])}</td>")
            html.append(f"<td>{fmt(stats['max_crown'])}</td>")
            
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
            # 🆕 AUTOMATED FILENAME GENERATION
            default_filename = "Reporte_Revancha.pdf"
            
            try:
                main_dialog = self.parent()
                current_dem_path = getattr(main_dialog, 'dem_file_path', None)
                
                if current_dem_path:
                    dem_name = os.path.splitext(os.path.basename(current_dem_path))[0]
                    
                    # Pattern check: DEM_MURO_FECHA (e.g. DEM_MP_260217)
                    if dem_name.startswith("DEM_") and len(dem_name.split('_')) >= 3:
                        # Replace 'DEM' with 'Reporte_Revancha'
                        default_filename = dem_name.replace("DEM", "Reporte_Revancha", 1) + ".pdf"
                        print(f"🤖 Nombre de reporte automatizado: {default_filename}")
            except Exception as e:
                print(f"⚠️ Error al generar nombre automático: {e}")

            filename, _ = QFileDialog.getSaveFileName(self, "Guardar Reporte PDF", default_filename, "PDF Files (*.pdf)")
            if not filename:
                return

            # 🛑 VERIFICAR SI EL ARCHIVO ESTÁ BLOQUEADO (ABIERTO POR OTRO PROGRAMA)
            if os.path.exists(filename):
                try:
                    with open(filename, 'ab'): pass
                except PermissionError:
                    QMessageBox.critical(self, "Error - Archivo Abierto", 
                        f"El archivo PDF está abierto por otro programa:\n{filename}\n\n"
                        "⚠️ Por favor, CIERRE el archivo PDF y vuelva a intentar.")
                    return
                except Exception as e:
                    # Si falla la verificación por otra razón (ej: disco lleno, ruta inválida), avisar pero intentar continuar
                    print(f"⚠️ Advertencia al verificar archivo: {e}")

            # 3. Load Geomembrane Data (from CSV)
            from .core.geomembrane_manager import GeomembraneManager
            plugin_dir = os.path.dirname(__file__)
            geo_manager = GeomembraneManager(plugin_dir)
            wall_name = self.profiles_data[self.current_profile_index].get('wall_name', "Muro 1")
            
            # Check/Update CSV Data (Append missing PKs)
            current_pks = [str(p.get('pk', '')) for p in self.profiles_data]
            if geo_manager.ensure_data(wall_name, current_pks):
                display_name = geo_manager.get_display_name(wall_name)
                QMessageBox.information(
                    self, 
                    "Datos Faltantes Agregados", 
                    f"Se ha actualizado el archivo de cotas en:\n{geo_manager.csv_path}\n\n"
                    f"Se han agregado los PKs faltantes para '{display_name}'.\n"
                    "Por favor, complete la columna 'Cota_Geomembrana' y vuelva a generar el reporte."
                )
                return

            # 4. Generate Assets (Chart & Tables)
            import tempfile
            
            temp_dir = tempfile.gettempdir()
            chart_path = os.path.join(temp_dir, "temp_profile_chart.png")
            
            if not self.generate_longitudinal_chart(chart_path):
                QMessageBox.warning(self, "Aviso", "No se pudo generar el gráfico longitudinal.")

            # 🎯 CONFIGURACIÓN: Altura del frame detail_table en el QPT (ajustar según tu layout)
            DETAIL_FRAME_HEIGHT_MM = 220  # Cambiar este valor si ajustas el frame en el Layout Designer
            
            html_detail = self.generate_detail_html_table(geo_manager, frame_height_mm=DETAIL_FRAME_HEIGHT_MM)
            html_summary = self.generate_summary_html_table(geo_manager)
            
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
            
            # 🆕 FIX: Convertir rutas de imágenes hardcodeadas en Rutas Relativas al Plugin actual
            print("🖼️ Verificando portabilidad de imágenes en el layout...")
            for item in layout.items():
                if isinstance(item, QgsLayoutItemPicture):
                    old_path = item.picturePath()
                    if not old_path: continue
                    
                    filename_only = os.path.basename(old_path)
                    item_id = item.id() or "Sin ID"
                    
                    # Criterios para corregir: es una ruta absoluta de Windows/AppData o apunta al plugin viejo
                    is_suspicious = "AppData" in old_path or "PLUGIN_Canchas_Las_Tortolas" in old_path or "C:" in old_path
                    
                    if is_suspicious:
                        # 1. Intentar encontrar el archivo en la carpeta de logos del plugin actual
                        potential_path = os.path.join(plugin_dir, 'resources', 'logos', filename_only)
                        
                        # 2. Fallback: buscarlo en la raíz del plugin
                        if not os.path.exists(potential_path):
                            fallback = os.path.join(plugin_dir, filename_only)
                            if os.path.exists(fallback):
                                potential_path = fallback
                        
                        # Si encontramos el archivo localmente, forzamos la ruta
                        if os.path.exists(potential_path):
                            item.setPicturePath(potential_path)
                            print(f"   ✅ Imagen '{item_id}' corregida: {filename_only} -> {potential_path}")
                        else:
                            print(f"   ⚠️ Imagen '{item_id}' detectada como no-portátil, pero no se encontró '{filename_only}' en el plugin.")
            
            # 5. Inject Content into Template Items
            
            # 📅 Extraer y establecer fecha y muro del DEM actual
            try:
                main_dialog = self.parent()
                current_dem_path = getattr(main_dialog, 'dem_file_path', None)
                
                if current_dem_path:
                    # Extraer nombre de archivo sin extensión
                    dem_filename = os.path.splitext(os.path.basename(current_dem_path))[0]
                    print(f"📁 Nombre DEM: {dem_filename}")
                    
                    # Formato esperado: DEM_MP_YYMMDD (ej: DEM_MP_260209 = 09-02-2026)
                    # Estructura: DEM_[MURO]_[FECHA]
                    parts = dem_filename.split('_')
                    print(f"📊 Partes del nombre: {parts}")
                    
                    if len(parts) >= 3:
                        # Extraer código de muro (MP, MO, ME)
                        muro_code = parts[1]  # Segunda parte: MP, MO, o ME
                        
                        # Mapear código a nombre completo con "Revancha"
                        muro_names = {
                            'MP': 'Revancha Muro Principal',
                            'MO': 'Revancha Muro Oeste',
                            'ME': 'Revancha Muro Este'
                        }
                        muro_name = muro_names.get(muro_code.upper(), f'Revancha {muro_code}')
                        
                        # Inyectar en layout si existe muro_label
                        muro_label = layout.itemById('muro_label')
                        if muro_label and isinstance(muro_label, QgsLayoutItemLabel):
                            muro_label.setText(muro_name)
                            print(f"✅ Muro inyectado en 'muro_label': {muro_name}")
                        else:
                            print(f"⚠️ No se encontró 'muro_label' en el layout (opcional)")
                        
                        # Extraer fecha (última parte)
                        date_str = parts[2]  # Tercera parte: YYMMDD
                        
                        if len(date_str) >= 6:
                            try:
                                # Parsear YYMMDD
                                yy = int(date_str[0:2])
                                mm = int(date_str[2:4])
                                dd = int(date_str[4:6])
                                
                                # Convertir YY a año completo (asumiendo 20XX)
                                yyyy = 2000 + yy
                                
                                # Formatear como DD-MM-YYYY
                                formatted_date = f"{dd:02d}-{mm:02d}-{yyyy}"
                                print(f"📅 Fecha formateada: {formatted_date}")
                                
                                # Inyectar en layout - Buscar date_label
                                print(f"🔍 Buscando 'date_label' en layout...")
                                date_label = layout.itemById('date_label')
                                print(f"   Resultado búsqueda: {date_label}")
                                print(f"   Tipo: {type(date_label)}")
                                
                                if date_label:
                                    if isinstance(date_label, QgsLayoutItemLabel):
                                        date_label.setText(f"Fecha: {formatted_date}")
                                        print(f"✅ Fecha inyectada en 'date_label': {formatted_date}")
                                    else:
                                        print(f"⚠️ 'date_label' encontrado pero no es QgsLayoutItemLabel, es: {type(date_label)}")
                                else:
                                    print("❌ No se encontró 'date_label' en el layout")
                                    # Listar todos los items del layout para debug
                                    print("📋 Items disponibles en layout:")
                                    for item in layout.items():
                                        if hasattr(item, 'id'):
                                            print(f"   - {item.id()} ({type(item).__name__})")
                            except (ValueError, IndexError) as e:
                                print(f"⚠️ Error parseando fecha del DEM: {e}")
                        else:
                            print(f"⚠️ Fecha muy corta en nombre DEM: {date_str}")
                    else:
                        print(f"⚠️ Formato de nombre DEM no esperado (esperado: DEM_MURO_FECHA): {dem_filename}")
                else:
                    print("⚠️ No se encontró path del DEM actual")
            except Exception as e:
                print(f"❌ Error extrayendo fecha/muro del DEM: {e}")
                import traceback
                traceback.print_exc()
            
            # Chart
            chart_item = layout.itemById('chart')
            if chart_item and isinstance(chart_item, QgsLayoutItemPicture):
                chart_item.setPicturePath(chart_path)
            
            # Map Generation (NEW)
            try:
                # Recuperar datos del diálogo principal
                main_dialog = self.parent()
                current_dem = getattr(main_dialog, 'dem_file_path', None)
                prev_dem = getattr(main_dialog, 'previous_dem_file_path', None)
                wall_name = getattr(main_dialog, 'selected_wall', "Muro 1")
                
                if current_dem and prev_dem and self.ecw_file_path:
                    map_path = os.path.join(temp_dir, "temp_wall_map.png")
                    
                    # Importar generador
                    from .core.map_generator import MapGenerator
                    # profile_viewer_dialog está en root, así que dirname es el root del plugin
                    plugin_root = os.path.dirname(__file__)
                    map_gen = MapGenerator(plugin_root)
                    
                    print(f"🗺️ Generando mapa para reporte: {wall_name}")
                    
                    # 🆕 Forzar actualización de spinboxes (leer texto escrito aunque no haya focus out)
                    self.map_min_spin.interpretText()
                    self.map_max_spin.interpretText()
                    
                    # 🆕 Obtener valores personalizados de Min/Max
                    custom_min = self.map_min_spin.value()
                    custom_max = self.map_max_spin.value()
                    print(f"   ⚙️ Configuración Mapa: Min={custom_min}, Max={custom_max} (0=Auto)")
                    
                    if map_gen.generate_map_image(wall_name, self.ecw_file_path, current_dem, prev_dem, map_path, 
                                                 custom_min=custom_min, custom_max=custom_max):
                        # Inyectar en layout
                        map_item = layout.itemById('main_map')
                        if map_item and isinstance(map_item, QgsLayoutItemPicture):
                            map_item.setPicturePath(map_path)
                            print(f"✅ Mapa inyectado en item 'main_map': {map_path}")
                        else:
                            print("⚠️ No se encontró item 'main_map' en el layout o no es una imagen")
                    else:
                        print("❌ Falló la generación del mapa para el reporte")
            except Exception as e:
                print(f"❌ Error intentando generar mapa para reporte: {e}")
                # No interrumpimos el reporte si falla el mapa, solo log
            
            # Summary Table (Fix: Handle Frames for HTML)
            summary_frame = layout.itemById('summary_table')
            if summary_frame and isinstance(summary_frame, QgsLayoutFrame):
                summary_mf = summary_frame.multiFrame()
                if isinstance(summary_mf, QgsLayoutItemHtml):
                    # Wrap in proper HTML structure
                    final_summary_html = f"<html><head><meta charset='UTF-8'></head><body>{html_summary}</body></html>"
                    print(f"📊 Injecting Summary Table (Length: {len(final_summary_html)})")
                    
                    summary_mf.setContentMode(QgsLayoutItemHtml.ManualHtml)
                    summary_mf.setHtml(final_summary_html)
                    summary_mf.loadHtml()
                else:
                    print(f"⚠️ summary_table no es QgsLayoutItemHtml: {type(summary_mf)}")
            else:
                print(f"⚠️ summary_table no encontrado o no es Frame: {type(summary_frame)}")
                
            # Detail Table (Fix: Handle Frames for HTML)
            detail_frame = layout.itemById('detail_table')
            if detail_frame and isinstance(detail_frame, QgsLayoutFrame):
                detail_mf = detail_frame.multiFrame()
                if isinstance(detail_mf, QgsLayoutItemHtml):
                    # Wrap in proper HTML structure
                    final_detail_html = f"<html><head><meta charset='UTF-8'></head><body>{html_detail}</body></html>"
                    print(f"📊 Injecting Detail Table (Length: {len(final_detail_html)})")
                    
                    detail_mf.setContentMode(QgsLayoutItemHtml.ManualHtml)
                    detail_mf.setHtml(final_detail_html)
                    detail_mf.loadHtml()
                else:
                    print(f"⚠️ detail_table no es QgsLayoutItemHtml: {type(detail_mf)}")
            else:
                print(f"⚠️ detail_table no encontrado o no es Frame: {type(detail_frame)}")

            # CRITICAL: Force HTML processing before export
            # HTML tables need time to render, otherwise they appear blank in PDF
            print("⏳ Procesando HTML de tablas...")
            QApplication.processEvents()  # Process pending UI events
            
            # Wait for HTML to fully load (QGIS async rendering)
            import time
            time.sleep(1.0)  # 1000ms - increased from 500ms for better reliability
            
            # Force layout refresh
            layout.refresh()
            QApplication.processEvents()  # Process refresh events
            print("✅ HTML procesado, continuando con export...")

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
                print(f"📸 Detectadas {len(alert_profiles)} alertas, generando screenshots...")
                    
                # ENHANCED SYSTEM: Automatic slot discovery
                # Instead of a hardcoded list, we find ALL items that start with 'alert_screenshot_'
                # This lets the user add page after page in the QPT with more slots.
                all_qpt_slots = []
                for item in layout.items():
                    if isinstance(item, QgsLayoutItemPicture) and item.id() and item.id().startswith('alert_screenshot_'):
                        try:
                            # Extraer el número del ID para ordenar correctamente
                            num = int(item.id().replace('alert_screenshot_', ''))
                            all_qpt_slots.append((num, item))
                        except ValueError:
                            continue
                
                # Ordenar por número (1, 2, 3...)
                all_qpt_slots.sort(key=lambda x: x[0])
                print(f"🔎 Encontrados {len(all_qpt_slots)} espacios para capturas en el QPT.")
                
                screenshots_placed = 0
                
                # Step 1: Fill slots found in QPT
                for i, (slot_num, qpt_item) in enumerate(all_qpt_slots):
                    if i >= len(alert_profiles):
                        break
                        
                    pk = alert_profiles[i]
                    
                    # Generate screenshot
                    self.current_pk = pk
                    for p_idx, p in enumerate(self.profiles_data):
                        if str(p.get('pk')) == pk:
                            self.current_profile_index = p_idx
                            break
                    self.update_profile_display(export_mode=True)
                    QApplication.processEvents()
                    
                    # Save and inject
                    screenshot_path = os.path.join(temp_dir, f"alert_{pk.replace('+','_')}.png")
                    self.figure.savefig(screenshot_path)
                    qpt_item.setPicturePath(screenshot_path)
                    
                    print(f"✅ Screenshot {i+1} inyectado en slot QPT '{qpt_item.id()}'")
                    screenshots_placed += 1
                
                # Step 2: Inform if there are more alerts than slots in QPT
                if screenshots_placed < len(alert_profiles):
                    print(f"⚠️ AVISO: Quedaron {len(alert_profiles) - screenshots_placed} alertas sin espacio en el QPT.")
                    # El usuario prefiere no crear hojas dinámicas "feas", 
                    # así que solo avisamos para que añada más hojas al QPT si lo necesita.
            
            # 🆕 LOGICA CONSOLIDADA DE LIMPIEZA DE PÁGINAS (Páginas 3+ / Índices 2+)
            # Esta lógica determina cuántas páginas de alertas se necesitan realmente
            # y elimina CUALQUIER página sobrante del layout (tanto QPT como dinámicas si sobran)
            
            import math
            num_alerts = len(alert_profiles)
            alert_pages_needed = math.ceil(num_alerts / 4)
            first_alert_page_idx = 2  # Hoja 3 (donde empiezan los perfiles)
            
            # El índice de la primera página a ELIMINAR es:
            start_delete_idx = first_alert_page_idx + alert_pages_needed
            
            page_collection = layout.pageCollection()
            total_pages_now = page_collection.pageCount()
            
            if start_delete_idx < total_pages_now:
                print(f"🧹 Limpiando {total_pages_now - start_delete_idx} páginas vacías (desde índice {start_delete_idx})...")
                # Eliminar en orden inverso para no alterar los índices durante el proceso
                for page_idx in range(total_pages_now - 1, start_delete_idx - 1, -1):
                    # 1. Eliminar items de la página
                    items_to_remove = [item for item in layout.items() 
                                     if hasattr(item, 'page') and item.page() == page_idx]
                    for item in items_to_remove:
                        layout.removeLayoutItem(item)
                    
                    # 2. Eliminar página
                    page_collection.deletePage(page_idx)
                    print(f"   ✅ Página {page_idx + 1} eliminada")
            else:
                print(f"📋 No hay páginas que limpiar (Necesarias: {alert_pages_needed}, Actuales: {total_pages_now - first_alert_page_idx} de alertas)")
            
            # 🆕 Generate Longitudinal Chart (Before Export)
            try:
                from .core.report_generator import ReportGenerator
                # Ensure plugin_root is available (it was defined at start of method)
                report_gen = ReportGenerator(plugin_root, self.profiles_data, self.saved_measurements)
                
                chart_path = os.path.join(temp_dir, "longitudinal_profile.png")
                print(f"📊 Intentando generar gráfico en: {chart_path}")
                
                if report_gen.generate_longitudinal_chart(chart_path):
                    # Use confirmed ID 'chart'
                    chart_item = layout.itemById('chart')
                        
                    if chart_item and isinstance(chart_item, QgsLayoutItemPicture):
                        chart_item.setPicturePath(chart_path)
                        print(f"✅ Gráfico longitudinal inyectado en item '{chart_item.id()}'")
                    else:
                        print(f"⚠️ Item 'chart' no encontrado o no es Picture. Verifique el Layout.")
                        logger.warning(f"Chart Item ID 'chart' not found in layout or is not QgsLayoutItemPicture.")
                else:
                    print(f"❌ Falló generate_longitudinal_chart (ver logs anteriores)")
            except Exception as e:
                print(f"❌ Error crítico generando gráfico: {e}")
                import traceback
                traceback.print_exc()

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
