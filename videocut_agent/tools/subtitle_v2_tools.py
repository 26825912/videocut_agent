import os
import json
import time
import azure.cognitiveservices.speech as speechsdk
import pysubs2
from pysubs2 import SSAEvent, SSAStyle, Color
from pydub import AudioSegment
import logging
import json
from pydub import AudioSegment
import uuid
from langchain_core.tools import tool

from tools.video_ops_v2 import VideoFormat


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


AZURE_SERVICE_REGION = os.getenv("AZURE_SERVICE_REGION","eastasia")
AZURE_SERVICE_KEY = os.getenv("AZURE_SERVICE_KEY")


# ================= 默认配置 (供前端参考) =================
DEFAULT_STYLE_CONFIG = {
    "PlayResX": 720,
    "PlayResY": 1280,
    "name": "Default",
    "fontname": "Arial",
    "fontsize": 30,
    "colors": {
        "primary": "#FFFFFF",
        "secondary": "#FF0000",
        "outline": "#000000",
        "back": "#000000",
        "alpha": 255
    },
    "opacity": { "back": 120 },
    "bold": False,
    "italic": False,
    "underline": False,
    "strikeout": False,
    "scale_x": 100,
    "scale_y": 100,
    "spacing": 0,
    "angle": 0,
    "border_style": 1,
    "outline_width": 3,
    "shadow_depth": 0,
    "alignment": 2,
    "margins": { "l": 50, "r": 50, "v": 60 },
    "encoding": 1
}

schema_mapping = {
                # === 基础信息 ===
                "name": {
                    "type": "String",
                    "describe": "样式名称",
                    "editable": True  # 可扩展字段：是否允许用户重命名
                },
                "fontname": {
                    "type": "List",
                    "describe": "字体系列",
                    "Range": ["Arial", "Times New Roman", "Microsoft YaHei", "SimHei", "Courier New"]
                },
                "fontsize": {
                    "type": "Number",
                    "describe": "字体大小 (px)",
                    "Range": [10, 200]  # 限制大小范围，防止过大或过小
                },

                # === 颜色设置 (嵌套处理) ===
                # 对应 colors.primary
                "colors.primary": {
                    "type": "Color",
                    "describe": "主文本颜色",
                    "default": "#FFFFFF"
                },
                # 对应 colors.secondary (通常用于卡拉OK模式的次色)
                "colors.secondary": {
                    "type": "Color",
                    "describe": "次要颜色 (卡拉OK)",
                    "default": "#000000"
                },
                # 对应 colors.outline
                "colors.outline": {
                    "type": "Color",
                    "describe": "描边颜色",
                    "default": "#000000"
                },
                # 对应 colors.back
                "colors.back": {
                    "type": "Color",
                    "describe": "阴影/背景颜色",
                    "default": "#000000"
                },
                # 对应 colors.alpha
                "colors.alpha": {
                    "type": "Slider", # 建议前端用滑块
                    "describe": "文本透明度",
                    "Range": [0, 255],
                    "step": 1
                },

                # === 透明度 (嵌套处理) ===
                # ASS 中透明度通常是 0-255 (0是不透明, 255是全透明)
                # 对应 opacity.back
                "opacity.back": {
                    "type": "Slider", # 建议前端用滑块
                    "describe": "背景透明度",
                    "Range": [0, 255],
                    "step": 120
                },

                # === 字体风格 (布尔开关) ===
                "bold": {
                    "type": "Boolean",
                    "describe": "粗体",
                    "Range":[0,1],
                    "options_label": {0: "关闭", 1: "开启"}
                },
                "italic": {
                    "type": "Boolean",
                    "describe": "斜体",
                    "Range":[0,1]
                },
                "underline": {
                    "type": "Boolean",
                    "describe": "下划线",
                    "Range":[0,1]
                },
                "strikeout": {
                    "type": "Boolean",
                    "describe": "删除线",
                    "Range":[0,1]
                },

                # === 几何变换 ===
                "scale_x": {
                    "type": "Number",
                    "describe": "横向缩放 (%)",
                    "Range": [20, 200] # 限制缩放比例
                },
                "scale_y": {
                    "type": "Number",
                    "describe": "纵向缩放 (%)",
                    "Range": [20, 200]
                },
                "spacing": {
                    "type": "Number",
                    "describe": "字间距 (px)",
                    "Range": [-10, 100] # 允许负值紧凑排列
                },
                "angle": {
                    "type": "Number", # 或 Slider/Knob
                    "describe": "旋转角度",
                    "Range": [-360, 360]
                },

                # === 边框与阴影 ===
                "border_style": {
                    "type": "Radio", # 或 List
                    "describe": "边框模式",
                    # 1=Outline + Drop shadow, 3=Opaque Box
                    "Range": [1, 3, 4], 
                    "options_label": {1: "描边+阴影", 3: "不透明背景框", 4: "透明背景框"} # 可选：前端映射显示文本
                },
                "outline_width": {
                    "type": "Number",
                    "describe": "描边宽度",
                    "Range": [0, 20]
                },
                "shadow_depth": {
                    "type": "Number",
                    "describe": "阴影深度/偏移",
                    "Range": [0, 20]
                },

                # === 对齐与布局 ===
                "alignment": {
                    "type": "GridSelect", # 建议前端做一个九宫格选择器
                    "describe": "对齐方式 (1=左下, 2=中下, 3=右下, 5=居中, 7=左上, 8=",
                    # ASS 小键盘布局: 1=左下, 2=中下, 3=右下, 5=居中, 7=左上...
                    "Range": [1, 2, 3, 4, 5, 6, 7, 8, 9] 
                },
                
                # === 边距设置 (嵌套处理) ===
                # 对应 margins.l
                "margins.l": {
                    "type": "Number",
                    "describe": "左边距 (L)",
                    "Range": [0, 720]
                },
                # 对应 margins.r
                "margins.r": {
                    "type": "Number",
                    "describe": "右边距 (R)",
                    "Range": [0, 720]
                },
                # 对应 margins.v
                "margins.v": {
                    "type": "Number",
                    "describe": "垂直边距 (V)",
                    "Range": [0, 1280]
                }
            }

