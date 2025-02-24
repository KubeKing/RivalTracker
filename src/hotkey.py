import win32con
import win32api
import win32gui
import threading
import logging
import ctypes
from ctypes import wintypes, windll
import atexit
import time

class GlobalHotkey:
    """Global hotkey handler using Windows RegisterHotKey."""
    
    def __init__(self, key, callback):
        self.logger = logging.getLogger(__name__)
        self.key = key
        self.callback = callback
        self.running = False
        self.thread = None
        
        # Map key names to virtual key codes
        self.key_map = {
            'home': win32con.VK_HOME,
        }

    def _register_hotkey(self):
        """Register the global hotkey."""
        try:
            vk_code = self.key_map.get(self.key.lower())
            if not vk_code:
                raise ValueError(f"Unsupported key: {self.key}")
            
            # Register with Alt modifier
            MOD_ALT = 0x0001
            
            # Try to register the hotkey
            if not windll.user32.RegisterHotKey(None, 1, MOD_ALT, vk_code):
                error = ctypes.get_last_error()
                raise Exception(f"Failed to register hotkey. Error code: {error}")
            
            self.logger.info(f"Successfully registered Alt+{self.key} (VK: {vk_code})")
            return True
            
        except Exception as e:
            self.logger.error(f"Error registering hotkey: {str(e)}")
            return False

    def _message_loop(self):
        """Run the message loop."""
        try:
            if not self._register_hotkey():
                return
            
            self.logger.info("Starting hotkey listener...")
            msg = wintypes.MSG()
            
            while self.running:
                if windll.user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, win32con.PM_REMOVE):
                    if msg.message == win32con.WM_HOTKEY:
                        self.logger.info(f"Hotkey triggered: {self.key}")
                        self.callback(self.key)
                    
                    windll.user32.TranslateMessage(ctypes.byref(msg))
                    windll.user32.DispatchMessageW(ctypes.byref(msg))
                else:
                    # Small sleep to prevent high CPU usage
                    time.sleep(0.01)
                
        except Exception as e:
            self.logger.error(f"Error in message loop: {str(e)}")
        finally:
            try:
                windll.user32.UnregisterHotKey(None, 1)
            except:
                pass

    def start(self):
        """Start the hotkey listener."""
        if self.running:
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._message_loop)
        self.thread.daemon = True
        self.thread.start()
        
        # Register cleanup
        atexit.register(self.stop)

    def stop(self):
        """Stop the hotkey listener."""
        if not self.running:
            return
            
        self.running = False
        try:
            windll.user32.UnregisterHotKey(None, 1)
        except:
            pass
            
        self.logger.info("Hotkey listener stopped")
