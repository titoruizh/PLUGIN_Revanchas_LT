# 📐 Guía de Ajuste Dinámico de Tablas HTML en Reportes PDF

## Problema

Cada muro tiene diferente cantidad de perfiles (filas), por lo que la tabla de detalles puede:
- **Desbordarse** (muros con muchas filas)
- **Quedar con espacio vacío** (muros con pocas filas)

## Solución Implementada

### 1. **Ajuste Automático de CSS** (Ya implementado) ✅

El código ahora ajusta **automáticamente**:
- `font-size` (tamaño de letra)
- `padding` (espaciado interno de celdas)
- `line-height` (altura de línea)

Según esta tabla:

| Filas | Font Size | Padding | Line Height | Comentario |
|-------|-----------|---------|-------------|------------|
| > 80  | 4.5px     | 0.5px   | 1.1         | Compresión máxima |
| > 60  | 5px       | 1px     | 1.15        | Alta densidad |
| > 40  | 6px       | 2px     | 1.2         | Densidad media |
| > 25  | 6.5px     | 2.5px   | 1.25        | Densidad normal |
| ≤ 25  | 7px       | 3px     | 1.3         | Layout estándar |

### 2. **Ajuste Manual del Frame en QPT** (Requerido) ⚙️

El Frame `detail_table` en el Layout QPT tiene un **tamaño fijo** que debes ajustar según el muro con **MÁS filas**.

---

## 🔍 Herramientas de Diagnóstico

### Opción A: Script Independiente

Ejecuta desde la raíz del plugin:

```python
# En QGIS Python Console
import os
os.chdir(r'C:\Users\LT_Gabinete_1\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\PLUGIN_Revanchas_LT')
exec(open('diagnose_table_layout.py').read())
```

**Esto te dará**:
- ✅ Análisis de TODOS los muros
- ✅ Cantidad de filas de cada uno
- ✅ Configuración CSS aplicada automáticamente
- ✅ **Recomendación de altura del Frame** para el Layout QPT
- ✅ Archivo JSON con el análisis completo

### Opción B: Desde el Dialog de Perfiles

Cuando tengas un muro cargado en el visor de perfiles:

```python
# En QGIS Python Console (con el dialog abierto)
dialog = iface.activeWindow()  # O referencia directa al ProfileViewerDialog
dialog.diagnose_table_sizing()
```

**Esto te dará**:
- ✅ Análisis del muro ACTUAL
- ✅ Configuración CSS que se está aplicando
- ✅ Altura estimada de la tabla
- ✅ Recomendación de Frame Height

---

## 🛠️ Pasos para Ajustar el Layout QPT

### 1. Ejecutar Diagnóstico

Usa cualquiera de las opciones anteriores para saber:
- ¿Cuál es el muro con más filas?
- ¿Qué altura de Frame necesitas?

**Ejemplo de salida**:
```
🔍 DIAGNÓSTICO COMPLETO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📌 MURO 3
   Total Perfiles: 68
   Frame Sugerido: 210mm
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🛠️ SOLUCIÓN RECOMENDADA:
   Ajustar Frame 'detail_table' a: 210mm
```

### 2. Abrir el Layout Designer

1. En QGIS: **Proyecto → Gestor de Composiciones de Impresión**
2. Selecciona o abre `report_template.qpt`

### 3. Seleccionar el Frame

1. En el canvas, haz clic en el elemento **`detail_table`**
2. Verás que se resalta en el panel izquierdo ("Elementos")

### 4. Ajustar Propiedades

En el panel derecho (**Propiedades del elemento**):

1. Ve a la sección **"Posición y tamaño"**
2. Busca el campo **Alto (Height)**
3. Cambia el valor a la altura recomendada (ej: `210mm`)
4. Presiona **Enter** para aplicar

