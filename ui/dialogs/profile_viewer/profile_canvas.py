# -*- coding: utf-8 -*-
"""
Profile Canvas Module - Revanchas LT Plugin
Gestiona el renderizado de perfiles topográficos con matplotlib

Este módulo fue extraído de profile_viewer_dialog.py para mejorar
la modularidad y mantenibilidad del código.
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

from qgis.PyQt.QtWidgets import QWidget, QVBoxLayout
from qgis.PyQt.QtCore import Qt, pyqtSignal, QObject

# Importar matplotlib con manejo de errores
try:
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    HAS_MATPLOTLIB = True
except ImportError:
    try:
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
        HAS_MATPLOTLIB = True
    except ImportError:
        HAS_MATPLOTLIB = False
        Figure = None
        FigureCanvas = None


@dataclass
class ProfileRenderConfig:
    """Configuración de renderizado de perfil."""
    # Colores
    terrain_color: str = '#8B4513'
    terrain_fill_color: str = '#D2B48C'
    lama_color: str = '#FFD700'
    lama_line_color: str = '#FFA500'
    crown_color: str = '#00FF00'
    width_line_color: str = '#FF00FF'
    reference_color: str = '#0000FF'
    centerline_color: str = '#FF0000'
    
    # Estilos
    terrain_linewidth: float = 2.0
    reference_linewidth: float = 2.0
    marker_size: int = 10
    
    # Opciones
    show_legend: bool = False
    show_grid: bool = True
    fill_terrain: bool = True


class ProfileCanvas(QObject):
    """
    Componente de renderizado de perfiles topográficos.
    
    Encapsula la lógica de matplotlib para dibujar perfiles,
    puntos LAMA, líneas de referencia, y mediciones.
    
    Signals:
        canvas_clicked: Emitido cuando se hace clic en el canvas (x, y, button)
        canvas_scrolled: Emitido cuando se hace scroll (x, y, direction)
    """
    
    canvas_clicked = pyqtSignal(float, float, int)
    canvas_scrolled = pyqtSignal(float, float, str)
    
    def __init__(self, 
                 parent: Optional[QWidget] = None,
                 figsize: Tuple[float, float] = (14, 8),
                 config: Optional[ProfileRenderConfig] = None):
        """
        Inicializa el canvas de perfiles.
        
        Args:
            parent: Widget padre
            figsize: Tamaño de la figura matplotlib
            config: Configuración de renderizado
        """
        super().__init__(parent)
        
        self.config = config or ProfileRenderConfig()
        self._parent = parent
        
        if not HAS_MATPLOTLIB:
            self.figure = None
            self.canvas = None
            self.ax = None
            return
        
        # Crear figura y canvas de matplotlib
        self.figure = Figure(figsize=figsize)
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        
        # Configurar eventos
        self.canvas.mpl_connect('button_press_event', self._on_click)
        self.canvas.mpl_connect('scroll_event', self._on_scroll)
        
        # Configurar canvas
        self.canvas.setFocusPolicy(Qt.StrongFocus)
    
    @property
    def is_available(self) -> bool:
        """Indica si matplotlib está disponible."""
        return HAS_MATPLOTLIB and self.canvas is not None
    
    def get_widget(self) -> Optional[QWidget]:
        """Obtiene el widget del canvas para agregar a layouts."""
        return self.canvas
    
    def clear(self) -> None:
        """Limpia el canvas."""
        if self.ax:
            self.ax.clear()
    
    def draw(self) -> None:
        """Redibuja el canvas."""
        if self.canvas:
            self.canvas.draw()
    
    def render_profile(self, 
                       distances: List[float], 
                       elevations: List[float],
                       pk: str,
                       x_range: Tuple[float, float] = (-40, 40),
                       title_extra: str = "") -> None:
        """
        Renderiza un perfil topográfico.
        
        Args:
            distances: Lista de distancias desde el eje
            elevations: Lista de elevaciones
            pk: Identificador del perfil (PK)
            x_range: Rango de visualización (min, max)
            title_extra: Texto adicional para el título
        """
        if not self.is_available:
            return
        
        self.clear()
        
        # Filtrar datos válidos
        valid_data = [
            (d, e) for d, e in zip(distances, elevations) 
            if e != -9999 and x_range[0] <= d <= x_range[1]
        ]
        
        if not valid_data:
            self.ax.text(0.5, 0.5, 'Sin datos válidos', 
                        ha='center', va='center', transform=self.ax.transAxes)
            self.draw()
            return
        
        valid_distances, valid_elevations = zip(*valid_data)
        
        # Dibujar terreno
        self.ax.plot(
            valid_distances, 
            valid_elevations, 
            color=self.config.terrain_color,
            linewidth=self.config.terrain_linewidth,
            label='Terreno Natural',
            zorder=5
        )
        
        # Rellenar bajo el terreno
        if self.config.fill_terrain:
            min_elev = min(valid_elevations)
            self.ax.fill_between(
                valid_distances, 
                valid_elevations, 
                min_elev - 0.5,
                color=self.config.terrain_fill_color,
                alpha=0.3,
                zorder=1
            )
        
        # Configurar ejes
        self.ax.set_xlim(x_range)
        self._auto_scale_y(valid_elevations)
        
        # Etiquetas y título
        self.ax.set_xlabel('Distancia desde eje (m)', fontweight='bold')
        self.ax.set_ylabel('Elevación (m)', fontweight='bold')
        
        title = f'Perfil Topográfico - PK {pk}'
        if title_extra:
            title += f' | {title_extra}'
        self.ax.set_title(title, fontsize=12, fontweight='bold')
        
        # Línea central
        self.ax.axvline(x=0, color=self.config.centerline_color, 
                       linestyle='--', linewidth=1.5, 
                       label='Eje Central', zorder=3)
        
        # Grid
        if self.config.show_grid:
            self.ax.grid(True, linestyle='--', alpha=0.7, zorder=0)
        
        # Leyenda
        if self.config.show_legend:
            self.ax.legend(loc='upper right', fontsize=8)
        
        self.draw()
    
    def render_lama_points(self, 
                          lama_points: List[Dict[str, Any]],
                          modified_lama: Optional[Tuple[float, float]] = None) -> None:
        """
        Renderiza puntos LAMA en el perfil.
        
        Args:
            lama_points: Lista de puntos LAMA del DEM
            modified_lama: Punto LAMA modificado manualmente (x, y)
        """
        if not self.is_available or not lama_points:
            return
        
        for lama in lama_points:
            if 'elevation_dem' in lama and lama['elevation_dem'] is not None:
                dist = lama.get('distance_from_centerline', 0)
                elev = lama['elevation_dem']
                
                # Determinar si es el punto original o modificado
                is_modified = (modified_lama is not None and 
                             abs(dist - modified_lama[0]) < 0.5)
                
                if is_modified:
                    # Mostrar punto original tachado
                    self.ax.scatter(
                        dist, elev,
                        color='gray',
                        marker='x',
                        s=80,
                        alpha=0.5,
                        zorder=8
                    )
                    # Mostrar punto modificado
                    self.ax.scatter(
                        modified_lama[0], modified_lama[1],
                        color=self.config.lama_color,
                        marker='o',
                        s=self.config.marker_size * 10,
                        edgecolors='black',
                        linewidths=2,
                        label='LAMA Modificada',
                        zorder=10
                    )
                else:
                    self.ax.scatter(
                        dist, elev,
                        color=self.config.lama_color,
                        marker='o',
                        s=self.config.marker_size * 10,
                        edgecolors='black',
                        linewidths=1,
                        label='Punto LAMA',
                        zorder=9
                    )
    
    def render_reference_line(self, 
                             elevation: float,
                             x_range: Tuple[float, float],
                             label: str = "Línea de Referencia",
                             color: Optional[str] = None,
                             style: str = '-') -> None:
        """
        Renderiza una línea de referencia horizontal.
        
        Args:
            elevation: Elevación de la línea
            x_range: Rango X de la línea
            label: Etiqueta para la leyenda
            color: Color de la línea (usa default si None)
            style: Estilo de línea ('-', '--', etc.)
        """
        if not self.is_available:
            return
        
        line_color = color or self.config.reference_color
        
        self.ax.hlines(
            y=elevation,
            xmin=x_range[0],
            xmax=x_range[1],
            colors=line_color,
            linestyles=style,
            linewidth=self.config.reference_linewidth,
            label=label,
            zorder=7
        )
    
    def render_crown_point(self, x: float, y: float) -> None:
        """
        Renderiza el punto de coronamiento.
        
        Args:
            x: Coordenada X
            y: Coordenada Y (elevación)
        """
        if not self.is_available:
            return
        
        self.ax.scatter(
            x, y,
            color=self.config.crown_color,
            marker='s',
            s=self.config.marker_size * 12,
            edgecolors='black',
            linewidths=2,
            label='Coronamiento',
            zorder=11
        )
    
    def render_width_measurement(self,
                                start_x: float,
                                end_x: float,
                                y: float,
                                show_annotation: bool = True) -> None:
        """
        Renderiza una medición de ancho.
        
        Args:
            start_x: X inicial
            end_x: X final
            y: Elevación de la línea
            show_annotation: Si mostrar anotación de distancia
        """
        if not self.is_available:
            return
        
        # Línea de medición
        self.ax.plot(
            [start_x, end_x], [y, y],
            color=self.config.width_line_color,
            linewidth=3,
            marker='|',
            markersize=15,
            label='Ancho Medido',
            zorder=12
        )
        
        # Anotación
        if show_annotation:
            distance = abs(end_x - start_x)
            mid_x = (start_x + end_x) / 2
            
            self.ax.annotate(
                f'{distance:.2f} m',
                xy=(mid_x, y),
                xytext=(0, 15),
                textcoords='offset points',
                ha='center',
                fontsize=10,
                fontweight='bold',
                color=self.config.width_line_color,
                zorder=13
            )
    
    def set_cursor(self, cursor_type: Qt.CursorShape) -> None:
        """Establece el cursor del canvas."""
        if self.canvas:
            self.canvas.setCursor(cursor_type)
    
    def set_focus(self) -> None:
        """Da el foco al canvas."""
        if self.canvas:
            self.canvas.setFocus()
    
    def get_xlim(self) -> Tuple[float, float]:
        """Obtiene los límites actuales del eje X."""
        if self.ax:
            return self.ax.get_xlim()
        return (0, 0)
    
    def get_ylim(self) -> Tuple[float, float]:
        """Obtiene los límites actuales del eje Y."""
        if self.ax:
            return self.ax.get_ylim()
        return (0, 0)
    
    def set_xlim(self, xmin: float, xmax: float) -> None:
        """Establece los límites del eje X."""
        if self.ax:
            self.ax.set_xlim(xmin, xmax)
    
    def set_ylim(self, ymin: float, ymax: float) -> None:
        """Establece los límites del eje Y."""
        if self.ax:
            self.ax.set_ylim(ymin, ymax)
    
    def _auto_scale_y(self, elevations: List[float], margin: float = 0.05) -> None:
        """Ajusta automáticamente el eje Y."""
        if not elevations:
            return
        
        y_min = min(elevations)
        y_max = max(elevations)
        y_range = y_max - y_min
        
        margin_val = y_range * margin
        self.ax.set_ylim(y_min - margin_val, y_max + margin_val)
    
    def _on_click(self, event) -> None:
        """Handler de clic en el canvas."""
        if event.inaxes == self.ax:
            button = 1 if event.button == 1 else (2 if event.button == 2 else 3)
            self.canvas_clicked.emit(event.xdata, event.ydata, button)
    
    def _on_scroll(self, event) -> None:
        """Handler de scroll en el canvas."""
        if event.inaxes == self.ax:
            direction = 'up' if event.button == 'up' else 'down'
            self.canvas_scrolled.emit(event.xdata, event.ydata, direction)
    
    def connect_key_events(self,
                          key_press_handler,
                          key_release_handler) -> None:
        """
        Conecta handlers de eventos de teclado.
        
        Args:
            key_press_handler: Función para key press
            key_release_handler: Función para key release
        """
        if self.canvas:
            self.canvas.mpl_connect('key_press_event', key_press_handler)
            self.canvas.mpl_connect('key_release_event', key_release_handler)
