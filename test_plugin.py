#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for Revanchas LT plugin components
Tests the core functionality without QGIS dependency
"""

import sys
import os

# Add the plugin directory to Python path
plugin_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, plugin_dir)

def test_alignment_data():
    """Test the alignment data module"""
    print("Testing AlignmentData...")
    
    from core.alignment_data import AlignmentData
    
    alignment_data = AlignmentData()
    
    # Test getting alignment for Muro 1
    muro1 = alignment_data.get_alignment("Muro 1")
    
    if muro1:
        print(f"  ✓ Muro 1 loaded: {muro1['start_pk']} to {muro1['end_pk']}")
        print(f"  ✓ Total stations: {len(muro1['stations'])}")
        print(f"  ✓ Interval: {muro1['interval']}m")
        
        # Test cross-section generation
        first_station = muro1['stations'][0]
        cross_points = alignment_data.get_cross_section_points(first_station, 80.0)
        print(f"  ✓ Cross-section points generated: {len(cross_points)}")
        
        return True
    else:
        print("  ✗ Failed to load Muro 1")
        return False

def test_dem_processor():
    """Test the DEM processor module (without actual DEM file)"""
    print("Testing DEMProcessor...")
    
    from core.dem_processor import DEMProcessor
    
    dem_processor = DEMProcessor()
    
    # Create mock DEM data for testing
    mock_header = {
        'ncols': 100,
        'nrows': 100,
        'xllcorner': 336500.0,  # Cover the new alignment area
        'yllcorner': 6334000.0,  # Cover the new alignment area  
        'cellsize': 1.0,
        'nodata_value': -9999
    }
    
    # Create simple elevation grid (slopes upward)
    try:
        import numpy as np
        mock_data = np.zeros((100, 100))
        for i in range(100):
            for j in range(100):
                mock_data[i, j] = 100.0 + i * 0.1 + j * 0.05
    except ImportError:
        # Fallback without numpy
        mock_data = []
        for i in range(100):
            row = []
            for j in range(100):
                row.append(100.0 + i * 0.1 + j * 0.05)
            mock_data.append(row)
    
    mock_dem = {
        'data': mock_data,
        'header': mock_header
    }
    
    # Test elevation extraction
    x, y = 336550.0, 6334050.0  # Point within the new coordinate area
    elevation = dem_processor.get_elevation_at_point(x, y, mock_dem)
    
    if elevation != mock_header['nodata_value']:
        print(f"  ✓ Elevation extraction works: {elevation:.2f}m at ({x}, {y})")
        return True
    else:
        print("  ✗ Failed to extract elevation")
        return False

def test_profile_generator():
    """Test the profile generator module"""
    print("Testing ProfileGenerator...")
    
    from core.profile_generator import ProfileGenerator
    from core.alignment_data import AlignmentData
    
    profile_gen = ProfileGenerator()
    alignment_data = AlignmentData()
    
    # Get test alignment
    alignment = alignment_data.get_alignment("Muro 1")
    
    if alignment and len(alignment['stations']) > 0:
        # Create mock DEM data
        try:
            import numpy as np
            mock_data = np.zeros((1000, 2000))  # Updated dimensions
            for i in range(1000):
                for j in range(2000):
                    mock_data[i, j] = 100.0 + i * 0.1
        except ImportError:
            # Fallback without numpy
            mock_data = []
            for i in range(1000):  # Updated dimensions
                row = []
                for j in range(2000):  # Updated dimensions
                    row.append(100.0 + i * 0.1)
                mock_data.append(row)
        
        mock_header = {
            'ncols': 2000,  # Larger area to cover full alignment 
            'nrows': 1000,  # Larger area to cover full alignment
            'xllcorner': 336500.0,  # Cover the new alignment area
            'yllcorner': 6334000.0,  # Cover the new alignment area
            'cellsize': 1.0,
            'nodata_value': -9999
        }
        
        mock_dem = {
            'data': mock_data,
            'header': mock_header
        }
        
        # Generate a single profile
        first_station = alignment['stations'][0]
        profile = profile_gen.generate_single_profile(mock_dem, first_station, 80.0)
        
        if profile and len(profile['elevations']) > 0:
            print(f"  ✓ Profile generated: {profile['pk']} with {profile['valid_points']} valid points")
            print(f"  ✓ Elevation range: {profile.get('min_elevation', 0):.2f} - {profile.get('max_elevation', 0):.2f}m")
            return True
    
    print("  ✗ Failed to generate profile")
    return False

def test_wall_analyzer():
    """Test the wall analyzer module"""
    print("Testing WallAnalyzer...")
    
    from core.wall_analyzer import WallAnalyzer
    
    analyzer = WallAnalyzer()
    
    # Test with sample data
    results = analyzer.analyze_wall("Muro 1")
    
    if results and results.get('profile_count', 0) > 0:
        print(f"  ✓ Analysis complete: {results['profile_count']} profiles")
        print(f"  ✓ Length: {results['total_length']}")
        print(f"  ✓ Elevation range: {results['min_elevation']:.1f} - {results['max_elevation']:.1f}m")
        
        # Test report generation
        report = analyzer.generate_analysis_report(results)
        if len(report) > 100:
            print("  ✓ Analysis report generated")
            return True
    
    print("  ✗ Failed to analyze wall")
    return False

def main():
    """Run all tests"""
    print("=" * 50)
    print("REVANCHAS LT PLUGIN - COMPONENT TESTS")
    print("=" * 50)
    
    tests = [
        test_alignment_data,
        test_dem_processor,
        test_profile_generator,
        test_wall_analyzer
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            print()
        except Exception as e:
            print(f"  ✗ Test failed with error: {e}")
            print()
    
    print("=" * 50)
    print(f"RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ All core components working correctly!")
    else:
        print("✗ Some components need attention")
    
    print("=" * 50)
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)