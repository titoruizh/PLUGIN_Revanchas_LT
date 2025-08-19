# -*- coding: utf-8 -*-
"""
Wall Analyzer Module
Provides analysis tools for retaining wall profiles
"""

import math
import statistics
from typing import List, Dict, Any


class WallAnalyzer:
    """Class to analyze retaining wall topographic data"""
    
    def __init__(self):
        self.analysis_results = {}
        
    def analyze_wall(self, wall_name, profiles=None):
        """Perform comprehensive analysis of wall profiles
        
        Args:
            wall_name: Name of the wall being analyzed
            profiles: List of profile data (optional, uses dummy data if None)
            
        Returns:
            Dictionary with analysis results
        """
        # For initial implementation, return sample analysis results
        # In full implementation, this would analyze actual profile data
        
        if profiles:
            return self._analyze_actual_profiles(wall_name, profiles)
        else:
            return self._get_sample_analysis(wall_name)
    
    def _analyze_actual_profiles(self, wall_name, profiles):
        """Analyze actual profile data"""
        results = {
            'wall_name': wall_name,
            'profile_count': len(profiles),
            'analysis_date': self._get_current_timestamp(),
        }
        
        # Extract valid elevations from all profiles
        all_elevations = []
        valid_profiles = 0
        total_length = 0
        
        for profile in profiles:
            if profile.get('valid_points', 0) > 0:
                valid_profiles += 1
                # Add all valid elevations from this profile
                valid_elevs = [e for e in profile['elevations'] if e != -9999]
                all_elevations.extend(valid_elevs)
                
                # Calculate length contribution
                if valid_profiles > 1:
                    total_length += 20  # 20m intervals
        
        if all_elevations:
            results.update({
                'total_length': f"{total_length:.0f}m",
                'valid_profiles': valid_profiles,
                'min_elevation': min(all_elevations),
                'max_elevation': max(all_elevations),
                'avg_elevation': statistics.mean(all_elevations),
                'elevation_std': statistics.stdev(all_elevations) if len(all_elevations) > 1 else 0,
                'elevation_range': max(all_elevations) - min(all_elevations)
            })
        else:
            results.update({
                'total_length': "0m",
                'valid_profiles': 0,
                'min_elevation': 0,
                'max_elevation': 0,
                'avg_elevation': 0,
                'elevation_std': 0,
                'elevation_range': 0
            })
        
        # Calculate average slope along the alignment
        results['avg_slope'] = self._calculate_average_slope(profiles)
        
        # Analyze cross-sectional characteristics
        cross_section_analysis = self._analyze_cross_sections(profiles)
        results.update(cross_section_analysis)
        
        return results
    
    def _get_sample_analysis(self, wall_name):
        """Return sample analysis results for demonstration"""
        return {
            'wall_name': wall_name,
            'profile_count': 72,  # PK 0+000 to 1+434 every 20m
            'total_length': "1434m",
            'valid_profiles': 72,
            'min_elevation': 95.5,
            'max_elevation': 125.8,
            'avg_elevation': 110.2,
            'elevation_std': 8.4,
            'elevation_range': 30.3,
            'avg_slope': 1.85,  # percentage
            'analysis_date': self._get_current_timestamp(),
            'cross_slope_left_avg': -2.1,
            'cross_slope_right_avg': -1.8,
            'max_cross_slope': 8.5,
            'terrain_variability': 'Moderate',
            'analysis_quality': 'Good',
            'recommendations': [
                'Terreno con pendiente moderada favorable para construcción',
                'Verificar drenaje en secciones con mayor pendiente transversal',
                'Considerar estabilización en zonas de mayor variabilidad'
            ]
        }
    
    def _calculate_average_slope(self, profiles):
        """Calculate average longitudinal slope along alignment"""
        if not profiles or len(profiles) < 2:
            return 0.0
        
        slopes = []
        
        for i in range(len(profiles) - 1):
            # Get centerline elevations (approximate)
            elev1 = profiles[i].get('avg_elevation')
            elev2 = profiles[i + 1].get('avg_elevation')
            
            if elev1 is not None and elev2 is not None:
                # Distance between stations (20m)
                distance = 20.0
                slope = ((elev2 - elev1) / distance) * 100  # Convert to percentage
                slopes.append(abs(slope))  # Use absolute value for average
        
        return statistics.mean(slopes) if slopes else 0.0
    
    def _analyze_cross_sections(self, profiles):
        """Analyze cross-sectional characteristics"""
        if not profiles:
            return {
                'cross_slope_left_avg': 0,
                'cross_slope_right_avg': 0,
                'max_cross_slope': 0,
                'terrain_variability': 'Unknown'
            }
        
        left_slopes = []
        right_slopes = []
        variabilities = []
        
        for profile in profiles:
            if profile.get('valid_points', 0) < 10:  # Need enough points
                continue
                
            distances = profile.get('distances', [])
            elevations = profile.get('elevations', [])
            
            if len(distances) != len(elevations):
                continue
            
            # Find centerline index (distance ≈ 0)
            center_idx = len(distances) // 2  # Middle point
            
            # Calculate left side slope (negative distances)
            left_indices = [i for i, d in enumerate(distances) if d < 0]
            if len(left_indices) >= 2:
                left_elev = [elevations[i] for i in left_indices if elevations[i] != -9999]
                left_dist = [abs(distances[i]) for i in left_indices if elevations[i] != -9999]
                if len(left_elev) >= 2:
                    left_slope = self._calculate_slope(left_dist, left_elev)
                    if left_slope is not None:
                        left_slopes.append(left_slope)
            
            # Calculate right side slope (positive distances)
            right_indices = [i for i, d in enumerate(distances) if d > 0]
            if len(right_indices) >= 2:
                right_elev = [elevations[i] for i in right_indices if elevations[i] != -9999]
                right_dist = [distances[i] for i in right_indices if elevations[i] != -9999]
                if len(right_elev) >= 2:
                    right_slope = self._calculate_slope(right_dist, right_elev)
                    if right_slope is not None:
                        right_slopes.append(right_slope)
            
            # Calculate variability (elevation range / width)
            valid_elevations = [e for e in elevations if e != -9999]
            if len(valid_elevations) > 5:
                elev_range = max(valid_elevations) - min(valid_elevations)
                variability = elev_range / 80.0  # Normalize by width
                variabilities.append(variability)
        
        # Summarize results
        avg_left_slope = statistics.mean(left_slopes) if left_slopes else 0
        avg_right_slope = statistics.mean(right_slopes) if right_slopes else 0
        max_slope = max(left_slopes + right_slopes) if (left_slopes + right_slopes) else 0
        avg_variability = statistics.mean(variabilities) if variabilities else 0
        
        # Classify terrain variability
        if avg_variability < 0.1:
            terrain_class = 'Low'
        elif avg_variability < 0.3:
            terrain_class = 'Moderate'
        else:
            terrain_class = 'High'
        
        return {
            'cross_slope_left_avg': avg_left_slope,
            'cross_slope_right_avg': avg_right_slope,
            'max_cross_slope': max_slope,
            'terrain_variability': terrain_class,
            'avg_variability_value': avg_variability
        }
    
    def _calculate_slope(self, distances, elevations):
        """Calculate slope from distance and elevation data"""
        if len(distances) < 2 or len(elevations) < 2:
            return None
        
        try:
            # Simple linear regression to find slope
            n = len(distances)
            sum_x = sum(distances)
            sum_y = sum(elevations)
            sum_xy = sum(x * y for x, y in zip(distances, elevations))
            sum_x2 = sum(x * x for x in distances)
            
            # Calculate slope (rise/run) and convert to percentage
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
            return slope * 100  # Convert to percentage
        except ZeroDivisionError:
            return None
    
    def _get_current_timestamp(self):
        """Get current timestamp for analysis"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def generate_analysis_report(self, analysis_results):
        """Generate a formatted analysis report"""
        if not analysis_results:
            return "No analysis data available."
        
        report = f"""
