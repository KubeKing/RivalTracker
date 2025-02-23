# backend/src/api/routes.py
from flask import Blueprint, jsonify
from ..ocr.processor import OCRProcessor
from ..ocr.regions import RegionDetector
from ..utils.capture import ScreenCapture

api = Blueprint('api', __name__)
screen_capture = ScreenCapture()
ocr_processor = OCRProcessor()

@api.route('/scan', methods=['GET'])
def scan_game():
    try:
        # Capture screen
        screen = screen_capture.capture_screen()
        width, height = screen_capture.get_screen_dimensions()
        
        # Get regions for both teams
        detector = RegionDetector(width, height)
        team1_regions, team2_regions = detector.get_team_regions()
        
        players = []
        
        # Process team 1
        for region in team1_regions:
            x1, y1, x2, y2 = region
            roi = screen[y1:y2, x1:x2]
            player_name = ocr_processor.extract_text(roi)
            if player_name:
                players.append(player_name)
                
        # Process team 2
        for region in team2_regions:
            x1, y1, x2, y2 = region
            roi = screen[y1:y2, x1:x2]
            player_name = ocr_processor.extract_text(roi)
            if player_name:
                players.append(player_name)
        
        return jsonify({
            'success': True,
            'players': players
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500