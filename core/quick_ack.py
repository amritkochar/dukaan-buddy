"""
Instant acknowledgment system. No LLM.
Simple round-robin natural responses - like a real kirana helper (छोटू).
Runs in <1ms. Gives the user immediate feedback while agents process in background.
"""

import random


# ══════════════════════════════════════════════════════════════
# NATURAL ACKNOWLEDGMENTS - Just like a real helper would say
# ══════════════════════════════════════════════════════════════

# General-purpose acks - natural, human, conversational
# These work for ANY request (stock, sale, expense, query, etc.)
GENERAL_ACKS = [
    # Energetic greetings
    "अरे भैया आ गए! बोलो बोलो, छोटू सब लिख रहा है...",
    "आइए आइए भैया! छोटू हाज़िर है, बोलिए क्या लिखूँ?",
    "ओहो भैया! आज भी छोटू से पहले कोई नहीं आया दुकान!",

    # Snarky/funny
    "हाँ हाँ, रुको ज़रा — पेन ढूंढ रहा हूँ...",
    "छोटू की नज़र से कुछ नहीं बचता, बोलो!",
    "अरे भैया, इतना बोलोगे तो पेन की स्याही ख़तम हो जाएगी!",
    "हाँ भैया, छोटू सो नहीं रहा था... बस आँखें बंद थीं!",
    "बोलो बोलो, छोटू के कान खुले हैं!",

    # Diligent/reliable
    "बस भैया, एक सेकंड में हिसाब लगा देता हूँ!",
    "ओहो, सुबह-सुबह माल आ गया? लिख लेता हूँ...",
    "रुको भैया, छोटू का दिमाग़ कैलकुलेटर से तेज़ चलता है!",
    "लिख लिया भैया, छोटू की कॉपी में सब दर्ज है!",
    "हाँ भैया, बोलते जाओ — छोटू लिखता जा रहा है!",

    # Processing
    "ठीक है भैया, ज़रा हिसाब लगाने दो...",
    "एक सेकंड भैया, छोटू गिन रहा है...",
    "रुको रुको, ये तो छोटू का favourite काम है — हिसाब!",
    "अच्छा अच्छा, समझ गया — लिख रहा हूँ...",

    # Confident
    "भैया, छोटू पर भरोसा रखो — सब सही लिखेगा!",
    "फ़िक्र मत करो भैया, छोटू सँभाल लेगा!",
    "छोटू है ना, सब याद रहता है इसको!",
    "हाँ भैया, बताओ — छोटू ready है!",
    "चलो भैया, जल्दी बोलो — छोटू को और भी काम है!",
    "अरे वाह भैया, आज तो बढ़िया धंधा हो रहा है!",
]


def get_ack_response(quick_intent: str = None, shopkeeper_name: str = "", honorific: str = "") -> str:
    """
    Get a random natural acknowledgment.

    Simple round-robin from general pool - no intent detection needed.
    Just like a real kirana helper would respond naturally to anything.

    Args:
        quick_intent: Ignored (kept for backward compatibility)
        shopkeeper_name: Optional shopkeeper name for personalization
        honorific: Optional honorific (ji, bhai, etc.)

    Returns:
        Random natural Hindi acknowledgment
    """
    # Pick random response
    response = random.choice(GENERAL_ACKS)

    # Personalize: replace "भैया" with actual name+honorific if available
    if shopkeeper_name and honorific:
        name_str = f"{shopkeeper_name} {honorific}"
        response = response.replace("भैया", name_str)
    elif shopkeeper_name:
        response = response.replace("भैया", shopkeeper_name)

    return response


# Backward compatibility - keep old function signature
def detect_quick_intent(text: str) -> str:
    """
    Legacy function - no longer needed but kept for backward compatibility.
    Always returns 'general' since we don't do intent detection anymore.
    """
    return "general"
