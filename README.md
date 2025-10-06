# 🏗️ Revanchas LT Plugin

Un plugin profesional de QGIS para análisis topográfico y medición de revanchas en muros de contención, con sincronización en tiempo real entre visualizador de perfiles y ortomosaicos.

[![QGIS](https://img.shields.io/badge/QGIS-3.x%2B-green)](https://qgis.org)
[![Python](https://img.shields.io/badge/Python-3.7%2B-blue)](https://python.org)
[![License](https://img.shields.io/badge/License-GPL%202.0-orange)](LICENSE)
[![Version](https://img.shields.io/badge/Version-2.0.0-brightgreen)]()

---

## ✨ Nuevas Funcionalidades v2.0

### 📁 Gestión de Proyectos
- **💾 Guardar Proyectos**: Preserve todo su trabajo en archivos `.rvlt`
- **📂 Cargar Proyectos**: Restaure sesiones completas con todas las mediciones
- **🔄 Persistencia Completa**: Mantiene archivos DEM/ECW, mediciones y configuraciones

### 🔄 Sincronización Avanzada
- **📏 Mediciones en Tiempo Real**: Las mediciones aparecen instantáneamente en ambos visualizadores
- **🎯 Puntos LAMA Sincronizados**: Detección automática desde CSV con visualización bidireccional  
- **📊 Coronamiento y Anchos**: Todas las mediciones se reflejan en profile viewer y ortomosaico
- **🎨 Simbología Mejorada**: Líneas de centro perpendiculares y ejes de referencia en ortomosaico

## 🚀 Características Principales

### 📈 Análisis de Perfiles Topográficos
- Procesamiento automático de archivos DEM (GeoTIFF)
- Generación de perfiles transversales precisos
- Visualización interactiva con matplotlib
- Navegación por PK con controles intuitivos

### 📐 Herramientas de Medición
- **Coronamiento**: Medición de elevación de corona del muro
- **Ancho de Muro**: Medición horizontal con distancia automática
- **Puntos LAMA**: Detección automática desde archivos CSV
- **Modo Ancho Proyectado**: Visualización inmediata en ambas ventanas

### 🗺️ Visualización de Ortomosaico
- Soporte nativo para archivos ECW
- Navegación sincronizada con perfiles
- Mediciones superpuestas en tiempo real
- Líneas de referencia perpendiculares al eje

### 🎮 Controles Avanzados
- **Detección Automática**: Auto-detección de características del terreno
- **Modos de Operación**: Medición manual y automática
- **Navegación por Teclado**: Controles eficientes con teclas de flecha
- **Zoom Sincronizado**: Coordinación entre visualizadores

## 📋 Requisitos del Sistema

### Dependencias QGIS
- QGIS 3.x o superior
- Python 3.7+
- PyQt5

### Librerías Python
```
matplotlib
numpy
pandas
rasterio
gdal
```

### Formatos de Archivo Soportados
- **DEM**: GeoTIFF (.tif, .tiff)
- **Ortomosaico**: ECW (.ecw)
- **Alineaciones**: CSV con columnas X, Y, PK
- **Puntos LAMA**: CSV con coordenadas específicas
- **Proyectos**: Formato nativo .rvlt (JSON)

## 🛠️ Instalación

### Método 1: Instalación Manual
1. Descargue el plugin desde el repositorio
2. Extraiga en la carpeta de plugins de QGIS:
   ```
   %APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\
   ```
3. Reinicie QGIS
4. Active el plugin en Complementos → Administrar e instalar complementos

### Método 2: Desde Repositorio
1. En QGIS, vaya a Complementos → Administrar e instalar complementos
2. Pestaña "Configuración" → Añadir repositorio personalizado
3. Introduzca la URL del repositorio
4. Instale "Revanchas LT"

## 📖 Guía de Uso

### 1. Configuración Inicial
1. Abra el plugin desde la barra de herramientas
2. **📁 Seleccione archivo DEM**: Elija su archivo GeoTIFF
3. **🗺️ Seleccione archivo ECW**: Elija su ortomosaico
4. **🎯 Seleccione muro**: Elija la alineación a analizar

### 2. Generación de Perfiles
1. Haga clic en **"Generar Perfiles Topográficos"**
2. Se abrirán dos ventanas sincronizadas:
   - **Visualizador de Perfiles**: Análisis topográfico detallado
   - **Visualizador de Ortomosaico**: Vista en planta con referencias

### 3. Realización de Mediciones
1. **Modo Coronamiento**: Haga clic en la corona del muro
2. **Modo Ancho**: Haga clic en los extremos del muro
3. **Puntos LAMA**: Se cargan automáticamente desde CSV
4. **Navegación**: Use flechas ← → para cambiar de PK

### 4. Gestión de Proyectos
1. **💾 Guardar**: Use el botón "Guardar Proyecto" para preservar todo su trabajo
2. **📂 Cargar**: Use "Cargar Proyecto" para restaurar sesiones anteriores
3. **📁 Archivos .rvlt**: Formato nativo que preserva mediciones y configuraciones

### 5. Sincronización en Tiempo Real
- Las mediciones aparecen **instantáneamente** en ambas ventanas
- Los puntos LAMA se sincronizan automáticamente desde archivos CSV
- Las líneas de ancho se muestran inmediatamente en modo "ancho proyectado"
- La navegación entre PK actualiza ambos visualizadores simultáneamente

## 📊 Estructura de Datos

### Archivos de Alineación (CSV)
```csv
X,Y,PK
615000.123,4650000.456,0+000
615020.789,4650015.234,0+020
615041.012,4650030.567,0+040
```

### Archivos de Puntos LAMA (CSV)
```csv
X,Y,Z,PK
615010.5,4650005.2,145.67,0+010
615030.8,4650020.1,146.23,0+030
```

### Formato de Proyecto (.rvlt)
```json
{
  "project_info": {
    "name": "proyecto_muro1",
    "version": "1.0",
    "created": "2024-01-15T10:30:00"
  },
  "project_data": {
    "dem_file_path": "C:/data/dem.tif",
    "ecw_file_path": "C:/data/ortho.ecw",
    "selected_wall": "muro1"
  },
  "measurements_data": {
    "saved_measurements": { ... }
  }
}
```

## 🎯 Características Avanzadas

### Detección Automática
- **IA de Terreno**: Detección automática de características topográficas
- **Optimización de Mediciones**: Sugerencias inteligentes de puntos de medición
- **Validación de Datos**: Verificación automática de coherencia

### Exportación de Datos
- **CSV de Mediciones**: Exportación completa de todas las mediciones
- **Reportes PDF**: Generación automática de informes técnicos
- **Intercambio de Datos**: Compatibilidad con software CAD

### Visualización Avanzada
- **Renderizado Optimizado**: Visualización fluida de grandes datasets
- **Simbología Personalizable**: Colores y estilos configurables
- **Overlays Dinámicos**: Superposición de información contextual

## 🐛 Solución de Problemas

### Errores Comunes

**Error: "No se puede cargar el archivo DEM"**
- Verifique que el archivo sea un GeoTIFF válido
- Asegúrese de que tenga sistema de coordenadas definido
- Compruebe permisos de lectura del archivo

**Error: "Visualizador de ortomosaico no disponible"**
- Instale los drivers ECW de GDAL
- Verifique que el archivo ECW no esté corrupto
- Compruebe la compatibilidad de versión

**Mediciones no sincronizadas**
- Reinicie ambos visualizadores
- Verifique que los archivos CSV de LAMA estén en la carpeta correcta
- Compruebe la configuración de sincronización

### Logs de Depuración
El plugin genera logs detallados en la consola de Python de QGIS:
```python
# Para activar logs adicionales
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🤝 Contribución

### Desarrollo
1. Fork el repositorio
2. Cree una rama para su feature: `git checkout -b feature/nueva-funcionalidad`
3. Commit sus cambios: `git commit -am 'Añadir nueva funcionalidad'`
4. Push a la rama: `git push origin feature/nueva-funcionalidad`
5. Cree un Pull Request

### Reporte de Bugs
Use GitHub Issues para reportar problemas:
- Incluya versión de QGIS y sistema operativo
- Proporcione archivos de ejemplo si es posible
- Describa pasos para reproducir el error

## 📚 Documentación Adicional

- [📖 Manual de Usuario Completo](docs/manual-usuario.md)
- [🔧 Guía de Desarrollo](docs/desarrollo.md)
- [📋 API Reference](docs/api-reference.md)
- [🎥 Tutoriales en Video](docs/tutoriales.md)

## 📄 Licencia

Este proyecto está licenciado bajo la Licencia GPL v3 - vea el archivo [LICENSE](LICENSE) para detalles.

## 👥 Autores

- **Equipo LT** - *Desarrollo inicial* - [GitHub](https://github.com/tu-usuario)

## 🏆 Reconocimientos

- Comunidad QGIS por el framework base
- Contribuidores del proyecto matplotlib
- Equipo de desarrollo GDAL/OGR

---

**🔄 Versión**: 2.0.0 | **📅 Última actualización**: Enero 2024 | **🌟 Estado**: Producción