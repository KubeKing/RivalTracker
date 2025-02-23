# backend/src/utils/validation.py
import re

def validate_player_name(name):
    if not name:
        return False
        
    # Remove common OCR artifacts
    cleaned = re.sub(r'[^a-zA-Z0-9_-]', '', name)
    
    # Basic validation rules
    if len(cleaned) < 3 or len(cleaned) > 20:
        return False
        
    return True