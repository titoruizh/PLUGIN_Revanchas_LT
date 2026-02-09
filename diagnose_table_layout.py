"""
🔍 HERRAMIENTA DE DIAGNÓSTICO - Ajuste de Tablas HTML en Layout QPT

Este script analiza los datos de cada muro y recomienda los ajustes óptimos
de tamaño de fuente, padding, y dimensiones del Frame en el Layout de QGIS.

USO:
1. Desde QGIS Python Console:
   >>> exec(open('diagnose_table_layout.py').read())

2. O ejecutar directamente este archivo después de cargar perfiles
"""

import os
import json

def analyze_wall_data():
    """Analiza todos los muros y genera reporte de dimensionamiento"""
    
    plugin_dir = os.path.dirname(__file__)
    data_dir = os.path.join(plugin_dir, 'data')
    
    print("\n" + "="*80)
    print("🔍 DIAGNÓSTICO COMPLETO - AJUSTE DE TABLAS PARA REPORTES PDF")
    print("="*80)
    
    # Buscar archivos CSV de lama points (indican cantidad de perfiles por muro)
    lama_dir = os.path.join(data_dir, 'lama_points')
    
    if not os.path.exists(lama_dir):
        print(f"⚠️ No se encontró directorio: {lama_dir}")
        print("   Primero debes cargar perfiles para cada muro.")
        return
    
    csv_files = [f for f in os.listdir(lama_dir) if f.endswith('.csv')]
    
    if not csv_files:
        print(f"⚠️ No hay archivos CSV en: {lama_dir}")
        return
    
    print(f"\n📁 Directorio de Datos: {lama_dir}")
    print(f"📊 Muros Encontrados: {len(csv_files)}\n")
    
    results = []
    
    for csv_file in sorted(csv_files):
        wall_name = csv_file.replace('_lama_points.csv', '').replace('_', ' ').title()
        csv_path = os.path.join(lama_dir, csv_file)
        
        # Contar líneas (filas) del CSV
        with open(csv_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            # Restar 1 por el header
            total_rows = len(lines) - 1 if len(lines) > 0 else 0
        
        # Determinar configuración óptima
        if total_rows > 80:
            config = {
                "font_size": "4.5px",
                "padding": "0.5px", 
                "line_height": "1.1",
                "frame_height": "220mm",
                "row_height_mm": 2.5
            }
        elif total_rows > 60:
            config = {
                "font_size": "5px",
                "padding": "1px",
                "line_height": "1.15", 
                "frame_height": "210mm",
                "row_height_mm": 2.8
            }
        elif total_rows > 40:
            config = {
                "font_size": "6px",
                "padding": "2px",
                "line_height": "1.2",
                "frame_height": "190mm",
                "row_height_mm": 3.2
            }
        elif total_rows > 25:
            config = {
                "font_size": "6.5px",
                "padding": "2.5px",
                "line_height": "1.25",
                "frame_height": "170mm",
                "row_height_mm": 3.5
            }
        else:
            config = {
                "font_size": "7px",
                "padding": "3px",
                "line_height": "1.3",
                "frame_height": "150mm",
                "row_height_mm": 4.0
            }
        
        estimated_height = total_rows * config["row_height_mm"]
        
        results.append({
            "wall": wall_name,
            "rows": total_rows,
            "config": config,
            "estimated_height": estimated_height
        })
        
        # Imprimir reporte individual
        print(f"{'─'*80}")
        print(f"📌 {wall_name.upper()}")
        print(f"{'─'*80}")
        print(f"   Total Perfiles: {total_rows}")
        print(f"   Font Size:      {config['font_size']}")
        print(f"   Padding:        {config['padding']}")
        print(f"   Line Height:    {config['line_height']}")
        print(f"   Altura Tabla:   ~{estimated_height:.1f} mm")
        print(f"   Frame Sugerido: {config['frame_height']}")
        
        # Alertas
        if total_rows > 70:
            print(f"   ⚠️ ALERTA: Muro con MUCHAS filas - Requiere compresión máxima")
        elif total_rows < 20:
            print(f"   ✅ OK: Muro con pocas filas - Layout estándar suficiente")
        
        print()
    
    print("="*80)
    print("📋 RESUMEN Y RECOMENDACIONES")
    print("="*80)
    
    max_rows = max(r["rows"] for r in results)
    min_rows = min(r["rows"] for r in results)
    avg_rows = sum(r["rows"] for r in results) / len(results)
    
    print(f"\n📊 Estadísticas Globales:")
    print(f"   • Mínimo de filas: {min_rows}")
    print(f"   • Máximo de filas: {max_rows}")
    print(f"   • Promedio:        {avg_rows:.1f}")
    
    if max_rows - min_rows > 30:
        print(f"\n⚠️ VARIACIÓN ALTA entre muros ({max_rows - min_rows} filas de diferencia)")
        print(f"   → El sistema ajusta AUTOMÁTICAMENTE el CSS según cada muro")
        print(f"   → Pero el FRAME del Layout QPT es FIJO para todos")
        print(f"\n🛠️ SOLUCIÓN RECOMENDADA:")
        print(f"   1. Ajustar el Frame 'detail_table' en report_template.qpt")
        print(f"   2. Usar el MÁXIMO recomendado: {results[0]['config']['frame_height']}")
        print(f"      (para el muro con más filas: {results[0]['wall']})")
        print(f"   3. Los muros con menos filas se verán OK (espacio sobrante abajo)")
    else:
        print(f"\n✅ VARIACIÓN BAJA - Todos los muros tienen cantidad similar de filas")
        print(f"   → Usar Frame de: {results[0]['config']['frame_height']}")
    
    print("\n" + "="*80)
    print("🎯 PASOS PARA AJUSTAR EN QGIS LAYOUT DESIGNER:")
    print("="*80)
    print("1. Proyecto → Gestor de Composición de Impresión")
    print("2. Abrir 'report_template.qpt' (o tu plantilla activa)")
    print("3. Seleccionar elemento 'detail_table' en el canvas")
    print("4. Panel derecho → 'Propiedades del elemento'")
    print("5. Sección 'Posición y tamaño':")
    print(f"   - Ajustar ALTO (Height) a: {max(r['config']['frame_height'] for r in results)}")
    print("6. Guardar plantilla (Ctrl+S)")
    print("7. Volver a generar el PDF y verificar")
    print("="*80 + "\n")
    
    # Guardar JSON para análisis posterior
    output_path = os.path.join(plugin_dir, 'table_sizing_analysis.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Análisis guardado en: {output_path}\n")

if __name__ == "__main__":
    analyze_wall_data()