class StyleManager:
    @staticmethod
    def hex_to_color(hex_str, alpha=255):
        """
        将 Hex 颜色 (#FFFFFF) 转换为 pysubs2.Color 对象
        :param hex_str: 前端传来的颜色字符串，如 "#RRGGBB"
        :param alpha: 透明度 0-255 (255=完全不透明)
        """
        hex_str = hex_str.lstrip('#')
        if len(hex_str) != 6:
            # 默认黑色作为 fallback
            return Color(0, 0, 0, alpha)
        
        r = int(hex_str[0:2], 16)
        g = int(hex_str[2:4], 16)
        b = int(hex_str[4:6], 16)
        
        return Color(r, g, b, alpha)

    @staticmethod
    def json_to_ssa_style(config_dict):
        """
        核心方法：将字典/JSON配置转换为 SSAStyle 对象
        """
        style = pysubs2.SSAStyle()
        
        # 1. 基础属性映射
        style.name = config_dict.get("name", "Default")
        style.fontname = config_dict.get("fontname", "Arial")
        style.fontsize = config_dict.get("fontsize", 80)
        
        # 2. 颜色处理 (前端传 Hex，这里转 Color 对象)
        colors = config_dict.get("colors", {})
        opacity = config_dict.get("opacity", {})
        
        # 提取透明度，默认255(不透明)
        back_alpha = opacity.get("back", 120) # 默认半透明背景
        
        style.primarycolor = StyleManager.hex_to_color(colors.get("primary", "#FFFFFF"), colors.get("alpha", 0))
        style.secondarycolor = StyleManager.hex_to_color(colors.get("secondary", "#FF0000"), colors.get("alpha", 0))
        style.outlinecolor = StyleManager.hex_to_color(colors.get("outline", "#000000"), colors.get("alpha", 0))
        style.backcolor = StyleManager.hex_to_color(colors.get("back", "#000000"), back_alpha)

        # 3. 布尔开关
        style.bold = config_dict.get("bold", False)
        style.italic = config_dict.get("italic", False)
        style.underline = config_dict.get("underline", False)
        style.strikeout = config_dict.get("strikeout", False)

        # 4. 数值参数
        style.scalex = config_dict.get("scale_x", 100)
        style.scaley = config_dict.get("scale_y", 100)
        style.spacing = config_dict.get("spacing", 0)
        style.angle = config_dict.get("angle", 0)
        style.borderstyle = config_dict.get("border_style", 1)
        style.outline = config_dict.get("outline_width", 3)
        style.shadow = config_dict.get("shadow_depth", 1.0)
        style.alignment = config_dict.get("alignment", 2) # 2=底部居中
        style.encoding = config_dict.get("encoding", 1)

        # 5. 边距
        margins = config_dict.get("margins", {})
        style.marginl = margins.get("l", 50)
        style.marginr = margins.get("r", 50)
        style.marginv = margins.get("v", 60)

        return style

    @staticmethod
    def load_from_file(json_path):
        """从文件加载批量样式配置"""
        if not os.path.exists(json_path):
            raise FileNotFoundError(f"样式配置文件 {json_path} 不存在")
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return StyleManager.json_to_ssa_style(data)
    
    @staticmethod
    def generate_ui_config(data, schema_map = schema_mapping, parent_path="$"):
        """
        递归将原始 JSON 数据转换为 UI 控件配置列表
        :param data: 当前层级的 JSON 数据 (dict)
        :param schema_map: 预定义的元数据映射表 (dict)
        :param parent_path: 当前层级的路径 (str)
        :return: 转换后的列表 (list)
        """
        ui_config_list = []

        for key, value in data.items():
            # 构建当前属性的 JSONPath，例如 $.colors.primary
            current_path = f"{parent_path}.{key}"
            
            # 1. 如果值是字典（嵌套结构），递归处理
            if isinstance(value, dict):
                # 递归调用并将结果扩展到当前列表
                ui_config_list.extend(StyleManager.generate_ui_config(value, schema_mapping, current_path))
            
            # 2. 如果是具体的值（字符串、数字、布尔），生成配置对象
            else:
                # 尝试从 schema_map 中获取预定义的元数据
                # 优先使用完整路径匹配 (colors.primary)，如果没有则尝试用键名匹配 (primary)
                # 这里为了准确，我们使用去掉 "$." 的路径作为 key 来查找
                lookup_key = current_path.replace("$.", "")
                metadata = schema_map.get(lookup_key, {})
                
                # 如果没有预定义 metadata，根据 Python 类型做简单的自动推断（兜底策略）
                if not metadata:
                    metadata = StyleManager._infer_metadata(key, value)

                # 构建最终对象
                config_item = {
                    "name": key,
                    "value": value,
                    "path": current_path,
                    # 合并元数据 (type, describe, Range)
                    "type": metadata.get("type", "String"), 
                    "describe": metadata.get("describe", key), # 没描述就用 key
                }
                
                # 只有定义了 Range 才添加该字段
                if "Range" in metadata:
                    config_item["Range"] = metadata["Range"]

                ui_config_list.append(config_item)

        return ui_config_list
    

    @staticmethod
    def _infer_metadata(key, value):
        """简单的类型推断兜底，防止 schema 漏写"""
        if isinstance(value, bool):
            return {"type": "Boolean", "describe": key}
        elif isinstance(value, (int, float)):
            return {"type": "Number", "describe": key}
        elif isinstance(value, str) and value.startswith("#"):
            return {"type": "Color", "describe": key}
        else:
            return {"type": "String", "describe": key}
    
    def _set_nested_value(obj, path, value):
        """
        根据点分隔的路径 (e.g., 'colors.primary') 在对象中设置值。
        如果路径中的键不存在，则创建嵌套的字典。
        """
        # 移除路径开头的 '$.'
        keys = path.lstrip('$.').split('.')
        
        current = obj
        # 遍历路径中的键，直到最后一个键
        for i, key in enumerate(keys):
            # 如果是最后一个键，则设置值并返回
            if i == len(keys) - 1:
                current[key] = value
                return
            
            # 如果当前键不存在，或者不是一个字典，则创建一个新的字典
            if key not in current or not isinstance(current[key], dict):
                current[key] = {}
            
            # 移动到下一级嵌套
            current = current[key]

    def convert_to_nested_config(config_list):
        """
        将扁平化的配置列表转换为嵌套的配置字典。
        
        :param config_list: 包含配置项的列表。
        :return: 转换后的嵌套配置字典。
        """
        nested_config = {}
        
        for item in config_list:
            path = item.get('path')
            value = item.get('value')
            
            if path and value is not None:
                StyleManager._set_nested_value(nested_config, path, value)
                
        return nested_config
    

    @staticmethod
    def update_config(config_file_path: str, config_dict) -> None:
        """更新字幕信息配置，只更新已存在的键"""
        try:
            # 加载现有配置
            existing_config = {}
            if os.path.exists(config_file_path):
                with open(config_file_path, 'r', encoding='utf-8') as f:
                    existing_config = json.load(f)
            
            # 逐个键更新配置，只更新已存在的键
            for key, value in config_dict.items():
                if key in existing_config:
                    if isinstance(value, dict) and isinstance(existing_config[key], dict):
                        # 对于字典类型，递归更新子键
                        for sub_key, sub_value in value.items():
                            if sub_key in existing_config[key]:
                                existing_config[key][sub_key] = sub_value
                    else:
                        # 对于非字典类型，直接更新
                        existing_config[key] = value
            
            # 确保目录存在
            os.makedirs(os.path.dirname(config_file_path), exist_ok=True)
            
            # 保存配置
            with open(config_file_path, 'w', encoding='utf-8') as f:
                json.dump(existing_config, f, indent=2, ensure_ascii=False)
            
            logger.info(f"配置已保存到: {config_file_path}")
            
        except Exception as e:
            logger.error(f"更新配置失败: {e}")
            raise
    
    @staticmethod
    def slice_audio(source_audio, start_ms, end_ms, output_filename, output_dir):
        """
        【静态方法】音频切片
        :param source_audio: pydub 的 AudioSegment 对象
        :param start_ms: 开始时间 (ms)
        :param end_ms: 结束时间 (ms)
        :param output_filename: 输出的文件名 (如 slice_0.mp3)
        :param output_dir: 存放目录 (由调用者传入)
        :return: web访问路径
        """
        # 1. 确保目录存在 (为了安全，每次写入前检查一下，或者在主逻辑检查)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # 2. 切片
        chunk = source_audio[start_ms:end_ms]
        
        # 3. 导出
        save_path = os.path.join(output_dir, output_filename)
        chunk.export(save_path, format="mp3")
        
        # 4. 返回相对路径 (假设 output_dir 是 static/audio)
        # 统一把反斜杠转为正斜杠，适配 Web URL
        web_path = f"{output_dir}/{output_filename}".replace("\\", "/")
        return web_path


    @staticmethod
    def ass_to_editor_json(ass_file, original_audio_file, output_dir=None):
        """
        【静态方法】ASS转JSON主逻辑
        :param ass_file: ASS字幕文件路径
        :param original_audio_file: 原始音频/视频文件路径
        :param output_dir: 切片音频的输出目录 (默认为 static/audio_slices)
        """
        # 1. 预先创建输出目录 (如果不存在)
        if output_dir is None:
            data_dir = get_data_dir()
            output_dir = os.path.join(data_dir, "output_audio","shorts_audio")
            os.makedirs(output_dir, exist_ok=True)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            logger.info(f"已创建输出目录: {output_dir}")

        logger.info(f"正在加载 ASS: {ass_file}")
        try:
            subs = pysubs2.load(ass_file)
        except Exception as e:
            logger.error(f"ASS 加载失败: {e}")
            return []

        logger.info(f"正在加载音频: {original_audio_file}")
        # 加载音频到内存
        try:
            full_audio = AudioSegment.from_file(original_audio_file)
        except Exception as e:
            logger.error(f"音频加载失败: {e}")
            return []

        editor_data = []
        logger.info("开始处理切片...")

        for index, event in enumerate(subs):
            if event.is_comment:
                continue

            start_ms = event.start
            end_ms = event.end
            
            # 生成文件名
            audio_filename = f"slice_{index}_{start_ms}.mp3"
            
            # 【关键】调用静态方法时，使用 类名.方法名
            # 将 output_dir 传递下去
            audio_url = StyleManager.slice_audio(
                source_audio=full_audio,
                start_ms=start_ms,
                end_ms=end_ms,
                output_filename=audio_filename,
                output_dir=output_dir 
            )

            base_data_dir = os.path.dirname(data_dir)
            
            relative_audio_url = os.path.relpath(audio_url,base_data_dir)
            # JSONPath
            json_path = f"$[{len(editor_data)}]" 

            item = {
                "name": index,
                "text": event.plaintext, # 纯文本
                "audio": relative_audio_url,      # 音频地址
                "path": json_path,       # 路径
                "start_time": start_ms / 1000.0,
                "end_time": end_ms / 1000.0,
                "_raw_start": start_ms,
                "_raw_end": end_ms
            }
            editor_data.append(item)

        logger.info(f"处理完成，生成 {len(editor_data)} 条数据")
        return editor_data
    
    
