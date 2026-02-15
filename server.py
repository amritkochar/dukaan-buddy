#!/usr/bin/env python3
"""
Dukaan Buddy - Flask REST API Server
Integrates Sarvam STT/TTS (client-side) with full business logic backend
"""

import os
import requests as http_requests
from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
from loguru import logger
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")

if not ANTHROPIC_API_KEY:
    logger.warning("ANTHROPIC_API_KEY not set - API features will not work until it is configured")
if not SARVAM_API_KEY:
    logger.warning("SARVAM_API_KEY not set - Speech features will not work until it is configured")

# Initialize Flask app
app = Flask(__name__, static_folder='static')
CORS(app)

@app.after_request
def add_cache_control(response):
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

# Global state (will be initialized after imports)
from core.state import StoreState
state = StoreState()
state.load_from_db()


@app.route('/')
def index():
    """Serve the frontend"""
    return send_from_directory('static', 'index.html')


@app.route('/<path:path>')
def static_files(path):
    """Serve static files"""
    return send_from_directory('static', path)


@app.route('/quick-ack', methods=['POST'])
def quick_ack():
    """Fast acknowledgment endpoint (keyword-based, no LLM)"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        language = data.get('language', 'hi-IN')  # Accept language parameter

        if not text:
            return jsonify({'error': 'No text provided'}), 400

        logger.info(f"Quick-ack: '{text}' (lang: {language})")

        from core.quick_ack import detect_quick_intent, get_ack_response

        quick_intent = detect_quick_intent(text)
        ack_text = get_ack_response(
            quick_intent,
            state.shopkeeper_name,
            state.shopkeeper_honorific
        )

        return jsonify({
            'ack_text': ack_text,
            'quick_intent': quick_intent
        })

    except Exception as e:
        logger.error(f"Error in quick-ack: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/process', methods=['POST'])
def process():
    """Main processing endpoint: router → agents → response generation"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        language = data.get('language', 'hi-IN')

        if not text:
            return jsonify({'error': 'No text provided'}), 400

        logger.info(f"Processing: '{text}' (lang: {language})")

        # Import agents and router
        from core.router import route_intent
        from core.llm import call_claude
        from agents.inventory import InventoryAgent
        from agents.sales import SalesAgent
        from agents.expense import ExpenseAgent
        from agents.summary import SummaryAgent
        from agents.alert import AlertAgent
        from prompts.response_prompt import get_response_system_prompt, build_response_user_prompt

        # 1. Route intents
        router_output = route_intent(text, ANTHROPIC_API_KEY)
        logger.info(f"Router output: {len(router_output.intents)} intent(s)")

        # 2. Execute agents
        inventory_agent = InventoryAgent(state)
        sales_agent = SalesAgent(state)
        expense_agent = ExpenseAgent(state)
        summary_agent = SummaryAgent(state)
        alert_agent = AlertAgent(state)

        agent_results = []
        for intent in router_output.intents:
            try:
                if intent.intent.value in ["inventory_in", "inventory_out", "query_stock", "correction"]:
                    result = inventory_agent.handle(intent)
                    agent_results.append(result)

                elif intent.intent.value == "expense":
                    result = expense_agent.handle(intent)
                    agent_results.append(result)

                elif intent.intent.value == "sale":
                    result = sales_agent.handle(intent)
                    agent_results.append(result)

                elif intent.intent.value in ["query_summary", "query_profit", "close_day"]:
                    result = summary_agent.handle(intent)
                    agent_results.append(result)

                elif intent.intent.value == "greeting":
                    agent_results.append({"action": "greeting"})

                else:
                    agent_results.append({"action": "unknown", "intent": intent.intent.value})

            except Exception as e:
                logger.error(f"Agent error for {intent.intent}: {e}")
                agent_results.append({"action": "error", "error": str(e)})

        # 3. Check for alerts
        alerts = alert_agent.check_alerts()

        # 4. Generate response
        system_prompt = get_response_system_prompt(
            state.shopkeeper_name,
            state.shopkeeper_honorific
        )
        user_prompt = build_response_user_prompt(text, agent_results, [alerts])

        response_text = call_claude(
            system_prompt=system_prompt,
            user_text=user_prompt,
            api_key=ANTHROPIC_API_KEY,
            max_tokens=300,
            temperature=0.2
        )

        logger.info(f"Generated response: {response_text}")

        # 5. Save state
        state.save_to_db()

        # 6. Return results
        return jsonify({
            'response_text': response_text,
            'intents': [{"intent": i.intent.value, "confidence": i.confidence} for i in router_output.intents],
            'alerts': alerts
        })

    except Exception as e:
        logger.error(f"Error in process: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/state', methods=['GET'])
def get_state():
    """Get current store state (for debugging)"""
    return jsonify({
        'inventory': {k: {
            'quantity': v.quantity,
            'unit': v.unit,
            'avg_cost_per_unit': v.avg_cost_per_unit,
            'last_updated': v.last_updated.isoformat()
        } for k, v in state.inventory.items()},
        'sales': [{
            'item_name': s.item_name,
            'quantity': s.quantity,
            'unit': s.unit,
            'price_per_unit': s.price_per_unit,
            'total': s.total,
            'timestamp': s.timestamp.isoformat()
        } for s in state.sales],
        'expenses': [{
            'category': e.category,
            'amount': e.amount,
            'description': e.description,
            'timestamp': e.timestamp.isoformat()
        } for e in state.expenses]
    })


@app.route('/api/stt', methods=['POST'])
def stt_proxy():
    if not SARVAM_API_KEY:
        return jsonify({'error': 'SARVAM_API_KEY not configured'}), 500
    try:
        file = request.files.get('file')
        if not file:
            return jsonify({'error': 'No audio file provided'}), 400

        files = {'file': (file.filename, file.stream, file.content_type)}
        data = {
            'model': request.form.get('model', 'saaras:v3'),
            'mode': request.form.get('mode', 'transcribe'),
            'language_code': request.form.get('language_code', 'unknown'),
        }

        resp = http_requests.post(
            'https://api.sarvam.ai/speech-to-text',
            headers={'api-subscription-key': SARVAM_API_KEY},
            files=files,
            data=data,
            timeout=30
        )
        return Response(resp.content, status=resp.status_code, content_type=resp.headers.get('Content-Type', 'application/json'))
    except Exception as e:
        logger.error(f"STT proxy error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/tts', methods=['POST'])
def tts_proxy():
    if not SARVAM_API_KEY:
        return jsonify({'error': 'SARVAM_API_KEY not configured'}), 500
    try:
        payload = request.get_json()
        resp = http_requests.post(
            'https://api.sarvam.ai/text-to-speech',
            headers={
                'api-subscription-key': SARVAM_API_KEY,
                'Content-Type': 'application/json'
            },
            json=payload,
            timeout=30
        )
        return Response(resp.content, status=resp.status_code, content_type=resp.headers.get('Content-Type', 'application/json'))
    except Exception as e:
        logger.error(f"TTS proxy error: {e}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    logger.info("Starting Dukaan Buddy Server...")
    logger.info(f"Inventory: {len(state.inventory)} items")
    logger.info(f"Today's sales: {len(state.sales)}")
    logger.info(f"Today's expenses: {len(state.expenses)}")

    app.run(host='0.0.0.0', port=5000, debug=False)
