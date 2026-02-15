# Test Commands for Normalization

## 1. Restart the server (in a separate terminal)
```bash
python3 server.py
```

## 2. Test Hindi item names (should store as "potato")
```bash
curl -X POST http://localhost:5000/process \
  -H 'Content-Type: application/json' \
  -d '{"text":"50 kilo aloo aaya 30 rupaye kilo", "language":"hi-IN"}'
```

## 3. Test English with different case (should also be "potato")
```bash
curl -X POST http://localhost:5000/process \
  -H 'Content-Type: application/json' \
  -d '{"text":"30 kg Potato becha 40 rupaye", "language":"hi-IN"}'
```

## 4. Test plurals (should be "potato")
```bash
curl -X POST http://localhost:5000/process \
  -H 'Content-Type: application/json' \
  -d '{"text":"10 POTATOES sold", "language":"hi-IN"}'
```

## 5. Test typo (should fuzzy match to "potato")
```bash
curl -X POST http://localhost:5000/process \
  -H 'Content-Type: application/json' \
  -d '{"text":"5 kg potahto", "language":"hi-IN"}'
```

## 6. Test different item (sugar)
```bash
curl -X POST http://localhost:5000/process \
  -H 'Content-Type: application/json' \
  -d '{"text":"100 kilo cheeni aaya 50 rupaye kilo", "language":"hi-IN"}'
```

## 7. Check state - ALL items should be in clean English
```bash
curl http://localhost:5000/state | python3 -m json.tool
```

Expected output:
```json
{
  "inventory": {
    "potato": {
      "quantity": 65.0,  // 50 + 30 - 10 - 5 (if all tests above ran)
      "unit": "kg",
      "avg_cost_per_unit": 30.0
    },
    "sugar": {
      "quantity": 100.0,
      "unit": "kg",
      "avg_cost_per_unit": 50.0
    }
  }
}
```

## 8. Test expense categories
```bash
curl -X POST http://localhost:5000/process \
  -H 'Content-Type: application/json' \
  -d '{"text":"200 ka bijli bill bhara", "language":"hi-IN"}'
```

```bash
curl -X POST http://localhost:5000/process \
  -H 'Content-Type: application/json' \
  -d '{"text":"500 RENT paid", "language":"hi-IN"}'
```

## 9. Check expenses - should be in English
```bash
curl http://localhost:5000/state | python3 -m json.tool | grep -A5 expenses
```

Expected:
```json
"expenses": [
  {
    "category": "electricity",
    "amount": 200.0
  },
  {
    "category": "rent",
    "amount": 500.0
  }
]
```

## Success Criteria

✅ All item names stored in lowercase English (potato, sugar, onion, etc.)
✅ No Hindi characters in inventory keys
✅ "potato", "Potato", "POTATO", "potatoes", "aloo", "आलू" all map to same item
✅ Typos like "potahto" fuzzy match to "potato"
✅ Expense categories in English (electricity, rent, labor, etc.)
✅ Responses still in Hindi (user-facing)
✅ Database has clean, queryable data
