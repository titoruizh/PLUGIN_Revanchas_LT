# -*- coding: utf-8 -*-
"""
Visualization Module - Revanchas LT Plugin
Maneja visualización matplotlib de perfiles topográficos

Refactorizado con type hints y logging estructurado.
"""

from typing import List, Dict, Any, Optional, Tuple

# Importar logging del plugin
try:
    from ..utils.logging_config import get_logger
except ImportError:
    get_logger = lambda x: __import__('logging').getLogger(x)

logger = get_logger(__name__)

# Importar matplotlib con manejo de errores
try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    
    try:
        test_fig = Figure(figsize=(1, 1))
        HAS_MATPLOTLIB = True
        logger.debug("Matplotlib funcionando correctamente")
    except (AttributeError, ImportError, Exception) as e:
        logger.warning(f"Matplotlib disponible pero con problemas: {e}")
        HAS_MATPLOTLIB = False
except ImportError:
    HAS_MATPLOTLIB = False
    logger.warning("Matplotlib no disponible")

from qgis.PyQt.QtWidgets import QWidget, QVBoxLayout, QMessageBox


# Constantes
NODATA_VALUE: float = -9999.0
DEFAULT_PROFILE_WIDTH: float = 90.0  # metros (±45m)
DEFAULT_DPI: int = 300


