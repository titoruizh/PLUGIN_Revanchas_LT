# -*- coding: utf-8 -*-
import os

def get_wall_code(wall_name):
    """Mapea nombre de muro a código de carpeta (MP/MO/ME)."""
    if not wall_name:
        return "MP"
        
    w = wall_name.upper()
    
    # MO detection
    if "OESTE" in w or "MURO 2" in w:
        return "MO"
        
    # ME detection (Check if contains ESTE but NOT OESTE if needed, 
    # but since we checked OESTE first, if it contains OESTE it returns MO.
    # If it fails first check and contains ESTE, it is ME. Correct.)
    elif "ESTE" in w or "MURO 3" in w:
        return "ME"
        
    return "MP"  # Default (Principal / Muro 1)

def get_sector_for_pk(pk_val, wall_name):
    """
    Retorna el nombre del sector basado en PK y Muro (Hardcoded User Ranges).
    """
    # Ensure pk_val is float
    try:
        val = pk_val
        if isinstance(val, str):
            val = float(val.replace('+', '').replace(',', '.'))
    except:
        return "Error PK"
        
    code = get_wall_code(wall_name)
    
    if code == "MO":
        # MO Ranges from User:
        # S1: 0-260
        # S2: 280-500
        # S3: 520+
        if 0 <= val <= 260: return "Sector 1"
        if 280 <= val <= 500: return "Sector 2"
        if val >= 520: return "Sector 3"
        return "Fuera de Sector" # Gap (Junta)

    elif code == "ME":
        # ME Ranges from User:
        # S1: 0-180
        # S2: 200-380
        # S3: 400+
        if 0 <= val <= 180: return "Sector 1"
        if 200 <= val <= 380: return "Sector 2"
        if val >= 400: return "Sector 3"
        return "Fuera de Sector"

    else: # MP
        # MP Ranges from User:
        # S1: 0-200
        # S2: 220-400
        # S3: 420-600
        # S4: 620-800
        # S5: 820-1000
        # S6: 1000-1200 (Assuming >1000)
        # S7: 1220+
        if 0 <= val <= 200: return "Sector 1"
        if 220 <= val <= 400: return "Sector 2"
        if 420 <= val <= 600: return "Sector 3"
        if 620 <= val <= 800: return "Sector 4"
        if 820 <= val <= 1000: return "Sector 5" # User: "820 hasta el 1000"
        if 1000 < val <= 1200: return "Sector 6" # User: "1000 hasta 1200" (Overlap handling)
        if val >= 1220: return "Sector 7"
        return "Fuera de Sector"

def get_sector_for_profile(profile_data, sectors_layer=None):
    """
    Determina sector basado en los datos del perfil.
    """
    pk = profile_data.get('pk', '')
    wall_name = profile_data.get('wall_name', '')
    
    return get_sector_for_pk(pk, wall_name)
