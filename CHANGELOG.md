# Changelog

Todos los cambios importantes de este proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
y este proyecto se adhiere a [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2025-09-30

### Añadido
- **Visualizador de Ortomosaico ECW**: Integración completa de archivos ECW para visualización geoespacial
- **Navegación Sincronizada**: Sincronización automática entre visualizador de perfiles y ortomosaico
- **Soporte ECW Opcional**: El plugin funciona completamente sin archivos ECW
- **Visualización de Perfiles en ECW**: Líneas de perfil superpuestas en el ortomosaico con bearing correcto
- **Estructura Profesional**: Reorganización completa del código para estándares de desarrollo

### Mejorado
- **Cálculo de Bearing**: Algoritmo mejorado para secciones curvas usando `bearing_tangent`
- **Rango de Perfiles Estandarizado**: Todos los muros ahora usan rango -40m a +40m
- **Interfaz No Modal**: Ventanas sincronizadas que permiten interacción simultánea
- **Documentación**: README profesional y documentación técnica organizada

### Corregido
- **Visualización en Curvas**: Corrección de bearing para Muro Oeste (MO) en secciones curvas
- **Inicialización de RubberBand**: Mejoras en la creación de elementos de visualización
- **Limpieza de Recursos**: Mejor gestión de memoria y limpieza de objetos gráficos

## [1.1.0] - 2025-09-01

### Añadido
- **Modo Ancho Proyectado**: Nuevo modo de análisis simplificado
- **Toggle de Modos**: Interfaz adaptativa entre Revancha y Ancho Proyectado
- **Auto-detección Inteligente**: Algoritmos avanzados de intersección
- **Exportación Específica**: CSV diferentes según el modo de operación

### Mejorado
- **Interfaz de Usuario**: Panel de herramientas adaptativo según el modo
- **Líneas de Referencia**: Sistema inteligente de líneas según el análisis
- **Navegación de Perfiles**: Controles mejorados con slider y botones

## [1.0.0] - 2025-08-01

### Añadido
- **Funcionalidad Base**: Análisis completo de revanchas tradicional
- **Visualizador Interactivo**: Navegación fluida entre perfiles topográficos
- **Soporte DEM**: Carga y procesamiento de archivos ASCII Grid
- **Tres Muros**: Soporte para Muro 1, 2 y 3 con alineaciones específicas
- **Exportación CSV**: Resultados completos en formato estándar
- **Herramientas de Medición**: Cota coronamiento, ancho, LAMA
- **Análisis Estadístico**: Procesamiento avanzado de datos topográficos

### Técnico
- **Arquitectura QGIS**: Plugin completo para QGIS 3.x
- **PyQt5**: Interfaz gráfica moderna y responsive
- **Matplotlib**: Visualización científica de perfiles
- **Modular**: Estructura de código mantenible y extensible

---

## Leyenda de Tipos de Cambios
- `Añadido` para nuevas funcionalidades
- `Mejorado` para cambios en funcionalidades existentes
- `Corregido` para corrección de bugs
- `Técnico` para cambios internos sin impacto en usuario
- `Seguridad` para correcciones de vulnerabilidades
- `Eliminado` para funcionalidades removidas