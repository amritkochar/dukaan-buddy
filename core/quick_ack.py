"""
Instant acknowledgment system. No LLM.
Snappy, smart one-liners from Chhotu.
Runs in <1ms. Gives the user immediate feedback while agents process in background.
"""

import random

ACKS_HI = [
    "हाँ भैया, रुको...",
    "बस एक सेकंड...",
    "अच्छा, देखता हूँ...",
    "ओके भैया, लिख रहा हूँ...",
    "हाँ हाँ, सुन लिया...",
    "रुको, छोटू देखता है...",
    "बस भैया, हो जाएगा...",
    "चलो, देख लेते हैं...",
    "ठीक है, नोट कर लिया...",
    "जी भैया, एक मिनट...",
    "सुन लिया, बस करता हूँ...",
    "हम्म, समझ गया...",
    "अच्छा अच्छा, रुको...",
    "हाँ बोलो, छोटू सुन रहा है...",
    "ओहो, ठीक है...",
]

ACKS_EN = [
    "Yeah, one sec...",
    "Okay, let me check...",
    "Got it, writing it down...",
    "Hmm, noted...",
    "Alright, on it...",
    "Sure thing, just a moment...",
    "Okay boss, checking...",
    "Right, let me see...",
    "Yep, give me a second...",
    "Done, processing...",
    "Alright alright, hold on...",
    "Yes boss, one moment...",
    "Hmm okay, let me look...",
    "Sure, Chhotu's on it...",
    "Got it boss, one sec...",
]


def get_ack_response(quick_intent: str = None, shopkeeper_name: str = "", honorific: str = "", language: str = "hi-IN") -> str:
    is_english = language.startswith("en")

    if is_english:
        response = random.choice(ACKS_EN)
        placeholder = "boss"
    else:
        response = random.choice(ACKS_HI)
        placeholder = "भैया"

    if shopkeeper_name and shopkeeper_name != "भैया" and honorific:
        name_str = f"{shopkeeper_name} {honorific}"
        response = response.replace(placeholder, name_str)
    elif shopkeeper_name and shopkeeper_name != "भैया":
        response = response.replace(placeholder, shopkeeper_name)

    return response


def detect_quick_intent(text: str) -> str:
    return "general"
