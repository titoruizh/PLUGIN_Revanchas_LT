# -*- coding: utf-8 -*-
"""
Alignment Data Module
Contains hardcoded alignment data for the walls
"""

import math


class AlignmentData:
    """Class to manage alignment data for retaining walls"""
    
    def __init__(self):
        # Hardcoded alignment data for Muro 1
        # This would normally come from Civil3D XML or other source
        self.alignments = {
            "Muro 1": self._create_muro1_alignment()
        }
    
    def _create_muro1_alignment(self):
        """Create alignment data for Muro 1 (PK 0+000 to 1+434, every 20m)"""
        
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
                'station_number': station_count
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
            'description': 'Alineación principal del Muro 1 - Las Tortolas'
        }
        
        return alignment
    
    def _format_pk(self, pk_decimal):
        """Format PK from decimal to string format (e.g., 0+000, 1+434)"""
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
    
    def get_cross_section_points(self, station, width=80.0, resolution=0.1):
        """Generate cross-section points perpendicular to alignment at station with high resolution
        
        Args:
            station: Station data dict
            width: Total width of cross-section (default 80m)
            resolution: Distance between points in meters (default 0.1m = 10cm)
            
        Returns:
            List of (x, y, offset) coordinates for cross-section
        """
        if not station:
            return []
        
        # Get station center point and bearing
        center_x = station['x']
        center_y = station['y']
        bearing_rad = math.radians(station['bearing'])
        
        # Calculate perpendicular direction
        perp_bearing = bearing_rad + math.pi / 2  # 90 degrees
        
        # 🚀 HIGH RESOLUTION: Generate points every 'resolution' meters
        points = []
        num_points = int(width / resolution) + 1  # Example: 801 points for 0.1m resolution
        
        for i in range(num_points):
            # Distance from center with high precision
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
            'interval': alignment['interval']
        }