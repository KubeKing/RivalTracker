# backend/src/ocr/regions.py
class RegionDetector:
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        
    def get_team_regions(self):
        # Calculate relative positions based on screen size
        left_team = [
            (
                int(0.1 * self.screen_width),
                int((0.2 + i * 0.1) * self.screen_height),
                int(0.3 * self.screen_width),
                int((0.25 + i * 0.1) * self.screen_height)
            )
            for i in range(6)
        ]
        
        right_team = [
            (
                int(0.7 * self.screen_width),
                int((0.2 + i * 0.1) * self.screen_height),
                int(0.9 * self.screen_width),
                int((0.25 + i * 0.1) * self.screen_height)
            )
            for i in range(6)
        ]
        
        return left_team, right_team