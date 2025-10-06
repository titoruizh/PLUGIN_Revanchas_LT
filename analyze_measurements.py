import json

file_path = r'C:\Users\LT_Gabinete_1\Downloads\Proyecto_Muro 1_20251002_1627.rvlt'
with open(file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

print('📊 Análisis detallado de mediciones guardadas:')
measurements = data.get('measurements_data', {})

for pk, pk_data in measurements.items():
    print(f'\n🎯 PK {pk}:')
    for measurement_type, measurement_data in pk_data.items():
        print(f'  ├─ {measurement_type}: {measurement_data}')

print(f'\n📈 Total PK con mediciones: {len(measurements)}')
print(f'📋 Estructura de cache esperada:')
print(f'  ├─ saved_measurements: dict con {len(measurements)} PK')
print(f'  ├─ operation_mode: {data.get("project_settings", {}).get("operation_mode", "N/A")}')
print(f'  └─ auto_detection_enabled: {data.get("project_settings", {}).get("auto_width_detection", "N/A")}')