# Plugin QGIS "Revanchas LT" - Manual de Usuario

## Descripción General
El plugin "Revanchas LT" automatiza el análisis topográfico de muros de contención, migrando el flujo de trabajo desde Civil3D a QGIS.

## Características Principales
- **Análisis automático de perfiles topográficos cada 20 metros**
- **Ancho de análisis de 80 metros en cada estación**
- **Alineaciones integradas para Muro Principal, Este y Oeste**
- **Carga de archivos DEM en formato ASCII Grid (.asc)**
- **Carga de ortomosaicos en formato ECW para visualización**
- **Visualización de perfiles con matplotlib (opcional)**
- **Análisis estadístico de elevaciones y pendientes**
- **Visualización de ortomosaico en coordenadas exactas de cada perfil**

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
  
<img width="1298" height="766" alt="complemento" src="https://github.com/user-attachments/assets/4ad4b287-8325-4e2e-b535-535bdf5b70f7" />

### 2. Pantalla de Bienvenida
- Seleccione el muro a analizar
  
<img width="510" height="321" alt="Menu_1" src="https://github.com/user-attachments/assets/c91faa4e-9e84-4802-b994-d2695fe2f520" />

### 3. Pantalla Principal

#### Información de Alineación
- Muestra los datos de la alineación seleccionada
- **Muro 1**: PK 0+000 a 1+434, estaciones cada 20m (72 estaciones total)

<img width="587" height="569" alt="info_alineacion" src="https://github.com/user-attachments/assets/faad7084-dacb-4504-bb37-bf8bb65d070d" />

#### Carga de DEM y Ortomosaico
- Haga clic en **"Examinar..."** para seleccionar un archivo DEM (.asc)
- El plugin mostrará información básica del DEM (dimensiones, resolución, extensión)
- Haga clic en **"Examinar..."** en la sección Ortomosaico para seleccionar un archivo ECW
- El plugin validará que tanto el DEM como el ECW cubran la alineación seleccionada

#### Generación de Perfiles
- Una vez cargados el DEM y el ECW, haga clic en **"Generar y Visualizar Perfiles"**
- El plugin generará perfiles cada 20 metros con 80m de ancho de análisis
- Se mostrará una barra de progreso durante la generación

#### Visualizador Interactivo de Perfiles
- Navegue entre perfiles usando botones o el deslizador
- Use el botón **"🌎 Visualiza Ortomosaico"** para ver el ECW en la ubicación exacta del perfil actual
- Herramientas de medición:
  - Cota Coronamiento
  - Ancho medido
  - LAMA
- Modos de operación:
  - Revancha
  - Ancho Proyectado

<img width="1843" height="921" alt="principal" src="https://github.com/user-attachments/assets/718ba640-a68f-4cfa-8f64-adfa01b0be01" />


## Estructura de Datos

### Alineaciones
Las alineaciones están integradas en el código del plugin:
- **Muro Principal**: 72 estaciones desde PK 0+000 hasta 1+434
- **Muro Oeste**: 36 estaciones desde PK 0+000 hasta 0+690
- **Muro Este**: 26 estaciones desde PK 0+000 hasta 0+551
- Cada estación incluye coordenadas X,Y, rumbo y elevación de referencia

### Perfiles Topográficos
Cada perfil incluye:
- Puntos espaciados cada metro (80m de ancho total)
- Distancias desde el eje de alineación (-40m a +40m)
- Elevaciones del terreno extraídas del DEM
- Coordenadas mundiales de cada punto

### Análisis de Resultados
El análisis proporciona:
- Estadísticas de elevación
- Pendientes longitudinales y transversales
- Clasificación de variabilidad del terreno
- Recomendaciones técnicas


## Soporte Técnico
Para problemas o sugerencias:
- Repositorio: https://github.com/titoruizh/PLUGIN_Revanchas_LT
- Email: truizh@linkapsis.com   |    tito.ruiz@usach.cl

---
*Plugin desarrollado para Las Tortolas Project - Versión 1.1.0*