class AutoSubtitleGenerator:
    def __init__(self, subscription_key = AZURE_SERVICE_KEY, service_region = AZURE_SERVICE_REGION,lang="en-US"):
        self.speech_config = speechsdk.SpeechConfig(subscription=subscription_key, region=service_region)
        # 【修改点 1】设置为英语
        self.speech_config.speech_recognition_language = lang
        
        self.speech_config.output_format = speechsdk.OutputFormat.Detailed
        self.speech_config.request_word_level_timestamps()
        self.speech_config.set_profanity(speechsdk.ProfanityOption.Raw)

    def preprocess_audio(self, input_path):
        """音频预处理 (保持不变)"""
        logger.info(f"🔄 [1/3] Preprocessing audio: {input_path}")
        try:
            filename_only = os.path.splitext(os.path.basename(input_path))[0]
            temp_wav = f"temp_{filename_only}.wav"
            audio = AudioSegment.from_file(input_path)
            audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
            audio.export(temp_wav, format="wav")
            return temp_wav
        except Exception as e:
            logger.error(f"❌ Audio conversion failed: {e}")
            return None

    def recognize_audio(self, audio_path,need_punc=False):
        """识别音频 (已修复标点符号缺失问题)"""
        logger.info(f"☁️ [2/3] Recognizing via Azure...")
        
        audio_config = speechsdk.AudioConfig(filename=audio_path)
        recognizer = speechsdk.SpeechRecognizer(speech_config=self.speech_config, audio_config=audio_config)

        all_words_with_punc = []
        done = False

        def stop_cb(evt):
            nonlocal done
            done = True

        def recognized_cb(evt):
            if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
                # 1. 获取带标点的完整句子 (Display Text)
                display_text = evt.result.text
                print('display_text',display_text)
                
                # 2. 获取带时间戳的原始单词 (Lexical Words)
                json_result = evt.result.properties.get(speechsdk.PropertyId.SpeechServiceResponse_JsonResult)
                if json_result:
                    data = json.loads(json_result)
                    if 'NBest' in data and len(data['NBest']) > 0:
                        raw_words = data['NBest'][0]['Words']

                        if need_punc:
                            raw_words_with_punc = self._merge_punctuation(raw_words, display_text)
                            for wp in raw_words_with_punc:
                                all_words_with_punc.append({
                                    "word": wp['word'], # 这里现在包含标点了，例如 "你好，"
                                    "start_ticks": wp['Offset'],
                                    "end_ticks": wp['Offset'] + wp['Duration']
                                })

                        else:
                            for wp in raw_words:
                                all_words_with_punc.append({
                                    "word": wp['Word'], # 这里现在包含标点了，例如 "你好，"
                                    "start_ticks": wp['Offset'],
                                    "end_ticks": wp['Offset'] + wp['Duration']
                                })

        recognizer.recognized.connect(recognized_cb)
        recognizer.session_stopped.connect(stop_cb)
        recognizer.canceled.connect(stop_cb)

        recognizer.start_continuous_recognition()
        while not done:
            time.sleep(0.5)
        recognizer.stop_continuous_recognition()
        
        logger.info(f"✅ Recognition complete. Extracted {len(all_words_with_punc)} words.")
        return all_words_with_punc


    def _merge_punctuation(self, raw_words, display_text):
        """
        修正版算法：
        1. 遇到 ITN (如 1.5) 时，将多个单词合并为一个，并累加时长。
        2. 【关键】彻底跳过被合并的中间词，不产生空字符串，解决多余空格问题。
        3. 标点截取使用 isalnum 熔断，防止粘连。
        """
        if not raw_words: return []
        
        merged_words = []
        search_index = 0
        
        # 辅助查找函数
        def find_word_index(text, word, start_idx):
            idx = text.find(word, start_idx)
            if idx == -1:
                idx = text.lower().find(word.lower(), start_idx)
            return idx

        i = 0
        while i < len(raw_words):
            word_obj = raw_words[i]
            word_str = word_obj['Word']
            
            # 1. 尝试在 Display Text 中查找当前单词
            found_idx = find_word_index(display_text, word_str, search_index)
            
            # ========================================================
            # 情况 A: 匹配失败 -> 触发合并逻辑 (处理 1.5)
            # ========================================================
            if found_idx == -1:
                anchor_idx = -1
                match_next_k = -1
                
                # 向后前瞻，寻找锚点 (最多看5个词)
                for k in range(1, 6):
                    if i + k >= len(raw_words): break
                    next_raw_word = raw_words[i + k]['Word']
                    next_found_idx = find_word_index(display_text, next_raw_word, search_index)
                    
                    if next_found_idx != -1:
                        anchor_idx = next_found_idx
                        match_next_k = k
                        break
                
                if anchor_idx != -1:
                    # 找到了锚点！
                    # 截取范围内的所有文本作为合并后的新词 (即 "1.5")
                    special_text = display_text[search_index : anchor_idx].strip()
                    
                    new_word_obj = word_obj.copy()
                    new_word_obj['word'] = special_text
                    
                    # 【核心 1】修正时长：Duration = (最后一个被合并词的结束) - (第一个词的开始)
                    # 最后一个被合并的词索引是: i + match_next_k - 1
                    last_merged_word = raw_words[i + match_next_k - 1]
                    
                    start_ticks = word_obj['Offset']
                    end_ticks = last_merged_word['Offset'] + last_merged_word['Duration']
                    new_word_obj['Duration'] = end_ticks - start_ticks
                    
                    merged_words.append(new_word_obj)
                    
                    # 【核心 2】跳过索引：直接跳过中间的词 (point, five)
                    # 这样列表中就不会出现空字符串，拼接时也就不会有多余的空格了
                    i += match_next_k 
                    search_index = anchor_idx
                else:
                    # 没找到锚点，不得不保留原样
                    new_word_obj = word_obj.copy()
                    new_word_obj['word'] = word_str
                    merged_words.append(new_word_obj)
                    i += 1

            # ========================================================
            # 情况 B: 匹配成功 (正常单词)
            # ========================================================
            else:
                real_word = display_text[found_idx : found_idx + len(word_str)]
                end_idx = found_idx + len(word_str)
                
                # 向后截取标点 (遇到字母数字立即熔断)
                punctuation_buffer = ""
                current_ptr = end_idx
                while current_ptr < len(display_text):
                    char = display_text[current_ptr]
                    if char.isalnum(): break
                    punctuation_buffer += char
                    current_ptr += 1
                
                clean_punctuation = punctuation_buffer.strip()
                
                new_word_obj = word_obj.copy()
                new_word_obj['word'] = real_word + clean_punctuation
                
                merged_words.append(new_word_obj)
                
                i += 1
                search_index = current_ptr
                
        return merged_words


    def generate_ass(self, all_words, output_file=None):
        logger.info(f"🎬 [3/3] Generating ASS subtitle: {output_file}")
        
        # --- 【修改点 2】英文参数配置 ---
        MAX_CHARS = 40            # 英文字幕一般一行 40-50 个字符
        MAX_PAUSE_TICKS = 6000000 # 0.5秒停顿
        # 英文标点断句
        SPLIT_PUNCTUATIONS = (",",".", "?", "!", ";") 

        subs = pysubs2.SSAFile()
        subs.info['Title'] = 'Auto Generated Subtitles'
        subs.info['ScriptType'] = 'v4.00+'
        subs.info['PlayResX'] = str(VideoFormat.Width)
        subs.info['PlayResY'] = str(VideoFormat.Height)
        subs.info['WrapStyle'] = '0'
        subs.info['ScaledBorderAndShadow'] = 'yes'
        subs.info['YCbCr Matrix'] = 'None'

        # --- 【修改点 3】英文字体样式 ---
        data_dir = get_data_dir()
        subtitle_front_style_path = os.path.join(data_dir,'paraments_info','subtitle','frontstyle.json')
        styles = StyleManager.load_from_file(subtitle_front_style_path)

        subs.styles[styles.name] = styles

        current_line_words = []

        for i, word in enumerate(all_words):
            word_text = word['word'] # 确保这里是通过 _merge_punctuation 处理过带标点的
            
            # --- 1. 异常数据清洗 ---
            # 如果这个词本身就巨长(超过MAX)，说明Azure返回了一整坨，直接当做新的一行
            if len(word_text) > MAX_CHARS:
                # 先保存之前的缓存
                if current_line_words:
                    self._add_event(subs, current_line_words)
                    current_line_words = []
                # 把这个巨型词单独成行
                self._add_event(subs, [word])
                continue

            # --- 2. 正常逻辑判断 ---
            need_new_line = False
            
            # A. 检查缓存是否为空
            if current_line_words:
                prev_word = current_line_words[-1]
                
                # B. 停顿检测
                if (word['start_ticks'] - prev_word['end_ticks']) > MAX_PAUSE_TICKS:
                    need_new_line = True
                
                # C. 长度检测 (当前行长度 + 空格 + 新词长度)
                current_len = sum(len(w['word']) for w in current_line_words) + len(current_line_words)
                if current_len + 1 + len(word_text) > MAX_CHARS:
                    need_new_line = True

            # D. 执行换行
            if need_new_line:
                self._add_event(subs, current_line_words)
                current_line_words = []

            # E. 加入当前词
            current_line_words.append(word)

            # --- 3. 后置检查：标点符号断句 ---
            # 只有当单词【以标点结尾】时才切分，防止 "1.5" 被切开
            # 使用 endswith 匹配元组
            if word_text.endswith(SPLIT_PUNCTUATIONS):
                self._add_event(subs, current_line_words)
                current_line_words = []

        # 处理残留
        if current_line_words:
            self._add_event(subs, current_line_words)

        self._save_formatted_ass(subs, output_file)


    def _add_event(self, subs, word_list):
        if not word_list: return
        
        start_ms = int(word_list[0]['start_ticks'] / 10000)
        end_ms = int(word_list[-1]['end_ticks'] / 10000)
        
        # --- 【修改点 4】核心修复：英文必须用空格拼接 ---
        # 提取单词文本
        words = [w['word'] for w in word_list]
        
        # 使用空格 join
        text = " ".join(words)
        
        # 【可选】清理一下多余的标点，如果你不想显示句号
        # text = text.strip(".?,!") 

        event = SSAEvent(start=start_ms, end=end_ms, text=text)
        event.style = "Default"
        subs.events.append(event)


    def _save_formatted_ass(self, subs, output_file):
        """格式化修复 (保持不变)"""
        ass_content = subs.to_string(format_="ass")
        if "[V4+ Styles]" in ass_content:
            ass_content = ass_content.replace("[V4+ Styles]", "\n[V4+ Styles]")
        if "[Events]" in ass_content:
            ass_content = ass_content.replace("[Events]", "\n[Events]")

        with open(output_file, "w", encoding="utf-8-sig") as f:
            f.write(ass_content)
        logger.info(f"🎉 Subtitle saved: {output_file}")


