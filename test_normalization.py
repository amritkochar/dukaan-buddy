#!/usr/bin/env python3
"""Test normalization with various inputs."""

from core.normalizer import normalize_item, normalize_category

print("=" * 60)
print("TESTING ITEM NORMALIZATION")
print("=" * 60)

test_items = [
    # Hindi
    ("आलू", "potato"),
    ("चीनी", "sugar"),
    ("प्याज", "onion"),

    # Hinglish
    ("aloo", "potato"),
    ("cheeni", "sugar"),
    ("pyaaz", "onion"),

    # English variations
    ("Potato", "potato"),
    ("POTATO", "potato"),
    ("potatoes", "potato"),
    ("Potatoes", "potato"),

    # Typos
    ("potahto", "potato"),
    ("potatos", "potato"),

    # More items
    ("टमाटर", "tomato"),
    ("tamatar", "tomato"),
    ("Tomatoes", "tomato"),
]

for input_item, expected in test_items:
    result = normalize_item(input_item)
    status = "✅" if result == expected else "❌"
    print(f"{status} '{input_item}' → '{result}' (expected: '{expected}')")

print("\n" + "=" * 60)
print("TESTING CATEGORY NORMALIZATION")
print("=" * 60)

test_categories = [
    # Hindi
    ("बिजली", "electricity"),
    ("किराया", "rent"),

    # Hinglish
    ("bijli", "electricity"),
    ("kiraya", "rent"),
    ("mazdoori", "labor"),

    # English
    ("Electricity", "electricity"),
    ("RENT", "rent"),
    ("phone", "phone"),
]

for input_cat, expected in test_categories:
    result = normalize_category(input_cat)
    status = "✅" if result == expected else "❌"
    print(f"{status} '{input_cat}' → '{result}' (expected: '{expected}')")

print("\n" + "=" * 60)
print("NORMALIZATION TEST COMPLETE")
print("=" * 60)
