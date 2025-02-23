# README.md
# Marvel Rivals Tracker

A tool to automatically look up player stats from Marvel Rivals matches.

## Features
- Automatic screen capture of player names
- Direct links to tracker.gg profiles
- Real-time OCR processing
- Clean and responsive UI

## Prerequisites
- Docker and Docker Compose
- X11 forwarding enabled (for screen capture)

## Setup
1. Clone the repository
2. Copy `.env.example` to `.env` and adjust as needed
3. Build and run with Docker Compose:
```bash
docker-compose up --build
```

## Development
- Frontend: `cd frontend && npm install && npm run dev`
- Backend: `cd backend && pip install -r requirements.txt && python app.py`

## Testing
- Frontend: `cd frontend && npm test`
- Backend: `cd backend && python -m pytest`

## Contributing
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License
MIT

## Security Notes
- This application requires screen capture permissions
- All processing is done locally
- No data is stored or transmitted except to tracker.gg