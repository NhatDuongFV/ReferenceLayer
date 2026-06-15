import json

filename = "province_27.json"
with open(filename, 'r', encoding='utf-8') as f:
    data = json.load(f)

with open("haiphong_districts.txt", "w", encoding="utf-8") as out:
    for feat in data.get('features', []):
        out.write(feat.get('properties', {}).get('NAME_2', 'Unknown') + "\n")
