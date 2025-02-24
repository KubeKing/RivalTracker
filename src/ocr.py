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
        self.preprocessing_enabled = config['ocr_settings']['preprocessing']

    def preprocess_image(self, image_path):
        """Preprocess the image to improve OCR accuracy."""
        try:
            self.logger.info(f"Starting image preprocessing on: {image_path}")
            
            # Read image using opencv
            image = cv2.imread(image_path)
            if image is None:
                self.logger.error("Failed to load image")
                return image_path
            self.logger.info(f"Loaded image size: {image.shape}")
            
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            self.logger.info("Converted to grayscale")
            
            # Increase contrast
            gray = cv2.convertScaleAbs(gray, alpha=1.5, beta=0)
            self.logger.info("Increased contrast")
            
            # Apply adaptive thresholding
            gray = cv2.adaptiveThreshold(
                gray,
                255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY,
                11,  # Block size
                2    # C constant
            )
            self.logger.info("Applied adaptive thresholding")

            # Apply slight dilation to connect text components
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2,2))
            gray = cv2.dilate(gray, kernel, iterations=1)
            self.logger.info("Applied dilation to connect text components")

            # Denoise
            gray = cv2.fastNlMeansDenoising(gray)
            self.logger.info("Applied denoising")

            # Write the grayscale image to disk as a temporary file
            temp_file = os.path.join(os.path.dirname(image_path), "temp_processed.png")
            cv2.imwrite(temp_file, gray)
            self.logger.info(f"Saved preprocessed image to: {temp_file}")
            
            return temp_file
        except Exception as e:
            self.logger.error(f"Error preprocessing image: {str(e)}")
            return image_path

    def extract_text(self, image_path):
        """Extract text from the image using OCR."""
        try:
            self.logger.info(f"Starting OCR processing on image: {image_path}")
            
            if self.preprocessing_enabled:
                self.logger.info("Preprocessing enabled, enhancing image...")
                processed_image_path = self.preprocess_image(image_path)
                self.logger.info(f"Image preprocessed, saved to: {processed_image_path}")
            else:
                processed_image_path = image_path
                self.logger.info("Preprocessing disabled, using original image")

            # Perform OCR with specific configuration for number-name pairs
            self.logger.info(f"Running Tesseract OCR with language: {self.language}")
            custom_config = (
                '--psm 6 '  # Assume uniform block of text
                '--oem 3 '  # Default, LSTM only
                '-c tessedit_char_whitelist="0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz _-" '
                '-c tessedit_fix_fuzzy_spaces=1 '  # Fix spaces between text
                '-c load_system_dawg=0 '  # Disable dictionary
                '-c load_freq_dawg=0'     # Disable frequency-based correction
            )
            self.logger.info(f"Using custom OCR config: {custom_config}")
            
            text = pytesseract.image_to_string(
                Image.open(processed_image_path),
                lang=self.language,
                config=custom_config
            )
            
            # Log extracted text
            cleaned_text = text.strip()
            self.logger.info("Raw extracted text:")
            for line in cleaned_text.split('\n'):
                if line.strip():
                    self.logger.info(f"  > {line.strip()}")

            # Clean up temporary processed image if it exists
            if self.preprocessing_enabled and os.path.exists(processed_image_path):
                os.remove(processed_image_path)
                self.logger.info("Cleaned up temporary preprocessed image")

            return cleaned_text
        except Exception as e:
            self.logger.error(f"Error performing OCR: {str(e)}")
            return None

    def find_game_info(self, text):
        """Extract game-specific information from OCR text."""
        try:
            self.logger.info("Analyzing extracted text for game information...")
            lines = text.split('\n')
            game_info = {
                'match_type': None,
                'friendly_team': [],
                'enemy_team': []
            }

            # Patterns to match all player name formats:
            # Removed end boundaries to catch multiple players per line
            patterns = [
                re.compile(r'(?:^|\s)(\d{1,3})\s+([A-Za-z][A-Za-z0-9_-]{2,20})'),  # With space
                re.compile(r'(?:^|\s)(\d{1,3})([A-Za-z][A-Za-z0-9_-]{2,20})')      # Without space
            ]

            # Process each line
            for line in lines:
                line = line.strip()
                
                # Look for match type
                if 'ATTACK' in line.upper():
                    game_info['match_type'] = 'ATTACK'
                    self.logger.info(f"Found match type: ATTACK in line '{line}'")
                elif 'DEFEND' in line.upper():
                    game_info['match_type'] = 'DEFEND'
                    self.logger.info(f"Found match type: DEFEND in line '{line}'")
                
                # Log line analysis start
                self.logger.debug(f"\nAnalyzing line: '{line}'")
                matches_found = []
                
                # Look for player names using both patterns
                for pattern in patterns:
                    for match in pattern.finditer(line):
                        number, name = match.groups()
                        matches_found.append((number, name, match.start()))
                        
                # Log all matches found in this line
                if matches_found:
                    self.logger.debug(f"Found {len(matches_found)} potential players in line:")
                    for num, name, pos in matches_found:
                        self.logger.debug(f"  {num} {name} at position {pos}")
                
                # Process each match
                for number, name, start_pos in matches_found:
                    try:
                        num = int(number)
                        if 1 <= num <= 999:  # Player numbers are typically 1-3 digits
                            # Only clean up whitespace, preserve capitalization
                            name = name.strip()
                            
                            # Add name if it's valid and not a duplicate in either team
                            if len(name) >= 2 and name not in game_info['friendly_team'] and name not in game_info['enemy_team']:
                                # Calculate end position and relative position
                                name_end_pos = start_pos + len(name)
                                line_position = (name_end_pos / len(line)) * 100 if len(line) > 0 else 0
                                
                                # Log position details
                                self.logger.debug(f"Player position analysis:")
                                self.logger.debug(f"  Full line: '{line}'")
                                self.logger.debug(f"  Line length: {len(line)} chars")
                                self.logger.debug(f"  Player: {number} {name}")
                                self.logger.debug(f"  Start position: {start_pos}")
                                self.logger.debug(f"  End position: {name_end_pos}")
                                self.logger.debug(f"  Name length: {len(name)} chars")
                                self.logger.debug(f"  End relative position: {line_position:.1f}%")
                                
                                # Assign to team based on name's end position
                                if line_position <= 50:
                                    game_info['friendly_team'].append(name)
                                    self.logger.info(f"Found friendly player (name ends at {line_position:.1f}%): Number {number}, Name: {name}")
                                else:
                                    game_info['enemy_team'].append(name)
                                    self.logger.info(f"Found enemy player (name ends at {line_position:.1f}%): Number {number}, Name: {name}")
                    except ValueError:
                        self.logger.debug(f"Invalid number format: {number}")

            self.logger.info(f"Analysis complete - Match type: {game_info['match_type']}")
            self.logger.info(f"Found {len(game_info['friendly_team'])} friendly players and {len(game_info['enemy_team'])} enemy players")
            
            return game_info
        except Exception as e:
            self.logger.error(f"Error extracting game info: {str(e)}")
            return None