def detect_global_change(new_list, old_list):
    """
    将列表中的所有文本拼接成一句完整的话进行对比。
    :return: (is_changed: bool, full_text: str)
             返回一个元组：(是否修改了, 拼接后的新文本)
    """
    
    # 1. 提取并拼接新文本
    # 使用 " " (空格) 连接，防止单词粘连。strip()用于去除单个片段首尾多余空格
    new_full_text = " ".join([str(item.get('text', '')).strip() for item in new_list])
    
    # 2. 提取并拼接旧文本
    old_full_text = " ".join([str(item.get('text', '')).strip() for item in old_list])

    # 3. 对比
    # 移除多余的连续空格，避免因为手误多打一个空格导致判断不一致
    # 比如 "Hello  World" 和 "Hello World" 应该视为相同
    import re
    clean_new = re.sub(r'\s+', ' ', new_full_text).strip()
    clean_old = re.sub(r'\s+', ' ', old_full_text).strip()

    is_changed = (clean_new != clean_old)

    if is_changed:
        print("🔴 检测到全文有变动！")
        print(f"旧: {clean_old[:50]}...")
        print(f"新: {clean_new[:50]}...")
    else:
        print("🟢 全文无实质变动")

    return is_changed, clean_new


def get_data_dir():
    data_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    data_dir = os.path.join(data_dir,'data')
    return data_dir


