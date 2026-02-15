"""
Item and category normalization with Hindi→English translation.
Ensures consistent storage keys regardless of how items are spoken.
"""

import re
from difflib import SequenceMatcher


# ══════════════════════════════════════════════════════════════
# ITEM MAPPINGS: Hindi/Hinglish → English (lowercase, singular)
# ══════════════════════════════════════════════════════════════

ITEM_MAPPINGS = {
    # Vegetables
    "आलू": "potato",
    "aloo": "potato",
    "aaloo": "potato",
    "alu": "potato",
    "प्याज": "onion",
    "pyaaz": "onion",
    "pyaz": "onion",
    "पियाज": "onion",
    "टमाटर": "tomato",
    "tamatar": "tomato",
    "tamater": "tomato",
    "टोमेटो": "tomato",
    "भिंडी": "okra",
    "bhindi": "okra",
    "बैंगन": "eggplant",
    "baingan": "eggplant",
    "गोभी": "cauliflower",
    "gobhi": "cauliflower",
    "पत्तागोभी": "cabbage",
    "pattagobhi": "cabbage",
    "पालक": "spinach",
    "palak": "spinach",
    "गाजर": "carrot",
    "gajar": "carrot",
    "मूली": "radish",
    "mooli": "radish",

    # Grains & Pulses
    "चावल": "rice",
    "chawal": "rice",
    "चाबल": "rice",
    "आटा": "wheat_flour",
    "atta": "wheat_flour",
    "आटे": "wheat_flour",
    "मैदा": "refined_flour",
    "maida": "refined_flour",
    "दाल": "lentil",
    "dal": "lentil",
    "दाल": "lentil",
    "बेसन": "gram_flour",
    "besan": "gram_flour",

    # Groceries
    "चीनी": "sugar",
    "cheeni": "sugar",
    "chini": "sugar",
    "शक्कर": "sugar",
    "shakkar": "sugar",
    "नमक": "salt",
    "namak": "salt",
    "तेल": "oil",
    "tel": "oil",
    "घी": "ghee",
    "ghee": "ghee",
    "दूध": "milk",
    "doodh": "milk",
    "dudh": "milk",
    "दही": "yogurt",
    "dahi": "yogurt",
    "मक्खन": "butter",
    "makkhan": "butter",

    # Spices
    "मसाला": "spice",
    "masala": "spice",
    "मिर्च": "chili",
    "mirch": "chili",
    "हल्दी": "turmeric",
    "haldi": "turmeric",
    "धनिया": "coriander",
    "dhaniya": "coriander",
    "जीरा": "cumin",
    "jeera": "cumin",

    # Common typos/variations
    "potatoes": "potato",
    "potatos": "potato",
    "potahto": "potato",
    "onions": "onion",
    "tomatoes": "tomato",
    "tomatos": "tomato",
}


# ══════════════════════════════════════════════════════════════
# CATEGORY MAPPINGS: Expense categories → English
# ══════════════════════════════════════════════════════════════

CATEGORY_MAPPINGS = {
    # Electricity
    "bijli": "electricity",
    "बिजली": "electricity",
    "बिज्ली": "electricity",
    "electric": "electricity",
    "electricity": "electricity",
    "light bill": "electricity",

    # Rent
    "kiraya": "rent",
    "किराया": "rent",
    "किराय": "rent",
    "rent": "rent",

    # Transport
    "transport": "transport",
    "ट्रांसपोर्ट": "transport",
    "गाड़ी": "transport",
    "gaadi": "transport",
    "petrol": "transport",
    "diesel": "transport",

    # Labor
    "mazdoori": "labor",
    "मजदूरी": "labor",
    "labor": "labor",
    "labour": "labor",
    "worker": "labor",

    # Phone/Recharge
    "phone": "phone",
    "फोन": "phone",
    "recharge": "phone",
    "रिचार्ज": "phone",
    "mobile": "phone",

    # Water
    "paani": "water",
    "पानी": "water",
    "water": "water",

    # Cleaning
    "safai": "cleaning",
    "सफाई": "cleaning",
    "cleaning": "cleaning",

    # Other
    "other": "other",
    "अन्य": "other",
    "misc": "other",
}


# ══════════════════════════════════════════════════════════════
# NORMALIZATION FUNCTIONS
# ══════════════════════════════════════════════════════════════

def normalize_item(item_name: str) -> str:
    """
    Normalize item name to canonical English form.

    Steps:
    1. Lowercase and strip
    2. Check direct mapping
    3. Remove plural suffixes
    4. Fuzzy match against known items

    Args:
        item_name: Raw item name (can be Hindi, Hinglish, English)

    Returns:
        Normalized English item name (lowercase, singular)
    """
    if not item_name:
        return ""

    # Step 1: Basic cleanup
    normalized = item_name.lower().strip()

    # Step 2: Check direct mapping
    if normalized in ITEM_MAPPINGS:
        return ITEM_MAPPINGS[normalized]

    # Step 3: Try singularization
    singular = singularize(normalized)
    if singular in ITEM_MAPPINGS:
        return ITEM_MAPPINGS[singular]

    # Step 4: Fuzzy match (for typos like "potahto")
    fuzzy_match = fuzzy_match_item(normalized)
    if fuzzy_match:
        return fuzzy_match

    # Step 5: Return cleaned version if no match
    return singular


def normalize_category(category: str) -> str:
    """
    Normalize expense category to standard English form.

    Args:
        category: Raw category name

    Returns:
        Normalized English category
    """
    if not category:
        return "other"

    normalized = category.lower().strip()

    # Check mapping
    if normalized in CATEGORY_MAPPINGS:
        return CATEGORY_MAPPINGS[normalized]

    # Default to other
    return "other"


def singularize(word: str) -> str:
    """
    Simple singularization (remove common plural suffixes).

    Args:
        word: Plural word

    Returns:
        Singular form
    """
    # Remove common plural endings
    if word.endswith("ies") and len(word) > 4:
        return word[:-3] + "y"
    elif word.endswith("es") and len(word) > 3:
        # Check if it's -oes, -ses, -ches, -xes, -zes
        if word[-3] in "oszx" or word[-3:-1] in ["sh", "ch"]:
            return word[:-2]
        return word[:-1]
    elif word.endswith("s") and len(word) > 2:
        return word[:-1]

    return word


def fuzzy_match_item(item: str, threshold: float = 0.8) -> str:
    """
    Fuzzy match against known items to handle typos.

    Args:
        item: Item name to match
        threshold: Similarity threshold (0-1)

    Returns:
        Best matching canonical item, or empty string if no match
    """
    # Get all canonical item names (values from mapping)
    canonical_items = set(ITEM_MAPPINGS.values())

    best_match = None
    best_score = 0

    for canonical in canonical_items:
        score = SequenceMatcher(None, item, canonical).ratio()
        if score > best_score:
            best_score = score
            best_match = canonical

    if best_score >= threshold:
        return best_match

    return ""


def get_all_known_items() -> list[str]:
    """Get list of all known canonical item names."""
    return sorted(set(ITEM_MAPPINGS.values()))


def get_all_known_categories() -> list[str]:
    """Get list of all known canonical categories."""
    return sorted(set(CATEGORY_MAPPINGS.values()))
