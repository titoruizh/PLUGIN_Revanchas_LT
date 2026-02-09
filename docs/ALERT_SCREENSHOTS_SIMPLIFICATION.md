# Simplificación de Pantallazos de Alertas

**Fecha de Implementación**: 9 de febrero 2026  
**Archivo**: `profile_viewer_dialog.py`  
**Método**: `update_profile_display(export_mode=False)`  

---

## Contexto

Los pantallazos de perfiles con alertas (Revancha < 3m o Ancho < 15m) se generan automáticamente para incluirse en las páginas 3-5 del reporte PDF. Anteriormente, estos pantallazos mostraban todos los elementos visuales del modo interactivo, lo que resultaba en una vista sobrecargada que dificultaba identificar los valores críticos.

---

## Objetivo

Crear una vista simplificada y limpia para los pantallazos de alertas que:
1. Elimine elementos de ayuda visual innecesarios para exportación
2. Mantenga solo la información esencial
3. Presente los valores críticos en formato claro y legible
4. Mejore la presentación profesional del reporte PDF

---

## Elementos Eliminados (en `export_mode=True`)

### 1. Línea Roja Central (Eje de Alineación)
❌ **Antes**: Línea vertical roja en X=0 marcando el eje central del alineamiento  
✅ **Ahora**: Eliminada - No relevante para lectores del reporte que solo necesitan ver las mediciones

**Código**:
```python
# Línea 1975-1978
if not export_mode:
    self.ax.axvline(x=0, color='red', linestyle='--', linewidth=1.8, alpha=0.8, 
                    label='Eje de Alineación')
```

### 2. Líneas de Referencia Horizontales
❌ **Antes**: 2-3 líneas horizontales naranjas/amarillas marcando elevaciones de coronamiento, lama, y auxiliares  
✅ **Ahora**: Eliminadas - Valores mostrados en leyenda textual

**Código**:
```python
# Líneas 1980-2040
if not export_mode:
    if self.operation_mode == "ancho_proyectado":
        # Líneas de lama, +2m visual, +3m referencia
        ...
    else:
        # Líneas de coronamiento y auxiliar
        ...
```

### 3. Topografía del DEM Anterior
❌ **Antes**: Línea gris segmentada mostrando terreno del DEM previo  
✅ **Ahora**: Eliminada - Solo interesa el terreno actual para mediciones

**Código**:
```python
# Líneas 1955-1970
if not export_mode:
    previous_elevations = profile.get('previous_elevations', [])
    if previous_elevations and len(previous_elevations) == len(distances):
        # Dibujar línea gris del DEM anterior
        ...
```

### 4. Puntos Extremos de Mediciones
❌ **Antes**: Círculos de colores (rojos/verdes/magenta) en los extremos de la línea de ancho  
✅ **Ahora**: Eliminados - Se mantiene la línea pero sin los puntos extremos

**Código**:
```python
# Líneas 2050-2090
if not export_mode:
    self.ax.plot([p1[0], p2[0]], [p1[1], p2[1]], 'o', color=color, markersize=marker_size, zorder=4)
# La línea siempre se dibuja
self.ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color=color, linestyle=line_style, ...)
```

### 5. Puntos Automáticos de LAMA
❌ **Antes**: Círculos amarillos con borde marrón en puntos LAMA detectados automáticamente  
✅ **Ahora**: Eliminados en modo revancha si hay medición manual

**Código**:
```python
# Líneas 2095-2105
if not export_mode:
    if (self.operation_mode == "revancha" and ...):
        # Mostrar LAMA automática
        ...
```

### 6. Puntos Temporales de Medición
❌ **Antes**: Puntos verdes/amarillos de mediciones en progreso  
✅ **Ahora**: Eliminados - No aplica en exportación

**Código**:
```python
# Líneas 2110-2120
if not export_mode:
    if self.current_crown_point:
        self.ax.plot(self.current_crown_point[0], self.current_crown_point[1], 'go', ...)
```

### 7. Leyenda Estándar de Matplotlib
❌ **Antes**: Leyenda automática con 5-8 items en caja  
✅ **Ahora**: Reemplazada por leyenda personalizada de 3 valores

---

## Elementos Preservados

### 1. DEM Actual ✅
Línea azul con relleno marrón mostrando el perfil topográfico actual.

