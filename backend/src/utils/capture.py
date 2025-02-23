# backend/src/utils/capture.py
import mss
import numpy as np
import cv2

class ScreenCapture:
    def __init__(self):
        self.sct = mss.mss()

    def capture_screen(self):
        monitor = self.sct.monitors[1]  # Primary monitor
        screenshot = self.sct.grab(monitor)
        return np.array(screenshot)

    def get_screen_dimensions(self):
        monitor = self.sct.monitors[1]
        return monitor["width"], monitor["height"]
