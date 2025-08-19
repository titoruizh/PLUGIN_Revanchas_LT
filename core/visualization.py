# -*- coding: utf-8 -*-
"""
Visualization Module
Handles matplotlib plotting for profile visualization
"""

try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    
from qgis.PyQt.QtWidgets import QWidget, QVBoxLayout, QMessageBox


class ProfileVisualization(QWidget):
    """Widget for displaying topographic profile plots"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        
        if not HAS_MATPLOTLIB:
            self.init_no_matplotlib()
        else:
            self.init_matplotlib()
    
    def init_no_matplotlib(self):
        """Initialize widget when matplotlib is not available"""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        from qgis.PyQt.QtWidgets import QLabel
        label = QLabel("Matplotlib no disponible.\nInstale matplotlib para visualizar perfiles.")
        label.setWordWrap(True)
        layout.addWidget(label)
    
    def init_matplotlib(self):
        """Initialize matplotlib components"""
        self.figure = Figure(figsize=(12, 6))
        self.canvas = FigureCanvas(self.figure)
        
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)
    
    def plot_profile(self, profile_data):
        """Plot a single topographic profile
        
        Args:
            profile_data: Profile data dictionary from ProfileGenerator
        """
        if not HAS_MATPLOTLIB:
            QMessageBox.warning(
                self.parent,
                "Visualización no disponible",
                "Matplotlib no está instalado. No se puede mostrar la visualización de perfiles."
            )
            return
        
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        # Extract data
        distances = profile_data.get('distances', [])
        elevations = profile_data.get('elevations', [])
        pk = profile_data.get('pk', 'Unknown')
        
        # Filter out NODATA values
        valid_data = [(d, e) for d, e in zip(distances, elevations) if e != -9999]
        
        if not valid_data:
            ax.text(0.5, 0.5, 'No hay datos válidos para mostrar', 
                   ha='center', va='center', transform=ax.transAxes)
            ax.set_title(f'Perfil Topográfico - {pk}')
            self.canvas.draw()
            return
        
        valid_distances, valid_elevations = zip(*valid_data)
        
        # Plot the profile
        ax.plot(valid_distances, valid_elevations, 'b-', linewidth=2, label='Terreno Natural')
        ax.fill_between(valid_distances, valid_elevations, 
                       min(valid_elevations) - 2, alpha=0.3, color='brown', label='Terreno')
        
        # Mark centerline
        ax.axvline(x=0, color='red', linestyle='--', alpha=0.7, label='Eje de Alineación')
        
        # Add grid and labels
        ax.grid(True, alpha=0.3)
        ax.set_xlabel('Distancia desde Eje (m)')
        ax.set_ylabel('Elevación (m)')
        ax.set_title(f'Perfil Topográfico - {pk}')
        ax.legend()
        
        # Set equal aspect ratio for realistic visualization
        ax.set_aspect('equal', adjustable='box')
        
        # Format axes
        ax.set_xlim(-45, 45)  # 90m total width, centered
        
        self.figure.tight_layout()
        self.canvas.draw()
    
    def plot_multiple_profiles(self, profiles_data, max_profiles=5):
        """Plot multiple profiles in subplots
        
        Args:
            profiles_data: List of profile data dictionaries
            max_profiles: Maximum number of profiles to show
        """
        if not HAS_MATPLOTLIB:
            QMessageBox.warning(
                self.parent,
                "Visualización no disponible", 
                "Matplotlib no está instalado."
            )
            return
        
        profiles_to_show = profiles_data[:max_profiles]
        num_profiles = len(profiles_to_show)
        
        if num_profiles == 0:
            return
        
        self.figure.clear()
        
        # Calculate subplot arrangement
        cols = min(2, num_profiles)
        rows = (num_profiles + cols - 1) // cols
        
        for i, profile in enumerate(profiles_to_show):
            ax = self.figure.add_subplot(rows, cols, i + 1)
            
            # Extract data
            distances = profile.get('distances', [])
            elevations = profile.get('elevations', [])
            pk = profile.get('pk', f'Profile {i+1}')
            
            # Filter valid data
            valid_data = [(d, e) for d, e in zip(distances, elevations) if e != -9999]
            
            if valid_data:
                valid_distances, valid_elevations = zip(*valid_data)
                
                # Plot profile
                ax.plot(valid_distances, valid_elevations, 'b-', linewidth=1.5)
                ax.fill_between(valid_distances, valid_elevations,
                               min(valid_elevations) - 1, alpha=0.3, color='brown')
                
                # Mark centerline
                ax.axvline(x=0, color='red', linestyle='--', alpha=0.5)
                
                # Format subplot
                ax.grid(True, alpha=0.3)
                ax.set_title(pk, fontsize=10)
                ax.set_xlim(-45, 45)
            else:
                ax.text(0.5, 0.5, 'Sin datos', ha='center', va='center', transform=ax.transAxes)
                ax.set_title(pk, fontsize=10)
        
        # Add common labels
        self.figure.text(0.5, 0.02, 'Distancia desde Eje (m)', ha='center')
        self.figure.text(0.02, 0.5, 'Elevación (m)', va='center', rotation='vertical')
        
        self.figure.suptitle('Perfiles Topográficos Múltiples', fontsize=14)
        self.figure.tight_layout()
        self.canvas.draw()
    
    def plot_longitudinal_profile(self, profiles_data):
        """Plot longitudinal profile along the alignment
        
        Args:
            profiles_data: List of profile data dictionaries
        """
        if not HAS_MATPLOTLIB or not profiles_data:
            return
        
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        # Extract centerline elevations
        stations = []
        centerline_elevs = []
        
        for profile in profiles_data:
            pk_decimal = profile.get('pk_decimal', 0)
            
            # Get centerline elevation (middle of profile)
            elevations = profile.get('elevations', [])
            if elevations:
                # Find middle point (centerline)
                mid_idx = len(elevations) // 2
                if elevations[mid_idx] != -9999:
                    stations.append(pk_decimal)
                    centerline_elevs.append(elevations[mid_idx])
        
        if stations and centerline_elevs:
            # Plot longitudinal profile
            ax.plot(stations, centerline_elevs, 'b-o', linewidth=2, markersize=4, 
                   label='Perfil Longitudinal')
            
            # Add grid and labels
            ax.grid(True, alpha=0.3)
            ax.set_xlabel('Progresiva (m)')
            ax.set_ylabel('Elevación (m)')
            ax.set_title('Perfil Longitudinal del Eje')
            ax.legend()
            
            # Format x-axis with PK labels
            ax.set_xlim(0, max(stations))
            
            self.figure.tight_layout()
            self.canvas.draw()
    
    def export_plot(self, filename, dpi=300):
        """Export current plot to file
        
        Args:
            filename: Output filename
            dpi: Resolution for export
        """
        if HAS_MATPLOTLIB and hasattr(self, 'figure'):
            try:
                self.figure.savefig(filename, dpi=dpi, bbox_inches='tight')
                return True
            except Exception as e:
                if self.parent:
                    QMessageBox.warning(
                        self.parent,
                        "Error de Exportación",
                        f"No se pudo exportar la imagen: {str(e)}"
                    )
                return False
        return False