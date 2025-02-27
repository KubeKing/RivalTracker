# Marvel Tracker

A tool for tracking player statistics in Marvel Rivals.

## Setup Instructions

### 1. FlareSolverr Setup

FlareSolverr is used to bypass Cloudflare protection on the tracker.gg API. The updated configuration uses a non-headless browser with stealth mode to better handle Cloudflare challenges.

#### Install Docker and Docker Compose

If you don't have Docker and Docker Compose installed, follow the instructions for your operating system:
- [Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows-install/)
- [Docker Desktop for Mac](https://docs.docker.com/desktop/install/mac-install/)
- [Docker Engine for Linux](https://docs.docker.com/engine/install/)

#### Start FlareSolverr

1. Navigate to the project directory:
   ```
   cd path/to/MarvelTracker
   ```

2. Start FlareSolverr using Docker Compose:
   ```
   docker-compose up -d
   ```

3. Verify that FlareSolverr is running:
   ```
   docker ps
   ```
   You should see the FlareSolverr container running.

### 2. Application Setup

1. Install the required Python packages:
   ```
   pip install -r requirements.txt
   ```

2. Run the application:
   ```
   python src/main.py
   ```

## Troubleshooting

### FlareSolverr Issues

If you encounter issues with FlareSolverr:

1. Check the FlareSolverr logs:
   ```
   docker logs flaresolverr
   ```

2. Restart FlareSolverr:
   ```
   docker-compose restart flaresolverr
   ```

3. If problems persist, try rebuilding the container:
   ```
   docker-compose down
   docker-compose up -d --build
   ```

### Cloudflare Challenges

If you're still encountering Cloudflare challenges:

1. Increase the delay between requests in `config/config.json`:
   ```json
   "flaresolverr": {
       "min_request_delay": 10000,
       "max_request_delay": 15000
   }
   ```

2. Try using a different browser profile in `config/config.json`:
   ```json
   "browser_profiles": [
       {
           "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
           "language": "en-US,en;q=0.7"
       }
   ]
   ```

## Configuration

The application can be configured by editing `config/config.json`. Key settings include:

- `flaresolverr`: Settings for the FlareSolverr integration
- `lookup_friendly_team`: Whether to look up friendly team players
- `lookup_enemy_team`: Whether to look up enemy team players

## License

This project is licensed under the MIT License - see the LICENSE file for details.
