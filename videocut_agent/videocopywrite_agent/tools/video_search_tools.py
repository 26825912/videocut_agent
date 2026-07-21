import requests
import os
import random
import logging
import uuid
from langchain_core.tools import tool
from tools.videocut_methods import VideoOpsV2

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# --- 全局配置 ---
API_KEY = os.getenv("PIXABAY_API_KEY")
BASE_URL = os.getenv("PIXABAY_API_URL", "https://pixabay.com/api/videos/")


def get_data_dir():
    data_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    data_dir = os.path.join(data_dir,'data')
    return data_dir

def search_and_download(
                    query, 
                    # --- 1. 下载行为控制参数 ---
                    download_count=1,      # 需要下载的视频数量
                    is_random=False,       # True=在结果中随机抽取, False=按顺序抽取
                    # --- 2. Pixabay API 原生参数 ---
                    video_type="all",      # 可选: "all", "film", "animation"
                    category="nature",           # 可选: "nature", "science", "business" 等
                    quality="medium",        # 可选: "tiny","small", "medium", "large"
                    duration = None,        # 视频时长栓选
                    per_page=20,           # API一次返回多少个结果 (3 - 200)
                    page=1,                 # 页码
                    Orientation="Vertical",     # 可选: "Any", "Horizontal", "Vertical"
                ):
    """
    根据 API 参数搜索并执行智能下载
    """
    data_dir = get_data_dir()
    save_dir = os.path.join(data_dir,'videos')
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    params = {
        "key": API_KEY,
        "q": query,
        "video_type": video_type,
        "category": category,
        "per_page": per_page,  # 这里直接使用你传入的参数
        "page": page,
        "safesearch": "true",
        "orientation": Orientation,
    }
    logger.info(f"正在搜索 '{query}' (类型:{video_type}, 分类:{category}, 页码:{page})...")
    # 3. 发送请求
    try:
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        logger.error(f"API 请求失败: {e}")
        return

    # 4. 获取搜索结果列表
    all_hits = data.get('hits', [])
    total_hits = len(all_hits)
    
    if total_hits == 0:
        logger.info("未找到任何视频，请尝试更换关键词或分类。")
        return

    logger.info(f"本页共获取到 {total_hits} 个视频资源。")

    filtered_hits = []
    
    for hit in all_hits:
        # A. 时长筛选
        if duration and hit["duration"] < duration:
            continue # 跳过时长不足的

        # B. 方向筛选 (根据返回的 JSON 结构判断)
        if Orientation != "Any":
            # 获取视频尺寸信息，通常取 medium 即可代表该视频的比例
            # 防止某个清晰度缺失，做一个简单的容错获取
            vid_info = hit['videos'].get('medium') or hit['videos'].get('large') or hit['videos'].get('small')
            
            if not vid_info:
                continue # 数据异常，跳过

            w = vid_info['width']
            h = vid_info['height']

            if Orientation == "Horizontal" and h >= w:
                continue # 需要横屏，但实际是竖屏或正方 -> 跳过
            
            if Orientation == "Vertical" and w >= h:
                continue # 需要竖屏，但实际是横屏或正方 -> 跳过

        # 满足所有条件，加入列表
        filtered_hits.append(hit)
    
    if filtered_hits:
        all_hits = filtered_hits
    else:
        all_hits = all_hits

    if duration:
        choosed_duration = [hit for hit in all_hits if hit["duration"] >= duration]
        total_hits = len(all_hits)

        if total_hits == 0:
            all_hits = all_hits
        else:
            all_hits = choosed_duration
            
    real_download_count = min(download_count, total_hits)
    
    if is_random:
        logger.info(f"模式: [随机抽取] {real_download_count} 个视频...")
        final_selection = random.sample(all_hits, real_download_count)
    else:
        logger.info(f"模式: [顺序抽取] 前 {real_download_count} 个视频...")
        final_selection = all_hits[:real_download_count]

    logger.info(f"开始下载 {len(final_selection)} 个文件...\n")
    
    results = []
    for index, hit in enumerate(final_selection):
        video_id = hit['id']
        quality_list = hit['videos'].keys()
        if quality in hit['videos']:
            video_obj = hit['videos'].get(quality)
        else: 
            if "large" in quality_list: 
                video_obj = hit['videos'].get("large") 
            elif "medium" in quality_list: 
                video_obj = hit['videos'].get("medium") 
            elif "small" in quality_list: 
                video_obj = hit['videos'].get("small") 
            elif "tiny" in quality_list: 
                video_obj = hit['videos'].get("tiny") 
            else: 
                video_obj = None
            
        if not video_obj:
            logger.info(f"ID {video_id} 缺少 medium 资源，跳过。")
            continue

        download_url = video_obj['url']
        width = video_obj['width']
        height = video_obj['height']
        
        file_name = f"{save_dir}/{query.replace(' ', '_')}_{video_id}.mp4"
        logger.info(f"[{index+1}/{len(final_selection)}] 下载中... ID:{video_id} | 尺寸:{width}x{height}")

        try:
            # 验证保存目录存在
            os.makedirs(os.path.dirname(file_name), exist_ok=True)

            # 网络请求加超时和重试机制
            with requests.get(download_url, stream=True, timeout=30) as r:
                # 检查HTTP状态码
                r.raise_for_status()

                # 检查内容类型
                content_type = r.headers.get('content-type', '')
                if not content_type.startswith('video/'):
                    logger.warning(f"意外的内容类型: {content_type}")

                # 安全的文件写入
                temp_file = file_name + '.tmp'
                try:
                    with open(temp_file, 'wb') as f:
                        downloaded_size = 0
                        for chunk in r.iter_content(chunk_size=1024*1024):  # 1MB chunk
                            if chunk:  # 过滤空chunk
                                f.write(chunk)
                                downloaded_size += len(chunk)

                    # 验证下载完成后重命名
                    if downloaded_size > 0:
                        os.rename(temp_file, file_name)
                        results.append(file_name)
                        logger.info(f"   -> 完成: {file_name} ({downloaded_size} bytes)")
                    else:
                        logger.error(f"   -> 失败: 下载文件为空")
                        if os.path.exists(temp_file):
                            os.remove(temp_file)

                except OSError as e:
                    logger.error(f"   -> 文件写入失败: {e}")
                    if os.path.exists(temp_file):
                        os.remove(temp_file)

        except requests.exceptions.Timeout:
            logger.error(f"   -> 超时: 下载超时 ({download_url})")
        except requests.exceptions.HTTPError as e:
            logger.error(f"   -> HTTP错误: {e.response.status_code} - {download_url}")
        except requests.exceptions.ConnectionError:
            logger.error(f"   -> 连接错误: 无法连接到服务器 ({download_url})")
        except requests.exceptions.RequestException as e:
            logger.error(f"   -> 请求失败: {e}")
        except Exception as e:
            logger.error(f"   -> 未知错误: {e}")
            # 清理可能的临时文件
            temp_file = file_name + '.tmp'
            if os.path.exists(temp_file):
                os.remove(temp_file)

    logger.info("\n所有任务结束。")
    return results


