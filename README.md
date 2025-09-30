# Revanchas LT - QGIS Plugin

**Análisis topográfico automatizado para muros de contención**

[![QGIS](https://img.shields.io/badge/QGIS-3.x%2B-green)](https://qgis.org)
[![Python](https://img.shields.io/badge/Python-3.7%2B-blue)](https://python.org)
[![License](https://img.shields.io/badge/License-GPL%202.0-orange)](LICENSE)

---

## 📖 Descripción

Plugin  para QGIS que simplifica y automatiza el análisis topográfico de muros de contención de Las Tortolas - Anglo American. Migra flujos de trabajo desde Civil3D a QGIS, proporcionando facilidad en el analisis de perfiles topográficos con soporte para ortomosaicos ECW.

## ✨ Características Principales

### 🔧 Modo Revancha 
- Análisis automático de perfiles topográficos cada 20m
- Cálculo de coronamiento, LAMA, revancha y ancho
- Exportación completa de todas las métricas

### 📐 Modo Ancho Proyectado
- Selección de punto LAMA en terreno natural
- Auto-generación de línea de referencia +3m
- Exportación simplificada (PK + Ancho)


## � Instalación

### Requisitos del Sistema
- QGIS 3.0 o superior
- Python 3.7+
- PyQt5
- matplotlib

## 🎮 Uso Rápido

1. **Ejecutar el plugin** → Se abre el diálogo de bienvenida
2. **Seleccionar muro** → Carga automática de alineaciones
3. **Cargar DEM** → Archivo ASCII Grid (.asc)
4. **Cargar ECW** → Ortomosaico (opcional)
5. **Generar perfiles** → Análisis automático cada 20m
6. **Elegir modo** → Revancha o Ancho Proyectado
7. **Realizar análisis** → Herramientas interactivas: Anchos, Lama, Coronamiento, Etc.
8. **Exportar resultados** → CSV según modo seleccionado

## � Estructura del Proyecto

```
PLUGIN_Revanchas_LT/
├── __init__.py                 # Punto de entrada del plugin
├── revanchas_lt_plugin.py      # Clase principal del plugin
├── dialog.py                   # Diálogo principal
├── profile_viewer_dialog.py    # Visualizador interactivo
├── orthomosaic_viewer.py       # Visualizador de ortomosaico
├── welcome_dialog.py           # Diálogo de bienvenida
├── core/                       # Módulos principales
│   ├── alignment_data.py       # Gestión de alineaciones
│   ├── dem_processor.py        # Procesamiento de DEM
│   ├── profile_generator.py    # Generación de perfiles
│   └── wall_analyzer.py        # Análisis de muros
├── data/                       # Datos del proyecto
│   ├── alignments/             # Alineaciones por muro
│   └── lama_points/           # Puntos LAMA
├── docs/                       # Documentación
│   ├── user-manual.md          # Manual de usuario
│   ├── NUEVAS_FUNCIONALIDADES.md
│   └── development/            # Documentación técnica
├── metadata.txt               # Metadatos del plugin
└── resources.qrc             # Recursos Qt
```

## 📊 Datos Soportados

### Formatos de Entrada
- **DEM**: ASCII Grid (.asc)
- **Ortomosaico**: ECW (.ecw)

### Formatos de Salida
- **CSV Modo Revancha**: PK, Cota_Coronamiento, Revancha, LAMA, Ancho
- **CSV Modo Ancho Proyectado**: PK, Ancho_Proyectado

## 📚 Documentación

- [Manual de Usuario](docs/user-manual.md) - Guía completa de uso
- [Nuevas Funcionalidades](docs/NUEVAS_FUNCIONALIDADES.md) - Detalles técnicos
- [Documentación de Desarrollo](docs/development/) - Historial técnico

## 📧 Soporte

- **Proyecto**: PLUGIN Revancha Las Tortolas
- **Repository**: [GitHub](https://github.com/titoruizh/PLUGIN_Revanchas_LT)
- **Email**: truizh@linkapsis.com   |    tito.ruiz@usach.cl

## 📄 Licencia

Este proyecto está licenciado bajo la Licencia GPL 2.0 - vea el archivo [LICENSE](LICENSE) para detalles.

---

**Desarrollado por Linkapsis** | **Versión 1.2.0** | **2025**
