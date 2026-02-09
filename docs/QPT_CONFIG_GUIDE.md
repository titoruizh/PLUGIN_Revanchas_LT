# Configuración del QPT para Sistema Híbrido

## Elementos Necesarios en `report_template.qpt`

### Página 1: Tablas y Screenshots de Alerta

**1. Elemento Gráfico** (Ya tienes ✅)
- **Tipo**: Picture
- **ID**: `chart`
- **Posición**: Arriba de la página

**2. Tablas HTML**
- **summary_table** - Tabla resumen (MIN/MAX por sector)
  - **Tipo**: HTML Frame
  - **ID**: `summary_table`
  
- **detail_table** - Tabla detalle (todas las mediciones)
  - **Tipo**: HTML Frame
  - **ID**: `detail_table`

**3. Screenshots de Alerta (1 a 4)** (Híbrido)
- **Tipo**: Picture (para cada uno)
- **IDs**: 
  - `alert_screenshot_1`
  - `alert_screenshot_2`
  - `alert_screenshot_3`
  - `alert_screenshot_4`
- **Posición**: Debajo de las tablas, grid 2x2
- **Tamaño recomendado**: ~130mm x 80mm cada uno

### Página 2: Mapa

**4. Mapa del Muro** (Ya tienes ✅)
- **Tipo**: Picture
- **ID**: `main_map`
- **Posición**: Toda la página

### Página 3+: Screenshots Adicionales (Dinámico)

- Se crean **automáticamente** si hay más de 4 alertas
- Grid 2x2, 4 screenshots por página

## Flujo del Sistema Híbrido

```
Alertas detectadas: N

Si N <= 4:
  → Usa solo elementos del QPT (alert_screenshot_1 a N)
  
Si N > 4:
  → Primeros 4: Usa elementos del QPT en página 1
  → Restantes: Crea páginas dinámicas desde página 3
```

## Ejemplo

**Proyecto con 7 alertas:**
- Página 1: Gráfico + Tablas + 4 screenshots (QPT)
- Página 2: Mapa
- Página 3: 3 screenshots restantes (dinámico)

**Proyecto con 2 alertas:**
- Página 1: Gráfico + Tablas + 2 screenshots (QPT)
- Página 2: Mapa

**Proyecto sin alertas:**
- Página 1: Gráfico + Tablas
- Página 2: Mapa
