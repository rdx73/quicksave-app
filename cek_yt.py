from engines.youtube import get_yt_info

url = "https://youtube.com/shorts/LQkV4z9ASn4"
print("Sedang mengetes YouTube...")
hasil = get_yt_info(url)

if hasil['success']:
    print("✅ BERHASIL!")
    print(f"Judul: {hasil['title']}")
    print(f"URL Download: {hasil['download_url'][:50]}...")
else:
    print("❌ GAGAL!")
    print(f"Error: {hasil['error']}")
