# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Dukaan Buddy** is a voice-first store management system designed for Indian shopkeepers. Users speak in Hindi to manage inventory, record sales, track expenses, and get business insights - no typing required.

## Tech Stack

**Backend:**
- Flask (synchronous, no async) on Python 3
- SQLite (built-in sqlite3 module) for persistence
- Raw Anthropic REST API (no official SDK) for Claude integration
- Pydantic 2.x for data validation and schemas
- Loguru for structured logging

**Frontend:**
- Vanilla HTML/CSS/JavaScript (no frameworks)
- Web Audio API for microphone recording
- Sarvam AI API for Hindi STT (Speech-to-Text) and TTS (Text-to-Speech)

**AI/LLM:**
- Claude Sonnet 4 for intent routing and natural language response generation
- No LLM for business logic - pure Python agents ensure deterministic behavior

## Architecture Overview

### Request Flow

```
User speaks Hindi → Client records WAV → Sarvam STT → transcript

       ↓ (Client fires TWO parallel requests)

┌─────────────────────┐         ┌──────────────────────┐
│  POST /quick-ack    │         │   POST /process      │
│  (keyword match)    │         │   (full pipeline)    │
│  ~1ms, no LLM       │         │   ~3-5s with LLM     │
└─────────────────────┘         └──────────────────────┘
         ↓                                  ↓
    {ack_text}                      {response_text, intents, alerts}
         ↓                                  ↓
  Sarvam TTS plays            Waits for ack to finish,
  immediately                  then plays full response
```

### Core Components

1. **Router** (`core/router.py`): Uses Claude to classify user intent and extract structured data
   - Returns list of `SingleIntent` objects with intent type + extracted parameters
   - Supports multi-intent sentences (e.g., "sold onions AND paid rent")

2. **Agents** (`agents/`): Pure Python business logic, no LLM
   - `InventoryAgent`: Stock in/out/query with weighted-average costing
   - `SalesAgent`: Records sales, auto-deducts inventory
   - `ExpenseAgent`: Categorized expense tracking
   - `SummaryAgent`: Daily profit calculation (Sales - COGS - Expenses)
   - `AlertAgent`: Low stock notifications

3. **State Management** (`core/state.py`): In-memory state with SQLite persistence
   - Inventory: `dict[item_name, InventoryItem]` with weighted avg cost
   - Sales/Expenses: Daily lists, persisted to DB
   - Auto-loads on startup, saves after each `/process` request

4. **Normalization** (`core/normalizer.py`): Critical for data consistency
   - Maps Hindi/Hinglish/English/typos → canonical English (e.g., "आलू"/"aloo"/"Potato"/"potatoes" → "potato")
   - Fuzzy matching for typos using SequenceMatcher
   - Category normalization for expenses ("bijli"/"बिजली" → "electricity")

5. **Quick Acknowledgment** (`core/quick_ack.py`): Instant Hindi feedback
   - Keyword-based detection (no LLM) returns context-aware ack in <1ms
   - Examples: "अच्छा, लिख लेता हूँ..." (stock in), "बेचा? लिख रहा हूँ..." (sale)

## Common Development Commands

### Running the Server

```bash
# Development server
python3 server.py

# Production with Gunicorn (if needed)
gunicorn server:app --bind 0.0.0.0:5000
```

Server runs on `http://localhost:5000`

### Testing

**Test item/category normalization:**
```bash
python3 test_normalization.py
```

**Manual API testing with curl:**
```bash
# Test quick acknowledgment
curl -X POST http://localhost:5000/quick-ack \
  -H 'Content-Type: application/json' \
  -d '{"text":"50 kilo aloo aaya 30 rupaye kilo"}'

# Test full pipeline
curl -X POST http://localhost:5000/process \
  -H 'Content-Type: application/json' \
  -d '{"text":"50 kilo aloo aaya 30 rupaye kilo", "language":"hi-IN"}'

# View current state (debugging)
curl http://localhost:5000/state | python3 -m json.tool
```

More test examples in `docs/TEST_COMMANDS.md`

### Database

SQLite database stored at: `db/store.db`

**Schema:**
- `inventory`: item_name (PK), quantity, unit, avg_cost, updated_at
- `sales`: id, item_name, quantity, unit, price, total, created_at, day
- `expenses`: id, category, amount, description, created_at, day

## Key Design Patterns

### 1. Parallel Quick-Ack Pattern
The client fires `/quick-ack` and `/process` simultaneously. User hears instant Hindi acknowledgment (~1ms) while Claude processes the full pipeline in the background (~3-5s). This creates the illusion of real-time voice interaction.

### 2. Weighted Average Costing
When adding stock, the system calculates:
```python
new_avg_cost = (existing_qty * existing_cost + new_qty * new_cost) / total_qty
```
This ensures accurate profit calculations when buying at different prices.

### 3. Normalization Layer
All item names and expense categories pass through normalization before storage. This prevents:
- Duplicate items with different spellings ("aloo" vs "Potato" vs "आलू")
- Inconsistent reporting and analytics
- Fuzzy matching handles typos automatically

### 4. Sync Flask Architecture
Deliberately avoids async complexity. Each request is independent and completes in linear fashion. Simplifies debugging and deployment.

### 5. Raw REST API (No SDK)
Uses direct HTTP requests to Anthropic API instead of official SDK. Provides explicit control over request format and easier troubleshooting of LLM interactions.

## Critical Files

- `server.py` - Flask app entry point, route handlers
- `core/state.py` - State management and SQLite persistence
- `core/router.py` - Intent classification via Claude
- `core/normalizer.py` - Item/category normalization
- `core/schemas.py` - Pydantic models for all data structures
- `core/llm.py` - Raw Anthropic API helper
- `prompts/router_prompt.py` - System prompt for intent classification
- `prompts/response_prompt.py` - System prompt for Hindi response generation
- `agents/*.py` - Business logic agents

## Environment Variables

Required in `.env`:
```
ANTHROPIC_API_KEY=sk-ant-...
SARVAM_API_KEY=...
```

The server will start without keys but API features won't work.

## Adding New Features

### Adding a New Intent

1. Add intent type to `IntentType` enum in `core/schemas.py`
2. Update `ROUTER_SYSTEM_PROMPT` in `prompts/router_prompt.py` to teach Claude about the new intent
3. Create or update relevant agent in `agents/` to handle the intent
4. Add handler in `server.py` `/process` endpoint

### Adding New Items to Normalizer

Edit `ITEM_MAPPINGS` in `core/normalizer.py` to add Hindi/Hinglish/English variants:
```python
ITEM_MAPPINGS = {
    "नया_item": "canonical_english_name",
    "naya": "canonical_english_name",
    ...
}
```

### Modifying Database Schema

1. Update `save_to_db()` and `load_from_db()` in `core/state.py`
2. SQLite will auto-create new columns with `CREATE TABLE IF NOT EXISTS`
3. For breaking changes, manually migrate `db/store.db` or delete and regenerate

## Debugging Tips

- Check logs: Loguru outputs to stdout with structured formatting
- Inspect state: `curl http://localhost:5000/state`
- Test normalization: Run `python3 test_normalization.py` to verify item mappings
- Router debugging: Check `logger.debug(f"Router raw response: {response_text}")` in `core/router.py`
- Client-side errors: Open browser console at `http://localhost:5000`

## Deployment

Currently configured for Replit hosting (see `.replit` file). Can deploy to any platform supporting Python Flask:
- Gunicorn included in requirements.txt for production
- Ensure `db/` directory is writable for SQLite persistence
- Set environment variables in hosting platform
