import json

islands_to_remove = ["Bạch Long Vĩ", "Cát Hải"]

def remove_islands_from_file(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        original_count = len(data.get('features', []))
        data['features'] = [
            feat for feat in data.get('features', [])
            if feat.get('properties', {}).get('NAME_2') not in islands_to_remove
        ]
        new_count = len(data.get('features', []))
        
        if original_count != new_count:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False)
            print(f"Updated {filename}: removed {original_count - new_count} features.")
        else:
            print(f"No islands found in {filename}.")
    except Exception as e:
        print(f"Error processing {filename}: {e}")

# Process full.json
remove_islands_from_file("full.json")

# Process Hai Phong file
remove_islands_from_file("province_27.json")

print("Island removal for Hai Phong completed.")
