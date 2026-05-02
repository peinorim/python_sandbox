# watcher.py — surveille l'apparition des marchés cibles
import requests, time, re

print("Surveillance... (Ctrl+C pour arrêter)")
while True:
    resp = requests.get(
        "https://gamma-api.polymarket.com/markets",
        params={"active": "true", "closed": "false", "limit": 100, "offset": 3000},
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=20,
    )
    found = [
        m.get("question","")[:70]
        for m in resp.json()
        if "temperature" in m.get("question","").lower()
        or re.search(r'(Bitcoin|ETH).*Up or Down', m.get("question",""), re.I)
    ]
    if found:
        print(f"✅ TROUVÉ : {len(found)} marchés cibles !")
        for q in found:
            print(f"  → {q}")
        break
    print(f"  Pas encore disponibles... ({time.strftime('%H:%M:%S')})")
    time.sleep(60)