# Plugin QGIS "Revanchas LT" - Manual de Usuario

## Descripción General
El plugin "Revanchas LT" automatiza el análisis topográfico de muros de contención, migrando el flujo de trabajo desde Civil3D a QGIS.

## Características Principales
- **Análisis automático de perfiles topográficos cada 20 metros**
- **Ancho de análisis de 80 metros en cada estación**
- **Alineaciones integradas (actualmente Muro 1: PK 0+000 a 1+434)**
- **Carga de archivos DEM en formato ASCII Grid (.asc)**
- **Visualización de perfiles con matplotlib (opcional)**
- **Análisis estadístico de elevaciones y pendientes**

## Instalación

### Requisitos
- QGIS 3.0 o superior
- PyQt5
- Opcional: numpy, matplotlib (para funcionalidades avanzadas)

### Instalación del Plugin
1. Copie la carpeta del plugin en el directorio de plugins de QGIS
2. Active el plugin desde el administrador de complementos de QGIS
3. El plugin aparecerá en el menú de plugins

## Uso del Plugin

### 1. Inicio del Plugin
- Abra QGIS y vaya al menú **Complementos**
- Busque **"Revanchas LT - Análisis Topográfico"**
- Haga clic para ejecutar el plugin

### 2. Pantalla de Bienvenida
- Seleccione el muro a analizar (actualmente solo "Muro 1" disponible)
- Los Muros 2 y 3 estarán disponibles en versiones futuras

### 3. Pantalla Principal

#### Información de Alineación
- Muestra los datos de la alineación seleccionada
- **Muro 1**: PK 0+000 a 1+434, estaciones cada 20m (72 estaciones total)

#### Carga de DEM
- Haga clic en **"Examinar..."** para seleccionar un archivo DEM (.asc)
- El plugin mostrará información básica del DEM (dimensiones, resolución, extensión)

#### Generación de Perfiles
- Una vez cargado el DEM, haga clic en **"Generar Perfiles Topográficos"**
- El plugin generará perfiles cada 20 metros con 80m de ancho de análisis
- Se mostrará una barra de progreso durante la generación

#### Análisis
- Después de generar los perfiles, haga clic en **"Analizar Perfiles"**
- El análisis incluye:
  - Elevaciones mínima, máxima y promedio
  - Pendiente longitudinal promedio
  - Características del terreno
  - Recomendaciones de diseño

## Estructura de Datos

### Alineaciones
Las alineaciones están integradas en el código del plugin:
- **Muro 1**: 72 estaciones desde PK 0+000 hasta 1+434
- Cada estación incluye coordenadas X,Y, rumbo y elevación de referencia

### Perfiles Topográficos
Cada perfil incluye:
- 81 puntos espaciados cada metro (80m de ancho total)
- Distancias desde el eje de alineación (-40m a +40m)
- Elevaciones del terreno extraídas del DEM
- Coordenadas mundiales de cada punto

### Análisis de Resultados
El análisis proporciona:
- Estadísticas de elevación
- Pendientes longitudinales y transversales
- Clasificación de variabilidad del terreno
- Recomendaciones técnicas

## Archivos de Ejemplo

### Formato DEM (ASCII Grid)
```
ncols         1000
nrows         1000
xllcorner     400000.0
yllcorner     6000000.0
cellsize      1.0
NODATA_value  -9999
100.1 100.2 100.3 ...
100.2 100.3 100.4 ...
...
```

### Estructura de Archivos del Plugin
```
PLUGIN_Revanchas_LT/
├── __init__.py                 # Punto de entrada
├── revanchas_lt_plugin.py      # Clase principal
├── dialog.py                   # Diálogo principal
├── dialog.ui                   # Interfaz principal
├── welcome_dialog.py           # Diálogo de bienvenida
├── welcome_dialog.ui           # Interfaz de bienvenida
├── core/                       # Módulos principales
│   ├── dem_processor.py        # Procesamiento de DEM
│   ├── alignment_data.py       # Datos de alineación
│   ├── profile_generator.py    # Generación de perfiles
│   ├── wall_analyzer.py        # Análisis de muros
│   └── visualization.py        # Visualización (matplotlib)
├── data/                       # Datos del proyecto
│   └── alignments/            # Archivos de alineación
├── metadata.txt               # Metadatos del plugin
└── resources.qrc             # Recursos Qt
```

## Solución de Problemas

### Error: "No se pudo leer información del DEM"
- Verifique que el archivo .asc tenga el formato correcto
- Asegúrese de que el archivo no esté corrupto

### Error: "Matplotlib no disponible"
- La visualización de perfiles requiere matplotlib
- Instale matplotlib: `pip install matplotlib`

### Plugin no aparece en QGIS
- Verifique que todos los archivos estén en la carpeta correcta
- Reinicie QGIS después de instalar el plugin

## Desarrollo Futuro

### Versión 2.0 (Planificada)
- Soporte para Muro 2 y Muro 3
- Importación directa de datos de Civil3D XML
- Exportación a formatos CAD
- Análisis de estabilidad avanzado

### Funcionalidades Avanzadas
- Visualización 3D de perfiles
- Comparación entre diferentes escenarios
- Generación automática de reportes
- Integración con bases de datos geotécnicas

## Soporte Técnico
Para problemas o sugerencias:
- Repositorio: https://github.com/titoruizh/PLUGIN_Revanchas_LT
- Email: support@lastortolas.com

---
*Plugin desarrollado para Las Tortolas Project - Versión 1.0.0*