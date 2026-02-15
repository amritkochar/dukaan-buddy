# Dukaan Buddy

## Overview
Dukaan Buddy is a voice-powered store management assistant for Indian shopkeepers. It uses speech-to-text and text-to-speech (via Sarvam AI) along with Claude AI (Anthropic) to handle inventory tracking, sales recording, expense management, and daily summaries through natural voice commands in Hindi and English.

## Recent Changes
- 2026-02-15: Migrated database from SQLite to PostgreSQL (Replit built-in). Moved Sarvam API key from frontend to backend proxy endpoints (/api/stt, /api/tts) for security. Set up both API keys as secrets.

## Project Architecture
- **Backend**: Python Flask server (`server.py`) on port 5000
- **Frontend**: Static HTML/CSS/JS served by Flask from `static/` directory
- **Database**: PostgreSQL (Replit built-in, via DATABASE_URL) for persistent storage of inventory, sales, and expenses
- **AI**: Anthropic Claude API (server-side) for intent routing and response generation; Sarvam AI (server-side proxy) for STT/TTS
- **Deployment**: Gunicorn WSGI server, autoscale target

### Directory Structure
- `server.py` - Main Flask application entry point with API proxy endpoints
- `static/` - Frontend assets (HTML, JS, logo)
- `agents/` - Business logic agents (inventory, sales, expense, summary, alert)
- `core/` - Core modules (LLM helper, router, state management, schemas, normalizer)
- `prompts/` - Prompt templates for Claude
- `docs/` - Documentation

### Key Dependencies
- Flask, Flask-CORS
- Pydantic (data schemas)
- Loguru (logging)
- Requests (HTTP client for Anthropic and Sarvam APIs)
- psycopg2-binary (PostgreSQL driver)
- python-dotenv (environment variables)
- gunicorn (production WSGI server)

### Environment Variables (Secrets)
- `ANTHROPIC_API_KEY` (required for AI features)
- `SARVAM_API_KEY` (required for speech-to-text and text-to-speech)
- `DATABASE_URL` (auto-configured by Replit PostgreSQL)
