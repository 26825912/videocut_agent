import yt_dlp
import os
import time
import logging
from datetime import datetime
import json

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
    data_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    data_dir = os.path.join(data_dir,'data')
    return data_dir



def save_json_to_file(data):
    """
    将JSON数据保存到文件
    
    inputs:
        data: 要保存的JSON数据
        filename: 文件名（可选，不提供则自动生成）
        directory: 目录路径（可选，不提供则使用默认目录）
    return: 保存的文件路径
    """
    data_dir = get_data_dir()
    directory = os.path.join(data_dir, 'videoscript_json')
    
    # 创建目录（如果不存在）
    os.makedirs(directory, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"result_{timestamp}.json"
    
    file_path = os.path.join(directory, filename)
    
    # 写入JSON文件
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    
    logger.info(f"JSON数据已保存到: {file_path}")
    relative_path = os.path.relpath(file_path, data_dir)
    return relative_path


if __name__ == "__main__":
    url = r'https://www.youtube.com/shorts/xiFI5QwHmw8?t=5&feature=share'
    download_video_from_url(url)
    
