# Marvel Rivals Match Tracker

A Python application that captures and tracks Marvel Rivals match information using screen capture and OCR.

## Features

- Automatic screen capture of Marvel Rivals loading screens
- OCR-based text extraction to identify match type (ATTACK/DEFEND) and player names
- Local SQLite database storage for match history
- Configurable hotkey (default: Home key) for capturing
- Automatic cleanup of old captures and records

## Requirements

- Python 3.8+
- Tesseract OCR
- Windows OS

## Installation

1. Install Tesseract OCR:
   - Download and install from: https://github.com/UB-Mannheim/tesseract/wiki
   - Add Tesseract to your system PATH

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

The application can be configured through `config/config.json`:

- `capture_key`: Hotkey for triggering screen capture (default: "home")
- `game_window_title`: Title of the game window to capture
- `temp_folder`: Location for temporary capture storage
- `database_path`: Location of the SQLite database
- `ocr_settings`: OCR configuration options

## Usage

1. Start the application:
```bash
python src/main.py
```

2. When in a Marvel Rivals loading screen:
   - Press the Home key to capture the screen
   - The application will automatically:
     - Capture the screen
     - Extract text using OCR
     - Identify match type and player names
     - Store the information in the database

3. To exit:
   - Press Ctrl+C in the terminal

## Data Storage

Match data is stored in a SQLite database with the following information:
- Match type (ATTACK/DEFEND)
- Player names
- Timestamp
- Original capture image path
- Raw extracted text

## Maintenance

The application automatically:
- Cleans up temporary capture files older than 24 hours
- Removes database records older than 30 days

## Troubleshooting

Common issues:

1. **OCR Not Working**:
   - Ensure Tesseract is properly installed and in your PATH
   - Check the logs for specific error messages

2. **Screen Capture Failed**:
   - Verify the game window is open and visible
   - Check if the window title matches the configuration

3. **Hotkey Not Responding**:
   - Ensure no other application is using the same hotkey
   - Try running the application as administrator

Logs are stored in the `logs` directory for debugging.
