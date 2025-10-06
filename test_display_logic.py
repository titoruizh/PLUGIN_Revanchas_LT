import json

# Simular mediciones guardadas del proyecto
project_file = r'C:\Users\LT_Gabinete_1\Downloads\Proyecto_Muro 1_20251002_1627.rvlt'

with open(project_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

measurements = data['measurements_data']
pk_sample = '0+000'

print('🔍 Testing measurement display logic:')
print('=' * 50)

sample_measurement = measurements[pk_sample]
print(f'Sample measurement for {pk_sample}:')
print(json.dumps(sample_measurement, indent=2))

print('\n🧪 Testing display code:')
if 'width' in sample_measurement:
    width_data = sample_measurement['width']
    p1, p2 = width_data['p1'], width_data['p2']
    auto_detected = width_data.get('auto_detected', False)
    
    print(f'p1: {p1} (type: {type(p1)})')
    print(f'p2: {p2} (type: {type(p2)})')
    print(f'auto_detected: {auto_detected}')
    
    # Test access pattern from display code
    try:
        print(f'p1[0]: {p1[0]}, p1[1]: {p1[1]}')
        print(f'p2[0]: {p2[0]}, p2[1]: {p2[1]}')
        print('✅ Index access works correctly')
    except Exception as e:
        print(f'❌ Index access error: {e}')
        
    # Test the actual plotting values
    print(f'Distance: {width_data["distance"]:.2f}m')
    
print('\n🎯 Expected result:')
print('Should show green line with auto-detected width on profile')