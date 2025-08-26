# -*- coding: utf-8 -*-
"""
Alignment Data Module - IMPROVED FOR CURVED ALIGNMENTS
Contains hardcoded alignment data for the walls with proper curve handling
"""

import math

class AlignmentData:
    """Class to manage alignment data for retaining walls with proper curve support"""
    
    def __init__(self):
        self.alignments = {
            "Muro 1": self._create_muro1_alignment(),
            "Muro 2": self._create_muro2_alignment(),
            "Muro 3": self._create_muro3_alignment()
        }
    
    def _create_muro1_alignment(self):
        """Create alignment data for Muro 1 (PK 0+000 to 1+434, every 20m) - STRAIGHT"""
        
        # Real project coordinates from Las Tortolas project
        start_x = 337997.913  # UTM coordinate at PK 0+000
        start_y = 6334753.227  # UTM coordinate at PK 0+000
        end_x = 336688.230    # UTM coordinate at PK 1+434
        end_y = 6334170.246   # UTM coordinate at PK 1+434
        
        # Calculate deltas for linear interpolation
        delta_x = end_x - start_x  # -1309.691
        delta_y = end_y - start_y  # -582.964
        
        # Calculate constant bearing for straight line alignment
        bearing_rad = math.atan2(delta_y, delta_x)
        bearing = math.degrees(bearing_rad)  # Mathematical bearing (counterclockwise from +X)
        
        stations = []
        total_length = 1434.0  # meters
        interval = 20.0  # meters
        
        # Generate stations every 20m, plus the exact endpoint
        current_pk = 0.0
        station_count = 0
        
        while current_pk <= total_length:
            # Progress along alignment (0 to 1)
            progress = current_pk / total_length
            
            # Linear interpolation between start and end points
            x = start_x + progress * delta_x
            y = start_y + progress * delta_y
            
            station_data = {
                'pk': self._format_pk(current_pk),
                'pk_decimal': current_pk,
                'x': x,
                'y': y,
                'bearing': bearing,  # degrees from north (mathematical angle)
                'elevation': 100.0 + progress * 20,  # approximate reference elevation
                'station_number': station_count,
                'alignment_type': 'straight'  # NEW: alignment type
            }
            
            stations.append(station_data)
            
            # Move to next station
            current_pk += interval
            station_count += 1
            
            # Special case: if we've passed the total length but haven't reached exactly 1434,
            # add the final station at exactly PK 1+434
            if current_pk > total_length and stations[-1]['pk_decimal'] < total_length:
                current_pk = total_length  # Set to exactly 1434
                # Don't increment station_count yet - will be done at the start of next iteration
        
        alignment = {
            'name': 'Muro 1',
            'start_pk': '0+000',
            'end_pk': '1+434',
            'total_length': total_length,
            'interval': interval,
            'stations': stations,
            'description': 'Alineación principal del Muro 1 - Las Tortolas',
            'alignment_type': 'straight'
        }
        
        return alignment

    def _create_muro2_alignment(self):
        """
        Create alignment data for Muro 2 (Oeste) - CURVED ALIGNMENT with proper tangent calculation
        """
        def heading_to_degrees(heading_str):
            # Convierte string tipo "31° 38' 20.16879\"" a grados decimales
            import re
            match = re.match(r"(\d+)°\s*(\d+)'[\s]*(\d+\.\d+)", heading_str)
            if match:
                deg = int(match.group(1))
                min_ = int(match.group(2))
                sec = float(match.group(3))
                return deg + min_/60 + sec/3600
            else:
                # Si es "---", retorna None
                return None

        csv_stations = [
            # idx, x, y, pk_decimal, heading (en grados decimales)
            (1, 336193.0247, 6332549.931, 0.0, heading_to_degrees("31° 38' 20.16879\"")),
            (2, 336203.2293, 6332567.132, 20.00138, heading_to_degrees("31° 38' 19.93323\"")),
            (3, 336213.4338, 6332584.333, 40.00277, heading_to_degrees("31° 38' 19.69761\"")),
            (4, 336223.6383, 6332601.533, 60.0042, heading_to_degrees("31° 38' 19.46207\"")),
            (5, 336233.8428, 6332618.734, 80.0055, heading_to_degrees("31° 38' 19.22648\"")),
            (6, 336244.0473, 6332635.935, 100.0069, heading_to_degrees("31° 38' 18.99092\"")),
            (7, 336254.2518, 6332653.136, 120.0083, heading_to_degrees("31° 38' 18.75536\"")),
            (8, 336264.4564, 6332670.337, 140.0097, heading_to_degrees("31° 38' 18.51976\"")),
            (9, 336274.6609, 6332687.537, 160.0111, heading_to_degrees("31° 38' 18.28421\"")),
            (10, 336284.8654, 6332704.738, 180.0125, heading_to_degrees("31° 38' 18.04853\"")),
            (11, 336295.0699, 6332721.939, 200.0139, heading_to_degrees("31° 38' 17.81308\"")),
            (12, 336305.2744, 6332739.14, 220.0153, heading_to_degrees("31° 09' 08.37437\"")),
            (13, 336315.3316, 6332756.425, 240.0143, heading_to_degrees("23° 44' 03.00473\"")),
            (14, 336323.0646, 6332774.843, 259.992, heading_to_degrees("14° 03' 40.65630\"")),
            (15, 336327.5929, 6332794.3, 279.9696, heading_to_degrees("4° 23' 18.37456\"")),
            (16, 336328.7878, 6332814.24, 299.9473, heading_to_degrees("354° 42' 56.16278\"")),
            (17, 336326.6153, 6332834.098, 319.9249, heading_to_degrees("352° 00' 29.86720\"")),
            (18, 336323.5037, 6332853.853, 339.9255, heading_to_degrees("351° 40' 15.09395\"")),
            (19, 336320.2759, 6332873.589, 359.9251, heading_to_degrees("348° 52' 35.40728\"")),
            (20, 336316.0895, 6332893.146, 379.9265, heading_to_degrees("348° 52' 35.47241\"")),
            (21, 336311.903, 6332912.703, 399.9279, heading_to_degrees("348° 52' 35.53747\"")),
            (22, 336307.7165, 6332932.26, 419.9293, heading_to_degrees("348° 52' 35.60252\"")),
            (23, 336303.5301, 6332951.817, 439.9307, heading_to_degrees("348° 52' 35.66764\"")),
            (24, 336299.3436, 6332971.374, 459.9321, heading_to_degrees("348° 52' 35.73267\"")),
            (25, 336295.1571, 6332990.931, 479.9335, heading_to_degrees("348° 19' 00.75144\"")),
            (26, 336290.7798, 6333010.446, 499.9349, heading_to_degrees("348° 17' 59.71255\"")),
            (27, 336286.3967, 6333029.96, 519.936, heading_to_degrees("348° 17' 59.78187\"")),
            (28, 336282.0136, 6333049.474, 539.938, heading_to_degrees("348° 17' 59.85113\"")),
            (29, 336277.6305, 6333068.988, 559.939, heading_to_degrees("348° 17' 59.92038\"")),
            (30, 336273.2474, 6333088.501, 579.94, heading_to_degrees("348° 17' 59.98964\"")),
            (31, 336268.8643, 6333108.015, 599.942, heading_to_degrees("348° 18' 00.05891\"")),
            (32, 336264.4812, 6333127.529, 619.943, heading_to_degrees("348° 18' 00.12818\"")),
            (33, 336260.0981, 6333147.043, 639.945, heading_to_degrees("348° 18' 00.19741\"")),
            (34, 336255.715, 6333166.557, 659.946, heading_to_degrees("348° 18' 00.26734\"")),
            (35, 336251.3319, 6333186.07, 679.947, heading_to_degrees("348° 18' 00.34011\"")),
            (36, 336249.1673, 6333195.707, 689.825, None),
        ]

        stations = []
        interval = 20.0  # Casi todos son 20m salvo algunos, pero se usa para info

        for idx, x, y, pk_decimal, bearing in csv_stations:
            pk = self._format_pk(pk_decimal)
            station_data = {
                'pk': pk,
                'pk_decimal': pk_decimal,
                'x': x,
                'y': y,
                'bearing': bearing if bearing is not None else 0.0,  # Si no hay, pon 0.0
                'elevation': 100.0 + pk_decimal * 0.01,  # valor referencial, modificar si tienes elevación real
                'station_number': idx - 1,
                'alignment_type': 'curved'  # NEW: alignment type
            }
            stations.append(station_data)

        # 🆕 CALCULATE TANGENT BEARINGS for smooth curve transitions
        self._calculate_curve_tangents(stations)

        alignment = {
            'name': 'Muro 2',
            'start_pk': stations[0]['pk'],
            'end_pk': stations[-1]['pk'],
            'total_length': stations[-1]['pk_decimal'],
            'interval': interval,
            'stations': stations,
            'description': 'Alineación Muro Oeste (curva real)',
            'alignment_type': 'curved'
        }
        return alignment

    def _create_muro3_alignment(self):
        """Create alignment data for Muro 3 (Este) - STRAIGHT"""
        import math

        start_x = 340114.954
        start_y = 6333743.678
        end_x = 339816.955
        end_y = 6334206.922

        # Calcula la longitud real entre los puntos
        delta_x = end_x - start_x
        delta_y = end_y - start_y
        total_length = math.hypot(delta_x, delta_y)

        interval = 20.0  # metros entre estaciones

        bearing_rad = math.atan2(delta_y, delta_x)
        bearing = math.degrees(bearing_rad)

        stations = []
        current_pk = 0.0
        station_count = 0

        # Genera las estaciones cada 20m hasta el punto final
        while current_pk <= total_length:
            progress = current_pk / total_length
            x = start_x + progress * delta_x
            y = start_y + progress * delta_y

            station_data = {
                'pk': self._format_pk(current_pk),
                'pk_decimal': current_pk,
                'x': x,
                'y': y,
                'bearing': bearing,
                'elevation': 100.0 + progress * 8,  # Elevación referencial, ajusta si tienes datos reales
                'station_number': station_count,
                'alignment_type': 'straight'  # NEW: alignment type
            }
            stations.append(station_data)
            current_pk += interval
            station_count += 1

            # Agrega el último punto si no cayó justo
            if current_pk > total_length and stations[-1]['pk_decimal'] < total_length:
                current_pk = total_length

        alignment = {
            'name': 'Muro 3',
            'start_pk': stations[0]['pk'],
            'end_pk': self._format_pk(total_length),
            'total_length': total_length,
            'interval': interval,
            'stations': stations,
            'description': 'Alineación Muro Este',
            'alignment_type': 'straight'
        }
        return alignment

    def _calculate_curve_tangents(self, stations):
        """
        🆕 NEW METHOD: Calculate smooth tangent bearings for curved alignments
        This ensures perpendicular cross-sections are properly oriented
        """
        print(f"🔧 Calculating tangent bearings for {len(stations)} stations...")
        
        for i, station in enumerate(stations):
            original_bearing = station['bearing']
            
            if i == 0:
                # First station: use direction to next station
                next_station = stations[i + 1]
                dx = next_station['x'] - station['x']
                dy = next_station['y'] - station['y']
                tangent_bearing = math.degrees(math.atan2(dy, dx))
                
            elif i == len(stations) - 1:
                # Last station: use direction from previous station
                prev_station = stations[i - 1]
                dx = station['x'] - prev_station['x']
                dy = station['y'] - prev_station['y']
                tangent_bearing = math.degrees(math.atan2(dy, dx))
                
            else:
                # Middle stations: average of incoming and outgoing directions
                prev_station = stations[i - 1]
                next_station = stations[i + 1]
                
                # Incoming direction (from previous)
                dx1 = station['x'] - prev_station['x']
                dy1 = station['y'] - prev_station['y']
                incoming_bearing = math.degrees(math.atan2(dy1, dx1))
                
                # Outgoing direction (to next)
                dx2 = next_station['x'] - station['x']
                dy2 = next_station['y'] - station['y']
                outgoing_bearing = math.degrees(math.atan2(dy2, dx2))
                
                # Average the bearings (handle angle wrap-around)
                tangent_bearing = self._average_angles(incoming_bearing, outgoing_bearing)
            
            # Store both original and calculated tangent bearing
            station['bearing_original'] = original_bearing
            station['bearing_tangent'] = tangent_bearing  # This will be used for cross-sections
            
            print(f"  Station {i+1} ({station['pk']}): Original={original_bearing:.2f}°, Tangent={tangent_bearing:.2f}°")

    def _average_angles(self, angle1, angle2):
        """Average two angles handling wrap-around correctly"""
        # Convert to radians
        a1_rad = math.radians(angle1)
        a2_rad = math.radians(angle2)
        
        # Convert to unit vectors
        x1, y1 = math.cos(a1_rad), math.sin(a1_rad)
        x2, y2 = math.cos(a2_rad), math.sin(a2_rad)
        
        # Average the vectors
        avg_x = (x1 + x2) / 2
        avg_y = (y1 + y2) / 2
        
        # Convert back to angle
        avg_angle_rad = math.atan2(avg_y, avg_x)
        return math.degrees(avg_angle_rad)

    def _format_pk(self, pk_decimal):
        km = int(pk_decimal // 1000)
        meters = pk_decimal % 1000
        return f"{km}+{meters:03.0f}"
    
    def get_alignment(self, wall_name):
        """Get alignment data for specified wall"""
        return self.alignments.get(wall_name)
    
    def get_station_by_pk(self, wall_name, pk_decimal):
        """Get station data by PK (decimal meters)"""
        alignment = self.get_alignment(wall_name)
        if not alignment:
            return None
            
        # Find closest station
        min_diff = float('inf')
        closest_station = None
        
        for station in alignment['stations']:
            diff = abs(station['pk_decimal'] - pk_decimal)
            if diff < min_diff:
                min_diff = diff
                closest_station = station
        
        return closest_station
    
    def get_cross_section_points(self, station, width=80.0, resolution=1.0):
        """
        🔧 IMPROVED: Generate cross-section points perpendicular to alignment with proper curve handling
        
        Args:
            station: Station data dict
            width: Total width of cross-section (default 80m)
            resolution: Distance between points in meters (default 1.0m)
            
        Returns:
            List of (x, y, offset) coordinates for cross-section
        """
        if not station:
            return []
        
        # Get station center point
        center_x = station['x']
        center_y = station['y']
        
        # 🆕 IMPROVED: Use tangent bearing for curved alignments
        alignment_type = station.get('alignment_type', 'straight')
        
        if alignment_type == 'curved' and 'bearing_tangent' in station:
            # Use calculated tangent bearing for smooth curves
            bearing_rad = math.radians(station['bearing_tangent'])
            print(f"🔧 Using tangent bearing {station['bearing_tangent']:.2f}° for curved alignment")
        else:
            # Use original bearing for straight alignments
            bearing_rad = math.radians(station['bearing'])
            print(f"📏 Using original bearing {station['bearing']:.2f}° for straight alignment")
        
        # Calculate perpendicular direction (90° rotation)
        perp_bearing = bearing_rad + math.pi / 2  # 90 degrees counterclockwise
        
        # Generate points with specified resolution
        points = []
        num_points = int(width / resolution) + 1  # e.g., 81 points for 1m resolution over 80m
        
        for i in range(num_points):
            # Distance from center with specified resolution
            distance = -width/2 + (i * resolution)
            
            # Calculate point coordinates
            x = center_x + distance * math.cos(perp_bearing)
            y = center_y + distance * math.sin(perp_bearing)
            
            points.append((x, y, distance))  # Include offset distance
        
        return points
    
    def get_available_walls(self):
        """Get list of available wall names"""
        return list(self.alignments.keys())
    
    def get_wall_summary(self, wall_name):
        """Get summary information for a wall"""
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
            'alignment_type': alignment.get('alignment_type', 'unknown')  # NEW
        }