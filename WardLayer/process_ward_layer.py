import os
import json
import re
import sys
import unicodedata
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')

print("Starting WardLayer processing...")

# 1. Load source files
geojson_path = os.path.join("WardLayer", "gadm41_VNM_3.json")
excel_path = os.path.join("WardLayer", "ward.xlsx")
output_dir = "WardLayer"
output_excel_path = os.path.join("WardLayer", "ward_master_data.xlsx")

with open(geojson_path, "r", encoding="utf-8") as f:
    gadm_data = json.load(f)

excel_df = pd.read_excel(excel_path)

print(f"Loaded {len(gadm_data['features'])} features from GADM JSON.")
print(f"Loaded {len(excel_df)} rows from Excel.")

# 2. Text un-concatenation function
def split_concatenated_vn(text):
    if not isinstance(text, str):
        return text
    if text == 'NA' or not text:
        return text
    
    type_map = {
        'Thịtrấn': 'Thị trấn',
        'Trungtâmhuấnluyện': 'Trung tâm huấn luyện',
        'Phường': 'Phường',
        'Xã': 'Xã',
        'Đảo': 'Đảo'
    }
    if text in type_map:
        return type_map[text]
    
    # Handle hyphenated words
    text_clean = re.sub(r'([a-zàáảãạăắằẳẵặânấầnẩẫnậeéèẻẽẹêếềểễệiíìỉĩịoóòỏõọôốồổỗộơớờởỡợuúùủũụưứừửữựyýỳỷỹỵđ])-([A-ZÀÁẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬEÉÈẺẼẸÊẾỀỂỄỆIÍÌỈĨỊOÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢUÚÙỦŨỤƯỨỪỬỮỰYÝỲỶỸỴĐ])', r'\1 - \2', text)
    
    # Insert space before upper case chars
    pattern1 = r'([a-zàáảãạăắằẳẵặânấầnẩẫnậeéèẻẽẹêếềểễệiíìỉĩịoóòỏõọôốồổỗộơớờởỡợuúùủũụưứừửữựyýỳỷỹỵđ])([A-ZÀÁẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬEÉÈẺẼẸÊẾỀỂỄỆIÍÌỈĨỊOÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢUÚÙỦŨỤƯỨỪỬỮỰYÝỲỶỸỴĐ])'
    prev = ""
    res = text_clean
    while prev != res:
        prev = res
        res = re.sub(pattern1, r'\1 \2', res)
        
    # Insert space around digits
    res = re.sub(r'([a-zàáảãạăắằẳẵặânấầnẩẫnậeéèẻẽẹêếềểễệiíìỉĩịoóòỏõõọôốồổỗộơớờởỡợuúùủũụưứừửữựyýỳỷỹỵđA-ZÀÁẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬEÉÈẺẼẸÊẾỀỂỄỆIÍÌỈĨỊOÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢUÚÙỦŨỤƯỨỪỬỮỰYÝỲỶỸỴĐ])(\d+)', r'\1 \2', res)
    res = re.sub(r'(\d+)([a-zàáảãạăắằẳẵặânấầnẩẫnậeéèẻẽẹêếềểễệiíìỉĩịoóòỏõọôốồổỗộơớờởỡợuúùủũụưứừửữựyýỳỷỹỵđA-ZÀÁẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬEÉÈẺẼẸÊẾỀỂỄỆIÍÌỈĨỊOÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢUÚÙỦŨỤƯỨỪỬỮỰYÝỲỶỸỴĐ])', r'\1 \2', res)
    
    return res

# 3. String normalization for key matching
def remove_vn_accent(text):
    if not isinstance(text, str):
        return ""
    text = unicodedata.normalize('NFD', text)
    text = re.sub(r'[\u0300-\u036f]', '', text)
    text = text.replace('đ', 'd').replace('Đ', 'D')
    return text.lower()

def clean_key(text):
    if not isinstance(text, str):
        return ""
    text = re.sub(r'\(.*?\)', '', text)
    no_acc = remove_vn_accent(text)
    no_acc = re.sub(r'\bqui\b', 'quy', no_acc)
    no_acc = re.sub(r'\b0+(\d+)\b', r'\1', no_acc)
    cleaned = re.sub(r'[^a-z0-9]', '', no_acc)
    if cleaned in ['hue', 'thuathienhue']:
        return 'thuathienhue'
    return cleaned

# Build lookup structures from Excel
excel_provinces = excel_df[['province_id', 'province_name']].drop_duplicates()
excel_prov_map = {}
for _, row in excel_provinces.iterrows():
    k = clean_key(row['province_name'])
    excel_prov_map[k] = row['province_id']

excel_by_prov = {}
for _, row in excel_df.iterrows():
    pid = int(row['province_id'])
    if pid not in excel_by_prov:
        excel_by_prov[pid] = []
    
    w_clean = clean_key(row['ward_name'])
    d_clean = clean_key(row['district_name'])
    excel_by_prov[pid].append({
        'province_id': int(row['province_id']),
        'province_name': str(row['province_name']),
        'district_id': int(row['district_id']),
        'district_name': str(row['district_name']),
        'ward_id': int(row['ward_id']),
        'ward_name': str(row['ward_name']),
        'w_clean': w_clean,
        'd_clean': d_clean,
        'w_sub': re.sub(r'^(phuong|xa|thitran|dao|trungtamhuanluyen)', '', w_clean),
        'd_sub': re.sub(r'^(quan|huyen|thixa|thanhpho)', '', d_clean)
    })

