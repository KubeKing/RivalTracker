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

class MarvelTracker:
    def __init__(self):
        self.setup_logging()
        self.load_config()
        self.initialize_components()
        self.setup_hotkey()
        self.logger.info("Marvel Tracker initialized successfully")

    def setup_logging(self):
        """Set up logging configuration."""
        log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(os.path.join(log_dir, 'app.log')),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)

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
            self.ocr_processor = OCRProcessor(self.config)
            self.database = Database(self.config)
            self.logger.info("Components initialized successfully")
        except Exception as e:
            self.logger.error(f"Error initializing components: {str(e)}")
            sys.exit(1)

    def setup_hotkey(self):
        """Set up the hotkey listener."""
        try:
            self.logger.info("Setting up global hotkey...")
            print("\nInitializing hotkey system...")
            
            self.hotkey = GlobalHotkey(self.config['capture_key'], self.handle_hotkey)
            self.hotkey.start()
            
            # Give the hotkey thread a moment to initialize
            time.sleep(0.5)
            
            print(f"Listening for Alt+{self.config['capture_key'].upper()} key combination...")
            print("Debug logging enabled - check logs/app.log for key events")
        except Exception as e:
            self.logger.error(f"Error setting up hotkey: {str(e)}")
            sys.exit(1)

    def handle_hotkey(self, key):
        """Handle hotkey press event."""
        try:
            self.logger.info(f"Global hotkey triggered: {key}")
            print(f"\nCapture triggered with {key} key")
            
            # Capture screen
            image_path = self.screen_capture.capture_window()
            if not image_path:
                self.logger.error("Failed to capture screen")
                return

            # Process image with OCR
            text = self.ocr_processor.extract_text(image_path)
            if not text:
                self.logger.error("Failed to extract text from image")
                return

            # Extract game information
            game_info = self.ocr_processor.find_game_info(text)
            if not game_info:
                self.logger.error("Failed to extract game information")
                return

            # Store in database
            match_id = self.database.store_match(
                game_info['match_type'],
                game_info['friendly_team'],
                game_info['enemy_team'],
                text,
                image_path
            )

            if match_id:
                self.logger.info(f"Successfully processed and stored match {match_id}")
                print(f"\nMatch captured! Type: {game_info['match_type']}")
                print(f"Friendly team: {', '.join(game_info['friendly_team'])}")
                print(f"Enemy team: {', '.join(game_info['enemy_team'])}")
            else:
                self.logger.error("Failed to store match data")

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
            print(f"\nMarvel Tracker is running!")
            print(f"Press 'Alt+{self.config['capture_key']}' to capture the game screen")
            print("Press Ctrl+C to exit")
            
            # Keep the main thread alive and handle cleanup
            try:
                while True:
                    time.sleep(0.1)  # Small sleep to prevent high CPU usage
            except KeyboardInterrupt:
                self.logger.info("Received shutdown signal")
                if hasattr(self, 'hotkey'):
                    self.hotkey.stop()
                print("\nShutting down Marvel Tracker...")
        finally:
            self.cleanup()
            print("Goodbye!")

if __name__ == "__main__":
    tracker = MarvelTracker()
    tracker.run()
