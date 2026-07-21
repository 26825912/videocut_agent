import yt_dlp
import os
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)    


def lang_to_asr_lang(lang):
    if lang == "英文":
        return "en-US"
    elif lang == "中文":
        return "zh-CN"

def download_video_from_url(url):
    """
    从tiktok、youtube或者抖音上下载视频到本地
    
    :param url: 说明
    """
    data_dir = get_data_dir()
    save_dir = os.path.join(data_dir,"download_shorts")
    os.makedirs(save_dir,exist_ok=True)
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best', # 下载最高画质
        'outtmpl': '%(title)s.%(ext)s',       # 文件名模板
        'paths': {'home': save_dir},
        # 'proxy': 'http://127.0.0.1:7890',     # 如果需要代理
        'postprocessors': [{                  # 使用 FFmpeg 合并音视频
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4',
        }],
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        base_name, _ = os.path.splitext(filename)
        filename = base_name + ".mp4"
        logger.info(f"视频下载完成: {filename}")
        
    return filename
    


def get_data_dir():
    data_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    data_dir = os.path.join(data_dir,'data')
    return data_dir



if __name__ == "__main__":
    url = r'https://www.youtube.com/shorts/xiFI5QwHmw8?t=5&feature=share'
    download_video_from_url(url)