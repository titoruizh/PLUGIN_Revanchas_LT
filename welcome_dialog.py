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
        """Constructor."""
        super(WelcomeDialog, self).__init__(parent)
        # Set up the user interface from Designer through FORM_CLASS.
        # After self.setupUi() you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html#autconnecting-slots
        self.setupUi(self)
        
        # Initialize selected wall
        self.selected_wall = None
        
        # Connect button signals
        self.wall1_button.clicked.connect(lambda: self.select_wall("Muro 1"))
        self.wall2_button.clicked.connect(lambda: self.select_wall("Muro 2"))
        self.wall3_button.clicked.connect(lambda: self.select_wall("Muro 3"))
        
        # Disable future walls for now
        self.wall2_button.setEnabled(False)
        self.wall3_button.setEnabled(False)
        self.wall2_button.setToolTip("Disponible en versiones futuras")
        self.wall3_button.setToolTip("Disponible en versiones futuras")
        
    def select_wall(self, wall_name):
        """Handle wall selection"""
        if wall_name == "Muro 1":
            self.selected_wall = wall_name
            self.accept()
        else:
            QMessageBox.information(
                self,
                "Información",
                f"{wall_name} estará disponible en versiones futuras del plugin."
            )
    
    def get_selected_wall(self):
        """Return the selected wall"""
        return self.selected_wall