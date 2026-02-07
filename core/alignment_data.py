# -*- coding: utf-8 -*-
"""
Alignment Data Module - Revanchas LT Plugin
Gestión de datos de alineación para muros de contención

Este módulo fue refactorizado para usar ConfigManager y logging estructurado.
"""

import math
import re
from typing import Dict, List, Optional, Tuple, Any

# Importar utilidades y configuración del plugin
try:
    from ..config import get_config
    from ..utils.logging_config import get_logger
except ImportError:
    # Fallback para ejecución directa
    get_config = None
    get_logger = lambda x: __import__('logging').getLogger(x)


logger = get_logger(__name__)


def heading_to_degrees(heading_str: str) -> Optional[float]:
    """
    Convierte string de heading a grados decimales.
    
    Args:
        heading_str: Formato "31° 38' 20.16879\""
        
    Returns:
        Grados decimales o None si es inválido
    """
    if not heading_str or heading_str == "---":
        return None
    
    match = re.match(r"(\d+)°\s*(\d+)'\s*(\d+\.?\d*)", heading_str)
    if match:
        deg = int(match.group(1))
        min_ = int(match.group(2))
        sec = float(match.group(3))
        return deg + min_/60 + sec/3600
    
    return None


def format_pk(pk_decimal: float) -> str:
    """
    Formatea un valor decimal de PK a formato estándar.
    
    Args:
        pk_decimal: Valor decimal (ej: 1434.5)
        
    Returns:
        String formateado (ej: "1+434")
    """
    km = int(pk_decimal // 1000)
    meters = pk_decimal % 1000
    return f"{km}+{meters:03.0f}"


def average_angles(angle1: float, angle2: float) -> float:
    """
    Promedia dos ángulos manejando correctamente el wrap-around.
    
    Args:
        angle1: Primer ángulo en grados
        angle2: Segundo ángulo en grados
        
    Returns:
        Ángulo promedio en grados
    """
    # Convertir a radianes
    a1_rad = math.radians(angle1)
    a2_rad = math.radians(angle2)
    
    # Convertir a vectores unitarios
    x1, y1 = math.cos(a1_rad), math.sin(a1_rad)
    x2, y2 = math.cos(a2_rad), math.sin(a2_rad)
    
    # Promediar vectores
    avg_x = (x1 + x2) / 2
    avg_y = (y1 + y2) / 2
    
    # Convertir de vuelta a ángulo
    avg_angle_rad = math.atan2(avg_y, avg_x)
    return math.degrees(avg_angle_rad)


class AlignmentData:
    """
    Clase para gestionar datos de alineación de muros de contención.
    
    Soporta alineaciones rectas (straight) y curvas (curved) con
    cálculo apropiado de tangentes para secciones transversales.
    """
    
    def __init__(self):
        """Inicializa los datos de alineación desde configuración."""
        self.alignments: Dict[str, Dict[str, Any]] = {}
        self._config = get_config() if get_config else None
        
        self._load_alignments()
        
        logger.info(f"AlignmentData inicializado con {len(self.alignments)} muros")
    
    def _load_alignments(self) -> None:
        """Carga las alineaciones desde configuración o datos hardcodeados."""
        # Intentar cargar desde ConfigManager
        if self._config:
            wall_names = self._config.get_wall_names()
            logger.debug(f"Muros disponibles en config: {wall_names}")
        
        # Por ahora, usar métodos de creación existentes
        # TODO: Migrar completamente a JSON cuando los datos de estaciones
        # estén externalizados
        self.alignments = {
            "Muro 1": self._create_muro1_alignment(),
            "Muro 2": self._create_muro2_alignment(),
            "Muro 3": self._create_muro3_alignment()
        }
    
    def _create_muro1_alignment(self) -> Dict[str, Any]:
        """
        Crea datos de alineación para Muro 1 (PK 0+000 a 1+434) - RECTO.
        
        Returns:
            Diccionario con datos de alineación
        """
        # Coordenadas reales del proyecto Las Tortolas
        start_x = 337997.913  # Coordenada UTM en PK 0+000
        start_y = 6334753.227
        end_x = 336688.230    # Coordenada UTM en PK 1+434
        end_y = 6334170.246
        
        # Calcular deltas para interpolación lineal
        delta_x = end_x - start_x
        delta_y = end_y - start_y
        
        # Calcular bearing constante para alineación recta
        bearing_rad = math.atan2(delta_y, delta_x)
        bearing = math.degrees(bearing_rad)
        
        stations: List[Dict[str, Any]] = []
        total_length = 1434.0
        interval = 20.0
        
        current_pk = 0.0
        station_count = 0
        
        logger.debug(f"Generando estaciones para Muro 1 (0 - {total_length}m)")
        
        while current_pk <= total_length:
            progress = current_pk / total_length
            
            x = start_x + progress * delta_x
            y = start_y + progress * delta_y
            
            station_data = {
                'pk': format_pk(current_pk),
                'pk_decimal': current_pk,
                'x': x,
                'y': y,
                'bearing': bearing,
                'elevation': 100.0 + progress * 20,
                'station_number': station_count,
                'alignment_type': 'straight'
            }
            
            stations.append(station_data)
            current_pk += interval
            station_count += 1
            
            if current_pk > total_length and stations[-1]['pk_decimal'] < total_length:
                current_pk = total_length
        
        logger.info(f"Muro 1: {len(stations)} estaciones generadas")
        
        return {
            'name': 'Muro 1',
            'start_pk': '0+000',
            'end_pk': '1+434',
            'total_length': total_length,
            'interval': interval,
            'stations': stations,
            'description': 'Alineación principal del Muro 1 - Las Tortolas',
            'alignment_type': 'straight'
        }
    
    def _create_muro2_alignment(self) -> Dict[str, Any]:
        """
        Crea datos de alineación para Muro 2 (Oeste) - CURVO.
        
        Returns:
            Diccionario con datos de alineación
        """
        csv_stations = [
            (1, 336193.0247, 6332549.931, 0.0, "31° 38' 20.16879\""),
            (2, 336203.2293, 6332567.132, 20.00138, "31° 38' 19.93323\""),
            (3, 336213.4338, 6332584.333, 40.00277, "31° 38' 19.69761\""),
            (4, 336223.6383, 6332601.533, 60.0042, "31° 38' 19.46207\""),
            (5, 336233.8428, 6332618.734, 80.0055, "31° 38' 19.22648\""),
            (6, 336244.0473, 6332635.935, 100.0069, "31° 38' 18.99092\""),
            (7, 336254.2518, 6332653.136, 120.0083, "31° 38' 18.75536\""),
            (8, 336264.4564, 6332670.337, 140.0097, "31° 38' 18.51976\""),
            (9, 336274.6609, 6332687.537, 160.0111, "31° 38' 18.28421\""),
            (10, 336284.8654, 6332704.738, 180.0125, "31° 38' 18.04853\""),
            (11, 336295.0699, 6332721.939, 200.0139, "31° 38' 17.81308\""),
            (12, 336305.2744, 6332739.14, 220.0153, "31° 09' 08.37437\""),
            (13, 336315.3316, 6332756.425, 240.0143, "23° 44' 03.00473\""),
            (14, 336323.0646, 6332774.843, 259.992, "14° 03' 40.65630\""),
            (15, 336327.5929, 6332794.3, 279.9696, "4° 23' 18.37456\""),
            (16, 336328.7878, 6332814.24, 299.9473, "354° 42' 56.16278\""),
            (17, 336326.6153, 6332834.098, 319.9249, "352° 00' 29.86720\""),
            (18, 336323.5037, 6332853.853, 339.9255, "351° 40' 15.09395\""),
            (19, 336320.2759, 6332873.589, 359.9251, "348° 52' 35.40728\""),
            (20, 336316.0895, 6332893.146, 379.9265, "348° 52' 35.47241\""),
            (21, 336311.903, 6332912.703, 399.9279, "348° 52' 35.53747\""),
            (22, 336307.7165, 6332932.26, 419.9293, "348° 52' 35.60252\""),
            (23, 336303.5301, 6332951.817, 439.9307, "348° 52' 35.66764\""),
            (24, 336299.3436, 6332971.374, 459.9321, "348° 52' 35.73267\""),
            (25, 336295.1571, 6332990.931, 479.9335, "348° 19' 00.75144\""),
            (26, 336290.7798, 6333010.446, 499.9349, "348° 17' 59.71255\""),
            (27, 336286.3967, 6333029.96, 519.936, "348° 17' 59.78187\""),
            (28, 336282.0136, 6333049.474, 539.938, "348° 17' 59.85113\""),
            (29, 336277.6305, 6333068.988, 559.939, "348° 17' 59.92038\""),
            (30, 336273.2474, 6333088.501, 579.94, "348° 17' 59.98964\""),
            (31, 336268.8643, 6333108.015, 599.942, "348° 18' 00.05891\""),
            (32, 336264.4812, 6333127.529, 619.943, "348° 18' 00.12818\""),
            (33, 336260.0981, 6333147.043, 639.945, "348° 18' 00.19741\""),
            (34, 336255.715, 6333166.557, 659.946, "348° 18' 00.26734\""),
            (35, 336251.3319, 6333186.07, 679.947, "348° 18' 00.34011\""),
            (36, 336249.1673, 6333195.707, 689.825, None),
        ]
        
        stations: List[Dict[str, Any]] = []
        interval = 20.0
        
        for idx, x, y, pk_decimal, heading_str in csv_stations:
            bearing = heading_to_degrees(heading_str) if heading_str else 0.0
            pk = format_pk(pk_decimal)
            
            station_data = {
                'pk': pk,
                'pk_decimal': pk_decimal,
                'x': x,
                'y': y,
                'bearing': bearing if bearing is not None else 0.0,
                'elevation': 100.0 + pk_decimal * 0.01,
                'station_number': idx - 1,
                'alignment_type': 'curved'
            }
            stations.append(station_data)
        
        # Calcular tangentes para curvas
        self._calculate_curve_tangents(stations)
        
        logger.info(f"Muro 2: {len(stations)} estaciones generadas (curvo)")
        
        return {
            'name': 'Muro 2',
            'start_pk': stations[0]['pk'],
            'end_pk': stations[-1]['pk'],
            'total_length': stations[-1]['pk_decimal'],
            'interval': interval,
            'stations': stations,
            'description': 'Alineación Muro Oeste (curva real)',
            'alignment_type': 'curved'
        }
    
    def _create_muro3_alignment(self) -> Dict[str, Any]:
        """
        Crea datos de alineación para Muro 3 (Este) - RECTO.
        
        Returns:
            Diccionario con datos de alineación
        """
        start_x = 340114.954
        start_y = 6333743.678
        end_x = 339816.955
        end_y = 6334206.922
        
        delta_x = end_x - start_x
        delta_y = end_y - start_y
        total_length = math.hypot(delta_x, delta_y)
        interval = 20.0
        
        bearing_rad = math.atan2(delta_y, delta_x)
        bearing = math.degrees(bearing_rad)
        
        stations: List[Dict[str, Any]] = []
        current_pk = 0.0
        station_count = 0
        
        while current_pk <= total_length:
            progress = current_pk / total_length
            x = start_x + progress * delta_x
            y = start_y + progress * delta_y
            
            station_data = {
                'pk': format_pk(current_pk),
                'pk_decimal': current_pk,
                'x': x,
                'y': y,
                'bearing': bearing,
                'elevation': 100.0 + progress * 8,
                'station_number': station_count,
                'alignment_type': 'straight'
            }
            stations.append(station_data)
            current_pk += interval
            station_count += 1
            
            if current_pk > total_length and stations[-1]['pk_decimal'] < total_length:
                current_pk = total_length
        
        logger.info(f"Muro 3: {len(stations)} estaciones generadas")
        
        return {
            'name': 'Muro 3',
            'start_pk': stations[0]['pk'],
            'end_pk': format_pk(total_length),
            'total_length': total_length,
            'interval': interval,
            'stations': stations,
            'description': 'Alineación Muro Este',
            'alignment_type': 'straight'
        }
    
    def _calculate_curve_tangents(self, stations: List[Dict[str, Any]]) -> None:
        """
        Calcula bearings tangentes suavizados para alineaciones curvas.
        
        Args:
            stations: Lista de estaciones a procesar
        """
        logger.debug(f"Calculando tangentes para {len(stations)} estaciones")
        
        for i, station in enumerate(stations):
            original_bearing = station['bearing']
            
            if i == 0:
                # Primera estación: usar dirección a siguiente
                next_station = stations[i + 1]
                dx = next_station['x'] - station['x']
                dy = next_station['y'] - station['y']
                tangent_bearing = math.degrees(math.atan2(dy, dx))
                
            elif i == len(stations) - 1:
                # Última estación: usar dirección desde anterior
                prev_station = stations[i - 1]
                dx = station['x'] - prev_station['x']
                dy = station['y'] - prev_station['y']
                tangent_bearing = math.degrees(math.atan2(dy, dx))
                
            else:
                # Estaciones intermedias: promedio de entrante y saliente
                prev_station = stations[i - 1]
                next_station = stations[i + 1]
                
                dx1 = station['x'] - prev_station['x']
                dy1 = station['y'] - prev_station['y']
                incoming_bearing = math.degrees(math.atan2(dy1, dx1))
                
                dx2 = next_station['x'] - station['x']
                dy2 = next_station['y'] - station['y']
                outgoing_bearing = math.degrees(math.atan2(dy2, dx2))
                
                tangent_bearing = average_angles(incoming_bearing, outgoing_bearing)
            
            station['bearing_original'] = original_bearing
            station['bearing_tangent'] = tangent_bearing
            
            logger.debug(
                f"Estación {i+1} ({station['pk']}): "
                f"Original={original_bearing:.2f}°, Tangente={tangent_bearing:.2f}°"
            )
    
    def get_alignment(self, wall_name: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene datos de alineación para un muro específico.
        
        Args:
            wall_name: Nombre del muro
            
        Returns:
            Diccionario con datos de alineación o None
        """
        return self.alignments.get(wall_name)
    
    def get_station_by_pk(self, 
                          wall_name: str, 
                          pk_decimal: float) -> Optional[Dict[str, Any]]:
        """
        Obtiene datos de estación por PK (metros decimales).
        
        Args:
            wall_name: Nombre del muro
            pk_decimal: PK en metros decimales
            
        Returns:
            Diccionario de estación más cercana o None
        """
        alignment = self.get_alignment(wall_name)
        if not alignment:
            return None
        
        min_diff = float('inf')
        closest_station = None
        
        for station in alignment['stations']:
            diff = abs(station['pk_decimal'] - pk_decimal)
            if diff < min_diff:
                min_diff = diff
                closest_station = station
        
        return closest_station
    
    def get_cross_section_points(self, 
                                  station: Dict[str, Any], 
                                  width: float = 140.0, 
                                  resolution: float = 1.0) -> List[Tuple[float, float, float]]:
        """
        Genera puntos de sección transversal perpendicular a la alineación.
        
        Args:
            station: Diccionario de datos de estación
            width: Ancho total de sección (default 140m = ±70m)
            resolution: Distancia entre puntos en metros
            
        Returns:
            Lista de tuplas (x, y, offset) para la sección transversal
        """
        if not station:
            return []
        
        center_x = station['x']
        center_y = station['y']
        
        alignment_type = station.get('alignment_type', 'straight')
        
        if alignment_type == 'curved' and 'bearing_tangent' in station:
            bearing_rad = math.radians(station['bearing_tangent'])
            logger.debug(
                f"Usando bearing tangente {station['bearing_tangent']:.2f}° "
                f"para alineación curva"
            )
        else:
            bearing_rad = math.radians(station['bearing'])
            logger.debug(
                f"Usando bearing original {station['bearing']:.2f}° "
                f"para alineación recta"
            )
        
        # Dirección perpendicular (rotación 90°)
        perp_bearing = bearing_rad + math.pi / 2
        
        points: List[Tuple[float, float, float]] = []
        num_points = int(width / resolution) + 1
        
        for i in range(num_points):
            distance = -width/2 + (i * resolution)
            
            x = center_x + distance * math.cos(perp_bearing)
            y = center_y + distance * math.sin(perp_bearing)
            
            points.append((x, y, distance))
        
        return points
    
    def get_available_walls(self) -> List[str]:
        """Obtiene lista de nombres de muros disponibles."""
        return list(self.alignments.keys())
    
    def get_wall_summary(self, wall_name: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene información resumida de un muro.
        
        Args:
            wall_name: Nombre del muro
            
        Returns:
            Diccionario con resumen o None
        """
        alignment = self.get_alignment(wall_name)
        if not alignment:
            return None
        
        return {
            'name': alignment['name'],
            'length': alignment['total_length'],
            'stations': len(alignment['stations']),
            'start_pk': alignment['start_pk'],
            'end_pk': alignment['end_pk'],
            'interval': alignment['interval'],
            'alignment_type': alignment.get('alignment_type', 'unknown')
        }