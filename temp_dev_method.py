
    def generate_dev_map(self):
        """🆕 Método DEV para probar generación de mapas rápidamente"""
        from .core.map_generator import MapGenerator
        
        try:
            # 1. Validar requisitos
            if not self.ecw_file_path or not os.path.exists(self.ecw_file_path):
                QMessageBox.warning(self, "Falta Ortomosaico", "Debe cargar un Ortomosaico (ECW/TIF) primero.")
                return
                
            has_previous_dem = False
            prev_dem_path = None
            
            # Recuperar path del DEM anterior desde el diálogo principal?
            # profile_viewer no tiene el path directo, solo los datos en profiles_data
            # Necesitamos el PATH real del archivo para que QGIS lo cargue en MapGenerator.
            # 
            # Solution: We need to pass previous_dem_path to ProfileViewer or access it from parent.
            # "parent" is often RevanchasLTDialog.
            
            main_dialog = self.parent()
            if hasattr(main_dialog, 'previous_dem_file_path') and main_dialog.previous_dem_file_path:
                prev_dem_path = main_dialog.previous_dem_file_path
                has_previous_dem = True
            
            if not has_previous_dem:
                QMessageBox.warning(self, "Falta DEM Anterior", "Debe cargar un DEM Anterior en la ventana principal.")
                return
                
            # Current DEM Path? 
            current_dem_path = None
            if hasattr(main_dialog, 'dem_file_path') and main_dialog.dem_file_path:
                current_dem_path = main_dialog.dem_file_path
                
            if not current_dem_path:
                QMessageBox.warning(self, "Falta DEM Actual", "No se detectó el path del DEM actual.")
                return
                
            # 2. Pedir destino
            output_path, _ = QFileDialog.getSaveFileName(
                self, "Guardar Mapa de Prueba", "Mapa_Contexto_Dev.png", "Images (*.png *.jpg)"
            )
            
            if not output_path:
                return
                
            # 3. Llamar al generador
            plugin_dir = os.path.dirname(__file__)
            generator = MapGenerator(plugin_dir)
            
            # Obtener nombre del muro (e.g. "Muro 1")
            # Está en self.windowTitle()? o self.profile_combobox?
            # self.profiles_data[0]['wall_name'] ??
            # Vamos a asumir que "current_wall_name" está disponible o lo deducimos.
            
            wall_name = "Muro 1" # Default fallback
            if hasattr(main_dialog, 'selected_wall'):
                wall_name = main_dialog.selected_wall
            
            QApplication.setOverrideCursor(Qt.WaitCursor)
            
            success = generator.generate_map_image(
                wall_name,
                self.ecw_file_path,
                current_dem_path,
                prev_dem_path,
                output_path
            )
            
            QApplication.restoreOverrideCursor()
            
            if success:
                QMessageBox.information(self, "Éxito", f"Mapa generado en:\n{output_path}")
                # Abrir imagen?
                import os
                os.startfile(output_path)
            else:
                QMessageBox.critical(self, "Error", "Falló la generación del mapa. Ver log/consola.")
                
        except Exception as e:
            QApplication.restoreOverrideCursor()
            QMessageBox.critical(self, "Error Crítico", str(e))
            import traceback
            traceback.print_exc()