# @tool
# def video_serach_and_merge_cut_tools2(query, 
#                                     duration, 
#                                     download_count=3, 
#                                     is_random=False, 
#                                     category="nature", 
#                                     video_type="all", 
#                                     quality="medium", 
#                                     Orientation="Vertical",     # 可选: "Any", "Horizontal", "Vertical"
#                                     per_page=20, 
#                                     page=1):
#     """
#     根据输入的关键词去检索素材，并返回一个指定时长的视频素材片段
    
#     :param query: 视频素材检索关键词
#     :param duration: 用户指定的视频素材片段时长（秒）
#     :param download_count: 用户指定的视频素材下载数量,必须使用默认值2
#     :param is_random: 对检索的素材是否随机抽取,Ture或False
#     :param category: 视频素材分类,默认使用:backgrounds,
#             根据主题和文案进行分析选择可选值有： backgrounds, fashion, nature, science, education, 
#             feelings, health, people, religion, places, animals, industry, computer, food, sports, 
#             transportation, travel, buildings, business, music
#     :param video_type: 视频素材类型,默认值"all"，可选值有： "all", "film", "animation"
#     :param quality: 视频素材质量,默认值"medium"
#     :param Orientation: 视频素材方向,默认值"Any", youtube等长视频可选"Horizontal", 短视频可选"Vertical"
#     :param per_page: 每个页面返回的视频素材数量,默认值20 可选1-20
#     :param page: 要检索的页面编号,默认值1
#     """
#     videos_path_list = search_and_download(
#         query=query, 
#         download_count=download_count, 
#         is_random=is_random,
#         category=category,
#         video_type=video_type,
#         quality=quality,
#         per_page=per_page,
#         page=page,
#         Orientation=Orientation,
#     )
    

