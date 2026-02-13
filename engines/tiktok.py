import requests

def get_tt_info(video_url):
    try:
        # Menggunakan API TikWM untuk bypass watermark
        api_url = "https://www.tikwm.com/api/"
        payload = {'url': video_url}
        
        res = requests.post(api_url, data=payload, timeout=10)
        data = res.json()
        
        if data.get('code') == 0:
            video_data = data['data']
            return {
                'success': True,
                'title': video_data.get('title', 'TikTok Video'),
                'thumbnail': video_data.get('cover'),
                'duration': f"{video_data.get('duration', 0)}s",
                'download_url': video_data.get('play') # Video tanpa watermark
            }
        else:
            return {'success': False, 'error': 'Gagal mengambil data TikTok'}
            
    except Exception as e:
        return {'success': False, 'error': f"TikTok Error: {str(e)}"}
