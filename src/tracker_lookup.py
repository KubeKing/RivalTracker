import logging
import time
import requests
import random
import json
import re

class TrackerLookup:
    def __init__(self, config):
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.base_url = "https://api.tracker.gg/api/v2/marvel-rivals"
        
        # FlareSolverr settings
        flaresolverr_config = config.get('flaresolverr', {})
        self.flaresolverr_url = flaresolverr_config.get('url', "http://localhost:8191/v1")
        self.max_timeout = flaresolverr_config.get('max_timeout', 60000)
        self.retry_attempts = flaresolverr_config.get('retry_attempts', 3)
        self.retry_delay = flaresolverr_config.get('retry_delay', 1000)
        
        self.lookup_friendly = config.get('lookup_friendly_team', False)
        self.lookup_enemy = config.get('lookup_enemy_team', True)
        
        # Session management
        self.session_id = None
        self.last_session_check = 0
        self.session_check_interval = 60  # Check session validity every 60 seconds

        self.headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Encoding': 'gzip',
            'Accept-Language': 'en-US,en;q=0.9',
            'Origin': 'https://tracker.gg',
            'Referer': 'https://tracker.gg/',
            'sec-ch-ua': '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"'
        }

    def ensure_session(self):
        """Ensure a FlareSolverr session exists and is valid."""
        current_time = time.time()
        
        # Check if we need to validate the session
        if self.session_id and (current_time - self.last_session_check) < self.session_check_interval:
            return True
            
        try:
            # List current sessions
            sessions_response = requests.post(self.flaresolverr_url, json={"cmd": "sessions.list"})
            sessions_data = sessions_response.json()
            
            # Check if our session is still valid
            if self.session_id:
                if self.session_id in [s.get('id') for s in sessions_data.get("sessions", [])]:
                    self.logger.debug(f"Existing session {self.session_id} is valid")
                    self.last_session_check = current_time
                    return True
                else:
                    self.logger.info(f"Session {self.session_id} no longer valid")
                    self.session_id = None
            
            # Create new session if needed
            self.logger.info("Creating new FlareSolverr session")
            create_response = requests.post(self.flaresolverr_url, json={
                "cmd": "sessions.create",
                "options": {
                    "browser": "firefox"  # More reliable than chrome for Cloudflare
                }
            })
            create_data = create_response.json()
            
            if create_data.get("status") != "ok":
                self.logger.error(f"Failed to create FlareSolverr session: {create_data.get('message')}")
                return False
            
            self.session_id = create_data.get('session')
            self.last_session_check = current_time
            self.logger.info(f"Created new session: {self.session_id}")
            return True

        except Exception as e:
            self.logger.error(f"Error managing FlareSolverr session: {str(e)}")
            return False

    def check_flaresolverr(self):
        """Check if FlareSolverr is running and accessible."""
        try:
            health_check = requests.post(self.flaresolverr_url, json={"cmd": "sessions.list"})
            if not health_check.ok:
                return False
                
            # Ensure we have a valid session
            return self.ensure_session()
                
        except requests.RequestException as e:
            self.logger.error(f"FlareSolverr health check failed: {str(e)}")
            return False

    def extract_json_from_html(self, html_text):
        """Extract JSON from HTML-wrapped response."""
        if html_text.startswith('<html>'):
            self.logger.debug("Received HTML-wrapped response, extracting JSON")
            json_match = re.search(r'<pre[^>]*>(.*?)</pre>', html_text, re.DOTALL)
            if not json_match:
                self.logger.error("Could not extract JSON from HTML response")
                return None
            return json_match.group(1)
        return html_text

    def flaresolverr_request(self, url):
        """Uses FlareSolverr to bypass Cloudflare restrictions with retry logic."""
        if not self.check_flaresolverr():
            self.logger.error("FlareSolverr is not running or not accessible")
            self.logger.error("Please start FlareSolverr and try again.")
            return None

        payload = {
            "cmd": "request.get",
            "url": url,
            "maxTimeout": self.max_timeout,
            "headers": self.headers,
            "session": self.session_id
        }

        for attempt in range(self.retry_attempts):
            try:
                self.logger.debug(f"FlareSolverr request attempt {attempt + 1} for URL: {url}")
                response = requests.post(
                    self.flaresolverr_url, 
                    json=payload, 
                    timeout=self.max_timeout / 1000 + 5  # Convert to seconds and add buffer
                )
                
                # Debug log response details
                self.logger.debug(f"Raw FlareSolverr response status: {response.status_code}")
                self.logger.debug(f"Raw FlareSolverr response headers: {dict(response.headers)}")
                self.logger.debug(f"Raw FlareSolverr response content: {response.text[:1000]}")
                
                if not response.ok:
                    self.logger.error(f"FlareSolverr HTTP error: {response.status_code}")
                    if attempt < self.retry_attempts - 1:
                        time.sleep(self.retry_delay / 1000)
                        continue
                    return None

                data = response.json()
                
                # Check FlareSolverr status
                if data.get("status") != "ok":
                    self.logger.error(f"FlareSolverr error status: {data.get('status')}, message: {data.get('message')}")
                    if attempt < self.retry_attempts - 1:
                        time.sleep(self.retry_delay / 1000)
                        continue
                    return None

                # Validate solution exists and has response
                if not data.get("solution", {}).get("response"):
                    self.logger.error("FlareSolverr response missing solution or response data")
                    if attempt < self.retry_attempts - 1:
                        time.sleep(self.retry_delay / 1000)
                        continue
                    return None
                
                return data

            except requests.RequestException as e:
                self.logger.error(f"Request to FlareSolverr failed (attempt {attempt + 1}): {str(e)}")
                if attempt < self.retry_attempts - 1:
                    time.sleep(self.retry_delay / 1000)
                    continue
                return None
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse FlareSolverr response (attempt {attempt + 1}): {str(e)}")
                self.logger.debug(f"Response content: {response.text[:200]}")
                if attempt < self.retry_attempts - 1:
                    time.sleep(self.retry_delay / 1000)
                    continue
                return None

    def lookup_player(self, player_name):
        """Look up a single player using FlareSolverr."""
        try:
            # URL encode the player name for the API request
            encoded_name = requests.utils.quote(player_name)
            search_url = f"{self.base_url}/standard/search?platform=ign&query={encoded_name}"
            result = self.flaresolverr_request(search_url)

            if not result:
                self.logger.error(f"Empty response from FlareSolverr for {player_name}")
                return

            if "solution" not in result:
                self.logger.error(f"No 'solution' in FlareSolverr response for {player_name}")
                return

            if "response" not in result["solution"]:
                self.logger.error(f"No 'response' in solution for {player_name}")
                return

            response_text = result["solution"]["response"]
            if not response_text:
                self.logger.error(f"Empty response text for {player_name}")
                return

            # Extract JSON from response
            search_json = self.extract_json_from_html(response_text)
            if not search_json:
                return

            search_data = json.loads(search_json)
            if not search_data.get('data'):
                self.logger.error(f"No search results found for {player_name}")
                return
            
            self.logger.debug(f"Parsed search data: {json.dumps(search_data, indent=2)}")
            # Get player's stats
            stats_url = f"{self.base_url}/standard/profile/ign/{encoded_name}"
            stats_result = self.flaresolverr_request(stats_url)

            if not stats_result:
                self.logger.error(f"Empty stats response from FlareSolverr for {player_name}")
                return

            if "solution" not in stats_result:
                self.logger.error(f"No 'solution' in stats response for {player_name}")
                return

            if "response" not in stats_result["solution"]:
                self.logger.error(f"No 'response' in stats solution for {player_name}")
                return

            stats_response_text = stats_result["solution"]["response"]
            if not stats_response_text:
                self.logger.error(f"Empty stats response text for {player_name}")
                return

            # Extract JSON from stats response
            stats_json = self.extract_json_from_html(stats_response_text)
            if not stats_json:
                return

            try:
                stats_data = json.loads(stats_json)
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse JSON data: {e}")
                self.logger.debug(f"Raw JSON data: {stats_json[:1000]}")
                return

            if not isinstance(stats_data, dict):
                self.logger.error(f"Stats data is not a dictionary: {type(stats_data)}")
                return
                
            if 'data' not in stats_data:
                self.logger.error("No 'data' key in stats data")
                return
                
            if not stats_data['data']:
                self.logger.error("Empty data array in stats response")
                return

            # Log full data structure for debugging
            self.logger.debug(f"Full stats data structure: {json.dumps(stats_data, indent=2)}")

            # Get segments from the data
            segments = stats_data.get('data', {}).get('segments', [])
            if not isinstance(segments, list):
                self.logger.error(f"Unexpected segments structure - expected list, got {type(segments)}")
                return

            # Filter for hero segments
            hero_segments = [
                seg for seg in segments 
                if isinstance(seg, dict) and seg.get('type') == 'hero'
            ]
            
            if not hero_segments:
                self.logger.error(f"No hero segments found for {player_name}")
                return
            
            # Process hero stats
            hero_stats = {}
            for segment in hero_segments:
                hero_name = segment.get('metadata', {}).get('name', 'Unknown Hero')
                hero_id = segment.get('attributes', {}).get('heroId')
                
                if not hero_id:
                    self.logger.warning(f"Missing heroId for hero: {hero_name}")
                    continue
                
                if hero_id not in hero_stats:
                    hero_stats[hero_id] = {
                        'name': hero_name,
                        'matches': 0,
                        'wins': 0,
                        'kda': 0
                    }
                
                stats = segment.get('stats', {})
                if not stats:
                    self.logger.warning(f"No stats found for hero: {hero_name}")
                    continue
                    
                # Extract stats from the response structure
                matches = float(stats.get('matchesPlayed', {}).get('value', 0))
                wins = float(stats.get('matchesWon', {}).get('value', 0))
                kda = float(stats.get('kdaRatio', {}).get('value', 0))
                
                hero_stats[hero_id]['matches'] += matches
                hero_stats[hero_id]['wins'] += wins
                hero_stats[hero_id]['kda'] = max(hero_stats[hero_id]['kda'], kda)

            # Sort heroes by matches played
            sorted_heroes = sorted(hero_stats.values(), key=lambda x: x['matches'], reverse=True)
            
            # Display top 3 heroes
            print(f"\n{player_name}")
            for hero in sorted_heroes[:3]:
                losses = hero['matches'] - hero['wins']
                win_rate = (hero['wins'] / hero['matches'] * 100) if hero['matches'] > 0 else 0
                print(f"  • {hero['name']} ({hero['matches']} games)")
                print(f"    {win_rate:.1f}% WR ({hero['wins']} W - {losses} L), KDA: {hero['kda']:.2f}")

        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing response for {player_name}: {str(e)}")
            self.logger.debug("Response that failed to parse:")
            self.logger.debug(f"Search URL: {search_url}")
            self.logger.debug(f"Stats URL: {stats_url}")
            self.logger.debug(f"Response text: {response_text[:500] if 'response_text' in locals() else 'N/A'}")
        except Exception as e:
            self.logger.error(f"Unexpected error looking up {player_name}: {str(e)}")

    def lookup_players(self, friendly_team=None, enemy_team=None):
        """Look up player stats based on configuration settings."""
        if not friendly_team and not enemy_team:
            self.logger.error("No player teams provided for lookup")
            return

        if self.lookup_friendly and friendly_team:
            print("\nFriendly Team:")
            for player in friendly_team:
                self.lookup_player(player)
                time.sleep(random.uniform(1, 2))  # Add delay between requests

        if self.lookup_enemy and enemy_team:
            print("\nEnemy Team:")
            for player in enemy_team:
                self.lookup_player(player)
                time.sleep(random.uniform(1, 2))  # Add delay between requests
