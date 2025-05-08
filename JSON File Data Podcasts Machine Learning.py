
import json

# Datei laden
with open("/Users/jann/Desktop/structured_user_profiles.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Alle 180 Nutzer drucken, sauber formatiert
for i, user in enumerate(data):
    print(f"User #{i}:")
    print(json.dumps(user, indent=2, ensure_ascii=False))
    print("=" * 60)  