def get_ass_style_info(subtitle_front_style = None):
    """提供前端需要使用到字幕样式信息"""
    if not subtitle_front_style:
        data_dir = get_data_dir()
        subtitle_front_style = os.path.join(data_dir,'paraments_info','subtitle','frontstyle.json')
    front_ass_body = json.load(open(subtitle_front_style,'r',encoding='utf-8'))
    generate_ui_config = StyleManager.generate_ui_config(front_ass_body)
    logger.info(f"成功加载字幕样式信息并编码返回给前端")
    return generate_ui_config


def update_ass_style_info(front_json_data,subtitle_front_style = None):
    """将前端返回的字段更新到字幕样式信息中"""
    if not subtitle_front_style:
        data_dir = get_data_dir()
        subtitle_front_style = os.path.join(data_dir,'paraments_info','subtitle','frontstyle.json')
    update_config = StyleManager.convert_to_nested_config(front_json_data)
    StyleManager.update_config(subtitle_front_style, update_config)
    logger.info(f"成功将字幕样式信息跟新到{subtitle_front_style}中")



def audio2ass(audio_file, save_file = None,need_punc=False):
    """根据识别结果生成ASS字幕文件"""
    
    data_dir = get_data_dir()
    base_name = os.path.splitext(os.path.basename(audio_file))[0]
    if not save_file:
        save_dir = os.path.join(data_dir,'result_video','subtitles')
        os.makedirs(save_dir, exist_ok=True)
        output_ass = os.path.join(save_dir,f"{uuid.uuid4()}.ass")
    else:
        save_dir = os.path.join(data_dir,'result_video',save_file,'subtitles')
        os.makedirs(save_dir, exist_ok=True)
        output_ass = os.path.join(save_dir,f"{uuid.uuid4()}.ass")

    generator = AutoSubtitleGenerator()
    temp_wav = generator.preprocess_audio(audio_file)
    try:
        if temp_wav:
            words_data = generator.recognize_audio(temp_wav,need_punc)
            logger.info(f"成功识别了单词数据，开始进程字幕生成！")
            if words_data:
                generator.generate_ass(words_data, output_ass)
                logger.info(f"成功生成ASS字幕文件: {output_ass}")
            # editor_data = StyleManager.ass_to_editor_json(output_ass,temp_wav)
            relative_path = os.path.relpath(output_ass, data_dir)
            return relative_path
    except Exception as e:
        logger.error(f"生成ASS字幕文件时出错: {e}")
    finally:
        if os.path.exists(temp_wav):
            os.remove(temp_wav)


