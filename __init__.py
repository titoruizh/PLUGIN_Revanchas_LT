# -*- coding: utf-8 -*-
"""
/***************************************************************************
 RevanchasLT - Plugin QGIS para Análisis de Muros de Contención
                              A QGIS plugin
 Plugin para análisis de perfiles topográficos de muros de contención
                             -------------------
        begin                : 2024-01-01
        copyright            : (C) 2024-2026 by Las Tortolas Project
        email                : support@lastortolas.com
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/

Estructura del Plugin:
----------------------
├── config/           - Configuración y constantes
│   ├── settings.py   - Configuración estática
│   ├── config_manager.py - Gestor de configuración dinámica
│   └── walls.json    - Datos de muros externalizados
│
├── core/             - Lógica de negocio
│   ├── alignment_data.py    - Gestión de alineaciones
│   ├── dem_processor.py     - Procesamiento DEM
│   ├── dem_validator.py     - Validación de cobertura
│   ├── lama_points.py       - Puntos LAMA
│   ├── profile_generator.py - Generación de perfiles
│   ├── project_manager.py   - Gestión de proyectos
│   ├── visualization.py     - Visualización matplotlib
│   └── wall_analyzer.py     - Análisis de muros
│
├── ui/               - Interfaz de usuario
│   ├── dialogs/      - Diálogos
│   │   └── profile_viewer/  - Visor de perfiles modularizado
│   └── widgets/      - Widgets reutilizables
│
├── utils/            - Utilidades
│   ├── logging_config.py - Sistema de logging
│   └── validators.py     - Validaciones centralizadas
│
└── data/             - Datos del plugin
    └── lama_points/  - Archivos CSV de puntos LAMA
"""

__version__ = '1.3.0'
__author__ = 'Las Tortolas Project'


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """
    Load RevanchasLT class from file RevanchasLT.
    
    Esta es la función de entrada que QGIS llama para inicializar el plugin.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    :returns: RevanchasLT plugin instance
    """
    from .revanchas_lt_plugin import RevanchasLT
    return RevanchasLT(iface)