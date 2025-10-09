"""
🔄 Actualización Automática de Revanchas
========================================

Este script implementa la actualización automática de los cálculos
de revancha en el visualizador de perfiles sin necesidad de navegar
entre PKs para ver los resultados.
"""

def update_revancha_calculation(self, current_pk=None):
    """
    Actualiza los cálculos de revancha basados en los datos actuales
    sin necesidad de navegar entre PKs.
    
    Esta función se llamará después de cada modificación de crown o LAMA.
    """
    if current_pk is None:
        if hasattr(self, 'profiles_data') and hasattr(self, 'current_profile_index'):
            profile = self.profiles_data[self.current_profile_index]
            current_pk = profile.get('PK') or profile.get('pk')
        else:
            return
    
    # Get LAMA point - check saved first, then auto LAMA
    manual_lama = None
    if current_pk in self.saved_measurements and 'lama' in self.saved_measurements[current_pk]:
        manual_lama = self.saved_measurements[current_pk]['lama']
    
    # Get auto LAMA points if available
    auto_lama_points = None
    if hasattr(self, 'profiles_data') and hasattr(self, 'current_profile_index'):
        profile = self.profiles_data[self.current_profile_index]
        auto_lama_points = profile.get('lama_points', [])
    
    # Get LAMA elevation (manual takes priority)
    lama_elevation = None
    if manual_lama:
        lama_elevation = manual_lama['y']
        lama_source = "manual"
    elif auto_lama_points:
        lama_elevation = auto_lama_points[0]['elevation']
        lama_source = "auto"
    
    # Get Crown elevation
    crown_elevation = None
    if current_pk in self.saved_measurements and 'crown' in self.saved_measurements[current_pk]:
        crown_elevation = self.saved_measurements[current_pk]['crown']['y']
    elif hasattr(self, 'current_crown_point') and self.current_crown_point:
        crown_elevation = self.current_crown_point[1]
    
    # Calculate Revancha
    if crown_elevation is not None and lama_elevation is not None:
        revancha = crown_elevation - lama_elevation
        self.revancha_result.setText(f"Revancha: {revancha:.2f} m")
        
        # Update LAMA display
        self.lama_result.setText(f"Cota LAMA: {lama_elevation:.2f} m ({lama_source})")
        
        print(f"✅ Revancha calculada: {revancha:.2f}m (crown: {crown_elevation:.2f}m, lama: {lama_elevation:.2f}m)")
        return revancha
    else:
        # Show what's missing
        missing_parts = []
        if crown_elevation is None:
            missing_parts.append("coronamiento")
        if lama_elevation is None:
            missing_parts.append("lama")
        
        self.revancha_result.setText(f"Revancha: -- (falta {', '.join(missing_parts)})")
        
        # Still show LAMA if available
        if lama_elevation is not None:
            self.lama_result.setText(f"Cota LAMA: {lama_elevation:.2f} m ({lama_source})")
        else:
            self.lama_result.setText("Cota LAMA: --")
        
        return None