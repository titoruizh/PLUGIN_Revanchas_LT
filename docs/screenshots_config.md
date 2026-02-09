# Screenshots de Alerta - Configuración

## Cómo Funciona Actualmente

**Sistema Dinámico (Páginas Automáticas)**:
- Detecta perfiles con alertas (revancha < 3m o ancho < 15m)
- Crea **páginas nuevas automáticamente** (página 2, 3, 4...)
- Posiciona 4 screenshots por página (grid 2x2)
- **NO usa elementos del QPT**, genera todo programáticamente

## Opciones para Personalizar

### Opción 1: Usar Elementos del QPT (Tu Preferencia)

**Cómo implementarlo**:

1. **En tu QPT**, agrega elementos Picture con IDs:
   - `alert_screenshot_1`
   - `alert_screenshot_2`
   - `alert_screenshot_3`
   - `alert_screenshot_4`

2. **El código** buscará estos elementos y los llenará
3. **Ventaja**: Control total de posición/tamaño en el diseñador QGIS
4. **Limitación**: Solo 4 screenshots por página (o los que definas)

### Opción 2: Sistema Híbrido

- Primeros 4 screenshots usan elementos del QPT
- Si hay más de 4 alertas, se crean páginas adicionales dinámicamente

### Opción 3: Deshabilitar Screenshots

Si prefieres reportes sin screenshots de alerta, puedo comentar esa sección.

## Código Actual

Los screenshots se generan en la línea **3186-3270** de `profile_viewer_dialog.py`:

```python
if alert_profiles:
    # Crea páginas nuevas
    # Cambia perfiles uno por uno
    # Captura screenshots
    # Los posiciona en grid 2x2
```

## ¿Qué Prefieres?

1. ✅ **Opción 1**: Modifico el código para usar `alert_screenshot_1` ... `alert_screenshot_4` del QPT
2. ⚠️ **Opción 2**: Híbrido (primeros 4 en QPT, resto en páginas nuevas)
3. ❌ **Opción 3**: Deshabilitar screenshots completamente

**Déjame saber y lo implemento!**
