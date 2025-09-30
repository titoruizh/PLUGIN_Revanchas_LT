# Revanchas LT - QGIS Plugin

**Análisis topográfico automatizado para muros de contención**

[![QGIS](https://img.shields.io/badge/QGIS-3.x%2B-green)](https://qgis.org)
[![Python](https://img.shields.io/badge/Python-3.7%2B-blue)](https://python.org)
[![License](https://img.shields.io/badge/License-GPL%202.0-orange)](LICENSE)

---

## 📖 Descripción

Plugin profesional para QGIS que automatiza el análisis topográfico de muros de contención en el proyecto Las Tortolas. Migra flujos de trabajo desde Civil3D a QGIS, proporcionando análisis automático de perfiles topográficos con soporte para ortomosaicos ECW.

## ✨ Características Principales

### 🔧 Modo Revancha (Análisis Completo)
- Análisis automático de perfiles topográficos cada 20m
- Cálculo de coronamiento, LAMA, revancha y ancho
- Exportación completa de todas las métricas

### 📐 Modo Ancho Proyectado (Análisis Simplificado)
- Selección de punto LAMA en terreno natural
- Auto-generación de línea de referencia +3m
- Exportación simplificada (PK + Ancho)

### 🌍 Visualización Avanzada
- Visualizador interactivo de perfiles con matplotlib
- Soporte para ortomosaicos ECW con visualización sincronizada
- Navegación fluida entre perfiles con herramientas de zoom/pan
- Auto-detección inteligente de anchos con snap automático

## � Instalación

### Requisitos del Sistema
- QGIS 3.0 o superior
- Python 3.7+
- PyQt5
- matplotlib (opcional, para visualización avanzada)

### Instalación del Plugin
1. Clone este repositorio en su directorio de plugins de QGIS:
   ```bash
   git clone https://github.com/titoruizh/PLUGIN_Revanchas_LT.git
   ```
2. Active el plugin desde el Administrador de Complementos de QGIS
3. El plugin aparecerá en la barra de herramientas

## 🎮 Uso Rápido

1. **Ejecutar el plugin** → Se abre el diálogo de bienvenida
2. **Seleccionar muro** → Carga automática de alineaciones
3. **Cargar DEM** → Archivo ASCII Grid (.asc)
4. **Cargar ECW** → Ortomosaico (opcional)
5. **Generar perfiles** → Análisis automático cada 20m
6. **Elegir modo** → Revancha o Ancho Proyectado
7. **Realizar análisis** → Herramientas interactivas
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
- **Alineaciones**: CSV integrado

### Formatos de Salida
- **CSV Modo Revancha**: PK, Cota_Coronamiento, Revancha, LAMA, Ancho
- **CSV Modo Ancho Proyectado**: PK, Ancho_Proyectado

## 🛠️ Desarrollo

### Requisitos de Desarrollo
```bash
pip install matplotlib PyQt5
```

### Estructura de Alineaciones
- **Muro 1**: PK 0+000 a 1+434 (72 estaciones)
- **Futuros**: Muro 2 y Muro 3 (planificados)

## 📚 Documentación

- [Manual de Usuario](docs/user-manual.md) - Guía completa de uso
- [Nuevas Funcionalidades](docs/NUEVAS_FUNCIONALIDADES.md) - Detalles técnicos
- [Documentación de Desarrollo](docs/development/) - Historial técnico

## 🤝 Contribución

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Cree una rama para su función (`git checkout -b feature/AmazingFeature`)
3. Commit sus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abra un Pull Request

## 📧 Soporte

- **Proyecto**: Las Tortolas
- **Repository**: [GitHub](https://github.com/titoruizh/PLUGIN_Revanchas_LT)
- **Issues**: Use GitHub Issues para reportar bugs o solicitar funcionalidades
- **Email**: support@lastortolas.com

## 📄 Licencia

Este proyecto está licenciado bajo la Licencia GPL 2.0 - vea el archivo [LICENSE](LICENSE) para detalles.

---

**Desarrollado para Las Tortolas Project** | **Versión 1.2.0** | **2025**