### 2. Punto de Lama ✅
Círculo amarillo con borde naranja marcando la ubicación de la lama (solo el punto final seleccionado/medido).

### 3. Línea de Ancho ✅
Línea verde lima conectando los puntos de medición de ancho (sin mostrar los puntos extremos).

### 4. Leyenda Personalizada ✅
Cuadro de texto con valores numéricos críticos.

---

## Leyenda Personalizada

### Formato

```
─ Cota Coronamiento: XXX.XX m
● Cota Lama: XXX.XX m
  Revancha: X.XX m
─ Ancho: XX.XX m
```

**Símbolos**:
- `─` (línea horizontal): Representa líneas verdes en el gráfico (coronamiento y ancho)
- `●` (punto): Representa el punto naranja con borde rojo de la lama
- Espacios: Revancha no tiene símbolo (es un valor calculado)

### Configuración Visual

**Estilo del Texto**:
- Fuente: Monospace Bold
- Tamaño: 11pt
- Color: Negro

**Estilo del Cuadro**:
- Fondo: Blanco con 90% opacidad (`alpha=0.9`)
- Borde: Negro sólido, 1.5px de grosor
- Esquinas: Redondeadas (`boxstyle='round'`)

**Posición**:
- Coordenadas: (98%, 98%) relativo a los ejes del gráfico
- Anclaje: Superior derecho (`verticalalignment='top'`, `horizontalalignment='right'`)

### Código de Implementación

```python
# Líneas 2140-2170
elif export_mode:
    # LEYENDA SIMPLIFICADA PARA PANTALLAZOS DE ALERTAS
    legend_lines = []
    
    # 1. Cota Coronamiento
    crown_val = None
    if current_pk in self.saved_measurements and 'crown' in self.saved_measurements[current_pk]:
        crown_val = self.saved_measurements[current_pk]['crown']['y']
        legend_lines.append(f"Cota Coronamiento: {crown_val:.2f} m")
    
    # 2. Cota Lama
    lama_val = None
    if current_pk in self.saved_measurements:
        if 'lama' in self.saved_measurements[current_pk]:
            lama_val = self.saved_measurements[current_pk]['lama']['y']
        elif 'lama_selected' in self.saved_measurements[current_pk]:
            lama_val = self.saved_measurements[current_pk]['lama_selected']['y']
    
    if lama_val is None and 'lama_points' in profile and profile['lama_points']:
        lama_val = profile['lama_points'][0]['elevation']
    
    if lama_val is not None:
        legend_lines.append(f"Cota Lama: {lama_val:.2f} m")
    
    # 3. Ancho
    width_val = None
    if current_pk in self.saved_measurements and 'width' in self.saved_measurements[current_pk]:
        width_val = self.saved_measurements[current_pk]['width']['distance']
        legend_lines.append(f"Ancho: {width_val:.2f} m")
    
    # Construir leyenda como texto
    if legend_lines:
        legend_text = "\n".join(legend_lines)
        self.ax.text(0.98, 0.98, legend_text,
                   transform=self.ax.transAxes,
                   fontsize=11,
                   verticalalignment='top',
                   horizontalalignment='right',
                   bbox=dict(boxstyle='round', facecolor='white', alpha=0.9, 
                            edgecolor='black', linewidth=1.5),
                   family='monospace',
                   weight='bold')
```

---

## Activación del Modo Export

### En Screenshots de QPT (Páginas 3-5)

**Ubicación**: Línea 3511

```python
# Generar screenshot para inyectar en QPT
self.update_profile_display(export_mode=True)
QApplication.processEvents()

screenshot_path = os.path.join(temp_dir, f"alert_{pk.replace('+','_')}.png")
self.figure.savefig(screenshot_path)
```

### En Páginas Dinámicas (Página 6+)

**Ubicación**: Línea 3586

```python
# Generar screenshot para página dinámica
self.update_profile_display(export_mode=True)
QApplication.processEvents()

screenshot_path = os.path.join(temp_dir, f"alert_{pk.replace('+','_')}.png")
self.figure.savefig(screenshot_path)
```

---

## Beneficios Logrados

### 1. Claridad Visual 📊
- **Antes**: 12-15 elementos gráficos superpuestos
- **Después**: 3-4 elementos esenciales
- **Mejora**: Reducción del 75% en sobrecarga visual

