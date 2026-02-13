from flask import Flask, render_template, request, jsonify, Response
import requests
import re
import os
import panel # Import modul panel/config

# Import mesin-mesin downloader
from engines.youtube import get_yt_info
from engines.tiktok import get_tt_info
from engines.general import get_general_info

app = Flask(__name__)

# Fungsi untuk membersihkan nama file dari karakter aneh
def slugify(text):
    if not text:
        return "video_download"
    text = re.sub(r'[^\w\s-]', '', text).strip()
    return text[:50] or "video_download"

# --- ROUTE UTAMA DENGAN INJEKSI CONFIG ---
@app.route('/')
def index():
    config = panel.get_config()
    return render_template('index.html', config=config)

# --- ROUTE PAGE ---
@app.route('/<path:page>')
def static_pages(page):
    try: 
        return render_template(f'{page}.html')
    except: 
        return "Halaman tidak ditemukan", 404

# --- ROUTE ADMIN PANEL ---
@app.route('/admin')
def admin_page():
    token = request.args.get('token')
    if token != panel.ADMIN_TOKEN:
        return "Akses Ditolak: Token Salah", 403
    
    config = panel.get_config()
    # Baca cookies saat ini untuk ditampilkan di editor
    current_cookies = ""
    if os.path.exists('cookies.txt'):
        with open('cookies.txt', 'r') as f:
            current_cookies = f.read()
            
    return render_template('panel.html', token=token, config=config, cookies=current_cookies)

@app.route('/admin/save', methods=['POST'])
def admin_save():
    data = request.json
    if data.get('token') != panel.ADMIN_TOKEN:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    target = data.get('target')
    content = data.get('content')

    if target == 'cookies':
        success = panel.update_cookies(content)
    else:
        # Update Meta Tags / Scripts
        success = panel.save_settings({
            "meta_tags": data.get('meta_tags'),
            "scripts": data.get('scripts')
        })

    return jsonify({'success': success})

# --- LOGIKA DOWNLOADER ---
@app.route('/get_info', methods=['POST'])
def get_info():
    url = request.form.get('url')
    if not url: 
        return jsonify({'success': False, 'error': 'URL kosong'})

    # Bersihkan URL dari spasi
    url = url.strip()

    try:
        if 'youtube.com' in url or 'youtu.be' in url:
            # Menggunakan engines/youtube.py yang sudah kita set pakai Deno
            return jsonify(get_yt_info(url))
        elif 'tiktok.com' in url:
            return jsonify(get_tt_info(url))
        else:
            return jsonify(get_general_info(url))
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# --- PROXY DOWNLOAD (Mengalirkan Video Agar Bisa Didownload Langsung) ---
@app.route('/download')
def proxy_download():
    video_url = request.args.get('url')
    title = request.args.get('title', 'video')
    safe_title = slugify(title)
    
    if not video_url:
        return "URL video tidak ditemukan", 400

    try:
        # Gunakan Header Desktop agar tidak dicurigai sebagai bot mobile murahan
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Connection': 'keep-alive'
        }
        
        # Stream=True penting agar RAM server Koyeb tidak penuh (Chunk streaming)
        req = requests.get(video_url, headers=headers, stream=True, timeout=120, verify=False)
        
        # Ambil tipe konten asli dari sumber (video/mp4, dsb)
        content_type = req.headers.get('Content-Type', 'video/mp4')

        def generate():
            for chunk in req.iter_content(chunk_size=1024*1024): # 1MB per chunk
                if chunk:
                    yield chunk

        return Response(
            generate(),
            headers={
                "Content-Type": content_type,
                "Content-Disposition": f"attachment; filename={safe_title}.mp4",
                "Cache-Control": "no-cache"
            }
        )
    except Exception as e:
        return f"Gagal mendownload video: {str(e)}", 500

if __name__ == '__main__':
    # Koyeb menggunakan environment PORT
    port = int(os.environ.get("PORT", 8000))
    app.run(host='0.0.0.0', port=port)
