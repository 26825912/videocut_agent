import requests
import json
import os
import re
import logging

from .script_breakdown import scipt_breakdown2excel
from langchain.tools import tool
from .utils import save_json_to_file


SCRIPTS_BASE_URL = os.getenv("SCRIPTS_BASE_URL", "https://difyzzc.zuzuche.com/v1/workflows/run")
SCRIPTS_API_KEY = os.getenv("SCRIPTS_API_KEY")


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

    

def parse_llm_json(raw_data):
    """
    解析大模型返回的带有 markdown 标记的 JSON 字符串
    :param raw_data: 可以是包含 'scripts' key 的字典，也可以直接是那个字符串
    :return: 解析后的 Python 列表/字典
    """
    
    if isinstance(raw_data, dict) and 'scripts' in raw_data:
        json_str = raw_data['scripts']
    elif isinstance(raw_data, str):
        json_str = raw_data
    else:
        logger.error("输入数据格式错误，期望字典或字符串")
        return []

    # 2. 清洗数据（核心步骤）
    try:
        match = re.search(r'(\[.*\])', json_str, re.DOTALL)
        
        if match:
            clean_json_str = match.group(1)
            # 3. 转换为 Python 对象
            parsed_data = json.loads(clean_json_str)
            return parsed_data
        else:
            clean_str = json_str.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_str)

    except json.JSONDecodeError as e:
        logger.error(f"JSON 解析失败: {e}")
        # 打印出有问题的字符串方便调试
        logger.error(f"出错的字符串片段: {json_str[:100]}...")
        return []
    except Exception as e:
        logger.error(f"发生未知错误: {e}")
        return []
    

def extract_full_script(script_data):
    """
    将分镜列表中的 original_text 提取并拼接成完整的口播文案
    
    :param script_data: 解析后的 JSON 列表 (List[dict])
    :return: 拼接好的完整字符串 (String) 或 包含该字符串的字典
    """
    if not isinstance(script_data, list):
        print("错误：输入数据必须是列表")
        return ""
    lines = [item.get('original_text', '') for item in script_data]
    full_script = " ".join(lines)
    return {
        "full_script": full_script,  # 给 TTS 用
        "scene_count": len(script_data) # 统计信息（可选）
    }
    


@tool
def get_video_scripts(topic, times):
    """
    根据主题和时长范围生成视频文案
    input:
        topic: 视频主题
        times: 视频脚本时长范围以秒为单位,例如15-25
    return: 
        1. 解析后的 JSON 列表 (List[dict])
        2. 拼接好的完整字符串 (String) 或 包含该字符串的字典
    """
    
    headers = {
        'Authorization': f'Bearer {SCRIPTS_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        # === 核心修改点：在这里传入参数 ===
        "inputs": {
            "topic": topic,
            "times": str(times)
        },
        # =============================
        "response_mode": "blocking",  # 阻塞模式（非流式）
        "user": "abc-123"
    }

    try:
        logger.info(f"正在发送请求... 主题: {topic}, Times: {times}")
        response = requests.post(SCRIPTS_BASE_URL, headers=headers, json=payload)

        response.raise_for_status()
        
        result = response.json()
        if 'data' in result and 'outputs' in result['data']:
            decode_result = parse_llm_json(result['data']['outputs'])
            full_text = extract_full_script(decode_result)['full_script']
            return decode_result, full_text
        else:
            decode_result = parse_llm_json(result['data']['outputs'])
            full_text = extract_full_script(decode_result)['full_script']

            new_parsed_result = {
                "parsed_result": decode_result,
                "full_script": full_text,
            }
            # relative_parsed_result = save_json_to_file(new_parsed_result)
        
        return {
            "tool_return":{
                "relative_parsed_result": new_parsed_result,
                "describe": "根据主题和时间生成的视频脚本"
            },
        }

    except requests.exceptions.RequestException as e:
        logger.error(f"请求失败: {e}")
        if 'response' in locals() and response.text:
            logger.error(f"服务器返回错误: {response.text}")
        return None


if __name__ == "__main__":
    
    # 示例参数
    my_topic = "how to wake up early"
    my_times = 15-25  
    # 调用
    output, full_text = get_video_scripts( my_topic, my_times)
    
    if output:
        print("\n--- 工作流执行结果 ---")
        print(output)
        print("\n--- 完整口播文案 ---")
        print(full_text)
    else:
        print("获取视频脚本失败")