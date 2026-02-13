import os
import json

# TOKEN LOGIN (Ganti sesuai keinginan kamu)
ADMIN_TOKEN = "QUICKSAVE-2026-SAKTI"

def get_config():
    if not os.path.exists('config.json'):
        # Default config jika file belum ada
        return {"meta_tags": "", "scripts": ""}
    with open('config.json', 'r') as f:
        return json.load(f)

def save_settings(data):
    # Simpan meta tags dan script plugins
    with open('config.json', 'w') as f:
        json.dump(data, f, indent=4)
    return True

def update_cookies(content):
    # Update file cookies.txt agar Deno tetap sakti
    try:
        with open('cookies.txt', 'w') as f:
            f.write(content)
        return True
    except:
        return False
