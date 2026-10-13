# Multilingual AI Assistant and Vision Dashboard

An interactive multimodal conversational assistant supporting multi-language queries using Google Gemini AI, facial recognition for user identification, and local web automation.

## Key Features

- Gemini AI Chat Assistant (app.py): Natural language chat support in multiple languages.
- Multimodal Facial Recognition (assis.py): Detects and recognizes registered users using local camera feeds (known_faces/).
- Interactive UI: Web interface (fc.html) displaying responsive coordinate telemetry and conversational output.

## Setup & Usage

1. Configure your Gemini API key in .env (or set GEMINI_API_KEY environment variable).
2. Install dependencies: pip install google-generativeai opencv-python pillow
3. Run: python app.py
