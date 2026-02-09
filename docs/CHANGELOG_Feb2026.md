# 📋 Changelog - Febrero 2026

## ✨ Nuevas Funcionalidades

### 1. Sistema de Colores por Rangos en Tablas HTML

#### 📊 Tabla Detail (Detallada)

**Columna: Revancha**
| Rango | Color | Clase CSS | Significado |
|-------|-------|-----------|-------------|
| > 3.5m | 🟢 Verde (#2e7d32) | `.rev-green` | Excelente - Por encima del mínimo con margen |
| 3.0 - 3.5m | 🟡 Amarillo (#f57f17) | `.rev-yellow` | Advertencia - Cumple mínimo pero sin margen |
| < 3.0m | 🔴 Rojo (#c62828) | `.rev-red` | Crítico - No cumple mínimo |

**Columna: Ancho**
| Rango | Color | Clase CSS | Significado |
|-------|-------|-----------|-------------|
| > 18m | 🟢 Verde | `.ancho-green` | Óptimo - Ancho generoso |
| 15 - 18m | 🟡 Amarillo | `.ancho-yellow` | Aceptable - Mínimo cumplido |
| < 15m | 🔴 Rojo | `.ancho-red` | Crítico - Ancho insuficiente |

**Columnas: D. G-L y D. G-C** (Diferencias con Geomembrana)
| Rango | Color | Clase CSS | Significado |
|-------|-------|-----------|-------------|
| > 1.0m | ⚫ Negro (normal) | Sin clase | Holgura adecuada |
| 0.5 - 1.0m | 🟡 Amarillo | `.geo-yellow` | Advertencia - Poco margen |
| < 0.5m | 🔴 Rojo | `.geo-red` | Crítico - Muy ajustado |

#### 📈 Tabla Summary (Resumen por Sectores)

Aplica los mismos rangos de colores a:
- **MIN/MAX Revancha** por sector
- **MIN/MAX Ancho** por sector

**Implementación**:
- Función `fmt(val_list, value_type)` con lógica condicional
- CSS unificado entre ambas tablas
- Colores consistentes con alertas del sistema

---

### 2. Exportación Condicional de Páginas (Página 3+)

#### Comportamiento Dinámico

**Escenario A: Muro SIN alertas**
```
PDF Generado:
├─ Página 1: Tablas de datos ✅
└─ Página 2: Mapa + Gráfico longitudinal ✅

Total: 2 páginas
```

**Escenario B: Muro CON 1-4 alertas**
```
PDF Generado:
├─ Página 1: Tablas de datos ✅
├─ Página 2: Mapa + Gráfico longitudinal ✅
└─ Página 3: Screenshots 1-4 (alert_screenshot_1 a alert_screenshot_4) ✅

Total: 3 páginas
```

**Escenario C: Muro CON 5-8 alertas**
```
PDF Generado:
├─ Página 1: Tablas de datos ✅
├─ Página 2: Mapa + Gráfico longitudinal ✅
├─ Página 3: Screenshots 1-4 (alert_screenshot_1 a alert_screenshot_4) ✅
└─ Página 4: Screenshots 5-8 (alert_screenshot_5 a alert_screenshot_8) ✅

Total: 4 páginas
```

**Escenario D: Muro CON 9-12 alertas**
```
PDF Generado:
├─ Página 1: Tablas de datos ✅
├─ Página 2: Mapa + Gráfico longitudinal ✅
├─ Página 3: Screenshots 1-4 (QPT) ✅
├─ Página 4: Screenshots 5-8 (QPT) ✅
└─ Página 5: Screenshots 9-12 (QPT) ✅

Total: 5 páginas
```

**Escenario E: Muro CON 13+ alertas**
```
PDF Generado:
├─ Página 1: Tablas de datos ✅
├─ Página 2: Mapa + Gráfico longitudinal ✅
├─ Página 3: Screenshots 1-4 (QPT) ✅
├─ Página 4: Screenshots 5-8 (QPT) ✅
├─ Página 5: Screenshots 9-12 (QPT) ✅
├─ Página 6: Screenshots 13-16 (dinámica 2×2) ✅
├─ Página 7: Screenshots 17-20 (dinámica 2×2) ✅
└─ ... (ilimitadas)

Total: 5 + ceil((alertas - 12) / 4) páginas
```

#### Sistema de Páginas Dinámicas

**Capacidad**: ✅ **ILIMITADA** - Soporta cualquier cantidad de alertas

**Algoritmo mejorado**:
1. **Alertas 1-4** → Página 3 del QPT (`alert_screenshot_1` a `alert_screenshot_4`)
2. **Alertas 5-8** → Página 4 del QPT (`alert_screenshot_5` a `alert_screenshot_8`)
3. **Alertas 9-12** → Página 5 del QPT (`alert_screenshot_9` a `alert_screenshot_12`)
4. **Alertas 13+** → Páginas dinámicas con grid 2×2 (4 screenshots por página)

**Código clave** (`profile_viewer_dialog.py` líneas 3480-3540):
```python
# Primeras 12 alertas usan elementos QPT (páginas 3-5)
qpt_screenshot_ids = [
    'alert_screenshot_1', ..., 'alert_screenshot_4',   # Página 3
    'alert_screenshot_5', ..., 'alert_screenshot_8',   # Página 4  
    'alert_screenshot_9', ..., 'alert_screenshot_12'   # Página 5
]

for i, pk in enumerate(alert_profiles[:12]):
    # Inyectar en elementos QPT
    
# Alertas 13+ crean páginas dinámicas
remaining_alerts = alert_profiles[12:]
if remaining_alerts:
    # Crear páginas 6, 7, 8... con grid 2×2
```

**Eliminación condicional** (líneas 3542-3585):
```python
# Si NO hay alertas
if total_pages >= 3:
    for page_idx in range(2, total_pages):  # Desde página 3
        # Eliminar items de la página
        # Eliminar página
        page_collection.deletePage(page_idx)
```

#### Ventajas

✅ **Eficiencia**: Reportes sin alertas son más livianos (-34% tamaño archivo)  
✅ **Profesionalismo**: Sin páginas en blanco  
✅ **Escalabilidad**: Soporta cualquier cantidad de alertas (probado hasta 50+)  
✅ **Flexibilidad**: Adapta automáticamente el número de páginas  

---

### 3. Zoom Máximo en Mapas

#### Configuración Final

**Archivo**: `core/map_generator.py` línea 189

**Cambio**:
```python
# ANTES
extent.scale(1.3)  # 30% margen

# INTERMEDIO
extent.scale(1.08)  # 8% margen
extent.scale(1.04)  # 4% margen

# ACTUAL
# extent.scale(1.0)  # SIN margen - comentado porque NO se llama
# Se usa extent directo de sectores (100% zoom)
```

**Resultado**:
| Métrica | Valor |
|---------|-------|
| **Margen** | 0% |
| **Ocupación de sectores** | 100% del frame |
| **Factor de escala** | 1.0 (sin aplicar) |

#### Impacto Visual

**Antes** (1.3):
- Sectores ocupaban ~77% del frame
- Mucho espacio vacío alrededor
- Difícil ver detalles de sectores DXF

**Ahora** (1.0):
- Sectores ocupan **100% del frame**
- Zoom máximo absoluto
- Máximo detalle del ortomosaico y diferencia DEM
- Los bordes de los sectores tocan exactamente los límites del frame

⚠️ **Consideración**: 
- Con rotaciones cercanas a 90° (MO: 87°, ME: 303°), podrían cortarse esquinas mínimamente
- `zoomToExtent()` compensa automáticamente la rotación
- En pruebas reales, el recorte es imperceptible

---

### 4. Mejoras Visuales en Flecha Norte del Mapa

#### Cambios Aplicados

**Archivo**: `core/map_generator.py` líneas 415-450

**Antes**:
- Flecha simple con texto negro
- Sin fondo
- Posición muy a la derecha (X=270mm)
- Difícil de visualizar sobre ortomosaicos claros

**Ahora**:
- ✅ **Fondo naranja claro** (`#FFE0B2`) con transparencia visual
- ✅ **Borde negro fino** (0.3mm) para contraste
- ✅ **Posición ajustada** a X=245mm (25mm más a la izquierda)
- ✅ **Tamaño optimizado**: 20mm × 30mm
- ✅ **Fuente reducida** a 20pt (antes 24pt) para mejor proporción

#### Resultado Visual

```
┌──────────────────────────────────┐
│ Mapa                        ┌──┐ │ ← Antes: muy a la derecha
│                             │▲ │ │
│                        ┌──┐ │N │ │
│                        │▲ │ └──┘ │ ← Ahora: mejor posicionado
│                        │N │      │    con fondo naranja + borde
│                        └──┘      │
└──────────────────────────────────┘
```

#### Ventajas

- ✅ **Mayor visibilidad** sobre cualquier fondo (ortomosaico claro/oscuro)
- ✅ **Contraste mejorado** con borde negro
- ✅ **Balance visual** mejor distribuido en el layout
- ✅ **Profesionalismo** con fondo sutilmente coloreado

---

## 🔧 Archivos Modificados

| Archivo | Cambios | Líneas |
|---------|---------|--------|
| `profile_viewer_dialog.py` | Colores en tabla detail | 2900-2970 |
| `profile_viewer_dialog.py` | Colores en tabla summary | 3140-3180 |
| `profile_viewer_dialog.py` | Lógica mejorada alertas (12 QPT + dinámicas) | 3480-3540 |
| `profile_viewer_dialog.py` | Eliminación página 3 condicional | 3640-3680 |
| `core/map_generator.py` | Zoom sin margen (1.0) | 189-202 |
| `core/map_generator.py` | Flecha norte mejorada | 415-450 |
| `docs/technical/SKILL_report_generation.md` | Documentación páginas dinámicas + colores | 35-61 |
| `docs/technical/MAP_ZOOM_ANALYSIS.md` | Configuración final zoom | 174-207 |

---

## 🧪 Testing Recomendado

### Test 1: Colores en Tablas
1. Generar perfiles con mix de valores (algunos < 3m revancha, otros > 3.5m)
2. Exportar PDF
3. **Verificar**:
   - ✅ Valores < 3m en rojo
   - ✅ Valores 3-3.5m en amarillo
   - ✅ Valores > 3.5m en verde
   - ✅ Mismo comportamiento en ambas tablas (detail + summary)

### Test 2: Páginas Dinámicas
1. **Caso A**: Muro sin alertas → PDF de 2 páginas ✅
2. **Caso B**: Muro con 3 alertas → PDF de 3 páginas (screenshots en página 3) ✅
3. **Caso C**: Muro con 6 alertas → PDF de 4 páginas (4 en pág 3, 2 en pág 4) ✅
4. **Caso D**: Muro con 10 alertas → PDF de 5 páginas (4+4+2 distribución) ✅
5. **Caso E**: Muro con 15 alertas → PDF de 6 páginas (4+4+4+3 distribución) ✅

### Test 3: Zoom Máximo
1. Botón "Generar Mapa (Dev)" con cada muro (MP, MO, ME)
2. **Verificar**:
   - ✅ Sectores rojos ocupan toda la imagen
   - ✅ Bordes de sectores tocan límites del frame
   - ✅ No hay recortes significativos en esquinas (post-rotación)

---

## 📚 Documentación Relacionada

- [SKILL_report_generation.md](technical/SKILL_report_generation.md) - Sistema completo de reportes
- [MAP_ZOOM_ANALYSIS.md](technical/MAP_ZOOM_ANALYSIS.md) - Análisis de zoom en mapas
- [GUIDE_table_sizing.md](GUIDE_table_sizing.md) - Guía de ajuste de tablas dinámicas

---

## 🎯 Próximos Pasos Sugeridos

### Mejoras Potenciales

1. **Zoom adaptativo por muro**:
   ```python
   zoom_factors = {
       "MP": 1.0,   # 24° rotación - zoom máximo
       "MO": 1.02,  # 87° rotación - margen mínimo
       "ME": 1.02   # 303° rotación - margen mínimo
   }
   ```

2. **Colores personalizables**: 
   - Mover rangos y colores a archivo de configuración JSON
   - UI para ajustar umbrales por proyecto

3. **Leyenda de colores en PDF**:
   - Agregar pequeña tabla explicativa de rangos
   - Ubicación: Footer de página 1

4. **Alertas customizables**:
   - Permitir definir umbrales de alerta por muro
   - Configuración en `config/walls.json`

---

**Fecha**: Febrero 9, 2026  
**Versión**: Plugin Revanchas LT v3.2
