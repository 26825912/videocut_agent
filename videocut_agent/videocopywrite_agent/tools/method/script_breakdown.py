import requests
import os
import json
import pandas as pd
import json
import os
from datetime import datetime
import logging
from openpyxl.utils import get_column_letter
from openpyxl.styles import Alignment

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# 建议：API Key 最好不要硬编码在代码里，但测试时可以先这样
API_KEY = os.getenv("DIFY_API_KEY")
COPYWRITE_BASE_URL = os.getenv("COPYWRITE_BASE_URL", "https://difyzzc.zuzuche.com/v1/workflows/run")


def run_dify_workflow(input_text: str,language: str = "中文"):
    """
    调用 Dify 工作流 API
    """
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    # 修正2：inputs 必须是字典，且 Key 要与 Dify 开始节点的变量名一致
    # 请将下面代码中的 "query" 替换为你 Dify 工作流里实际设置的变量名
    workflow_inputs = {
        "content": input_text,  # 假设 Dify 里的变量名是 query
        "language": language
    }

    data = {
        "inputs": workflow_inputs,
        "response_mode": "blocking",
        "user": "abc-123"
    }

    try:
        response = requests.post(COPYWRITE_BASE_URL, headers=headers, json=data)
        if response.status_code != 200:
            logger.error(f"Error Response: {response.text}")
            
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"请求发生错误: {e}")
        return None
    

def get_data_dir():
    data_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
    data_dir = os.path.join(data_dir,'data')
    return data_dir


def append_single_analysis_to_excel(single_json_input, filename="视频拆解数据库.xlsx"):
    """
    接收单个 Dify 响应结果，并将其追加到 Excel 文件中。
    如果文件不存在会自动创建；如果存在则追加新的一行。
    """
    # -------------------------------------------------------
    # 1. 解析数据 (Parsing Data)
    # -------------------------------------------------------
    # 获取基础标识
    task_id = single_json_input.get('task_id', 'Unknown_ID')
    data_dir = get_data_dir()
    save_dir = os.path.join(data_dir, "video_script","script_break_down")
    # 定位 outputs 路径
    try:
        outputs = single_json_input['data']['outputs']
    except KeyError:
        logger.error(f"❌ 数据格式错误：未找到 ['data']['outputs'] 字段 (Task ID: {task_id})")
        return

    # --- 准备三层数据字典 ---
    # Row 1: 逻辑层 (需要展平)
    row_layer1 = {'Task_ID': task_id}
    if 'first_layer' in outputs:
        for module, content in outputs['first_layer'].items():
            if isinstance(content, dict):
                for key, val in content.items():
                    # 生成列名，如 "[The Hook] Formula"
                    col_name = f"[{module}] {key}"
                    row_layer1[col_name] = str(val)
            else:
                row_layer1[module] = str(content)

    # Row 2: 技法层 (直接映射)
    row_layer2 = {'Task_ID': task_id}
    if 'second_layer' in outputs:
        row_layer2.update(outputs['second_layer'])

    # Row 3: 模版层 (复杂对象转 JSON 字符串)
    row_layer3 = {'Task_ID': task_id}
    if 'third_layer' in outputs:
        for key, val in outputs['third_layer'].items():
            if isinstance(val, (list, dict)):
                row_layer3[key] = json.dumps(val, indent=2, ensure_ascii=False)
            else:
                row_layer3[key] = str(val)

    # -------------------------------------------------------
    # 2. 读取或创建 DataFrames (File Handling)
    # -------------------------------------------------------
    
    # 定义 Sheet 名称
    sheet_names = {
        "layer1": "1.逻辑架构横评",
        "layer2": "2.视听技法分析",
        "layer3": "3.万能模版库"
    }

    # 准备新数据的 DataFrame
    new_df_map = {
        "layer1": pd.DataFrame([row_layer1]),
        "layer2": pd.DataFrame([row_layer2]),
        "layer3": pd.DataFrame([row_layer3])
    }

    dfs_to_save = {}
    file_path = os.path.join(save_dir, filename)
    if not os.path.exists(file_path):
        # === 场景 A: 新文件 ===
        logger.info(f"🆕 文件不存在，正在创建新文件: {file_path}")
        dfs_to_save = {
            sheet_names["layer1"]: new_df_map["layer1"],
            sheet_names["layer2"]: new_df_map["layer2"],
            sheet_names["layer3"]: new_df_map["layer3"]
        }
    else:
        # === 场景 B: 追加到旧文件 ===
        logger.info(f"📂 发现已有文件，正在追加数据: {file_path}")
        try:
            # 逐个读取现有的 Sheet
            with pd.ExcelFile(file_path, engine='openpyxl') as xls:
                for layer_key, sheet_title in sheet_names.items():
                    new_data = new_df_map[layer_key]
                    
                    if sheet_title in xls.sheet_names:
                        # 如果 Sheet 存在，读取并合并
                        old_df = pd.read_excel(xls, sheet_name=sheet_title)
                        # 使用 concat 追加，ignore_index=True 重新排列索引
                        combined_df = pd.concat([old_df, new_data], ignore_index=True)
                        dfs_to_save[sheet_title] = combined_df
                    else:
                        # 如果文件存在但 Sheet 不存在（罕见情况），直接新建 Sheet
                        dfs_to_save[sheet_title] = new_data
            
        except Exception as e:
            logger.error(f"❌ 读取旧文件失败，请检查文件是否被打开: {e}")
            return

    # -------------------------------------------------------
    # 3. 写入并美化格式 (Writing & Formatting)
    # -------------------------------------------------------
    try:
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            for sheet_name, df in dfs_to_save.items():
                # 确保 Task_ID 始终在第一列
                cols = ['Task_ID'] + [c for c in df.columns if c != 'Task_ID']
                df = df[cols]
                
                df.to_excel(writer, sheet_name=sheet_name, index=False)
                
                # === 格式美化 ===
                worksheet = writer.sheets[sheet_name]
                align = Alignment(wrap_text=True, vertical='top')
                
                for col_idx, col in enumerate(worksheet.columns, 1):
                    col_letter = get_column_letter(col_idx)
                    # 第一列窄一点，后面宽一点
                    width = 25 if col_idx == 1 else 60
                    worksheet.column_dimensions[col_letter].width = width
                    
                    for cell in col:
                        cell.alignment = align
                        
        logger.info(f"✅ 成功追加 Task ID: {task_id} 到文件 {file_path}")
    
        return file_path,task_id
    except PermissionError:
        logger.error(f"❌ 保存失败！请先关闭 Excel 文件：{file_path}")
    except Exception as e:
        logger.error(f"❌ 保存时发生未知错误: {e}")