![Example](https://via.placeholder.com/600x300?text=Propiedades+del+Frame)

### 5. Ajustar Posición (Si es necesario)

Si al aumentar la altura el frame choca con otros elementos:
- Ajusta **Y (posición vertical)** para moverlo hacia arriba
- O mueve los elementos de abajo (ej: screenshots) más abajo

### 6. Guardar y Probar

1. **Guardar plantilla**: `Composición → Guardar como Plantilla` o `Ctrl+S`
2. Cierra el Layout Designer
3. **Genera un PDF de prueba** desde el plugin
4. Verifica que toda la tabla esté visible

---

## 📊 Verificación de Resultados

Al generar el PDF, revisa en la consola de QGIS:

```
📊 DIAGNÓSTICO TABLA DETAIL:
   Muro: Muro 3
   Total Filas: 68
   Ajuste aplicado: font=5px, padding=1px, line-height=1.15
```

Esto confirma que el CSS se está ajustando automáticamente.

Si la tabla **AÚN se corta**:
1. Aumenta el Frame en **+10mm** y prueba de nuevo
2. O reduce ligeramente el `font-size` manualmente en el código (última opción)

---

## 🎯 Casos de Uso Comunes

### Caso 1: Todos los muros tienen ~30 filas
✅ **Solución Simple**: Frame de `170mm` funciona para todos

### Caso 2: Mezcla (20 a 70 filas)
⚠️ **Solución**: Ajustar Frame al **máximo** (ej: `210mm`)
- Muros con pocas filas tendrán espacio vacío abajo (es normal)
- Muros con muchas filas calzarán perfecto

### Caso 3: Un muro tiene +80 filas
🔥 **Solución Agresiva**:
1. Frame de `220mm`
2. Si no alcanza, considera:
   - Reducir `font-size` mínimo a `4px` en el código
   - Usar layout de 2 páginas (dividir tabla)

---

## 🐛 Troubleshooting

### Problema: La tabla sigue cortada
**Causas posibles**:
- Frame muy pequeño → **Aumentar Height en +10mm**
- Márgenes internos del frame → Verificar en QPT que no tenga padding

### Problema: Letra muy pequeña, ilegible
**Causas posibles**:
- Demasiadas filas (>80) → **Reducir cantidad de perfiles** o usar 2 páginas
- Configuración CSS muy agresiva → Ajustar rangos en `generate_detail_html_table()`

### Problema: PDF en blanco
**Causas posibles**:
- El HTML no se procesó → Ya solucionado con `time.sleep(1.0)` en el código
- Item ID incorrecto → Verificar que el Frame se llame `detail_table` en QPT

---

## 📝 Notas Técnicas

### ¿Por qué no se auto-ajusta el Frame?

El Layout QPT de QGIS **NO permite cambiar dinámicamente** el tamaño de elementos via código (API limitada). Solo podemos:
- ✅ Cambiar contenido HTML (CSS)
- ❌ Cambiar dimensiones del Frame

Por eso necesitas **un ajuste manual único** del Frame para el peor caso (muro con más filas).

### ¿Puedo tener diferentes plantillas por muro?

Sí, puedes crear:
- `report_template_small.qpt` (para muros < 30 filas)
- `report_template_large.qpt` (para muros > 50 filas)

Y luego en el código, cargar condicionalmente:
```python
if total_rows > 50:
    template_path = os.path.join(plugin_dir, 'report_template_large.qpt')
else:
    template_path = os.path.join(plugin_dir, 'report_template_small.qpt')
```

---

## ✅ Checklist Final

Antes de generar PDFs de producción:

- [ ] Ejecutaste `diagnose_table_layout.py` para conocer el rango de filas
- [ ] Ajustaste el Frame `detail_table` en QPT a la altura máxima recomendada
- [ ] Guardaste la plantilla QPT
- [ ] Generaste un PDF de prueba del muro con MÁS filas
- [ ] Verificaste que toda la tabla es visible (sin cortes)
- [ ] Generaste un PDF del muro con MENOS filas (debe verse OK con espacio vacío)

---

**🎉 ¡Listo! Ahora tienes un sistema robusto que se adapta a cualquier cantidad de filas.**
