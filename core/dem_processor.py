# -*- coding: utf-8 -*-
"""
DEM Processor Module
Handles ASCII Grid (.asc) file loading and processing
"""

import os

try:
    import numpy as np
    # Test if numpy is working properly (handles _ARRAY_API issues)
    try:
        # Test basic functionality
        test_array = np.array([1, 2, 3])
        # Test if _ARRAY_API access causes problems (this is the main issue)
        try:
            _ = hasattr(np, '_ARRAY_API')  # This line can trigger the error
        except AttributeError as ae:
            if '_ARRAY_API' in str(ae):
                print(f"⚠️ NumPy _ARRAY_API error detectado en DEM processor: {ae}")
                raise ae
        HAS_NUMPY = True
        print("✅ NumPy funcionando correctamente en DEM processor")
    except (AttributeError, ImportError, Exception) as e:
        print(f"⚠️ NumPy disponible but con problemas en DEM processor: {e}")
        HAS_NUMPY = False
        # Set np to None to force fallback
        np = None
except ImportError:
    HAS_NUMPY = False
    np = None

if not HAS_NUMPY:
    # Fallback for environments without numpy or with problematic numpy
    class np:
        @staticmethod
        def array(data):
            return data
        
        @staticmethod
        def zeros(shape):
            if isinstance(shape, tuple) and len(shape) == 2:
                return [[0.0 for _ in range(shape[1])] for _ in range(shape[0])]
            return [0.0] * shape


class DEMProcessor:
    """Class to handle DEM file operations"""
    
    def __init__(self):
        self.dem_data = None
        self.header = None
        
    def get_dem_info(self, file_path):
        """Get basic information about a DEM file without fully loading it"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"DEM file not found: {file_path}")
            
        header = self._read_header(file_path)
        
        return {
            'cols': header['ncols'],
            'rows': header['nrows'],
            'xmin': header['xllcorner'],
            'ymin': header['yllcorner'],
            'xmax': header['xllcorner'] + header['ncols'] * header['cellsize'],
            'ymax': header['yllcorner'] + header['nrows'] * header['cellsize'],
            'cellsize': header['cellsize'],
            'nodata': header.get('nodata_value', -9999)
        }
    
    def load_dem(self, file_path):
        """Load DEM from ASCII Grid file"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"DEM file not found: {file_path}")
            
        # Read header
        self.header = self._read_header(file_path)
        
        # Read data
        data = []
        header_lines = 6  # Standard ASC header has 6 lines
        
        with open(file_path, 'r') as f:
            # Skip header
            for _ in range(header_lines):
                f.readline()
                
            # Read data
            for line in f:
                row = [float(val) for val in line.strip().split()]
                data.append(row)
        
        if HAS_NUMPY:
            self.dem_data = np.array(data)
        else:
            self.dem_data = data
        
        return {
            'data': self.dem_data,
            'header': self.header,
            'info': self.get_dem_info(file_path)
        }
    
    def _read_header(self, file_path):
        """Read ASC file header"""
        header = {}
        
        with open(file_path, 'r') as f:
            header['ncols'] = int(f.readline().strip().split()[1])
            header['nrows'] = int(f.readline().strip().split()[1])
            header['xllcorner'] = float(f.readline().strip().split()[1])
            header['yllcorner'] = float(f.readline().strip().split()[1])
            header['cellsize'] = float(f.readline().strip().split()[1])
            
            # NODATA_value is optional
            next_line = f.readline().strip().split()
            if next_line[0].lower().startswith('nodata'):
                header['nodata_value'] = float(next_line[1])
            else:
                header['nodata_value'] = -9999
                
        return header
    
    def get_elevation_at_point(self, x, y, dem_data=None):
        """Get elevation at a specific coordinate using bilinear interpolation"""
        if dem_data is None:
            dem_data = self.dem_data
            header = self.header
        else:
            header = dem_data['header']
            dem_data = dem_data['data']
            
        if dem_data is None or header is None:
            raise ValueError("No DEM data loaded")
        
        # Convert world coordinates to grid coordinates
        col = (x - header['xllcorner']) / header['cellsize']
        row = (header['yllcorner'] + header['nrows'] * header['cellsize'] - y) / header['cellsize']
        
        # Check bounds
        if col < 0 or col >= header['ncols'] - 1 or row < 0 or row >= header['nrows'] - 1:
            return header['nodata_value']
        
        # Bilinear interpolation
        col_int = int(col)
        row_int = int(row)
        
        # Get the four surrounding points
        if HAS_NUMPY:
            z11 = dem_data[row_int, col_int]
            z12 = dem_data[row_int, col_int + 1]
            z21 = dem_data[row_int + 1, col_int]
            z22 = dem_data[row_int + 1, col_int + 1]
        else:
            z11 = dem_data[row_int][col_int]
            z12 = dem_data[row_int][col_int + 1]
            z21 = dem_data[row_int + 1][col_int]
            z22 = dem_data[row_int + 1][col_int + 1]
        
        # Check for NODATA values
        if any(z == header['nodata_value'] for z in [z11, z12, z21, z22]):
            return header['nodata_value']
        
        # Interpolate
        dx = col - col_int
        dy = row - row_int
        
        z1 = z11 * (1 - dx) + z12 * dx
        z2 = z21 * (1 - dx) + z22 * dx
        z = z1 * (1 - dy) + z2 * dy
        
        return z
    
    def extract_profile_elevations(self, profile_points, dem_data=None):
        """Extract elevations along a profile line"""
        elevations = []
        
        for point in profile_points:
            elevation = self.get_elevation_at_point(point[0], point[1], dem_data)
            elevations.append(elevation)
            
        return elevations