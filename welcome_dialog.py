# -*- coding: utf-8 -*-
"""
/***************************************************************************
 WelcomeDialog
                                 A QGIS plugin
 Plugin para análisis de perfiles topográficos de muros de contención
                             -------------------
        begin                : 2024-01-01
        git sha              : $Format:%H$
        copyright            : (C) 2024 by Las Tortolas Project
        email                : support@lastortolas.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os

from qgis.PyQt import uic
from qgis.PyQt import QtWidgets
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QMessageBox

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'welcome_dialog.ui'))


class WelcomeDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        super(WelcomeDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.selected_wall = None

        # Cambia solo el texto que ve el usuario
        self.wall1_button.setText("Muro Principal")
        self.wall2_button.setText("Muro Oeste")
        self.wall3_button.setText("Muro Este")

        # Habilita todos los botones
        self.wall2_button.setEnabled(True)
        self.wall3_button.setEnabled(True)
        self.wall2_button.setToolTip("")
        self.wall3_button.setToolTip("")

        # Internamente usa las claves de alineación (importante para que funcione con los datos existentes)
        self.wall1_button.clicked.connect(lambda: self.select_wall("Muro 1"))
        self.wall2_button.clicked.connect(lambda: self.select_wall("Muro 2"))
        self.wall3_button.clicked.connect(lambda: self.select_wall("Muro 3"))
        
    def select_wall(self, wall_name):
        self.selected_wall = wall_name
        self.accept()
    
    def get_selected_wall(self):
        return self.selected_wall