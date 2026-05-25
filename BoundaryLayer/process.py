import json
import os

with open('system.json', 'r', encoding='utf-8') as f:
    system_data = json.load(f)

prov_map = {item['province_name']: item['province_id'] for item in system_data}

with open('full.json', 'r', encoding='utf-8') as f:
    full_data = json.load(f)

# Group features by province
prov_features = {}

for feature in full_data.get('features', []):
    prop = feature.get('properties', {})
    name_1 = prop.get('NAME_1', '')
    
    # Try exact match
    prov_id = prov_map.get(name_1)
    
    if not prov_id:
        # Try finding a close match
        for s_name, s_id in prov_map.items():
            if s_name.lower() in name_1.lower() or name_1.lower() in s_name.lower():
                prov_id = s_id
                break
                
    if prov_id:
        if prov_id not in prov_features:
            prov_features[prov_id] = []
        prov_features[prov_id].append(feature)
    else:
        print(f"Warning: Could not match province '{name_1}'")

# Write out the files
for prov_id, features in prov_features.items():
    out_data = {
        "type": full_data.get("type", "FeatureCollection"),
        "name": full_data.get("name", "gadm41_VNM_2"),
        "crs": full_data.get("crs", {}),
        "features": features
    }
    out_name = f"province_{prov_id}.json"
    with open(out_name, 'w', encoding='utf-8') as f:
        json.dump(out_data, f, ensure_ascii=False)
    print(f"Created {out_name} with {len(features)} features.")
print("Done!")
