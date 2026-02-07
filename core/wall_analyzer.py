# -*- coding: utf-8 -*-
"""
Wall Analyzer Module - Revanchas LT Plugin
Proporciona herramientas de análisis para perfiles de muros de contención

Refactorizado con type hints y logging estructurado.
"""

import math
import statistics
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

# Importar logging del plugin
try:
    from ..utils.logging_config import get_logger
except ImportError:
    get_logger = lambda x: __import__('logging').getLogger(x)

logger = get_logger(__name__)


# Constantes
NODATA_VALUE: float = -9999.0
PROFILE_INTERVAL: float = 20.0  # metros entre perfiles
PROFILE_WIDTH: float = 80.0     # ancho para normalización


class WallAnalyzer:
    """
    Clase para analizar datos topográficos de muros de contención.
    
    Proporciona análisis de elevaciones, pendientes y características
    del terreno a partir de datos de perfiles.
    """
    
    def __init__(self):
        """Inicializa el analizador de muros."""
        self.analysis_results: Dict[str, Any] = {}
        logger.debug("WallAnalyzer inicializado")
    
    def analyze_wall(self, 
                     wall_name: str, 
                     profiles: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Realiza análisis completo de perfiles de muro.
        
        Args:
            wall_name: Nombre del muro a analizar
            profiles: Lista de datos de perfiles (opcional)
            
        Returns:
            Diccionario con resultados del análisis
        """
        logger.info(f"Analizando muro: {wall_name}")
        
        if profiles:
            results = self._analyze_actual_profiles(wall_name, profiles)
        else:
            results = self._get_sample_analysis(wall_name)
        
        self.analysis_results[wall_name] = results
        return results
    
    def _analyze_actual_profiles(self, 
                                  wall_name: str, 
                                  profiles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analiza datos reales de perfiles.
        
        Args:
            wall_name: Nombre del muro
            profiles: Lista de perfiles
            
        Returns:
            Diccionario con resultados
        """
        results: Dict[str, Any] = {
            'wall_name': wall_name,
            'profile_count': len(profiles),
            'analysis_date': self._get_current_timestamp(),
        }
        
        # Extraer elevaciones válidas de todos los perfiles
        all_elevations: List[float] = []
        valid_profiles = 0
        total_length = 0.0
        
        for profile in profiles:
            if profile.get('valid_points', 0) > 0:
                valid_profiles += 1
                valid_elevs = [e for e in profile['elevations'] if e != NODATA_VALUE]
                all_elevations.extend(valid_elevs)
                
                if valid_profiles > 1:
                    total_length += PROFILE_INTERVAL
        
        if all_elevations:
            results.update({
                'total_length': f"{total_length:.0f}m",
                'total_length_m': total_length,
                'valid_profiles': valid_profiles,
                'min_elevation': min(all_elevations),
                'max_elevation': max(all_elevations),
                'avg_elevation': statistics.mean(all_elevations),
                'elevation_std': statistics.stdev(all_elevations) if len(all_elevations) > 1 else 0,
                'elevation_range': max(all_elevations) - min(all_elevations),
                'total_points': len(all_elevations)
            })
        else:
            results.update({
                'total_length': "0m",
                'total_length_m': 0,
                'valid_profiles': 0,
                'min_elevation': 0,
                'max_elevation': 0,
                'avg_elevation': 0,
                'elevation_std': 0,
                'elevation_range': 0,
                'total_points': 0
            })
        
        # Calcular pendiente promedio
        results['avg_slope'] = self._calculate_average_slope(profiles)
        
        # Analizar características de secciones transversales
        cross_section_analysis = self._analyze_cross_sections(profiles)
        results.update(cross_section_analysis)
        
        # Generar recomendaciones automáticas
        results['recommendations'] = self._generate_recommendations(results)
        results['analysis_quality'] = self._assess_analysis_quality(results)
        
        logger.info(
            f"Análisis completado: {valid_profiles} perfiles válidos, "
            f"rango de elevación {results['elevation_range']:.1f}m"
        )
        
        return results
    
    def _get_sample_analysis(self, wall_name: str) -> Dict[str, Any]:
        """
        Retorna resultados de análisis de muestra para demostración.
        
        Args:
            wall_name: Nombre del muro
            
        Returns:
            Diccionario con datos de ejemplo
        """
        logger.debug(f"Generando análisis de muestra para {wall_name}")
        
        return {
            'wall_name': wall_name,
            'profile_count': 72,
            'total_length': "1434m",
            'total_length_m': 1434,
            'valid_profiles': 72,
            'min_elevation': 95.5,
            'max_elevation': 125.8,
            'avg_elevation': 110.2,
            'elevation_std': 8.4,
            'elevation_range': 30.3,
            'avg_slope': 1.85,
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
    
    def _calculate_average_slope(self, 
                                  profiles: List[Dict[str, Any]]) -> float:
        """
        Calcula pendiente longitudinal promedio a lo largo de la alineación.
        
        Args:
            profiles: Lista de perfiles
            
        Returns:
            Pendiente promedio en porcentaje
        """
        if not profiles or len(profiles) < 2:
            return 0.0
        
        slopes: List[float] = []
        
        for i in range(len(profiles) - 1):
            elev1 = profiles[i].get('avg_elevation')
            elev2 = profiles[i + 1].get('avg_elevation')
            
            if elev1 is not None and elev2 is not None:
                slope = ((elev2 - elev1) / PROFILE_INTERVAL) * 100
                slopes.append(abs(slope))
        
        return statistics.mean(slopes) if slopes else 0.0
    
    def _analyze_cross_sections(self, 
                                 profiles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analiza características de las secciones transversales.
        
        Args:
            profiles: Lista de perfiles
            
        Returns:
            Diccionario con análisis de secciones transversales
        """
        if not profiles:
            return {
                'cross_slope_left_avg': 0,
                'cross_slope_right_avg': 0,
                'max_cross_slope': 0,
                'terrain_variability': 'Unknown',
                'avg_variability_value': 0
            }
        
        left_slopes: List[float] = []
        right_slopes: List[float] = []
        variabilities: List[float] = []
        
        for profile in profiles:
            if profile.get('valid_points', 0) < 10:
                continue
            
            distances = profile.get('distances', [])
            elevations = profile.get('elevations', [])
            
            if len(distances) != len(elevations):
                continue
            
            # Calcular pendiente lado izquierdo
            left_indices = [i for i, d in enumerate(distances) if d < 0]
            if len(left_indices) >= 2:
                left_elev = [elevations[i] for i in left_indices if elevations[i] != NODATA_VALUE]
                left_dist = [abs(distances[i]) for i in left_indices if elevations[i] != NODATA_VALUE]
                if len(left_elev) >= 2:
                    left_slope = self._calculate_slope(left_dist, left_elev)
                    if left_slope is not None:
                        left_slopes.append(left_slope)
            
            # Calcular pendiente lado derecho
            right_indices = [i for i, d in enumerate(distances) if d > 0]
            if len(right_indices) >= 2:
                right_elev = [elevations[i] for i in right_indices if elevations[i] != NODATA_VALUE]
                right_dist = [distances[i] for i in right_indices if elevations[i] != NODATA_VALUE]
                if len(right_elev) >= 2:
                    right_slope = self._calculate_slope(right_dist, right_elev)
                    if right_slope is not None:
                        right_slopes.append(right_slope)
            
            # Calcular variabilidad
            valid_elevations = [e for e in elevations if e != NODATA_VALUE]
            if len(valid_elevations) > 5:
                elev_range = max(valid_elevations) - min(valid_elevations)
                variability = elev_range / PROFILE_WIDTH
                variabilities.append(variability)
        
        # Resumir resultados
        avg_left_slope = statistics.mean(left_slopes) if left_slopes else 0
        avg_right_slope = statistics.mean(right_slopes) if right_slopes else 0
        max_slope = max(left_slopes + right_slopes) if (left_slopes + right_slopes) else 0
        avg_variability = statistics.mean(variabilities) if variabilities else 0
        
        # Clasificar variabilidad del terreno
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
    
    def _calculate_slope(self, 
                         distances: List[float], 
                         elevations: List[float]) -> Optional[float]:
        """
        Calcula pendiente usando regresión lineal simple.
        
        Args:
            distances: Lista de distancias
            elevations: Lista de elevaciones
            
        Returns:
            Pendiente en porcentaje o None si no es posible calcular
        """
        if len(distances) < 2 or len(elevations) < 2:
            return None
        
        try:
            n = len(distances)
            sum_x = sum(distances)
            sum_y = sum(elevations)
            sum_xy = sum(x * y for x, y in zip(distances, elevations))
            sum_x2 = sum(x * x for x in distances)
            
            denominator = n * sum_x2 - sum_x * sum_x
            if abs(denominator) < 1e-10:
                return None
            
            slope = (n * sum_xy - sum_x * sum_y) / denominator
            return slope * 100
        except (ZeroDivisionError, ValueError):
            return None
    
    def _generate_recommendations(self, 
                                   results: Dict[str, Any]) -> List[str]:
        """
        Genera recomendaciones basadas en el análisis.
        
        Args:
            results: Resultados del análisis
            
        Returns:
            Lista de recomendaciones
        """
        recommendations: List[str] = []
        
        avg_slope = results.get('avg_slope', 0)
        terrain_var = results.get('terrain_variability', 'Unknown')
        max_cross = results.get('max_cross_slope', 0)
        
        # Recomendaciones por pendiente
        if avg_slope < 2:
            recommendations.append(
                'Terreno con pendiente suave, favorable para construcción'
            )
        elif avg_slope < 5:
            recommendations.append(
                'Pendiente moderada, considerar medidas de drenaje'
            )
        else:
            recommendations.append(
                'Pendiente pronunciada, requiere análisis geotécnico detallado'
            )
        
        # Recomendaciones por variabilidad
        if terrain_var == 'High':
            recommendations.append(
                'Alta variabilidad del terreno, considerar estabilización'
            )
        elif terrain_var == 'Moderate':
            recommendations.append(
                'Verificar drenaje en secciones con mayor pendiente transversal'
            )
        
        # Recomendaciones por pendiente transversal
        if max_cross > 10:
            recommendations.append(
                'Pendientes transversales significativas, evaluar erosión'
            )
        
        return recommendations
    
    def _assess_analysis_quality(self, results: Dict[str, Any]) -> str:
        """
        Evalúa la calidad del análisis.
        
        Args:
            results: Resultados del análisis
            
        Returns:
            Clasificación de calidad
        """
        valid_profiles = results.get('valid_profiles', 0)
        total_profiles = results.get('profile_count', 0)
        
        if total_profiles == 0:
            return 'No data'
        
        coverage = valid_profiles / total_profiles
        
        if coverage >= 0.9:
            return 'Excellent'
        elif coverage >= 0.75:
            return 'Good'
        elif coverage >= 0.5:
            return 'Fair'
        else:
            return 'Poor'
    
    def _get_current_timestamp(self) -> str:
        """Obtiene timestamp actual para el análisis."""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def generate_analysis_report(self, 
                                  analysis_results: Dict[str, Any]) -> str:
        """
        Genera reporte de análisis formateado.
        
        Args:
            analysis_results: Resultados del análisis
            
        Returns:
            Reporte como string formateado
        """
        if not analysis_results:
            return "No hay datos de análisis disponibles."
        
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
    
    def get_summary_stats(self, wall_name: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene estadísticas resumidas de un análisis previo.
        
        Args:
            wall_name: Nombre del muro
            
        Returns:
            Diccionario con estadísticas o None
        """
        if wall_name not in self.analysis_results:
            return None
        
        results = self.analysis_results[wall_name]
        
        return {
            'wall_name': wall_name,
            'analyzed': True,
            'profiles': results.get('valid_profiles', 0),
            'length': results.get('total_length', 'N/A'),
            'elevation_range': results.get('elevation_range', 0),
            'avg_slope': results.get('avg_slope', 0),
            'quality': results.get('analysis_quality', 'N/A')
        }
    
    def compare_walls(self, 
                      wall_names: List[str]) -> Optional[Dict[str, Any]]:
        """
        Compara análisis de múltiples muros.
        
        Args:
            wall_names: Lista de nombres de muros a comparar
            
        Returns:
            Diccionario con comparación o None si faltan datos
        """
        comparison: Dict[str, Any] = {'walls': []}
        
        for name in wall_names:
            if name in self.analysis_results:
                comparison['walls'].append(self.get_summary_stats(name))
        
        if not comparison['walls']:
            return None
        
        # Calcular estadísticas agregadas
        all_ranges = [w['elevation_range'] for w in comparison['walls'] if w]
        all_slopes = [w['avg_slope'] for w in comparison['walls'] if w]
        
        comparison['aggregate'] = {
            'total_walls': len(comparison['walls']),
            'avg_elevation_range': statistics.mean(all_ranges) if all_ranges else 0,
            'avg_slope': statistics.mean(all_slopes) if all_slopes else 0
        }
        
        return comparison