import yt_dlp
import os

def get_yt_info(video_url):
    # Mengatur path dasar untuk cookies dan cache
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cookie_path = os.path.join(base_dir, 'cookies.txt')
    # Folder cache harus sama dengan yang ada di Dockerfile
    cache_path = '/app/yt_cache'

    ydl_opts = {
        'quiet': False,
        'verbose': True,
        'format': 'best', # Sederhanakan format untuk pengetesan
        'allow_unsecure_tools': True,
        'allow_remote_scripts': True,
        'cache_dir': cache_path,
        'cookiefile': cookie_path if os.path.exists(cookie_path) else None,
        'nocheckcertificate': True,
        'extractor_args': {
            'youtube': {
                # UBAH INI: Gunakan ios atau tv agar bypass n-challenge lebih mudah
                'player_client': ['ios', 'android', 'tv'],
                'js_runtime': 'node'
            }
        },
        'js_runtime':['node'],
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract info tanpa download file fisik
            info = ydl.extract_info(video_url, download=False)
            download_url = info.get('url')
            
            # Logika fallback jika URL langsung tidak ditemukan
            if not download_url and 'formats' in info:
                # Cari format yang punya video dan audio sekaligus (combined)
                combined = [f for f in info['formats'] 
                           if f.get('acodec') != 'none' and f.get('vcodec') != 'none']
                download_url = combined[-1].get('url') if combined else info['formats'][-1].get('url')

            if not download_url:
                raise Exception("Node.js gagal memecah n-challenge YouTube.")

            return {
                'success': True,
                'title': info.get('title', 'YouTube Video'),
                'thumbnail': info.get('thumbnail'),
                'duration': info.get('duration_string', 'N/A'),
                'download_url': download_url
            }
            
    except Exception as e:
        # Mencetak error ke log Koyeb agar mudah di-debug
        print(f"DEBUG YT ERROR: {str(e)}")
        return {'success': False, 'error': f"YouTube Engine Error: {str(e)}"}
