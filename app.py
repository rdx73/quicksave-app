from flask import Flask, render_template, request, jsonify, Response, redirect, url_for, session
import requests
import re
import os
import time
import shutil
import panel # Import modul panel/config

# Import mesin-mesin downloader
from engines.youtube import get_yt_info
from engines.tiktok import get_tt_info
from engines.general import get_general_info

app = Flask(__name__)
app.secret_key = "QUICKSAVE_SECURE_2026" # Baris Tambahan untuk Session

# --- SISTEM AUTO-CLEANUP (Pencegah RAM Penuh) ---
# Folder cache sesuai dengan Dockerfile
CACHE_DIR = os.environ.get('YTDLP_CACHE_DIR', '/app/yt_cache')

def cleanup_old_cache(max_age_seconds=1000):
    """Menghapus file sampah yang lebih tua dari 1 jam"""
    if not os.path.exists(CACHE_DIR):
        return
    
    now = time.time()
    for filename in os.listdir(CACHE_DIR):
        file_path = os.path.join(CACHE_DIR, filename)
        try:
            # Jika umur file sudah lebih dari 1 jam, hapus
            if os.path.getmtime(file_path) < now - max_age_seconds:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                print(f"Cleanup: Menghapus file sampah {filename}")
        except Exception as e:
            print(f"Cleanup Error: {e}")

# Fungsi untuk membersihkan nama file dari karakter aneh
def slugify(text):
    if not text:
        return "video_download"
    text = re.sub(r'[^\w\s-]', '', text).strip()
    return text[:50] or "video_download"

# --- ROUTE UTAMA DENGAN INJEKSI CONFIG ---
@app.route('/')
def index():
    panel.add_view_count() # INTEGRASI STATS
    config = panel.get_config()
    return render_template('index.html', config=config)

# --- ROUTE PAGE ---
@app.route('/<path:page>')
def static_pages(page):
    try: 
        return render_template(f'{page}.html')
    except: 
        return "Halaman tidak ditemukan", 404

# --- ROUTE LOGIN (TAMBAHAN) ---
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        token = request.form.get('token')
        if panel.login_admin(token):
            return redirect(url_for('admin_page'))
        return render_template('admin_login.html', error="Token Salah, Bang!")
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    panel.logout_admin()
    return redirect(url_for('admin_login'))

# --- ROUTE ADMIN PANEL ---

@app.route('/admin')
def admin_page():
    token = request.args.get('token')
    if not panel.is_logged_in() and token != panel.ADMIN_TOKEN:
        return redirect(url_for('admin_login'))
    
    # Dashboard cuma butuh Stats dan Logs
    stats = panel.get_stats()
    logs = panel.get_logs(10)
    return render_template('panel.html', stats=stats, logs=logs)

@app.route('/admin/cookies')
def admin_cookies():
    if not panel.is_logged_in(): 
        return redirect(url_for('admin_login'))
        
    # Halaman Cookies cuma butuh Cookies
    current_cookies = ""
    if os.path.exists('cookies.txt'):
        with open('cookies.txt', 'r') as f:
            current_cookies = f.read()
    return render_template('admin_cookies.html', cookies=current_cookies)

@app.route('/admin/seo')
def admin_seo():
    if not panel.is_logged_in(): 
        return redirect(url_for('admin_login'))
        
    # Halaman SEO cuma butuh Config
    config = panel.get_config()
    return render_template('admin_seo.html', config=config)

@app.route('/admin/save', methods=['POST'])
def admin_save():
    data = request.json
    # Cek session atau token manual
    if not panel.is_logged_in() and data.get('token') != panel.ADMIN_TOKEN:
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
    # SETIAP REQUEST MASUK, BERSIHKAN SAMPAH LAMA
    cleanup_old_cache()
    
    url = request.form.get('url')
    if not url: 
        return jsonify({'success': False, 'error': 'URL kosong'})

    # Bersihkan URL dari spasi
    url = url.strip()

    try:
        if 'youtube.com' in url or 'youtu.be' in url:
            # Engine YouTube secara otomatis akan menggunakan Deno di folder global
            res = get_yt_info(url)
        elif 'tiktok.com' in url:
            res = get_tt_info(url)
        else:
            res = get_general_info(url)
        
        # HITUNG DOWNLOAD JIKA SUKSES
        if res.get('success'):
            panel.add_download_count()
            
            # --- LOGIKA DETEKSI PLATFORM YANG LEBIH SPESIFIK ---
            url_lower = url.lower()
            if "youtube.com" in url_lower or "youtu.be" in url_lower:
                platform = "YouTube"
            elif "tiktok.com" in url_lower:
                platform = "TikTok"
            elif "instagram.com" in url_lower:
                platform = "Instagram"
            elif "facebook.com" in url_lower or "fb.watch" in url_lower:
                platform = "Facebook"
            elif "twitter.com" in url_lower or "x.com" in url_lower:
                platform = "Twitter/X"
            else:
                platform = "Lainnya"
            
            # Catat judul dan platform yang sudah spesifik
            panel.log_download(res.get('title', 'Unknown Title'), platform)

            
        return jsonify(res)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# --- PROXY DOWNLOAD ---
@app.route('/download')
def proxy_download():
    video_url = request.args.get('url')
    title = request.args.get('title', 'video')
    safe_title = slugify(title)
    
    if not video_url:
        return "URL video tidak ditemukan", 400

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Connection': 'keep-alive'
        }
        
        # Stream=True agar RAM server Koyeb tidak penuh
        req = requests.get(video_url, headers=headers, stream=True, timeout=120, verify=False)
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
    # Pastikan folder cache tersedia saat aplikasi dinyalakan
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR, exist_ok=True)
        
    port = int(os.environ.get("PORT", 8000))
    app.run(host='0.0.0.0', port=port)
