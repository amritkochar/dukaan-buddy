# Dukaan Buddy

## Overview
Dukaan Buddy is a voice-powered store management assistant for Indian shopkeepers. It uses speech-to-text and text-to-speech (via Sarvam AI, client-side) along with Claude AI (Anthropic, server-side) to handle inventory tracking, sales recording, expense management, and daily summaries through natural voice commands in Hindi and English.

## Recent Changes
- 2026-02-15: Imported project and configured for Replit environment. Made server gracefully handle missing API key instead of crashing.

## Project Architecture
- **Backend**: Python Flask server (`server.py`) on port 5000
- **Frontend**: Static HTML/CSS/JS served by Flask from `static/` directory
- **Database**: SQLite (`db/store.db`) for persistent storage of inventory, sales, and expenses
- **AI**: Anthropic Claude API (server-side) for intent routing and response generation; Sarvam AI (client-side) for STT/TTS

### Directory Structure
- `server.py` - Main Flask application entry point
- `static/` - Frontend assets (HTML, JS, logo)
- `agents/` - Business logic agents (inventory, sales, expense, summary, alert)
- `core/` - Core modules (LLM helper, router, state management, schemas, normalizer)
- `prompts/` - Prompt templates for Claude
- `docs/` - Documentation

### Key Dependencies
- Flask, Flask-CORS
- Pydantic (data schemas)
- Loguru (logging)
- Requests (HTTP client for Anthropic API)
- python-dotenv (environment variables)

### Environment Variables
- `ANTHROPIC_API_KEY` (required for AI features)