def scipt_breakdown2excel(content):
    """
    拆解文案后，将拆解的结果保存到 Excel 文件中
    
    :param content: 待拆解的文案内容
    :return:
        relative_path: 拆解结果保存的excel文件的相对路劲
        task_id: 拆解任务的ID,可用于在excel中查找拆解结果
    """
    # 调用函数
    data_dir = get_data_dir()
    result = run_dify_workflow(content)
    logger.info("成功拆解文案")

    if result:
        file_path,task_id = append_single_analysis_to_excel(result)
        logging.info(f"拆解结果已保存至 {file_path}, 任务ID为: {task_id}")
    
    relative_path = os.path.relpath(file_path, data_dir)
    logging.info(f"拆解结果相对路径: {relative_path}")
    return relative_path,task_id


def script_breakdown(content):
    """
    拆解文案，返回拆解后的结果
    :param content: 待拆解的文案内容
    :return: 拆解后的结果字典，包含以下键值对：
        - first_layer: 第一层拆解结果
        - second_layer: 第二层拆解结果
        - third_layer: 第三层拆解结果
    """
    logging.info("开始拆解文案")
    result = run_dify_workflow(content)
    data = result.get('data')
    if not data:
        logger.error(f"Dify 返回缺少 'data' 字段: {result}")
        raise ValueError("Dify API 响应结构缺失 data 字段")

    output = data.get('outputs', '')
    
    if not output:
        error_msg = f"Dify 工作流未返回有效 outputs。完整响应: {result}"
        logger.error(error_msg)
        raise ValueError("文案拆解失败：API 返回结果为空")
    logging.info("成功拆解文案")
    return output

    

if __name__ == "__main__":
    question = """随着人工智能技术的快速发展，越来越多的企业开始探索大模型在实际业务场景中的应用。无论是智能客服、内容生成，还是数据分析与决策支持，AI 正在深刻改变我们的工作方式。然而，在落地过程中，企业也面临诸多挑战，例如数据安全、模型幻觉、响应延迟以及与现有系统的集成难度。因此，构建一个稳定、可控、可解释的 AI 工作流显得尤为重要。通过模块化设计，将提示工程、工具 调用、多轮对话和人工审核等环节有机结合，不仅能提升系统可靠性，还能有效降低业务风险。未来，AI 不会完全取代人类，但会成为人类高效协作的智能助手。我们应当以开放的心态拥抱技术变革，同时保持理性与审慎，确保技术始终服务于人的核心需求。本测试文本用于验证工作流对输入语义的理解、结构化输出能力及整体响应稳定性。"""
    
    # 调用函数
    # result = run_dify_workflow(question)
    # if result:
    #     # 打印格式化后的 JSON，方便查看
    #     print(json.dumps(result, indent=2, ensure_ascii=False))
    # # result = json.dumps(result, indent=2, ensure_ascii=False)
    # append_single_analysis_to_excel(result)

    result = script_breakdown(question)

    print(result)
    
    
    