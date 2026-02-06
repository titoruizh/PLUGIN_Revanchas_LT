# -*- coding: utf-8 -*-
"""
Measurement Controller Module - Revanchas LT Plugin
Gestiona la lógica de medición de perfiles topográficos

Este módulo fue extraído de profile_viewer_dialog.py para mejorar
la modularidad y mantenibilidad del código.
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from qgis.PyQt.QtCore import QObject, pyqtSignal


class MeasurementMode(Enum):
    """Modos de medición disponibles."""
    NONE = "none"
    CROWN = "crown"       # Cota de coronamiento
    WIDTH = "width"       # Ancho
    LAMA = "lama"         # Modificar LAMA


class OperationMode(Enum):
    """Modos de operación del visor."""
    REVANCHA = "revancha"
    ANCHO_PROYECTADO = "ancho_proyectado"


@dataclass
class MeasurementPoint:
    """Punto de medición."""
    x: float
    y: float
    label: Optional[str] = None


@dataclass
class WidthMeasurement:
    """Medición de ancho."""
    start_x: float
    end_x: float
    y: float
    distance: float
    
    @classmethod
    def from_points(cls, p1: Tuple[float, float], p2: Tuple[float, float]) -> 'WidthMeasurement':
        """Crea medición desde dos puntos."""
        return cls(
            start_x=min(p1[0], p2[0]),
            end_x=max(p1[0], p2[0]),
            y=(p1[1] + p2[1]) / 2,
            distance=abs(p2[0] - p1[0])
        )


@dataclass
class ProfileMeasurements:
    """Mediciones completas para un perfil."""
    pk: str
    crown: Optional[MeasurementPoint] = None
    width: Optional[WidthMeasurement] = None
    lama_modified: Optional[MeasurementPoint] = None
    lama_original: Optional[float] = None
    revancha: Optional[float] = None
    
    def calculate_revancha(self) -> Optional[float]:
        """Calcula la revancha (diferencia entre coronamiento y LAMA)."""
        if self.crown is None:
            return None
        
        lama_y = None
        if self.lama_modified:
            lama_y = self.lama_modified.y
        elif self.lama_original:
            lama_y = self.lama_original
        
        if lama_y is not None:
            self.revancha = self.crown.y - lama_y
            return self.revancha
        
        return None


class MeasurementController(QObject):
    """
    Controla la lógica de mediciones de perfiles.
    
    Signals:
        measurement_changed: Emitido cuando cambia una medición
        mode_changed: Emitido cuando cambia el modo de medición
        operation_mode_changed: Emitido cuando cambia el modo de operación
    """
    
    measurement_changed = pyqtSignal(str, str)  # (pk, measurement_type)
    mode_changed = pyqtSignal(str)  # (new_mode)
    operation_mode_changed = pyqtSignal(str)  # (new_operation_mode)
    
    def __init__(self, parent=None):
        """Inicializa el controlador de mediciones."""
        super().__init__(parent)
        
        # Estado de medición
        self.measurement_mode: MeasurementMode = MeasurementMode.NONE
        self.operation_mode: OperationMode = OperationMode.REVANCHA
        
        # Auto-detección
        self.auto_width_detection = True
        
        # Mediciones temporales (no guardadas)
        self.current_crown_point: Optional[Tuple[float, float]] = None
        self.current_width_points: List[Tuple[float, float]] = []
        
        # Mediciones guardadas por PK
        self.saved_measurements: Dict[str, ProfileMeasurements] = {}
    
    def set_measurement_mode(self, mode: str) -> None:
        """
        Establece el modo de medición actual.
        
        Args:
            mode: 'crown', 'width', 'lama', o None
        """
        if mode == 'crown':
            self.measurement_mode = MeasurementMode.CROWN
        elif mode == 'width':
            self.measurement_mode = MeasurementMode.WIDTH
            self.current_width_points = []  # Reset puntos de ancho
        elif mode == 'lama':
            self.measurement_mode = MeasurementMode.LAMA
        else:
            self.measurement_mode = MeasurementMode.NONE
        
        self.mode_changed.emit(self.measurement_mode.value)
    
    def set_operation_mode(self, mode: str) -> None:
        """
        Cambia el modo de operación.
        
        Args:
            mode: 'revancha' o 'ancho_proyectado'
        """
        if mode == 'ancho_proyectado':
            self.operation_mode = OperationMode.ANCHO_PROYECTADO
        else:
            self.operation_mode = OperationMode.REVANCHA
        
        # Resetear modo de medición al cambiar operación
        self.set_measurement_mode(None)
        self.operation_mode_changed.emit(self.operation_mode.value)
    
    def toggle_operation_mode(self) -> str:
        """
        Alterna entre modos de operación.
        
        Returns:
            Nuevo modo de operación
        """
        if self.operation_mode == OperationMode.REVANCHA:
            self.set_operation_mode('ancho_proyectado')
        else:
            self.set_operation_mode('revancha')
        
        return self.operation_mode.value
    
    def toggle_auto_detection(self) -> bool:
        """
        Alterna la auto-detección de ancho.
        
        Returns:
            Nuevo estado de auto-detección
        """
        self.auto_width_detection = not self.auto_width_detection
        return self.auto_width_detection
    
    def set_crown_point(self, pk: str, x: float, y: float) -> None:
        """
        Establece el punto de coronamiento para un PK.
        
        Args:
            pk: Identificador del perfil
            x: Coordenada X
            y: Coordenada Y (elevación)
        """
        self.current_crown_point = (x, y)
        
        # Guardar en mediciones
        if pk not in self.saved_measurements:
            self.saved_measurements[pk] = ProfileMeasurements(pk=pk)
        
        self.saved_measurements[pk].crown = MeasurementPoint(x=x, y=y)
        
        # Recalcular revancha si hay LAMA
        self.saved_measurements[pk].calculate_revancha()
        
        self.measurement_changed.emit(pk, 'crown')
    
    def add_width_point(self, pk: str, x: float, y: float) -> Optional[WidthMeasurement]:
        """
        Añade un punto de medición de ancho.
        
        Args:
            pk: Identificador del perfil
            x: Coordenada X
            y: Coordenada Y
            
        Returns:
            WidthMeasurement si se completó la medición (2 puntos)
        """
        self.current_width_points.append((x, y))
        
        if len(self.current_width_points) >= 2:
            # Completar medición
            p1, p2 = self.current_width_points[0], self.current_width_points[1]
            width = WidthMeasurement.from_points(p1, p2)
            
            # Guardar
            if pk not in self.saved_measurements:
                self.saved_measurements[pk] = ProfileMeasurements(pk=pk)
            
            self.saved_measurements[pk].width = width
            
            # Reset puntos temporales
            self.current_width_points = []
            
            self.measurement_changed.emit(pk, 'width')
            return width
        
        return None
    
    def set_lama_point(self, pk: str, x: float, y: float) -> None:
        """
        Establece el punto LAMA modificado para un PK.
        
        Args:
            pk: Identificador del perfil
            x: Coordenada X
            y: Coordenada Y (elevación)
        """
        if pk not in self.saved_measurements:
            self.saved_measurements[pk] = ProfileMeasurements(pk=pk)
        
        self.saved_measurements[pk].lama_modified = MeasurementPoint(x=x, y=y)
        
        # Recalcular revancha
        self.saved_measurements[pk].calculate_revancha()
        
        self.measurement_changed.emit(pk, 'lama')
    
    def set_original_lama(self, pk: str, elevation: float) -> None:
        """
        Establece la elevación LAMA original (del DEM) para un PK.
        
        Args:
            pk: Identificador del perfil
            elevation: Elevación LAMA del DEM
        """
        if pk not in self.saved_measurements:
            self.saved_measurements[pk] = ProfileMeasurements(pk=pk)
        
        self.saved_measurements[pk].lama_original = elevation
        
        # Recalcular revancha si no hay LAMA modificado
        if self.saved_measurements[pk].lama_modified is None:
            self.saved_measurements[pk].calculate_revancha()
    
    def get_measurements(self, pk: str) -> Optional[ProfileMeasurements]:
        """
        Obtiene las mediciones de un PK.
        
        Args:
            pk: Identificador del perfil
            
        Returns:
            ProfileMeasurements o None
        """
        return self.saved_measurements.get(pk)
    
    def has_measurements(self, pk: str) -> bool:
        """Verifica si un PK tiene mediciones guardadas."""
        if pk not in self.saved_measurements:
            return False
        
        m = self.saved_measurements[pk]
        return m.crown is not None or m.width is not None or m.lama_modified is not None
    
    def clear_measurements(self, pk: str) -> None:
        """
        Limpia todas las mediciones de un PK.
        
        Args:
            pk: Identificador del perfil
        """
        if pk in self.saved_measurements:
            del self.saved_measurements[pk]
        
        self.current_crown_point = None
        self.current_width_points = []
        
        self.measurement_changed.emit(pk, 'cleared')
    
    def clear_all_measurements(self) -> None:
        """Limpia todas las mediciones."""
        self.saved_measurements.clear()
        self.current_crown_point = None
        self.current_width_points = []
    
    def get_all_measurements_dict(self) -> Dict[str, Any]:
        """
        Obtiene todas las mediciones en formato diccionario.
        
        Returns:
            Diccionario compatible con formato de proyecto
        """
        result = {}
        
        for pk, measurements in self.saved_measurements.items():
            result[pk] = {}
            
            if measurements.crown:
                result[pk]['crown'] = {
                    'x': measurements.crown.x,
                    'y': measurements.crown.y
                }
            
            if measurements.width:
                result[pk]['width'] = {
                    'start_x': measurements.width.start_x,
                    'end_x': measurements.width.end_x,
                    'y': measurements.width.y,
                    'distance': measurements.width.distance
                }
            
            if measurements.lama_modified:
                result[pk]['lama_modified'] = {
                    'x': measurements.lama_modified.x,
                    'y': measurements.lama_modified.y
                }
            
            if measurements.revancha is not None:
                result[pk]['revancha'] = measurements.revancha
        
        return {
            'saved_measurements': result,
            'operation_mode': self.operation_mode.value,
            'auto_detection_enabled': self.auto_width_detection
        }
    
    def restore_measurements(self, data: Dict[str, Any]) -> None:
        """
        Restaura mediciones desde un diccionario (formato proyecto).
        
        Args:
            data: Diccionario con mediciones guardadas
        """
        self.saved_measurements.clear()
        
        # Manejar formato nuevo o legacy
        saved = data.get('saved_measurements', data)
        
        for pk, m_data in saved.items():
            if not isinstance(m_data, dict):
                continue
            
            measurements = ProfileMeasurements(pk=pk)
            
            if 'crown' in m_data:
                crown_data = m_data['crown']
                measurements.crown = MeasurementPoint(
                    x=crown_data.get('x', 0),
                    y=crown_data.get('y', 0)
                )
            
            if 'width' in m_data:
                width_data = m_data['width']
                measurements.width = WidthMeasurement(
                    start_x=width_data.get('start_x', 0),
                    end_x=width_data.get('end_x', 0),
                    y=width_data.get('y', 0),
                    distance=width_data.get('distance', 0)
                )
            
            if 'lama_modified' in m_data:
                lama_data = m_data['lama_modified']
                measurements.lama_modified = MeasurementPoint(
                    x=lama_data.get('x', 0),
                    y=lama_data.get('y', 0)
                )
            
            if 'revancha' in m_data:
                measurements.revancha = m_data['revancha']
            else:
                measurements.calculate_revancha()
            
            self.saved_measurements[pk] = measurements
        
        # Restaurar modo de operación
        if 'operation_mode' in data:
            self.set_operation_mode(data['operation_mode'])
        
        if 'auto_detection_enabled' in data:
            self.auto_width_detection = data['auto_detection_enabled']
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de las mediciones.
        
        Returns:
            Diccionario con estadísticas
        """
        total = len(self.saved_measurements)
        with_crown = sum(1 for m in self.saved_measurements.values() if m.crown is not None)
        with_width = sum(1 for m in self.saved_measurements.values() if m.width is not None)
        with_lama = sum(1 for m in self.saved_measurements.values() if m.lama_modified is not None)
        with_revancha = sum(1 for m in self.saved_measurements.values() if m.revancha is not None)
        
        return {
            'total_profiles': total,
            'with_crown': with_crown,
            'with_width': with_width,
            'with_lama': with_lama,
            'with_revancha': with_revancha,
            'completion_rate': with_crown / max(total, 1) * 100
        }
