#!/usr/bin/env python3
"""
Test real coordinates implementation for alignment data
"""

import sys
import os
import math

# Add the plugin directory to Python path
plugin_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, plugin_dir)

def test_real_coordinates():
    """Test that alignment uses real project coordinates"""
    print("Testing real coordinates implementation...")
    
    from core.alignment_data import AlignmentData
    
    alignment_data = AlignmentData()
    muro1 = alignment_data.get_alignment("Muro 1")
    
    if not muro1:
        print("  ✗ Failed to load Muro 1")
        return False
    
    stations = muro1['stations']
    
    # Expected real coordinates
    expected_start = (337997.913, 6334753.227)
    expected_end = (336688.222, 6334170.263)
    
    # Check start point (PK 0+000)
    start_station = stations[0]
    actual_start = (start_station['x'], start_station['y'])
    
    # Check end point (PK 1+434) - should be last station
    end_station = stations[-1]
    actual_end = (end_station['x'], end_station['y'])
    
    print(f"  Expected start: {expected_start}")
    print(f"  Actual start: {actual_start}")
    print(f"  Expected end: {expected_end}")
    print(f"  Actual end: {actual_end}")
    
    # Tolerance for coordinate comparison (1cm)
    tolerance = 0.01
    
    start_match = (abs(actual_start[0] - expected_start[0]) < tolerance and 
                   abs(actual_start[1] - expected_start[1]) < tolerance)
    
    end_match = (abs(actual_end[0] - expected_end[0]) < tolerance and 
                 abs(actual_end[1] - expected_end[1]) < tolerance)
    
    if start_match and end_match:
        print("  ✓ Real coordinates implemented correctly")
        
        # Check that alignment is straight (constant bearing)
        bearings = [station['bearing'] for station in stations]
        bearing_variance = max(bearings) - min(bearings)
        
        if bearing_variance < 0.1:  # Less than 0.1 degree variation
            print(f"  ✓ Straight line alignment confirmed (bearing variance: {bearing_variance:.3f}°)")
        else:
            print(f"  ⚠ Warning: Large bearing variance: {bearing_variance:.3f}°")
        
        # Check total length
        expected_length = 1434.0
        actual_length = muro1['total_length']
        
        if abs(actual_length - expected_length) < 1.0:
            print(f"  ✓ Correct total length: {actual_length}m")
        else:
            print(f"  ✗ Incorrect length: {actual_length}m (expected {expected_length}m)")
        
        return True
    else:
        print("  ✗ Coordinates do not match expected values")
        if not start_match:
            print(f"    Start point mismatch: {actual_start} vs {expected_start}")
        if not end_match:
            print(f"    End point mismatch: {actual_end} vs {expected_end}")
        return False

if __name__ == "__main__":
    success = test_real_coordinates()
    if success:
        print("\n✓ Real coordinates test PASSED")
    else:
        print("\n✗ Real coordinates test FAILED")
    sys.exit(0 if success else 1)