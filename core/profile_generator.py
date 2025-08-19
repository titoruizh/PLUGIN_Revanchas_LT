# -*- coding: utf-8 -*-
"""
Profile Generator Module
Generates topographic profiles along alignment
"""

import math

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

from .dem_processor import DEMProcessor
from .alignment_data import AlignmentData


class ProfileGenerator:
    """Class to generate topographic profiles"""
    
    def __init__(self):
        self.dem_processor = DEMProcessor()
        self.alignment_data = AlignmentData()
        
    def generate_profiles(self, dem_data, alignment, progress_callback=None, resolution=0.1, wall_name=None):
        """Generate all profiles for the alignment (high resolution) with lama points"""
        from .lama_points import LamaPointsManager
        
        profiles = []
        total_stations = len(alignment['stations'])
        
        # Initialize lama points manager if wall_name provided
        lama_manager = None
        wall_lama_points = []
        
        if wall_name:
            try:
                lama_manager = LamaPointsManager()
                # Extract elevations for lama points from DEM
                lama_manager.extract_elevations_from_dem(wall_name, self.dem_processor, dem_data)
                wall_lama_points = lama_manager.get_lama_points(wall_name)
                print(f"✅ Found {len(wall_lama_points)} lama points for {wall_name}")
            except Exception as e:
                print(f"⚠️ Error loading lama points: {e}")
                wall_lama_points = []
        
        for i, station in enumerate(alignment['stations']):
            if progress_callback:
                progress = i / total_stations
                progress_callback(progress)
            
            # Generate cross-section points (high resolution)
            cross_section_points = self.alignment_data.get_cross_section_points(
                station, width=80.0, resolution=resolution
            )
            
            elevations = []
            distances = []
            coordinates = []
            
            for point in cross_section_points:
                x, y, offset = point
                elevation = self.dem_processor.get_elevation_at_point(x, y, dem_data)
                
                elevations.append(elevation)
                distances.append(offset)
                coordinates.append((x, y))
            
            profile = {
                'station': station,
                'pk': station['pk'],
                'pk_decimal': station['pk_decimal'],
                'centerline_x': station['x'],
                'centerline_y': station['y'],
                'bearing': station['bearing'],
                'distances': distances,
                'elevations': elevations,
                'coordinates': coordinates,
                'width': 80.0,
                'resolution': resolution,
                'total_points': len(distances),
                'valid_points': len([e for e in elevations if e != dem_data['header'].get('nodata_value', -9999)])
            }
            
            # 🆕 ADD LAMA POINTS TO PROFILE
            if wall_lama_points and lama_manager:
                profile_lama_points = lama_manager.find_lama_by_profile_number(profile, wall_lama_points)
                profile['lama_points'] = profile_lama_points
            else:
                profile['lama_points'] = []
            
            # Calculate elevation statistics
            valid_elevations = [e for e in elevations if e != dem_data['header'].get('nodata_value', -9999)]
            if valid_elevations:
                profile['min_elevation'] = min(valid_elevations)
                profile['max_elevation'] = max(valid_elevations)
                profile['avg_elevation'] = sum(valid_elevations) / len(valid_elevations)
                profile['elevation_range'] = profile['max_elevation'] - profile['min_elevation']
            else:
                profile['min_elevation'] = None
                profile['max_elevation'] = None
                profile['avg_elevation'] = None
                profile['elevation_range'] = None
            
            profiles.append(profile)
        
        if progress_callback:
            progress_callback(1.0)
        
        return profiles
    
    def generate_single_profile(self, dem_data, station, width=80.0, resolution=0.1):
        """Generate a single high-res profile"""
        cross_section_points = self.alignment_data.get_cross_section_points(
            station, width=width, resolution=resolution
        )
        
        elevations = []
        distances = []
        coordinates = []
        
        for point in cross_section_points:
            x, y, offset = point
            elevation = self.dem_processor.get_elevation_at_point(x, y, dem_data)
            elevations.append(elevation)
            distances.append(offset)
            coordinates.append((x, y))
        
        profile = {
            'station': station,
            'pk': station['pk'],
            'pk_decimal': station['pk_decimal'],
            'centerline_x': station['x'],
            'centerline_y': station['y'],
            'bearing': station['bearing'],
            'distances': distances,
            'elevations': elevations,
            'coordinates': coordinates,
            'width': width,
            'resolution': resolution,
            'total_points': len(distances),
            'valid_points': len([e for e in elevations if e != dem_data['header'].get('nodata_value', -9999)])
        }
        
        valid_elevations = [e for e in elevations if e != dem_data['header'].get('nodata_value', -9999)]
        if valid_elevations:
            profile['min_elevation'] = min(valid_elevations)
            profile['max_elevation'] = max(valid_elevations)
            profile['avg_elevation'] = sum(valid_elevations) / len(valid_elevations)
            profile['elevation_range'] = profile['max_elevation'] - profile['min_elevation']
        else:
            profile['min_elevation'] = None
            profile['max_elevation'] = None
            profile['avg_elevation'] = None
            profile['elevation_range'] = None
        
        return profile
    
    def export_profiles_to_csv(self, profiles, output_path):
        """Export profile data to CSV file
        
        Args:
            profiles: List of profile data
            output_path: Output CSV file path
        """
        import csv
        
        with open(output_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header
            writer.writerow([
                'PK', 'Station_X', 'Station_Y', 'Bearing', 
                'Offset', 'Elevation', 'Distance_From_Start'
            ])
            
            # Write data
            for profile in profiles:
                pk = profile['pk']
                station_x = profile['centerline_x']
                station_y = profile['centerline_y']
                bearing = profile['bearing']
                
                for i, (distance, elevation, coords) in enumerate(zip(
                    profile['distances'], 
                    profile['elevations'], 
                    profile['coordinates']
                )):
                    writer.writerow([
                        pk, station_x, station_y, bearing,
                        distance, elevation, profile['pk_decimal']
                    ])
    
    def create_profile_visualization_data(self, profile):
        """Create data structure suitable for matplotlib visualization
        
        Args:
            profile: Single profile data dictionary
            
        Returns:
            Dictionary with x, y data for plotting
        """
        valid_indices = []
        nodata_value = -9999  # Default NODATA value
        
        # Find valid elevation points
        for i, elevation in enumerate(profile['elevations']):
            if elevation != nodata_value:
                valid_indices.append(i)
        
        if not valid_indices:
            return None
        
        # Extract valid data
        distances = [profile['distances'][i] for i in valid_indices]
        elevations = [profile['elevations'][i] for i in valid_indices]
        
        return {
            'distances': distances,  # X-axis: distance from centerline
            'elevations': elevations,  # Y-axis: ground elevation
            'pk': profile['pk'],
            'centerline_elevation': profile.get('avg_elevation', 0),
            'title': f"Perfil Topográfico - {profile['pk']}",
            'xlabel': 'Distancia desde Eje (m)',
            'ylabel': 'Elevación (m)'
        }