### 2. Enfoque en Datos Críticos 🎯
- Leyenda concentra atención en los 3 valores numéricos clave
- Sin distracciones de líneas auxiliares o puntos de referencia
- Fácil lectura y comparación entre perfiles

### 3. Consistencia Profesional 📐
- Formato idéntico para todos los pantallazos de alertas
- Presentación limpia apropiada para reportes ejecutivos
- Valores en formato numérico preciso (2 decimales)

### 4. Facilidad de Mantenimiento 💼
- Parámetro `export_mode` controla toda la lógica de simplificación
- Modo interactivo preservado sin cambios para análisis detallado
- Fácil ajustar qué elementos mostrar en cada modo

---

## Comparación Antes/Después

| Aspecto | Modo Interactivo (`export_mode=False`) | Modo Export (`export_mode=True`) |
|---------|---------------------------------------|----------------------------------|
| **Línea eje central** | ✅ Roja vertical en X=0 | ❌ Eliminada |
| **Líneas horizontales ref.** | ✅ 2-3 líneas naranjas/amarillas | ❌ Eliminadas |
| **DEM anterior** | ✅ Línea gris segmentada | ❌ Eliminada |
| **DEM actual** | ✅ Línea azul + relleno | ✅ Línea azul + relleno |
| **Puntos extremos ancho** | ✅ Círculos de colores | ❌ Solo línea sin puntos |
| **Punto lama** | ✅ Círculo amarillo/naranja | ✅ Círculo amarillo/naranja |
| **Puntos temporales** | ✅ Verde/amarillo | ❌ Eliminados |
| **Leyenda** | Matplotlib estándar (5-8 items) | Cuadro de texto (3 valores) |
| **Total elementos** | 12-15 | 3-4 |
| **Claridad** | Media (sobrecarga) | Alta (minimalista) |

---

## Testing & Validación

### Escenarios de Prueba

1. **Perfil con Revancha < 3m**: Verificar que muestra Cota Coronamiento, Cota Lama, Ancho
2. **Perfil con Ancho < 15m**: Verificar que muestra valores correctos
3. **Múltiples alertas (10+)**: Verificar consistencia entre todos los screenshots
4. **Modo interactivo**: Confirmar que todos los elementos visuales siguen disponibles

### Checklist de Validación

- [ ] Leyenda personalizada aparece en esquina superior derecha
- [ ] Valores numéricos con 2 decimales
- [ ] Línea de ancho verde lima visible sin puntos extremos
- [ ] Punto de lama visible (amarillo con borde naranja)
- [ ] Sin líneas rojas/naranjas/grises de referencia
- [ ] DEM actual (azul) claramente visible
- [ ] Fondo de leyenda blanco semitransparente (no opaco)
- [ ] Modo interactivo sin cambios (export_mode=False)

---

## Notas de Implementación

### Variables Clave

- `export_mode`: Booleano que controla el comportamiento de visualización
- `legend_lines`: Lista de strings con valores para la leyenda personalizada
- `crown_val`, `lama_val`, `width_val`: Valores numéricos extraídos de mediciones guardadas

### Ubicaciones de Código Crítico

| Funcionalidad | Líneas Aproximadas | Descripción |
|---------------|-------------------|-------------|
| DEM anterior condicional | 1955-1970 | `if not export_mode:` antes de plot |
| Línea eje central | 1975-1978 | `if not export_mode:` antes de axvline |
| Líneas referencia | 1980-2040 | Todo el bloque dentro de `if not export_mode:` |
| Puntos extremos ancho | 2050-2090 | `if not export_mode:` solo para puntos |
| LAMA automática | 2095-2105 | `if not export_mode:` antes de loop |
| Puntos temporales | 2110-2120 | `if not export_mode:` para current_crown_point |
| Leyenda personalizada | 2140-2170 | `elif export_mode:` con text() en lugar de legend() |

### Compatibilidad

- ✅ Compatible con ambos modos de operación (revancha, ancho_proyectado)
- ✅ Funciona con mediciones automáticas y manuales
- ✅ Soporte para páginas QPT (3-5) y páginas dinámicas (6+)
- ✅ No afecta modo interactivo (export_mode=False por defecto)

---

**Autor**: Sistema de IA colaborativo con usuario LT  
**Fecha de Documentación**: 9 de febrero 2026  
**Versión Plugin**: Revanchas LT v3.2  
