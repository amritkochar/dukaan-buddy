"""
LLM helper using raw Anthropic REST API (no SDK).
"""

import requests
from loguru import logger


def call_claude(
    system_prompt: str,
    user_text: str,
    api_key: str,
    max_tokens: int = 500,
    temperature: float = 0.1
) -> str:
    """
    Call Claude API using raw REST requests.

    Args:
        system_prompt: System instructions
        user_text: User message
        api_key: Anthropic API key
        max_tokens: Max tokens in response
        temperature: Sampling temperature

    Returns:
        Response text from Claude
    """
    try:
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": max_tokens,
                "temperature": temperature,
                "system": system_prompt,
                "messages": [{"role": "user", "content": user_text}],
            },
            timeout=30
        )
        response.raise_for_status()

        result = response.json()
        return result["content"][0]["text"]

    except requests.exceptions.RequestException as e:
        logger.error(f"Claude API error: {e}")
        raise