#     if not videos_path_list:
#         logger.info("未下载到视频，流程结束")
#         return None

#     data_dir = get_data_dir() # 假设这是你的目录获取函数
#     save_dir = os.path.join(data_dir, "result_video", "clip_video")
#     os.makedirs(save_dir, exist_ok=True)
    
#     logger.info("正在检查是否有单个视频满足时长要求...")
    
#     valid_short_videos = [] # 用于存储不够长的视频，备用
    
#     for path in videos_path_list:
#         info = VideoOpsV2.get_video_info(path)
#         current_dur = info.get('duration', 0)
#         valid_short_videos.append({'path': path, 'duration': current_dur})
#         if Orientation == "Vertical":
#             if info.get('height', 0) > info.get('width', 0):
#                 continue
#             else:
#                 resize_path = os.path.join(save_dir, f"resized_{os.path.basename(path)}")
#                 resize_path = VideoOpsV2.resize_and_cut_video2(path, resize_path,720,1280, crop=True)
#                 path = resize_path
        
#         if current_dur >= duration:
#             logger.info(f"发现视频 {os.path.basename(path)} (时长{current_dur}s) 满足要求，直接使用！")
            
#             final_name = f"{query}_{uuid.uuid4()}_cut.mp4"
#             final_path = os.path.join(save_dir, final_name)
            
#             result = VideoOpsV2.clip_video(path, final_path, cut_duration=duration,save_audio=False)
#             relative_path = os.path.relpath(result, data_dir)
#             return relative_path
#         else:
#             continue
        
#     logger.info("没有单个视频满足时长，开始执行合并策略...")
    
#     if not valid_short_videos:
#         logger.info("有效视频列表为空，无法合并")
#         return None

#     clips_to_merge = []
#     current_total = 0
    
#     while current_total < duration:
#         for vid in valid_short_videos:
#             clips_to_merge.append(vid['path'])
#             current_total += vid['duration']
#             if current_total >= duration:
#                 break
        
#     logger.info(f"合并队列生成完毕: 共 {len(clips_to_merge)} 个片段，预计总长 {current_total}s")
    
#     temp_merged_name = f"temp_merge_{uuid.uuid4()}.mp4"
#     temp_merged_path = os.path.join(save_dir, temp_merged_name)
    
#     merged_path = VideoOpsV2.merge_videos(clips_to_merge, temp_merged_path)
    
#     if merged_path:
#         final_name = f"{query}_{uuid.uuid4()}_merged_cut.mp4"
#         final_path = os.path.join(save_dir, final_name)
        
#         final_result = VideoOpsV2.clip_video(merged_path, final_path, cut_duration=duration,save_audio=False)
        
#         if os.path.exists(merged_path):
#             os.remove(merged_path)
#         logger.info(f"最终视频已经生成: {final_result}")
#         relative_path = os.path.relpath(final_result, data_dir)
#         return relative_path
#     else:
#         return None