def video2ass(video_file, save_file = None,need_punc=False):
    """
    将视频转换为ASS字幕文件
    流程：视频 -> 提取临时音频 -> 调用 audio2ass -> 生成字幕 -> 删除临时音频
    """
    base_name = os.path.splitext(os.path.basename(video_file))[0]
    temp_audio_path = f"{base_name}.wav"
    try:
        logger.info(f"正在从视频中提取音频: {video_file}")
        
        audio = AudioSegment.from_file(video_file)
        audio.export(temp_audio_path, format="wav")
        logger.info(f"音频提取完成，保存为: {temp_audio_path}")
        logger.info("开始进行语音识别与字幕生成...")
        ass_file = audio2ass(temp_audio_path, save_file,need_punc)
        # editor_data = StyleManager.ass_to_editor_json(output_ass,temp_audio_path)
        # relative_path = os.path.relpath(output_ass, data_dir)
        return ass_file

    except Exception as e:
        logger.error(f"视频转字幕失败: {e}")
        
    finally:
        if os.path.exists(temp_audio_path):
            try:
                os.remove(temp_audio_path)
                logger.info(f"临时音频文件已清理: {temp_audio_path}")
            except Exception as e:
                logger.warning(f"清理临时文件失败: {e}")


@tool
def audio2ass_tool(audio_file, save_file = None,need_punc=False):
    """
    将音频文件识别后转换为ASS字幕文件
    :param audio_file: 音频文件路径，相对于data目录
    :param save_file: 字幕文件保存目录名称,默认为None,不需要赋值
    :param need_punc: 是否需要添加标点符号
    :return:
    :param relative_path: 字幕文件相对路径
    """
    audio_file = os.path.join(get_data_dir(),audio_file)
    ass_file = audio2ass(audio_file, save_file,need_punc)
    return ass_file

