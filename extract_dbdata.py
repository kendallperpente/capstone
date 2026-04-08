import json
import re

data = json.load(open('dog_breeds_rkc.json'))

def extract_field(content, field):
    pattern = rf'{field}\s+([^\n]+?)(?=\s+(?:Size of home|Grooming|Coat length|Sheds|Lifespan|Vulnerable|Town or country|Size of garden|Exercise|Size\b)|$)'
    match = re.search(pattern, content)
    return match.group(1).strip() if match else None

def extract_overview(content):
    # Text between the characteristics block and "Read the breed standard"
    match = re.search(r'Size of garden[^\n]+\n(.+?)(?=Read the breed standard|Images for this breed)', content, re.DOTALL)
    return match.group(1).strip() if match else None

def extract_temperament(content):
    match = re.search(r'Temperament\s+(.+?)(?=\n[A-Z])', content)
    return match.group(1).strip() if match else None

db_data = []
for item in data:
    content = item.get('content', '')
    db_data.append({
        "name":          item.get('title'),
        "size":          extract_field(content, 'Size(?! of)'),
        "exercise":      extract_field(content, 'Exercise'),
        "grooming":      extract_field(content, 'Grooming'),
        "shedding":      extract_field(content, 'Sheds'),
        "coat_length":   extract_field(content, 'Coat length'),
        "lifespan":      extract_field(content, 'Lifespan'),
        "breed_group":   extract_field(content, 'breed group'),
        "temperament":   extract_temperament(content),
        "overview":      extract_overview(content),
        "rkc_url":       item.get('url'),
        "standards_url": item.get('standards_url'),
        "has_overview":  1 if item.get('has_overview') else 0,
        "has_standards": 1 if item.get('has_standards') else 0,
    })

with open('DBdata.json', 'w', encoding='utf-8') as f:
    json.dump(db_data, f, indent=2, ensure_ascii=False)

print(f"Saved {len(db_data)} breeds to DBdata.json")
print("Sample:", json.dumps(db_data[0], indent=2))