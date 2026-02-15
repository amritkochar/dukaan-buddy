"""
Central router: intent classification + structured data extraction.
Uses Claude via raw REST API.
"""

import json
from loguru import logger
from core.schemas import RouterOutput, SingleIntent, IntentType
from core.llm import call_claude
from prompts.router_prompt import ROUTER_SYSTEM_PROMPT


def route_intent(text: str, api_key: str) -> RouterOutput:
    """
    Classify intent and extract structured data from transcribed text.

    Args:
        text: Transcribed speech from STT
        api_key: Anthropic API key

    Returns:
        RouterOutput with list of SingleIntent objects
    """
    # Skip if text is too short
    if not text or len(text.strip()) < 3:
        logger.warning("Text too short, returning greeting intent")
        return RouterOutput(intents=[SingleIntent(intent=IntentType.GREETING, confidence=0.5)])

    try:
        # Call Claude for classification + extraction
        response_text = call_claude(
            system_prompt=ROUTER_SYSTEM_PROMPT,
            user_text=text,
            api_key=api_key,
            max_tokens=500,
            temperature=0.1
        )

        logger.debug(f"Router raw response: {response_text}")

        # Parse JSON response
        try:
            # Sometimes Claude wraps JSON in markdown code blocks
            if response_text.startswith("```"):
                # Extract JSON from code block
                lines = response_text.split("\n")
                json_lines = [l for l in lines if l and not l.startswith("```")]
                response_text = "\n".join(json_lines)

            parsed = json.loads(response_text)
            router_output = RouterOutput(**parsed)

            logger.info(f"✅ Router extracted {len(router_output.intents)} intent(s) from: '{text[:50]}...'")
            return router_output

        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse router JSON response: {e}")
            logger.error(f"Raw response: {response_text}")
            return RouterOutput(intents=[SingleIntent(intent=IntentType.UNKNOWN, confidence=0.0)])

    except Exception as e:
        logger.error(f"Router error: {e}")
        return RouterOutput(intents=[SingleIntent(intent=IntentType.UNKNOWN, confidence=0.0)])
