from pydub import AudioSegment
import os
import uuid
import logging
from pathlib import Path
from typing import Tuple, Optional, Dict,Any

from .method.script_breakdown import scipt_breakdown2excel,script_breakdown
from .asr_tools import AzureTranscriber
from .utils import download_video_from_url,lang_to_asr_lang
from .method.ai_copywrite import ai_copywrite
import json
from datetime import datetime

from langchain_core.tools import tool

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def get_data_dir():
    data_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    data_dir = os.path.join(data_dir,'data')
    return data_dir



def videoscript_analysis2excel(video_url: str, language: str = "zh-CN") -> Tuple[Optional[str], Optional[str]]:
    """
    将视频文案分析结果保存到 Excel 文件中。
    inputs:
        video_url: 视频链接
        language: 语言代码
    return: (excel_path, task_id) 如果失败可能抛出异常
    """
    video_path = None
    audio_file_path = None

    try:
        # 1. 下载视频
        logger.info(f"开始下载视频: {video_url}")
        video_path = download_video_from_url(video_url)
        
        # 校验下载结果
        if not video_path or not os.path.exists(video_path):
            logger.error(f"视频下载失败: {video_url}")
            raise ValueError("视频下载失败或文件未找到")

        # 2. 准备音频路径 (使用 Path 对象更优雅)
        data_dir = get_data_dir()
        save_dir = Path(data_dir) / "result_video" / "clip_audio"
        save_dir.mkdir(parents=True, exist_ok=True)
        
        audio_file_path = save_dir / f"{uuid.uuid4().hex}.wav"

        # 3. 提取音频
        logger.info("正在提取音频...")
        try:
            audio = AudioSegment.from_file(video_path)
            audio.export(audio_file_path, format="wav")
        except Exception as e:
            logger.error(f"音频格式转换失败: {e}")
            raise RuntimeError(f"无法处理视频音频流: {e}")

        # 4. 语音转文字
        logger.info("正在进行语音转写...")
        transcriber = AzureTranscriber(lang=language)
        # 注意：转写器可能需要字符串路径而不是 Path 对象
        transcript = transcriber.file_to_text(str(audio_file_path))
        
        # 提取并清洗文本
        if not transcript:
            logger.warning("未能识别到语音内容，将生成空内容的分析结果或跳过")
            full_text = ""
        else:
            full_text = "".join([item.get('text', '') for item in transcript if item.get('text')])
            
        logger.info(f"提取文本长度: {len(full_text)} 字符")

        # 5. 生成 Excel
        # 注意：这里保留了你原来代码中的函数名拼写 'scipt'
        # 如果下游函数已经修复了拼写，请改为 script_breakdown2excel
        logger.info("正在生成 Excel 分析报告...")
        excel_path, task_id = scipt_breakdown2excel(content=full_text)
        
        return excel_path, task_id

    except Exception as e:
        logger.exception(f"视频分析转Excel流程发生错误: {str(e)}")
        raise e  # 将异常向上抛出，以便接口层捕获处理

    finally:
        try:
            if video_path and os.path.exists(video_path):
                os.remove(video_path)
                logger.debug(f"已清理临时视频: {video_path}")
                
            if audio_file_path and os.path.exists(audio_file_path):
                os.remove(audio_file_path)
                logger.debug(f"已清理临时音频: {audio_file_path}")
        except Exception as cleanup_err:
            logger.warning(f"清理临时文件失败: {cleanup_err}")



def video_script_analysis(video_url: str, language: str = "en-US") -> Dict[str, Any]:
    """
    拆解爆款视频文案
    
    inputs:
        video_url: 视频 URL
        language: 视频语言，默认 "en-US"可选值有"zh-CN","en-US"
    return: 拆解后的文案数据字典
    """
    video_path = None
    audio_file_path = None

    video_path = download_video_from_url(video_url)
    if not video_path or not os.path.exists(video_path):
        logger.error(f"视频下载失败: {video_url}")
        raise ValueError("视频下载失败或文件不存在")
    
    data_dir = get_data_dir()
    save_dir = Path(data_dir) / "result_video" / "clip_audio"
    save_dir.mkdir(parents=True, exist_ok=True)
    
    audio_file_path = save_dir / f"{uuid.uuid4().hex}.wav"

    logger.info(f"正在提取音频: {video_path}")
    try:
        audio = AudioSegment.from_file(video_path)
        audio.export(audio_file_path, format="wav")
    except Exception as e:
        logger.error(f"音频提取失败: {e}")
        raise RuntimeError(f"音频转换失败: {str(e)}")

    logger.info("正在进行语音转写...")
    transcriber = AzureTranscriber(lang=language)
    transcript = transcriber.file_to_text(str(audio_file_path))
    
    if not transcript:
        logger.warning("未能识别到任何语音文本")
        raise ValueError("未能识别到任何语音文本")

    full_text = "".join([item.get('text', '') for item in transcript if item.get('text')])
    print('full_text',full_text)
    
    logger.info("正在分析文案结构...")

    try:

        script_breakdown_data = script_breakdown(full_text)
        return script_breakdown_data
    except Exception as e:
        logger.error(f"文案分析失败: {e}")
        raise RuntimeError(f"文案分析失败: {str(e)}")
    
    finally:
        # 6. 【核心优化】清理临时文件
        # 无论成功还是失败，都必须删除下载的视频和提取的音频
        try:
            if video_path and os.path.exists(video_path):
                os.remove(video_path)
                logger.debug(f"已清理临时视频: {video_path}")
                
            if audio_file_path and os.path.exists(audio_file_path):
                os.remove(audio_file_path)
                logger.debug(f"已清理临时音频: {audio_file_path}")
        except Exception as cleanup_err:
            logger.warning(f"清理临时文件失败: {cleanup_err}")



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