@tool
def video_serach_and_clip_tools(query, 
                                    duration, 
                                    download_count=2, 
                                    is_random=False, 
                                    category="nature", 
                                    video_type="all", 
                                    quality="medium", 
                                    Orientation="Vertical", 
                                    per_page=20, 
                                    page=1):
    """
    视频素材检索工具，用户输入关键词和时间长度，返回符合要求的视频素材
    input:
        query: 检索关键词,每次只能传入一个关键词
        duration: 识破时长（秒）
        download_count: 下载数量,必须使用默认值2
        is_random: 是否随机抽取视频素材,默认值False
        category: 视频分类,默认使用:backgrounds,
            根据主题和文案进行分析选择,可选值有： backgrounds, fashion, nature, science, education, 
            feelings, health, people, religion, places, animals, industry, computer, food, sports, 
            transportation, travel, buildings, business, music
        video_type: 视频类型,默认值"all"，可选值有： "all", "film", "animation"
        quality: 视频质量,默认值"medium",可选值有： "high", "medium", "low"
        Orientation: 视频方向,默认值"Any",长视频可选"Horizontal", 短视频可选"Vertical"
        per_page: 每个页面返回的视频素材数量,默认值20 可选1-20
        page: 素材页面编号,默认值1

    return:
        1. 返回视频素材相对路劲列表
    """
    videos_path_list = search_and_download(
        query=query, 
        download_count=download_count, 
        is_random=is_random,
        category=category,
        video_type=video_type,
        quality=quality,
        per_page=per_page,
        page=page,
        Orientation=Orientation,
    )
    #计算所有视频的总时长
    total_duration = 0
    data_dir = get_data_dir()
    resize_videos = []
    save_dir = os.path.join(data_dir,'result_video','clip_video')
    os.makedirs(save_dir, exist_ok=True)    
    final_video_path = os.path.join(save_dir,f"{query}_{uuid.uuid4()}.mp4")
    for video in videos_path_list:
        info = VideoOpsV2.get_video_info(video)
        video_duration = info.get('duration',0)
        total_duration += video_duration
        resize_path = os.path.join(save_dir, f"resized_{os.path.basename(video)}")

        video = VideoOpsV2.resize_and_cut_video3(video, resize_path,720,1280)  #后期通过配置参数决定

        if video_duration > duration:
            result = VideoOpsV2.clip_video(video, final_video_path, cut_duration=duration,save_audio=False)
            relative_path = os.path.relpath(result, data_dir)
            return {
                "tool_return":[{
                    "relative_path": relative_path,
                    "describe": "检索后并根据duration进行视频剪辑后的视频相对路劲"
                }]
            }
        else:
            resize_videos.append(video)

    VideoOpsV2.merge_videos(resize_videos, final_video_path)

    final_video_duration = VideoOpsV2.get_video_info(final_video_path).get('duration',0)
    if final_video_duration < duration:
        logger.info(f"最终视频时长 {final_video_duration}s 小于指定时长 {duration}s，需要重复播放")
        new_final_video_path = os.path.join(save_dir, f"repeat_{os.path.basename(final_video_path)}")
        repeat_times = int(duration // final_video_duration) + 1
        repeat_video = VideoOpsV2.repeat_video(final_video_path, new_final_video_path, repeat_times=repeat_times) 
        result = VideoOpsV2.clip_video(repeat_video, final_video_path, cut_duration=duration,save_audio=False)
        relative_path = os.path.relpath(result, data_dir)
        return {
                "tool_return":[{
                    "relative_path": relative_path,
                    "describe": "检索后并根据duration进行视频剪辑后的视频相对路劲"
                }]
            }  
    else:
        clip_temp_video = os.path.join(save_dir,f"merge_{uuid.uuid4()}.mp4")
        result = VideoOpsV2.clip_video(final_video_path, clip_temp_video, cut_duration=duration,save_audio=False)
        relative_path = os.path.relpath(result, data_dir)
        return {
                "tool_return":[{
                    "relative_path": relative_path,
                    "describe": "检索后并根据duration进行视频剪辑后的视频相对路劲"
                }]
            }  

            

# --- 使用示例 ---
if __name__ == "__main__":
    
    final_result = video_serach_and_clip_tools(
        query="狗", 
        duration=5.5,
        download_count=2, 
        is_random=False,       # 开启随机
        category="nature",   # 指定分类
        video_type="all",
        quality="medium",
        Orientation="Vertical",     # 可选: "Any", "Horizontal", "Vertical"
        per_page=50,          # 获取50个作为随机池
        page=1,
    )
    print('final_result:',final_result)