class ProfileVisualization(QWidget):
    """
    Widget para visualización de perfiles topográficos.
    
    Proporciona funcionalidad de plotting para perfiles individuales,
    múltiples y longitudinales usando matplotlib.
    """
    
    def __init__(self, parent: Optional[QWidget] = None):
        """
        Inicializa el widget de visualización.
        
        Args:
            parent: Widget padre opcional
        """
        super().__init__(parent)
        self.parent = parent
        self.figure: Optional[Figure] = None
        self.canvas: Optional[FigureCanvas] = None
        
        if not HAS_MATPLOTLIB:
            self._init_no_matplotlib()
        else:
            self._init_matplotlib()
        
        logger.debug("ProfileVisualization inicializado")
    
    def _init_no_matplotlib(self) -> None:
        """Inicializa widget cuando matplotlib no está disponible."""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        from qgis.PyQt.QtWidgets import QLabel
        label = QLabel(
            "Matplotlib no disponible.\n"
            "Instale matplotlib para visualizar perfiles."
        )
        label.setWordWrap(True)
        layout.addWidget(label)
        
        logger.warning("Widget inicializado sin matplotlib")
    
    def _init_matplotlib(self) -> None:
        """Inicializa componentes matplotlib."""
        self.figure = Figure(figsize=(12, 6))
        self.canvas = FigureCanvas(self.figure)
        
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)
    
    def plot_profile(self, profile_data: Dict[str, Any]) -> bool:
        """
        Grafica un único perfil topográfico.
        
        Args:
            profile_data: Diccionario de datos del perfil
            
        Returns:
            True si el gráfico fue exitoso
        """
        if not HAS_MATPLOTLIB:
            QMessageBox.warning(
                self.parent,
                "Visualización no disponible",
                "Matplotlib no está instalado."
            )
            return False
        
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        # Extraer datos
        distances = profile_data.get('distances', [])
        elevations = profile_data.get('elevations', [])
        pk = profile_data.get('pk', 'Unknown')
        
        # Filtrar valores NODATA
        valid_data = [
            (d, e) for d, e in zip(distances, elevations) 
            if e != NODATA_VALUE
        ]
        
        if not valid_data:
            ax.text(
                0.5, 0.5, 'No hay datos válidos para mostrar',
                ha='center', va='center', transform=ax.transAxes
            )
            ax.set_title(f'Perfil Topográfico - {pk}')
            self.canvas.draw()
            logger.warning(f"Perfil {pk}: sin datos válidos")
            return False
        
        valid_distances, valid_elevations = zip(*valid_data)
        
        # Graficar perfil
        ax.plot(
            valid_distances, valid_elevations, 
            'b-', linewidth=2, label='Terreno Natural'
        )
        ax.fill_between(
            valid_distances, valid_elevations,
            min(valid_elevations) - 2, 
            alpha=0.3, color='brown', label='Terreno'
        )
        
        # Marcar línea central
        ax.axvline(x=0, color='red', linestyle='--', alpha=0.7, label='Eje de Alineación')
        
        # Configurar gráfico
        ax.grid(True, alpha=0.3)
        ax.set_xlabel('Distancia desde Eje (m)')
        ax.set_ylabel('Elevación (m)')
        ax.set_title(f'Perfil Topográfico - {pk}')
        ax.legend()
        ax.set_aspect('equal', adjustable='box')
        ax.set_xlim(-45, 45)
        
        self.figure.tight_layout()
        self.canvas.draw()
        
        logger.debug(f"Perfil {pk} graficado exitosamente")
        return True
    
    def plot_multiple_profiles(self, 
                               profiles_data: List[Dict[str, Any]], 
                               max_profiles: int = 5) -> bool:
        """
        Grafica múltiples perfiles en subplots.
        
        Args:
            profiles_data: Lista de diccionarios de perfiles
            max_profiles: Número máximo de perfiles a mostrar
            
        Returns:
            True si el gráfico fue exitoso
        """
        if not HAS_MATPLOTLIB:
            QMessageBox.warning(
                self.parent,
                "Visualización no disponible",
                "Matplotlib no está instalado."
            )
            return False
        
        profiles_to_show = profiles_data[:max_profiles]
        num_profiles = len(profiles_to_show)
        
        if num_profiles == 0:
            return False
        
        self.figure.clear()
        
        # Calcular disposición de subplots
        cols = min(2, num_profiles)
        rows = (num_profiles + cols - 1) // cols
        
        for i, profile in enumerate(profiles_to_show):
            ax = self.figure.add_subplot(rows, cols, i + 1)
            
            distances = profile.get('distances', [])
            elevations = profile.get('elevations', [])
            pk = profile.get('pk', f'Profile {i+1}')
            
            valid_data = [
                (d, e) for d, e in zip(distances, elevations) 
                if e != NODATA_VALUE
            ]
            
            if valid_data:
                valid_distances, valid_elevations = zip(*valid_data)
                
                ax.plot(valid_distances, valid_elevations, 'b-', linewidth=1.5)
                ax.fill_between(
                    valid_distances, valid_elevations,
                    min(valid_elevations) - 1, alpha=0.3, color='brown'
                )
                ax.axvline(x=0, color='red', linestyle='--', alpha=0.5)
                ax.grid(True, alpha=0.3)
                ax.set_title(pk, fontsize=10)
                ax.set_xlim(-45, 45)
            else:
                ax.text(
                    0.5, 0.5, 'Sin datos', 
                    ha='center', va='center', transform=ax.transAxes
                )
                ax.set_title(pk, fontsize=10)
        
        # Etiquetas comunes
        self.figure.text(0.5, 0.02, 'Distancia desde Eje (m)', ha='center')
        self.figure.text(0.02, 0.5, 'Elevación (m)', va='center', rotation='vertical')
        self.figure.suptitle('Perfiles Topográficos Múltiples', fontsize=14)
        
        self.figure.tight_layout()
        self.canvas.draw()
        
        logger.info(f"Graficados {num_profiles} perfiles múltiples")
        return True
    
    def plot_longitudinal_profile(self, 
                                   profiles_data: List[Dict[str, Any]]) -> bool:
        """
        Grafica perfil longitudinal a lo largo de la alineación.
        
        Args:
            profiles_data: Lista de diccionarios de perfiles
            
        Returns:
            True si el gráfico fue exitoso
        """
        if not HAS_MATPLOTLIB or not profiles_data:
            return False
        
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        # Extraer elevaciones de línea central
        stations: List[float] = []
        centerline_elevs: List[float] = []
        
        for profile in profiles_data:
            pk_decimal = profile.get('pk_decimal', 0)
            elevations = profile.get('elevations', [])
            
            if elevations:
                mid_idx = len(elevations) // 2
                if elevations[mid_idx] != NODATA_VALUE:
                    stations.append(pk_decimal)
                    centerline_elevs.append(elevations[mid_idx])
        
        if stations and centerline_elevs:
            ax.plot(
                stations, centerline_elevs, 
                'b-o', linewidth=2, markersize=4,
                label='Perfil Longitudinal'
            )
            
            ax.grid(True, alpha=0.3)
            ax.set_xlabel('Progresiva (m)')
            ax.set_ylabel('Elevación (m)')
            ax.set_title('Perfil Longitudinal del Eje')
            ax.legend()
            ax.set_xlim(0, max(stations))
            
            self.figure.tight_layout()
            self.canvas.draw()
            
            logger.info(f"Perfil longitudinal graficado: {len(stations)} puntos")
            return True
        
        return False
    
    def plot_comparison(self, 
                        profile1: Dict[str, Any], 
                        profile2: Dict[str, Any],
                        labels: Tuple[str, str] = ('Perfil 1', 'Perfil 2')) -> bool:
        """
        Grafica comparación de dos perfiles.
        
        Args:
            profile1: Primer perfil
            profile2: Segundo perfil
            labels: Tupla con etiquetas para cada perfil
            
        Returns:
            True si el gráfico fue exitoso
        """
        if not HAS_MATPLOTLIB:
            return False
        
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        colors = ['blue', 'green']
        
        for i, (profile, label) in enumerate([(profile1, labels[0]), (profile2, labels[1])]):
            distances = profile.get('distances', [])
            elevations = profile.get('elevations', [])
            
            valid_data = [
                (d, e) for d, e in zip(distances, elevations) 
                if e != NODATA_VALUE
            ]
            
            if valid_data:
                valid_distances, valid_elevations = zip(*valid_data)
                ax.plot(
                    valid_distances, valid_elevations,
                    color=colors[i], linewidth=2, label=label
                )
        
        ax.axvline(x=0, color='red', linestyle='--', alpha=0.5, label='Eje')
        ax.grid(True, alpha=0.3)
        ax.set_xlabel('Distancia desde Eje (m)')
        ax.set_ylabel('Elevación (m)')
        ax.set_title('Comparación de Perfiles')
        ax.legend()
        ax.set_xlim(-45, 45)
        
        self.figure.tight_layout()
        self.canvas.draw()
        
        logger.debug("Comparación de perfiles graficada")
        return True
    
    def export_plot(self, 
                    filename: str, 
                    dpi: int = DEFAULT_DPI) -> bool:
        """
        Exporta gráfico actual a archivo.
        
        Args:
            filename: Nombre del archivo de salida
            dpi: Resolución para exportación
            
        Returns:
            True si la exportación fue exitosa
        """
        if not HAS_MATPLOTLIB or self.figure is None:
            return False
        
        try:
            self.figure.savefig(filename, dpi=dpi, bbox_inches='tight')
            logger.info(f"Gráfico exportado a: {filename}")
            return True
        except Exception as e:
            logger.error(f"Error exportando gráfico: {e}")
            if self.parent:
                QMessageBox.warning(
                    self.parent,
                    "Error de Exportación",
                    f"No se pudo exportar la imagen: {str(e)}"
                )
            return False
    
    def clear_plot(self) -> None:
        """Limpia el gráfico actual."""
        if self.figure:
            self.figure.clear()
            if self.canvas:
                self.canvas.draw()
    
    def set_figure_size(self, width: float, height: float) -> None:
        """
        Establece el tamaño de la figura.
        
        Args:
            width: Ancho en pulgadas
            height: Alto en pulgadas
        """
        if self.figure:
            self.figure.set_size_inches(width, height)
    
    @staticmethod
    def is_available() -> bool:
        """Verifica si matplotlib está disponible."""
        return HAS_MATPLOTLIB