@tool
def video_script_analysis_tool(video_url: str, language: str = "en-US") -> Dict[str, Any]:
    """
    拆解爆款视频文案
    
    inputs:
        video_url: 视频 URL
        language: 视频语言，默认 "en-US"可选值有"zh-CN","en-US"
    return: 拆解后的文案数据字典
    """
    video_path = None
    audio_file_path = None

    video_path = download_video_from_url(video_url)
    if not video_path or not os.path.exists(video_path):
        logger.error(f"视频下载失败: {video_url}")
        raise ValueError("视频下载失败或文件不存在")
    
    data_dir = get_data_dir()
    save_dir = Path(data_dir) / "result_video" / "clip_audio"
    save_dir.mkdir(parents=True, exist_ok=True)
    
    audio_file_path = save_dir / f"{uuid.uuid4().hex}.wav"

    logger.info(f"正在提取音频: {video_path}")
    try:
        audio = AudioSegment.from_file(video_path)
        audio.export(audio_file_path, format="wav")
    except Exception as e:
        logger.error(f"音频提取失败: {e}")
        raise RuntimeError(f"音频转换失败: {str(e)}")

    logger.info("正在进行语音转写...")
    transcriber = AzureTranscriber(lang=language)
    transcript = transcriber.file_to_text(str(audio_file_path))
    
    if not transcript:
        logger.warning("未能识别到任何语音文本")
        raise ValueError("未能识别到任何语音文本")

    full_text = "".join([item.get('text', '') for item in transcript if item.get('text')])
    print('full_text',full_text)
    
    logger.info("正在分析文案结构...")
    try:

        script_breakdown_data = script_breakdown(full_text)
        
        return {
            "tool_return":[{
                "script_breakdown_data": script_breakdown_data,
                "describe": "拆解后的文案数据字典，包含视频时长、文案段落、每个段落的时间长度、文案内容等信息"
            }]
        }
    except Exception as e:
        logger.error(f"文案分析失败: {e}")
        raise RuntimeError(f"文案分析失败: {str(e)}")
    
    finally:
        # 6. 【核心优化】清理临时文件
        # 无论成功还是失败，都必须删除下载的视频和提取的音频
        try:
            if video_path and os.path.exists(video_path):
                os.remove(video_path)
                logger.debug(f"已清理临时视频: {video_path}")
                
            if audio_file_path and os.path.exists(audio_file_path):
                os.remove(audio_file_path)
                logger.debug(f"已清理临时音频: {audio_file_path}")
        except Exception as cleanup_err:
            logger.warning(f"清理临时文件失败: {cleanup_err}")


@tool
def ai_copywrite_tool(video_url: str, 
                topic: str,
                time: str = "20-25",
                lang: str = "英文"):
    """
    文案仿写工具
    inputs:
        video_url: 爆款视频的 URL 链接
        topic: 新的仿写主题 (例如 "租车应该注意些什么内容", "洛杉矶租车自驾")
        time: 目标视频时长范围 (秒)，例如 "20-25"
        lang: 目标语言,如果不说明，默认使用英文(可选: "英文", "中文")
    return: 仿写后的文案文件相对路劲
    """
    
    # 1. 基础参数校验
    if not video_url:
        logger.error("未提供视频 URL")
        raise ValueError("视频 URL 不能为空")
    if not topic:
        logger.error("未提供仿写主题")
        raise ValueError("仿写主题不能为空")

    parsed_result = None
    full_script = None

    try:
        logger.info(f"=== 开始执行 AI 仿写任务 ===")
        logger.info(f"视频: {video_url} | 主题: {topic} | 语言: {lang}")

        asr_lang = lang_to_asr_lang(lang)
        logger.debug(f"映射语言参数: {lang} -> ASR Code: {asr_lang}")

        logger.info(">>> 阶段 1/2: 正在拆解原视频文案...")
        break_data = video_script_analysis(video_url, language=asr_lang)
        
        if not break_data:
            logger.error("视频文案拆解返回为空，终止流程")
            raise RuntimeError("原视频分析失败")

        logger.info(">>> 阶段 2/2: 正在基于拆解结构进行仿写...")
        
        parsed_result, full_script = ai_copywrite(
            break_data, 
            topic=topic, 
            time=time, 
            lang=lang 
        )
        logger.info("=== 仿写任务执行成功 ===")
        parsed_result = parsed_result.get("script_timeline")
        if not parsed_result:
            logger.error("AI 仿写返回为空，终止流程")
            raise RuntimeError("AI 仿写失败")
        
        new_parsed_result = {
            "parsed_result": parsed_result,
            "full_script": full_script,
        }
        relative_parsed_result = save_json_to_file(new_parsed_result)
        
        return {
            "tool_return":{
                "relative_parsed_result": relative_parsed_result,
                "describe": "爆款视频拆仿写后的文案文件相对路劲"
            },
        }
    except Exception as e:
        logger.exception(f"AI 仿写工具执行过程中发生错误: {str(e)}")
        raise e 
    

if __name__ == "__main__":
    video_url= r'https://www.youtube.com/shorts/1MhpTieJQAQ?t=3&feature=share'
    # break_down_data = video_script_analysis(video_file_path)
    # print('break_down_data',break_down_data)

    # excel_path, task_id = videoscript_analysis2excel(video_file_path)
    # print('excel_path',excel_path)
    # print('task_id',task_id)
    parsed_result, full_script = ai_copywrite_tool(video_url,topic="广州自驾游",time="20-25",lang="英文")
    print('parsed_result',parsed_result)
    print('full_script',full_script)
