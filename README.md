# Dukaan Buddy

Voice-based store management system for Indian shopkeepers. Speak in Hindi to manage inventory, sales, expenses, and get real-time insights.

## Features

- 🎤 **Voice-First Interface** - No typing needed, just speak naturally in Hindi
- 📦 **Inventory Management** - Track stock in/out with automatic weighted-average costing
- 💰 **Sales Recording** - Record sales with automatic inventory deduction
- 💸 **Expense Tracking** - Categorized expense logging (bijli, kiraya, etc.)
- 📊 **Daily Summaries** - Get profit calculations (Sales - COGS - Expenses)
- ⚠️ **Low Stock Alerts** - Automatic notifications when items run low
- 💾 **SQLite Persistence** - All data saved locally and persists across sessions

## Architecture

```
User speaks → [Client: Mic → WAV → Sarvam STT → transcript]
                    ↓
        ┌──────────┴──────────┐
        ↓                     ↓
  POST /quick-ack        POST /process  (fired in PARALLEL)
  (keyword match,        (Claude intent routing → agents
   ~1ms, no LLM)         → Claude response gen, ~3-5s)
        ↓                     ↓
  {ack_text: "..."}      {response_text: "...", intents, alerts}
        ↓                     ↓
  Client: Sarvam TTS     Client: waits for ack audio to finish,
  plays ack immediately   then plays response via Sarvam TTS
```

## Tech Stack

**Backend:**
- Flask (sync, no async)
- SQLite (built-in sqlite3)
- Raw Anthropic REST API (no SDK)
- Pydantic for schemas
- Loguru for logging

**Frontend:**
- Vanilla HTML/CSS/JS
- Web Audio API for recording
- Sarvam AI for STT/TTS (client-side)

**AI:**
- Claude Sonnet 4 for intent routing and response generation
- No LLM for business logic (pure Python agents)

## Setup

1. **Install dependencies:**
```bash
python3 -m pip install -r requirements.txt
```

2. **Set environment variables** (already in `.env`):
```
SARVAM_API_KEY=your_key
ANTHROPIC_API_KEY=your_key
```

3. **Run server:**
```bash
python3 server.py
```

4. **Open browser:**
```
http://localhost:5000
```

## Usage Examples

**Stock In:**
> "50 kilo aloo aaya 30 rupaye kilo"

→ Adds 50kg potatoes at ₹30/kg with weighted average cost

**Sale:**
> "10 kilo aloo becha 40 rupaye"

→ Records sale, updates inventory, calculates remaining stock

**Expense:**
> "200 ka bijli bill bhara"

→ Logs ₹200 electricity expense

**Multi-Intent:**
> "30 kilo pyaaz becha 50 rupaye kilo aur 500 ka kiraya diya"

→ Processes both sale + expense in one sentence

**Query:**
> "Aloo kitna bacha hai?"

→ Returns current stock

**Summary:**
> "Aaj ka hisab bata"

→ Daily report: sales, expenses, profit, low stock

## API Endpoints

### POST /quick-ack
Fast keyword-based acknowledgment (no LLM, <1ms)

**Request:**
```json
{"text": "50 kilo aloo aaya"}
```

**Response:**
```json
{
  "ack_text": "अच्छा, लिख लेता हूँ...",
  "quick_intent": "stock_in"
}
```

### POST /process
Full pipeline: router → agents → response generation

**Request:**
```json
{
  "text": "50 kilo aloo aaya 30 rupaye kilo",
  "language": "hi-IN"
}
```

**Response:**
```json
{
  "response_text": "लिख लिया — 50 किलो आलू, ₹30 किलो। कुल ₹1500 का माल।",
  "intents": [{"intent": "inventory_in", "confidence": 0.95}],
  "alerts": {"low_stock_items": [], "threshold": 5.0}
}
```

### GET /state
Debug endpoint to view current state

**Response:**
```json
{
  "inventory": {
    "aloo": {
      "quantity": 50,
      "unit": "kg",
      "avg_cost_per_unit": 30,
      "last_updated": "2026-02-15T14:20:00"
    }
  },
  "sales": [...],
  "expenses": [...]
}
```

## Project Structure

```
dukaan-buddy/
├── .env                      # API keys
├── .gitignore
├── requirements.txt
├── server.py                 # Flask server
├── core/
│   ├── schemas.py            # Pydantic models
│   ├── state.py              # StoreState + SQLite persistence
│   ├── router.py             # Intent classification via Claude
│   ├── llm.py                # Raw Anthropic REST helper
│   └── quick_ack.py          # Keyword-based instant ack
├── agents/
│   ├── inventory.py          # Stock in/out/query
│   ├── sales.py              # Sale recording
│   ├── expense.py            # Expense tracking
│   ├── summary.py            # Daily summaries
│   └── alert.py              # Low stock alerts
├── prompts/
│   ├── router_prompt.py      # Intent classification prompt
│   └── response_prompt.py    # Response generation prompt
└── static/
    ├── index.html            # UI
    ├── app.js                # STT/TTS + parallel backend calls
    └── config.js             # Sarvam API config
```

## Key Design Decisions

1. **Parallel /quick-ack + /process** - User hears instant Hindi acknowledgment while Claude processes full pipeline

2. **Sync Flask** - No async complexity, simpler to debug

3. **Raw REST for Anthropic** - No SDK dependency, explicit control

4. **Pure Python Agents** - Business logic doesn't need LLM, faster + deterministic

5. **Client-side STT/TTS** - Leverages Sarvam AI directly from browser, reduces backend complexity

6. **SQLite with Duplicate Prevention** - Tracks saved counts to avoid re-inserting records

7. **Weighted Average Costing** - Proper inventory accounting for profit calculation

## License

MIT
