import yt_dlp
import os
import glob
import re
import unicodedata

def sanitize_filename(filename):
    turkish_map = {
        'ı': 'i', 'İ': 'I', 'ğ': 'g', 'Ğ': 'G',
        'ü': 'u', 'Ü': 'U', 'ş': 's', 'Ş': 'S',
        'ö': 'o', 'Ö': 'O', 'ç': 'c', 'Ç': 'C'
    }
    
    for turkish_char, replacement in turkish_map.items():
        filename = filename.replace(turkish_char, replacement)
    
    filename = filename.lower()
    filename = unicodedata.normalize('NFKD', filename)
    filename = filename.encode('ascii', 'ignore').decode('ascii')
    filename = filename.replace(' ', '_')
    filename = re.sub(r'[^\w\-.]', '_', filename)
    filename = re.sub(r'_+', '_', filename)
    filename = filename.strip('_')
    
    return filename

def download_youtube_audio(video_url, output_path="audio_downloads"):
    os.makedirs(output_path, exist_ok=True)
    
    info_opts = {
        'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
        'nocheckcertificate': True,
    }
    
    with yt_dlp.YoutubeDL(info_opts) as ydl:
        info = ydl.extract_info(video_url, download=False)
        original_title = info.get('title', 'video')
        sanitized_title = sanitize_filename(original_title)
        print(f"Original title: {original_title}")
        print(f"Sanitized title: {sanitized_title}")
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'{output_path}/{sanitized_title}.%(ext)s',
        'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
        'nocheckcertificate': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'keepvideo': False,
        'nopart': True,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        print(f"Downloading audio from: {video_url}")
        ydl.download([video_url])
        print("Download completed!")
    
    for part_file in glob.glob(f'{output_path}/*.part'):
        try:
            os.remove(part_file)
        except:
            pass

if __name__ == "__main__": 
    video_url = "https://www.youtube.com/watch?v=phQgJmz0KU4"
    download_youtube_audio(video_url)
