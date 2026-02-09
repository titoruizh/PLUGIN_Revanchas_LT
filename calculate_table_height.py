"""
📏 CALCULADORA DE DIMENSIONES - Tabla Detail HTML

Este script te ayuda a calcular exactamente cuánto espacio necesitas
en el Frame del Layout QPT según la cantidad de filas.

USO RÁPIDO:
>>> from calculate_table_height import calculate_height
>>> calculate_height(45)  # Para un muro con 45 perfiles
"""

def calculate_height(num_rows):
    """
    Calcula la altura estimada de la tabla HTML según número de filas
    
    Args:
        num_rows (int): Número de perfiles/filas en el muro
        
    Returns:
        dict: Configuración recomendada y altura estimada
    """
    
    # Lógica de escalado (igual que en generate_detail_html_table)
    if num_rows > 80:
        config = {
            "font_size": "4.5px",
            "padding": "0.5px",
            "line_height": "1.1",
            "row_height_mm": 2.5
        }
    elif num_rows > 60:
        config = {
            "font_size": "5px",
            "padding": "1px",
            "line_height": "1.15",
            "row_height_mm": 2.8
        }
    elif num_rows > 40:
        config = {
            "font_size": "6px",
            "padding": "2px",
            "line_height": "1.2",
            "row_height_mm": 3.2
        }
    elif num_rows > 25:
        config = {
            "font_size": "6.5px",
            "padding": "2.5px",
            "line_height": "1.25",
            "row_height_mm": 3.5
        }
    else:
        config = {
            "font_size": "7px",
            "padding": "3px",
            "line_height": "1.3",
            "row_height_mm": 4.0
        }
    
    # Calcular altura total
    header_height = 10  # Header + sub-header (aprox 10mm)
    content_height = num_rows * config["row_height_mm"]
    total_height = header_height + content_height
    
    # Agregar margen de seguridad (5%)
    recommended_frame = total_height * 1.05
    
    # Redondear a múltiplos de 5mm para facilidad
    recommended_frame_rounded = round(recommended_frame / 5) * 5
    
    result = {
        "num_rows": num_rows,
        "css_config": config,
        "header_height_mm": header_height,
        "content_height_mm": round(content_height, 1),
        "total_height_mm": round(total_height, 1),
        "recommended_frame_mm": recommended_frame_rounded,
        "recommended_frame_str": f"{recommended_frame_rounded}mm"
    }
    
    # Imprimir resultado
    print("\n" + "─"*60)
    print(f"📏 CÁLCULO DE ALTURA PARA {num_rows} FILAS")
    print("─"*60)
    print(f"Configuración CSS:")
    print(f"  • Font:        {config['font_size']}")
    print(f"  • Padding:     {config['padding']}")
    print(f"  • Line Height: {config['line_height']}")
    print(f"\nDimensiones:")
    print(f"  • Header:      ~{header_height} mm")
    print(f"  • Contenido:   ~{result['content_height_mm']} mm")
    print(f"  • Total:       ~{result['total_height_mm']} mm")
    print(f"\n🎯 Frame Recomendado: {result['recommended_frame_str']}")
    print("─"*60 + "\n")
    
    return result


def generate_sizing_table():
    """Genera una tabla de referencia rápida para diferentes cantidades"""
    
    print("\n" + "="*80)
    print("📊 TABLA DE REFERENCIA RÁPIDA - DIMENSIONAMIENTO DE FRAMES")
    print("="*80)
    print(f"{'Filas':<8} {'Font':<8} {'Padding':<10} {'Line H.':<10} {'Altura Est.':<15} {'Frame QPT':<12}")
    print("─"*80)
    
    test_cases = [10, 20, 25, 30, 40, 50, 60, 70, 80, 90, 100]
    
    for rows in test_cases:
        result = calculate_height(rows)
        
        print(f"{rows:<8} "
              f"{result['css_config']['font_size']:<8} "
              f"{result['css_config']['padding']:<10} "
              f"{result['css_config']['line_height']:<10} "
              f"~{result['total_height_mm']} mm{'':<10} "
              f"{result['recommended_frame_str']:<12}")
    
    print("="*80)
    print("💡 TIP: Usa el valor de 'Frame QPT' para ajustar el Frame 'detail_table'")
    print("         en el Layout Designer de QGIS.")
    print("="*80 + "\n")


def interactive_calculator():
    """Calculadora interactiva para usuarios"""
    
    print("\n" + "="*70)
    print("🧮 CALCULADORA INTERACTIVA DE DIMENSIONES DE TABLA")
    print("="*70)
    
    while True:
        try:
            user_input = input("\n📊 ¿Cuántas filas tiene tu muro? (o 'q' para salir): ")
            
            if user_input.lower() in ['q', 'quit', 'salir', 'exit']:
                print("👋 Hasta luego!\n")
                break
            
            num_rows = int(user_input)
            
            if num_rows <= 0:
                print("⚠️ Ingresa un número positivo")
                continue
            
            if num_rows > 150:
                print("⚠️ ALERTA: Más de 150 filas puede ser inmanejable en una sola página")
                print("   Considera dividir el reporte en múltiples páginas")
            
            calculate_height(num_rows)
            
            # Sugerencias adicionales
            if num_rows > 80:
                print("⚠️ Con tantas filas, verifica que la letra sea legible en el PDF")
            elif num_rows < 15:
                print("✅ Con pocas filas, el layout estándar será más que suficiente")
            
        except ValueError:
            print("❌ Error: Ingresa un número válido")
        except KeyboardInterrupt:
            print("\n\n👋 Hasta luego!\n")
            break


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        try:
            rows = int(sys.argv[1])
            calculate_height(rows)
        except ValueError:
            print("❌ Uso: python calculate_table_height.py <número_de_filas>")
    else:
        # Mostrar tabla de referencia por defecto
        generate_sizing_table()
        
        # Ofrecer calculadora interactiva
        response = input("\n¿Quieres usar la calculadora interactiva? (s/n): ")
        if response.lower() in ['s', 'si', 'y', 'yes']:
            interactive_calculator()
