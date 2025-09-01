# PLUGIN_Revanchas_LT
Mejora procesos y automatización Revanchas Las Tortolas

## 🎯 Descripción General

Plugin para QGIS especializado en análisis topográfico de muros de contención, con dos modos de operación:

- **🔧 MODO REVANCHA**: Análisis tradicional completo (Coronamiento, LAMA, Revancha, Ancho)
- **📐 MODO ANCHO PROYECTADO**: Análisis simplificado para cálculo de anchos proyectados

## 🚀 Nuevas Funcionalidades (2025)

### 📐 **MODO ANCHO PROYECTADO**
- **Toggle visual** para alternar entre modos de operación
- **Selección de punto Lama** en terreno natural
- **Auto-generación** de línea de referencia 3 metros arriba
- **Auto-detección** de ancho proyectado en línea +3m
- **Exportación simplificada** (solo PK + Ancho)
- **Interfaz adaptativa** que oculta elementos no necesarios

### 🔧 **MODO REVANCHA** (Funcionalidad Original)
- Análisis completo de perfiles topográficos
- Cálculo automático de Revanchas
- Puntos LAMA automáticos + override manual
- Exportación completa con todas las métricas

## 🎛️ Características Principales

### 📊 **Visualizador Interactivo de Perfiles**
- Navegación fluida entre perfiles (PK)
- Herramientas de zoom y pan optimizadas
- Auto-detección inteligente de anchos
- Medición manual con snap automático (tecla 'A')

### 📏 **Herramientas de Medición**
- **Cota Coronamiento/Lama**: Snap al terreno natural
- **Medición de Ancho**: Con líneas de referencia dinámicas
- **Auto-detección**: Algoritmos avanzados de intersección
- **Override manual**: Control total del usuario cuando necesario

### 📈 **Líneas de Referencia Inteligentes**
#### Modo Revancha:
- Línea de coronamiento horizontal
- Línea auxiliar (-1m) para referencia

#### Modo Ancho Proyectado:
- Línea visual en punto Lama
- Línea de medición (+3m) para cálculos

### 📋 **Exportación de Datos**
#### CSV Ancho Proyectado:
```csv
PK,Ancho_Proyectado
0+000,12.450
0+020,11.200
```

#### CSV Revancha Completa:
```csv
PK,Cota_Coronamiento,Revancha,Lama,Ancho
0+000,105.230,2.150,103.080,12.450
0+020,104.890,1.980,102.910,11.200
```

## 🖥️ Interfaz de Usuario

### 🧭 **Panel de Navegación**
- **Toggle de Modo**: Alternar entre Revancha/Ancho Proyectado
- **Controles de PK**: Botones anterior/siguiente + slider
- **Contador de perfiles**: Posición actual / total

### 🔧 **Panel de Herramientas**
#### Modo Revancha:
- 📍 Cota Coronamiento
- 📏 Medir Ancho  
- 🟡 Modificar LAMA
- 🗑️ Limpiar

#### Modo Ancho Proyectado:
- 📍 Seleccionar Lama
- 📏 Medir Ancho Proyectado
- 🗑️ Limpiar

### ℹ️ **Panel de Información**
- Información del perfil actual
- Coordenadas y elevaciones
- Puntos válidos y rangos de datos
- Estado de líneas de referencia

## 🎨 **Visualización Avanzada**

### 🌍 **Elementos Gráficos**
- **Terreno Natural**: Línea azul con relleno marrón
- **Eje de Alineación**: Línea roja discontinua (centerline)
- **Puntos de Medición**: Códigos de color por tipo y método
- **Líneas de Referencia**: Diferentes estilos según función

### 🎯 **Código de Colores**
- **Verde Lima**: Mediciones auto-detectadas
- **Magenta**: Mediciones manuales
- **Amarillo**: Puntos LAMA (auto/manual)
- **Naranja**: Líneas de referencia principales
- **Gris**: Líneas auxiliares

## ⚙️ **Algoritmos Avanzados**