# Group features by (province_id, district_id) for JSON output
# Also collect master data records
province_district_features = {}
master_data_records = []

matched_count = 0
unmatched_count = 0

for f in gadm_data['features']:
    props = f['properties']
    
    # Clean names in GADM properties
    g_p_name = split_concatenated_vn(props.get('NAME_1', ''))
    g_d_name = split_concatenated_vn(props.get('NAME_2', ''))
    g_w_name = split_concatenated_vn(props.get('NAME_3', ''))
    g_w_type = split_concatenated_vn(props.get('TYPE_3', ''))
    g_v_name = split_concatenated_vn(props.get('VARNAME_3', ''))
    
    # Update properties in place
    props['NAME_1'] = g_p_name
    props['NAME_2'] = g_d_name
    props['NAME_3'] = g_w_name
    props['TYPE_3'] = g_w_type
    if g_v_name and g_v_name != 'NA':
        props['VARNAME_3'] = g_v_name
        
    pk = clean_key(g_p_name)
    pid = excel_prov_map.get(pk)
    
    matched_row = None
    if pid and pid in excel_by_prov:
        g_w_clean = clean_key(g_w_name)
        g_full_w_clean = clean_key(f"{g_w_type} {g_w_name}")
        g_d_clean = clean_key(g_d_name)
        g_d_sub = re.sub(r'^(quan|huyen|thixa|thanhpho)', '', g_d_clean)
        
        prov_rows = excel_by_prov[pid]
        
        # Strategy 1: Match district AND ward
        for r in prov_rows:
            if (r['d_clean'] == g_d_clean or r['d_sub'] == g_d_sub or g_d_sub in r['d_clean']):
                if r['w_clean'] in [g_w_clean, g_full_w_clean] or r['w_sub'] == g_w_clean:
                    matched_row = r
                    break
                    
        # Strategy 2: Match ward within province
        if not matched_row:
            for r in prov_rows:
                if r['w_clean'] in [g_w_clean, g_full_w_clean] or r['w_sub'] == g_w_clean:
                    matched_row = r
                    break

    if matched_row:
        matched_count += 1
        sys_pid = matched_row['province_id']
        sys_pname = matched_row['province_name']
        sys_did = matched_row['district_id']
        sys_dname = matched_row['district_name']
        sys_wid = matched_row['ward_id']
        sys_wname = matched_row['ward_name']
    else:
        unmatched_count += 1
        sys_pid = pid if pid else None
        sys_pname = g_p_name
        sys_did = None
        sys_dname = g_d_name
        sys_wid = None
        sys_wname = None

    # Attach system codes to feature properties
    props['province_id'] = sys_pid
    props['province_name'] = sys_pname
    props['district_id'] = sys_did
    props['district_name'] = sys_dname
    props['ward_id'] = sys_wid
    props['ward_name'] = sys_wname
    
    # Store for district JSON grouping
    # Target folder: WardLayer/{sys_pid}
    # Target file: {sys_did or GID_2}.json
    folder_key = str(sys_pid) if sys_pid else "unassigned"
    file_key = str(sys_did) if sys_did else str(props.get('GID_2', 'unknown'))
    
    group_key = (folder_key, file_key)
    if group_key not in province_district_features:
        province_district_features[group_key] = []
    province_district_features[group_key].append(f)

    # Store master data row
    master_data_records.append({
        'GID_3': props.get('GID_3'),
        'GID_2': props.get('GID_2'),
        'GID_1': props.get('GID_1'),
        'gadm_province_name': g_p_name,
        'gadm_district_name': g_d_name,
        'gadm_ward_name': g_w_name,
        'gadm_ward_type': g_w_type,
        'province_id': sys_pid,
        'province_name': sys_pname,
        'district_id': sys_did,
        'district_name': sys_dname,
        'ward_id': sys_wid,
        'ward_name': sys_wname
    })

print(f"Matching complete: {matched_count} matched, {unmatched_count} unmatched.")

# 4. Write district GeoJSON files into WardLayer/{province_id}/{district_id}.json
files_created = 0
folders_created = set()

for (folder_key, file_key), features in province_district_features.items():
    prov_dir = os.path.join(output_dir, folder_key)
    os.makedirs(prov_dir, exist_ok=True)
    folders_created.add(prov_dir)
    
    json_path = os.path.join(prov_dir, f"{file_key}.json")
    feature_collection = {
        "type": "FeatureCollection",
        "name": f"District_{file_key}",
        "features": features
    }
    with open(json_path, "w", encoding="utf-8") as out_f:
        json.dump(feature_collection, out_f, ensure_ascii=False, indent=2)
    files_created += 1

print(f"Created {len(folders_created)} province folders and {files_created} district JSON files.")

# 5. Export Master Data Excel
master_df = pd.DataFrame(master_data_records)
master_df.to_excel(output_excel_path, index=False)
print(f"Exported master data Excel to: {output_excel_path}")
print("Process completed successfully!")
