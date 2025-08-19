#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test DEM loading with the sample file
"""

import sys
import os

# Add the plugin directory to Python path
plugin_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, plugin_dir)

def test_sample_dem():
    """Test loading the sample DEM file"""
    print("Testing Sample DEM Loading...")
    
    from core.dem_processor import DEMProcessor
    
    dem_processor = DEMProcessor()
    
    # Test with sample DEM
    sample_dem_path = os.path.join(plugin_dir, 'data', 'sample_dem.asc')
    
    if not os.path.exists(sample_dem_path):
        print(f"  ✗ Sample DEM not found: {sample_dem_path}")
        return False
    
    try:
        # Get DEM info
        dem_info = dem_processor.get_dem_info(sample_dem_path)
        print(f"  ✓ DEM Info: {dem_info['cols']}x{dem_info['rows']}, cellsize={dem_info['cellsize']}")
        print(f"  ✓ Extent: X({dem_info['xmin']:.1f}, {dem_info['xmax']:.1f}) Y({dem_info['ymin']:.1f}, {dem_info['ymax']:.1f})")
        
        # Load full DEM
        dem_data = dem_processor.load_dem(sample_dem_path)
        print(f"  ✓ DEM loaded successfully")
        
        # Test elevation extraction
        center_x = dem_info['xmin'] + (dem_info['xmax'] - dem_info['xmin']) / 2
        center_y = dem_info['ymin'] + (dem_info['ymax'] - dem_info['ymin']) / 2
        
        elevation = dem_processor.get_elevation_at_point(center_x, center_y, dem_data)
        print(f"  ✓ Center elevation: {elevation:.2f}m at ({center_x:.1f}, {center_y:.1f})")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Error loading DEM: {e}")
        return False

def test_complete_workflow():
    """Test the complete workflow with sample data"""
    print("\nTesting Complete Workflow...")
    
    from core.dem_processor import DEMProcessor
    from core.alignment_data import AlignmentData  
    from core.profile_generator import ProfileGenerator
    from core.wall_analyzer import WallAnalyzer
    
    # Initialize components
    dem_processor = DEMProcessor()
    alignment_data = AlignmentData()
    profile_generator = ProfileGenerator()
    wall_analyzer = WallAnalyzer()
    
    try:
        # Load sample DEM
        sample_dem_path = os.path.join(plugin_dir, 'data', 'sample_dem.asc')
        dem_data = dem_processor.load_dem(sample_dem_path)
        print("  ✓ DEM loaded")
        
        # Get alignment
        alignment = alignment_data.get_alignment("Muro 1")
        print(f"  ✓ Alignment loaded: {len(alignment['stations'])} stations")
        
        # Generate first 5 profiles for testing
        test_stations = alignment['stations'][:5]
        profiles = []
        
        for i, station in enumerate(test_stations):
            profile = profile_generator.generate_single_profile(dem_data, station, 80.0)
            profiles.append(profile)
            print(f"  ✓ Profile {i+1}: {profile['pk']} - {profile['valid_points']} valid points")
        
        # Analyze profiles
        analysis = wall_analyzer.analyze_wall("Muro 1", profiles)
        print(f"  ✓ Analysis complete: {analysis['valid_profiles']} profiles analyzed")
        print(f"    - Elevation range: {analysis['min_elevation']:.2f} - {analysis['max_elevation']:.2f}m")
        print(f"    - Average slope: {analysis['avg_slope']:.2f}%")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Workflow error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("REVANCHAS LT PLUGIN - DEM AND WORKFLOW TESTS")
    print("=" * 60)
    
    tests_passed = 0
    
    if test_sample_dem():
        tests_passed += 1
    
    if test_complete_workflow():
        tests_passed += 1
    
    print("\n" + "=" * 60)
    if tests_passed == 2:
        print("✓ All DEM and workflow tests PASSED!")
        print("Plugin is ready for use with QGIS.")
    else:
        print("✗ Some tests failed. Check the implementation.")
    print("=" * 60)