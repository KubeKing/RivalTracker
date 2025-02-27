import json
import logging
import base64
from openai import OpenAI
from dotenv import load_dotenv
import os
from capture import ScreenCapture
from tracker_lookup import TrackerLookup

class OCRProcessor:
    def __init__(self, config, screen_capture=None, tracker_lookup=None):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.screen_capture = screen_capture or ScreenCapture(config)
        self.tracker_lookup = tracker_lookup or TrackerLookup(config)

        # Load environment variables
        load_dotenv()
        
        # Get settings from config and environment
        openai_settings = self.config.get('openai_settings', {})
        self.openai_model = openai_settings.get('model', 'gpt-4-turbo')
        self.max_tokens = openai_settings.get('max_tokens', 300)

        # Initialize the OpenAI client using environment variable
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

    def encode_image(self, image_path):
        """
        Encodes an image file to base64 string.
        """
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode("utf-8")
        except Exception as e:
            self.logger.error(f"Error encoding image: {e}")
            return None

    def extract_usernames(self, image_path):
        try:
            # Encode the image to base64
            base64_image = self.encode_image(image_path)
            if not base64_image:
                self.logger.error("Image encoding failed.")
                return [], []

            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are analyzing a game screen image to identify player usernames. "
                        "Return valid JSON with the structure:\n"
                        "{\n"
                        "  \"friendly_team\": [\"username1\", \"username2\", ...],\n"
                        "  \"enemy_team\": [\"username3\", \"username4\", ...]\n"
                        "}\n"
                        "Only include real player usernames from the image. "
                        "No additional keys or text. Do not include ```json``` code block."
                    )
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "List all the usernames from this game screen. Focus only on player names. Return them in the JSON format described above."
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                        }
                    ]
                }
            ]

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # Using vision model instead of text model
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=0.5
            )

            # Log the raw GPT output for debugging purposes
            #self.logger.info("Raw GPT input: %s", messages)
            content = response.choices[0].message.content
            self.logger.info("Raw GPT JSON output: %s", content)

            # Parse the returned JSON
            extracted_data = json.loads(content.strip())

            friendly = extracted_data.get('friendly_team', [])
            enemy = extracted_data.get('enemy_team', [])

            return friendly, enemy

        except Exception as e:
            self.logger.error(f"Error extracting usernames: {e}")
            return [], []

    def process_uploaded_image(self, image_path):
        """
        Processes an uploaded image by extracting usernames via GPT and performing tracker lookup.
        """
        friendly_team, enemy_team = self.extract_usernames(image_path)

        if not friendly_team and not enemy_team:
            self.logger.error("No usernames were extracted from the uploaded image.")
            return

        self.logger.info(f"Extracted usernames - Friendly: {friendly_team}, Enemy: {enemy_team}")
        self.tracker_lookup.lookup_players(
            friendly_team=friendly_team, 
            enemy_team=enemy_team
        )