@tool
def video2ass_tool(video_file, save_file = None,need_punc=False):
    """
    将视频文件识别后转换为ASS字幕文件
    :param video_file: 视频文件路径，相对于data目录
    :param save_file: 字幕文件保存目录名称,默认为None,不需要赋值
    :param need_punc: 是否需要添加标点符号
    :return:
    :param relative_path: 字幕文件相对路径
    """
    video_file = os.path.join(get_data_dir(),video_file)
    ass_file = video2ass(video_file, save_file,need_punc)
    return ass_file



#需要继续完善到agent中
# @tool
# def update_subtitle_style(update_config: dict):
#     """
#     更新字幕样式
#     :param update_config: 包含更新信息的字典
#     """
#     update_ass_style_info(update_config)



# ==========================================
if __name__ == "__main__":


    INPUT_AUDIO = r"C:\Users\ddf\Desktop\zzc\code\seo_video_generate_main\seo_video_generate\services\temp_EnergeticMale1.wav" # 确保这里是英文音频
    OUTPUT_ASS = r"C:\Users\ddf\Desktop\zzc\code\seo_video_generate_main\data\test_video\english_subtitle.ass"
    ##########################################字幕生成测试###############################################
    # generator = AutoSubtitleGenerator(AZURE_SERVICE_KEY, AZURE_SERVICE_REGION)
    
    # # 1. 转码
    # temp_wav = generator.preprocess_audio(INPUT_AUDIO)
    
    # if temp_wav:
    #     try:
    #         # 2. 识别
    #         words_data = generator.recognize_audio(temp_wav)
    #         # 3. 生成
    #         if words_data:
    #             generator.generate_ass(words_data, OUTPUT_ASS)
    #     finally:
    #         if os.path.exists(temp_wav):
    #             os.remove(temp_wav)
    
    #############################################字幕更新测试###############################################
    # json_info = r'C:\Users\ddf\Desktop\zzc\code\seo_video_generate_main\seo_video_generate\data\paraments_info\subtitle\frontstyle.json'
    # result = StyleManager.load_from_file(json_info)
    # print('result',result.name,result.fontname,result.fontsize)
    # json_data = json.load(open(json_info, 'r', encoding='utf-8'))
    # generate_ui_config = StyleManager.generate_ui_config(json_data)
    # print('generate_ui_config',generate_ui_config)
    # print(10*"/n")
    # nested_config = StyleManager.convert_to_nested_config(generate_ui_config)
    # print('nested_config',nested_config)

    # StyleManager.update_config(json_info, nested_config)

    ###################################################测试接口调用##############################################
    import uuid
    json_info = r'C:\Users\ddf\Desktop\zzc\code\seo_video_generate_main\seo_video_generate\data\paraments_info\subtitle\frontstyle.json'
    audio_path = r"C:\Users\ddf\Desktop\zzc\code\seo_video_generate_main\data\video_cut_test\test.mp4"
    ass_save_path = r'C:\Users\ddf\Desktop\zzc\code\seo_video_generate_main\data\video_cut_test\test.ass'
    video_ass_save_path = r'C:\Users\ddf\Desktop\zzc\code\seo_video_generate_main\data\video_cut_test\english_subtitle4.ass'
    video_path = r"C:\Users\ddf\Desktop\zzc\code\seo_video_generate_main\seo_video_generate\data\gen_video_result\miami-3442-to-chicago-3546\question\video\question_res.mp4"
    front_ass_body = get_ass_style_info()
    save_file = "测试12.18"
    print('front_ass_body',front_ass_body)
    # update_ass_style_info(front_ass_body)
    # print('front_ass_body',front_ass_body)
    # editor_data = audio2ass(audio_path, save_file,need_punc=True)
    # print('editor_data',editor_data)
    video_editor_data = video2ass(video_path, save_file)
    print('video_editor_data',video_editor_data)


