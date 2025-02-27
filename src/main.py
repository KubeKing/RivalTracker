import json
from hotkey import GlobalHotkey
import logging
import os
import sys
import win32con
import time
from datetime import datetime
from capture import ScreenCapture
from ocr import OCRProcessor
from database import Database
from tracker_lookup import TrackerLookup

class MarvelTracker:
    def __init__(self):
        # Set up basic logging first
        self.setup_basic_logging()
        
        # Load config and reconfigure logging
        self.load_config()
        self.setup_logging()
        
        # Initialize rest of the application
        self.initialize_components()
        self.setup_hotkey()
        self.logger.info("Marvel Tracker initialized successfully")

    def setup_basic_logging(self):
        """Set up basic logging before config is loaded."""
        log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # Create basic logger for startup
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(os.path.join(log_dir, 'app.log'), encoding='utf-8')
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info("Basic logging initialized")

    def setup_logging(self):
        """Set up logging configuration."""
        log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # Get logging config from config file
        log_config = self.config.get('logging', {})
        log_level = getattr(logging, log_config.get('level', 'INFO'))
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        log_file = os.path.join(log_dir, log_config.get('file', 'app.log'))
        
        # Create file handler with config
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(logging.Formatter(log_format))
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        root_logger.handlers = []  # Remove any existing handlers
        root_logger.addHandler(file_handler)
        
        # Set up OCR logger with debug level
        ocr_logger = logging.getLogger('ocr')
        ocr_logger.setLevel(logging.INFO)
        # Ensure OCR logger propagates to root
        ocr_logger.propagate = True
        
        # Create main logger for this class
        self.logger = logging.getLogger(__name__)
        self.logger.info("Logging initialized with level %s", log_level)

    def load_config(self):
        """Load configuration from config file."""
        try:
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                'config',
                'config.json'
            )
            with open(config_path, 'r') as f:
                self.config = json.load(f)
            self.logger.info("Configuration loaded successfully")
        except Exception as e:
            self.logger.error(f"Error loading configuration: {str(e)}")
            sys.exit(1)

    def initialize_components(self):
        """Initialize main components."""
        try:
            self.screen_capture = ScreenCapture(self.config)
            self.tracker_lookup = TrackerLookup(self.config)
            self.ocr_processor = OCRProcessor(
                self.config,
                screen_capture=self.screen_capture,
                tracker_lookup=self.tracker_lookup
            )
            self.database = Database(self.config)
            self.logger.info("Components initialized successfully")
        except Exception as e:
            self.logger.error(f"Error initializing components: {str(e)}")
            sys.exit(1)

    def setup_hotkey(self):
        """Set up the hotkey listener."""
        try:
            self.hotkey = GlobalHotkey(self.config['capture_key'], self.handle_hotkey)
            self.hotkey.start()
            
            # Give the hotkey thread a moment to initialize
            time.sleep(0.5)
        except Exception as e:
            self.logger.error(f"Error setting up hotkey: {str(e)}")
            sys.exit(1)

    def handle_hotkey(self, key):
        """Handle hotkey press event."""
        try:
            self.logger.info(f"Global hotkey triggered: {key}")
            
            # Capture the screenshot and get the filepath
            screenshot_path = self.screen_capture.capture_window()
            if screenshot_path:
                # Process the captured screenshot
                self.ocr_processor.process_uploaded_image(screenshot_path)
            else:
                self.logger.error("Failed to capture screenshot")

        except Exception as e:
            self.logger.error(f"Error processing capture: {str(e)}")

    def cleanup(self):
        """Cleanup resources before exit."""
        try:
            # Cleanup old captures
            self.screen_capture.cleanup_old_captures()
            # Cleanup old database records
            self.database.cleanup_old_records()
            self.logger.info("Cleanup completed successfully")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")

    def run(self):
        """Run the main application loop."""
        try:
            print(f"Marvel Tracker running. Press Alt+{self.config['capture_key'].upper()} to capture, Ctrl+C to exit.")
            
            # Keep the main thread alive and handle cleanup
            try:
                while True:
                    time.sleep(0.1)  # Small sleep to prevent high CPU usage
            except KeyboardInterrupt:
                self.logger.info("Received shutdown signal")
                if hasattr(self, 'hotkey'):
                    self.hotkey.stop()
        finally:
            self.cleanup()

if __name__ == "__main__":
    tracker = MarvelTracker()
    tracker.run()
