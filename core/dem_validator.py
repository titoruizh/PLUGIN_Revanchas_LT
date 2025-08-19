# -*- coding: utf-8 -*-
"""
DEM Validator Module
Validates if DEM covers the alignment coordinates
"""

class DEMValidator:
    """Validates DEM coverage for alignment data"""
    
    @staticmethod
    def validate_dem_coverage(dem_info, alignment):
        """
        Validate that DEM covers the alignment area
        
        Args:
            dem_info: DEM extent info from DEMProcessor
            alignment: Alignment data with stations
            
        Returns:
            dict: validation results with coverage info
        """
        # Get alignment bounds
        x_coords = [station['x'] for station in alignment['stations']]
        y_coords = [station['y'] for station in alignment['stations']]
        
        align_xmin, align_xmax = min(x_coords), max(x_coords)
        align_ymin, align_ymax = min(y_coords), max(y_coords)
        
        # Add buffer for 80m cross-sections (40m each side)
        buffer = 50.0  # meters (with safety margin)
        align_xmin -= buffer
        align_xmax += buffer
        align_ymin -= buffer
        align_ymax += buffer
        
        # Check coverage
        dem_xmin, dem_xmax = dem_info['xmin'], dem_info['xmax']
        dem_ymin, dem_ymax = dem_info['ymin'], dem_info['ymax']
        
        coverage_ok = (
            align_xmin >= dem_xmin and align_xmax <= dem_xmax and
            align_ymin >= dem_ymin and align_ymax <= dem_ymax
        )
        
        return {
            'coverage_ok': coverage_ok,
            'alignment_bounds': {
                'xmin': align_xmin, 'xmax': align_xmax,
                'ymin': align_ymin, 'ymax': align_ymax
            },
            'dem_bounds': {
                'xmin': dem_xmin, 'xmax': dem_xmax,
                'ymin': dem_ymin, 'ymax': dem_ymax
            },
            'missing_coverage': {
                'x_deficit': max(0, align_xmin - dem_xmin) + max(0, dem_xmax - align_xmax),
                'y_deficit': max(0, align_ymin - dem_ymin) + max(0, dem_ymax - align_ymax)
            }
        }