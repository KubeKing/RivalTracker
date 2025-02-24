import win32gui
import win32con
import win32api
from PIL import Image, ImageGrab
import os
import logging
from datetime import datetime
import numpy as np
import hashlib
import time

class ScreenCapture:
    def __init__(self, config):
        self.config = config
        self.temp_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), config['temp_folder'])
        self.game_window_title = config['game_window_title']
        self.logger = logging.getLogger(__name__)
        self.last_image_hash = None

    def is_fullscreen(self, hwnd):
        """Check if window is in fullscreen mode."""
        try:
            # Get window style
            style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
            placement = win32gui.GetWindowPlacement(hwnd)
            
            # Check for fullscreen-specific styles
            is_popup = bool(style & win32con.WS_POPUP)
            is_maximized = placement[1] == win32con.SW_SHOWMAXIMIZED
            has_border = bool(style & win32con.WS_BORDER)
            has_caption = bool(style & win32con.WS_CAPTION)
            
            # Get window and screen dimensions
            monitor = win32api.GetSystemMetrics(win32con.SM_CXSCREEN), win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
            window = win32gui.GetWindowRect(hwnd)
            window_size = (window[2] - window[0], window[3] - window[1])
            
            self.logger.debug(f"Window style: {style}")
            self.logger.debug(f"Is popup: {is_popup}")
            self.logger.debug(f"Is maximized: {is_maximized}")
            self.logger.debug(f"Has border: {has_border}")
            self.logger.debug(f"Has caption: {has_caption}")
            self.logger.debug(f"Monitor size: {monitor}")
            self.logger.debug(f"Window size: {window_size}")
            
            return (is_popup and not has_border) or (is_maximized and window_size == monitor)
            
        except Exception as e:
            self.logger.error(f"Error checking fullscreen state: {str(e)}")
            return False

    def get_window_handle(self):
        """Find the game window handle."""
        self.logger.info(f"Searching for window with title: {self.game_window_title}")
        hwnd = win32gui.FindWindow(None, self.game_window_title)
        if not hwnd:
            self.logger.error(f"Could not find window with title: {self.game_window_title}")
            # List all windows to help debug
            def callback(hwnd, windows):
                if win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd)
                    if title:
                        windows.append(title)
                return True
            windows = []
            win32gui.EnumWindows(callback, windows)
            self.logger.info(f"Available windows: {', '.join(windows)}")
            return None
            
        self.logger.info(f"Found window handle: {hwnd}")
        
        # Check window state
        if self.is_fullscreen(hwnd):
            self.logger.info("Window is in fullscreen mode")
        else:
            self.logger.info("Window is in windowed mode")
            
        return hwnd

    def capture_window(self):
        """Capture the game window."""
        try:
            hwnd = self.get_window_handle()
            if not hwnd:
                return None

            # Get window dimensions
            left, top, right, bottom = win32gui.GetWindowRect(hwnd)
            width = right - left
            height = bottom - top

            self.logger.info("Capturing with ImageGrab")
            
            # Bring window to foreground
            if self.is_fullscreen(hwnd):
                win32gui.SetForegroundWindow(hwnd)
                time.sleep(0.1)  # Give window time to come to foreground
            
            # Capture the screen region
            image = ImageGrab.grab(bbox=(left, top, right, bottom))
            
            if image is None:
                self.logger.error("ImageGrab failed")
                return None

            # Calculate image hash
            img_array = np.array(image)
            current_hash = hashlib.md5(img_array.tobytes()).hexdigest()
            
            # Check if this is a duplicate image
            if self.last_image_hash == current_hash:
                self.logger.error("Captured image is identical to previous capture")
                return None
                
            self.last_image_hash = current_hash
            
            # Save image with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"capture_{timestamp}.png"
            filepath = os.path.join(self.temp_folder, filename)
            
            # Ensure temp directory exists
            os.makedirs(self.temp_folder, exist_ok=True)
            
            # Log capture details
            self.logger.info(f"New capture - Hash: {current_hash[:8]}")
            self.logger.info(f"Window dimensions: {width}x{height}")
            self.logger.info(f"Image dimensions: {image.size}")
            self.logger.info(f"Saving to: {filepath}")
            
            image.save(filepath)
            
            if os.path.exists(filepath):
                file_size = os.path.getsize(filepath)
                self.logger.info(f"Saved successfully. File size: {file_size} bytes")
                
                # Verify saved file
                with Image.open(filepath) as saved_img:
                    if saved_img.size != image.size:
                        self.logger.error("Saved image dimensions don't match capture")
                        return None
            else:
                self.logger.error("File was not created after save attempt")
                return None
            return filepath

        except Exception as e:
            self.logger.error(f"Error capturing screen: {str(e)}")
            return None

    def cleanup_old_captures(self, max_age_hours=24):
        """Clean up old capture files."""
        try:
            current_time = datetime.now()
            for filename in os.listdir(self.temp_folder):
                if filename.startswith("capture_") and filename.endswith(".png"):
                    filepath = os.path.join(self.temp_folder, filename)
                    file_time = datetime.fromtimestamp(os.path.getctime(filepath))
                    age = current_time - file_time
                    if age.total_seconds() > max_age_hours * 3600:
                        os.remove(filepath)
                        self.logger.info(f"Cleaned up old capture: {filepath}")
        except Exception as e:
            self.logger.error(f"Error cleaning up captures: {str(e)}")
