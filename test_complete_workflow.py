import json
import os

def test_workflow():
    """Test complete project save/load workflow"""
    print("🔧 Testing Complete Project Workflow")
    print("=" * 50)
    
    # Check if test project file exists
    test_project = r"C:\Users\LT_Gabinete_1\Downloads\Proyecto_Muro 1_20251002_1627.rvlt"
    
    if os.path.exists(test_project):
        print(f"📁 Found test project: {test_project}")
        
        # Load and analyze project
        with open(test_project, 'r', encoding='utf-8') as f:
            project_data = json.load(f)
        
        print("\n📊 Project Analysis:")
        print("-" * 30)
        
        # Check project structure
        sections = ['project_info', 'project_settings', 'file_paths', 'measurements_data']
        for section in sections:
            if section in project_data:
                print(f"✅ {section}: Present")
                if section == 'measurements_data':
                    measurements = project_data[section]
                    
                    # Check for new format (saved_measurements structure)
                    if 'saved_measurements' in measurements:
                        saved_measurements = measurements['saved_measurements']
                        print(f"   📏 Saved measurements (new format): {len(saved_measurements)} profiles")
                        for pk, data in saved_measurements.items():
                            print(f"      PK {pk}:")
                            if 'crown' in data:
                                print(f"         👑 Crown: {data['crown']}")
                            if 'width' in data:
                                print(f"         📐 Width: {data['width']['distance']:.2f}m")
                    else:
                        # Check for legacy format (direct PK keys)
                        direct_measurements = {}
                        for key, value in measurements.items():
                            if isinstance(value, dict) and ('crown' in value or 'width' in value):
                                direct_measurements[key] = value
                        
                        if direct_measurements:
                            print(f"   📏 Direct measurements (legacy format): {len(direct_measurements)} profiles")
                            for pk, data in direct_measurements.items():
                                print(f"      PK {pk}:")
                                if 'crown' in data:
                                    crown = data['crown']
                                    print(f"         👑 Crown: ({crown['x']:.2f}, {crown['y']:.2f})")
                                if 'width' in data:
                                    width = data['width']
                                    print(f"         📐 Width: {width['distance']:.2f}m")
                                    print(f"         🤖 Auto-detected: {width.get('auto_detected', False)}")
                    
                    if 'current_pk' in measurements:
                        print(f"   🎯 Current PK: {measurements['current_pk']}")
                    
                    if 'measurement_mode' in measurements:
                        print(f"   🔧 Measurement mode: {measurements['measurement_mode']}")
                    
                    if 'operation_mode' in measurements:
                        print(f"   ⚙️ Operation mode: {measurements['operation_mode']}")
                    
                    if 'auto_detection_enabled' in measurements:
                        print(f"   🤖 Auto-detection: {measurements['auto_detection_enabled']}")
                
                elif section == 'file_paths':
                    paths = project_data[section]
                    for path_type, path in paths.items():
                        exists = os.path.exists(path) if path else False
                        status = "✅" if exists else "❌"
                        print(f"   {path_type}: {status} {path}")
            else:
                print(f"❌ {section}: Missing")
        
        print("\n🔄 Workflow Test Results:")
        print("-" * 30)
        
        # Check if all essential components are present
        measurements_data = project_data.get('measurements_data', {})
        has_saved_measurements = 'saved_measurements' in measurements_data and len(measurements_data['saved_measurements']) > 0
        
        # Check for direct measurements (legacy format)
        has_direct_measurements = False
        if not has_saved_measurements:
            for key, value in measurements_data.items():
                if isinstance(value, dict) and ('crown' in value or 'width' in value):
                    has_direct_measurements = True
                    break
        
        workflow_checks = {
            "Project metadata": 'project_info' in project_data,
            "File paths": 'file_paths' in project_data,
            "Measurement data": 'measurements_data' in project_data,
            "Has measurement data": has_saved_measurements or has_direct_measurements
        }
        
        for check, passed in workflow_checks.items():
            status = "✅" if passed else "❌"
            print(f"{status} {check}")
        
        all_passed = all(workflow_checks.values())
        
        print(f"\n{'🎉 ALL TESTS PASSED!' if all_passed else '⚠️ SOME ISSUES FOUND'}")
        
        if all_passed:
            print("\n📋 Next Steps:")
            print("1. Load this project in QGIS plugin")
            print("2. Open profile viewer")
            print("3. Verify measurements appear correctly")
            print("4. Check orthomosaic synchronization")
        
    else:
        print(f"❌ Test project not found: {test_project}")
        print("\n📋 To test:")
        print("1. Create a project with measurements in QGIS plugin")
        print("2. Save the project")
        print("3. Run this test again")

if __name__ == "__main__":
    test_workflow()