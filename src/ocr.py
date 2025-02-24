import cv2
import numpy as np
import pytesseract
import logging
from PIL import Image
import os
import re

# Set Tesseract path
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

class OCRProcessor:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.language = config['ocr_settings']['language']
        self.preprocessing_enabled = False  # Default to disabled
        
        # Enable debug logging for OCR
        self.logger.setLevel(logging.DEBUG)

    def extract_text(self, image_path):
        """Extract raw text from an image using OCR."""
        try:
            self.logger.info(f"Extracting text from image: {image_path}")
            text = pytesseract.image_to_string(Image.open(image_path), lang=self.language)
            self.logger.info(f"Extracted text:\n{text}")
            return text.strip()
        except Exception as e:
            self.logger.error(f"Error performing OCR: {str(e)}")
            return None

    def extract_text_with_positions(self, image_path):
        """Extracts text along with bounding box positions."""
        try:
            image = cv2.imread(image_path)
            extracted_data = []
            seen_positions = set()  # Track text positions to avoid duplicates
            
            # Multiple OCR passes with different configurations
            configs = [
                # First pass - sparse text
                r'--oem 3 --psm 11 -c tessedit_char_whitelist="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-\\|\'!"',
                # Second pass - uniform text block
                r'--oem 3 --psm 6 -c tessedit_char_whitelist="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-\\|\'!"',
                # Third pass - single line
                r'--oem 3 --psm 7 -c tessedit_char_whitelist="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-\\|\'!"'
            ]
            
            for config in configs:
                data = pytesseract.image_to_data(
                    image,
                    output_type=pytesseract.Output.DICT,
                    config=config
                )

                for i in range(len(data["text"])):
                    text = data["text"][i].strip()
                    if text:
                        x = data["left"][i]
                        y = data["top"][i]
                        w = data["width"][i]
                        h = data["height"][i]
                        conf = float(data["conf"][i])
                        
                        # Create position key to avoid duplicates
                        pos_key = f"{x},{y}"
                        
                        # Only add if position is new
                        if pos_key not in seen_positions:
                            seen_positions.add(pos_key)
                            extracted_data.append({
                                "text": text,
                                "x": x,
                                "y": y,
                                "w": w,
                                "h": h,
                                "conf": conf
                            })
                            
                            # Debug logging
                            self.logger.debug(f"Detected text: '{text}' at ({x},{y}) with confidence {conf}")

            return extracted_data, image.shape[1]
        except Exception as e:
            self.logger.error(f"Error extracting text with positions: {str(e)}")
            return [], 0
        except Exception as e:
            self.logger.error(f"Error extracting text with positions: {str(e)}")
            return [], 0

    def classify_players_by_position(self, extracted_data, image_width):
        """Categorizes players based on their position in the image."""
        try:
            game_info = {"friendly_team": [], "enemy_team": []}
            midpoint = image_width // 2

            # More flexible pattern for level + player name format
            # Matches formats like "42\JeeSama", "35| DonFrank", "30! cipys", "40'KFKenny"
            # Also handles numbers in names like "ironman1731" and "aDuckOnQuack40"
            player_pattern = re.compile(r'(\d{1,3})(?:[\\\|\'!]\s*|\s+)([A-Za-z0-9][A-Za-z0-9_-]{2,})')

            # Core UI text to filter
            ui_text = {
                'DEFEND', 'ATTACK', 'HELP', 'PREVENT', 'UID', 'STATUE', 'BAST', 
                'HALL', 'DJALIA', 'INTERGALACTIC', 'EMPIRE', 'WAKANDA', 'COMPETITIVE', 
                'CONVERGENCE', 'EXPLORER', 'CHRONO', 'FPS'
            }

            # Special cases - known player names that might have low confidence
            special_cases = {
                'aDuckOnQuack40',
                'Khalteck_x2'
            }

            # Process each detected text
            for item in extracted_data:
                text = item["text"]
                x = item["x"]
                confidence = item.get("conf", 0)
                
                # Skip confidence check for special cases
                should_process = any(special_case in text for special_case in special_cases) or confidence >= 0.1
                
                if should_process:
                    # Look for level + name pattern
                    match = player_pattern.search(text)
                    if match:
                        level = match.group(1)
                        player_name = match.group(2).strip()
                        
                        # Basic validation rules
                        if (len(player_name) >= 3 and  # Must be at least 3 characters
                            player_name.upper() not in ui_text and  # Not UI text
                            not any(ui_word.lower() in player_name.lower() for ui_word in ['Chrono', 'Explorer'])):  # Not title text
                            
                            # Handle special cases directly
                            if any(special_case in text for special_case in special_cases):
                                for special_case in special_cases:
                                    if special_case in text:
                                        player_name = special_case
                                        break
                            
                            # Assign to team based on x position
                            if x < midpoint:
                                if player_name not in game_info["friendly_team"]:
                                    game_info["friendly_team"].append(player_name)
                            else:
                                if player_name not in game_info["enemy_team"]:
                                    game_info["enemy_team"].append(player_name)

            # Remove any duplicates
            game_info["friendly_team"] = list(dict.fromkeys(game_info["friendly_team"]))
            game_info["enemy_team"] = list(dict.fromkeys(game_info["enemy_team"]))

            return game_info
        except Exception as e:
            self.logger.error(f"Error classifying players: {str(e)}")
            return {"friendly_team": [], "enemy_team": []}
        
    def find_game_info(self, text, image_path):
        """Extracts game-related information from raw OCR text and image."""
        try:
            self.logger.info("Analyzing extracted text for game information...")
            game_info = {"match_type": None, "friendly_team": [], "enemy_team": []}

            # Detect match type from OCR text
            if "DEFEND" in text:
                game_info["match_type"] = "DEFEND"
            elif "ATTACK" in text:
                game_info["match_type"] = "ATTACK"

            # Extract player positions from image
            extracted_data, image_width = self.extract_text_with_positions(image_path)
            if extracted_data:
                player_positions = self.classify_players_by_position(extracted_data, image_width)
                game_info.update(player_positions)

            self.logger.info(f"Match Type: {game_info['match_type']}")
            self.logger.info(f"Friendly Team: {game_info['friendly_team']}")
            self.logger.info(f"Enemy Team: {game_info['enemy_team']}")

            return game_info
        except Exception as e:
            self.logger.error(f"Error extracting game info: {str(e)}")
            return None