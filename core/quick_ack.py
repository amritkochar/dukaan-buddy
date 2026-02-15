"""
Instant acknowledgment system. No LLM.
Simple round-robin natural responses - like a real kirana helper (छोटू).
Runs in <1ms. Gives the user immediate feedback while agents process in background.
"""

import random

GENERAL_ACKS_HI = [
    "अरे भैया आ गए! बोलो बोलो, छोटू सब लिख रहा है...",
    "आइए आइए भैया! छोटू हाज़िर है, बोलिए क्या लिखूँ?",
    "ओहो भैया! आज भी छोटू से पहले कोई नहीं आया दुकान!",
    "हाँ हाँ, रुको ज़रा — पेन ढूंढ रहा हूँ...",
    "छोटू की नज़र से कुछ नहीं बचता, बोलो!",
    "अरे भैया, इतना बोलोगे तो पेन की स्याही ख़तम हो जाएगी!",
    "हाँ भैया, छोटू सो नहीं रहा था... बस आँखें बंद थीं!",
    "बोलो बोलो, छोटू के कान खुले हैं!",
    "बस भैया, एक सेकंड में हिसाब लगा देता हूँ!",
    "ओहो, सुबह-सुबह माल आ गया? लिख लेता हूँ...",
    "रुको भैया, छोटू का दिमाग़ कैलकुलेटर से तेज़ चलता है!",
    "लिख लिया भैया, छोटू की कॉपी में सब दर्ज है!",
    "हाँ भैया, बोलते जाओ — छोटू लिखता जा रहा है!",
    "ठीक है भैया, ज़रा हिसाब लगाने दो...",
    "एक सेकंड भैया, छोटू गिन रहा है...",
    "रुको रुको, ये तो छोटू का favourite काम है — हिसाब!",
    "अच्छा अच्छा, समझ गया — लिख रहा हूँ...",
    "भैया, छोटू पर भरोसा रखो — सब सही लिखेगा!",
    "फ़िक्र मत करो भैया, छोटू सँभाल लेगा!",
    "छोटू है ना, सब याद रहता है इसको!",
    "हाँ भैया, बताओ — छोटू ready है!",
    "चलो भैया, जल्दी बोलो — छोटू को और भी काम है!",
    "अरे वाह भैया, आज तो बढ़िया धंधा हो रहा है!",
]

GENERAL_ACKS_EN = [
    "Yes boss, Chhotu is here! Tell me, what should I note down?",
    "Coming coming! Chhotu is ready with the register...",
    "Alright boss, just a second — let me grab my pen...",
    "Nothing escapes Chhotu's eyes, go ahead and tell me!",
    "Boss, if you talk this fast, my pen will run out of ink!",
    "No no, Chhotu wasn't sleeping... just resting my eyes!",
    "Go ahead, Chhotu's ears are wide open!",
    "One second boss, let me calculate this quickly!",
    "Oh nice, fresh stock arrived? Let me write it down...",
    "Hold on boss, Chhotu's brain works faster than a calculator!",
    "Got it boss, everything is recorded in Chhotu's register!",
    "Keep going boss — Chhotu is writing it all down!",
    "Alright boss, give me a moment to do the math...",
    "One second boss, Chhotu is counting...",
    "Wait wait, this is Chhotu's favourite job — accounting!",
    "Okay okay, understood — writing it down...",
    "Trust Chhotu boss — everything will be recorded correctly!",
    "Don't worry boss, Chhotu will handle it!",
    "Chhotu remembers everything, you know that!",
    "Yes boss, tell me — Chhotu is ready!",
    "Come on boss, tell me quickly — Chhotu has more work to do!",
    "Oh wow boss, business is booming today!",
]


def get_ack_response(quick_intent: str = None, shopkeeper_name: str = "", honorific: str = "", language: str = "hi-IN") -> str:
    is_english = language.startswith("en")

    if is_english:
        response = random.choice(GENERAL_ACKS_EN)
        placeholder = "boss"
    else:
        response = random.choice(GENERAL_ACKS_HI)
        placeholder = "भैया"

    if shopkeeper_name and honorific:
        name_str = f"{shopkeeper_name} {honorific}"
        response = response.replace(placeholder, name_str)
    elif shopkeeper_name:
        response = response.replace(placeholder, shopkeeper_name)

    return response


def detect_quick_intent(text: str) -> str:
    return "general"