### 🤖 **Auto-detección de Anchos**
- Intersección exacta con terreno natural
- Interpolación lineal entre puntos
- Búsqueda direccional optimizada
- Manejo robusto de casos límite

### 📐 **Cálculo de Ancho Proyectado**
- Generación automática de línea +3m
- Intersección con perfil topográfico
- Validación de resultados
- Fallback a medición manual

## 🗂️ **Estructura de Archivos**

```
PLUGIN_Revanchas_LT/
├── profile_viewer_dialog.py     # Visualizador principal ⭐ MODIFICADO
├── revanchas_lt_plugin.py       # Plugin principal
├── dialog.py                    # Dialog principal
├── welcome_dialog.py            # Dialog de bienvenida
├── core/
│   ├── alignment_data.py        # Datos de alineación
│   ├── dem_processor.py         # Procesamiento DEM
│   ├── profile_generator.py     # Generación de perfiles
│   ├── wall_analyzer.py         # Análisis de muros
│   └── visualization.py         # Herramientas de visualización
├── data/
│   ├── alignments/             # Datos de alineaciones
│   └── lama_points/           # Puntos LAMA por muro
├── NUEVAS_FUNCIONALIDADES.md   # 📄 Documentación detallada ⭐ NUEVO
└── README.md                   # Este archivo
```

## 🚀 **Instalación y Uso**

### 📥 Instalación
1. Copiar plugin a directorio QGIS plugins
2. Activar en "Administrador de Complementos"
3. Aparecerá ícono en barra de herramientas

### 🎮 Uso Básico
1. **Ejecutar plugin** → Dialog de bienvenida
2. **Seleccionar muro** → Carga automática de perfiles
3. **Elegir modo** → Toggle Revancha/Ancho Proyectado
4. **Navegar perfiles** → Usar controles de navegación
5. **Realizar mediciones** → Herramientas interactivas
6. **Exportar resultados** → CSV según modo seleccionado

### ⌨️ **Atajos de Teclado**
- **'A'**: Snap automático durante medición de ancho
- **Mouse wheel**: Zoom in/out en perfil
- **Click + Drag**: Pan en el perfil

## 🔄 **Flujos de Trabajo Recomendados**

### 🔧 **Para Análisis de Revanchas**
1. Modo **REVANCHA** activado
2. Definir Cota Coronamiento → Auto-detección ancho
3. Verificar/ajustar LAMA si necesario
4. Exportar datos completos
5. Analizar Revancha = Coronamiento - LAMA

### 📐 **Para Ancho Proyectado**
1. Modo **ANCHO PROYECTADO** activado  
2. Seleccionar punto Lama → Auto-generación línea +3m
3. Verificar ancho auto-detectado
4. Ajustar manualmente si necesario
5. Exportar solo PK + Ancho

## 📊 **Beneficios de la Actualización**

### ✅ **Versatilidad**
- Dos modos especializados en un solo plugin
- Interfaz adaptativa según necesidades
- Workflows optimizados por tipo de análisis

### ✅ **Eficiencia**  
- Auto-detección inteligente
- Exportación específica por modo
- Reducción significativa de tiempo de análisis

### ✅ **Robustez**
- Funcionalidad original preservada
- Código mantenible y extensible
- Manejo de casos límite mejorado

## 🛠️ **Requisitos Técnicos**

- **QGIS**: 3.x o superior
- **Python**: 3.7+
- **Dependencias**: matplotlib, PyQt5
- **Datos**: DEM, alineaciones, puntos LAMA

## 📞 **Soporte y Contacto**

- **Proyecto**: Las Tortolas
- **Email**: support@lastortolas.com
- **Documentación**: Ver `NUEVAS_FUNCIONALIDADES.md` para detalles técnicos

---

## 🎉 **¡Actualización 2025 Completa!**

Plugin completamente renovado con modo **Ancho Proyectado** funcionando en paralelo con **Revanchas** tradicionales. ¡Listo para análisis topográficos avanzados!
