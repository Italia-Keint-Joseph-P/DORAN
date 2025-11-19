import json

try:
    with open('database/locations/locations.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    print("JSON is valid")
except json.JSONDecodeError as e:
    print(f"JSON error: {e}")
    print(f"Line: {e.lineno}, Column: {e.colno}")
    print(f"Position: {e.pos}")
