# backend/src/ocr/processor.py
import cv2
import numpy as np
import pytesseract
from ..utils.validation import validate_player_name

class OCRProcessor:
    def __init__(self):
        self.config = '--psm 7'  # Assume a single line of text

    def preprocess_image(self, image):
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply thresholding
        thresh = cv2.threshold(
            gray, 0, 255, 
            cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )[1]
        
        # Remove noise
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3,3))
        opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
        
        return opening

    def extract_text(self, image):
        preprocessed = self.preprocess_image(image)
        text = pytesseract.image_to_string(
            preprocessed,
            config=self.config
        ).strip()
        
        if validate_player_name(text):
            return text
        return None