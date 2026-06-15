import json
import sys

with open("districts.txt", "w", encoding="utf-8") as out:
    def list_districts(prov_id):
        filename = f"province_{prov_id}.json"
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        out.write(f"--- Province {prov_id} ---\n")
        for feat in data.get('features', []):
            out.write(feat.get('properties', {}).get('NAME_2', 'Unknown') + "\n")

    list_districts(58) # Bà Rịa - Vũng Tàu
    list_districts(17) # Đà Nẵng
    list_districts(30) # Khánh Hòa
