import json

project_file = r'C:\Users\LT_Gabinete_1\Downloads\Proyecto_Muro 1_20251002_1627.rvlt'

with open(project_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

measurements = data['measurements_data']
pk_sample = '0+000'

print('Width data structure in saved measurement:')
print('=' * 50)
sample = measurements[pk_sample]
if 'width' in sample:
    width_data = sample['width']
    print('Width data:')
    print(json.dumps(width_data, indent=2))
    print()
    print('Point formats:')
    print('p1 type:', type(width_data["p1"]), ', value:', width_data["p1"])
    print('p2 type:', type(width_data["p2"]), ', value:', width_data["p2"])