ANÁLISIS TOPOGRÁFICO - {analysis_results.get('wall_name', 'Unknown')}
================================================================

INFORMACIÓN GENERAL:
- Fecha de análisis: {analysis_results.get('analysis_date', 'N/A')}
- Perfiles analizados: {analysis_results.get('profile_count', 0)}
- Longitud total: {analysis_results.get('total_length', 'N/A')}
- Perfiles válidos: {analysis_results.get('valid_profiles', 0)}

ELEVACIONES:
- Mínima: {analysis_results.get('min_elevation', 0):.2f} m
- Máxima: {analysis_results.get('max_elevation', 0):.2f} m
- Promedio: {analysis_results.get('avg_elevation', 0):.2f} m
- Desviación estándar: {analysis_results.get('elevation_std', 0):.2f} m
- Rango: {analysis_results.get('elevation_range', 0):.2f} m

PENDIENTES:
- Pendiente longitudinal promedio: {analysis_results.get('avg_slope', 0):.2f}%
- Pendiente transversal izquierda: {analysis_results.get('cross_slope_left_avg', 0):.2f}%
- Pendiente transversal derecha: {analysis_results.get('cross_slope_right_avg', 0):.2f}%
- Pendiente transversal máxima: {analysis_results.get('max_cross_slope', 0):.2f}%

CARACTERÍSTICAS DEL TERRENO:
- Variabilidad del terreno: {analysis_results.get('terrain_variability', 'N/A')}
- Calidad del análisis: {analysis_results.get('analysis_quality', 'N/A')}

RECOMENDACIONES:
"""
        
        recommendations = analysis_results.get('recommendations', [])
        for i, rec in enumerate(recommendations, 1):
            report += f"{i}. {rec}\n"
        
        return report