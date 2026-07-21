"""核心 Reflex State：聊天历史 / 流式处理 / 视频资产管理。

关键点：
- send 为 async generator 事件处理器，每次 yield 把当前 state 经 WebSocket 推给前端。
- 不直接 mutate 嵌套 dict（避免 Reflex 检测不到），统一用「重建列表再赋值」。
- 从 agent 工具结果里解析出生成文件路径，转成可访问的 URL，加入资产列表。
"""
import ast
import json
import os
from typing import Any
from urllib.parse import quote

import reflex as rx

from . import api
from .config import DATA_BASE_URL

# 文件扩展名 → 资产类型。通过扩展名识别，比固定字段名更健壮，
# 能覆盖 tool_return / serach_result / down_images_path 等各种返回结构。
_MEDIA_EXTS = {
    ".mp4": "video", ".mov": "video", ".avi": "video",
    ".mkv": "video", ".webm": "video", ".m4v": "video",
    ".mp3": "audio", ".wav": "audio", ".aac": "audio",
    ".m4a": "audio", ".flac": "audio", ".ogg": "audio",
    ".jpg": "image", ".jpeg": "image", ".png": "image",
    ".gif": "image", ".webp": "image", ".bmp": "image",
    ".srt": "subtitle", ".ass": "subtitle", ".vtt": "subtitle",
}


def _to_url(path: str) -> str:
    """把 agent 返回的相对路径转成浏览器可访问的 URL。

    agent 工具返回相对于 data/ 的路径（如 result_video/clip_video/x.mp4），
    server.py 把 <data> 目录挂载到 /data，故 URL = DATA_BASE_URL/data/<相对路径>。
    文件名可能含空格/中文，做 URL 编码（保留 '/'）。
    """
    p = path.replace("\\", "/").strip()
    # 兼容偶发带 data/ 前缀的写法
    if p.startswith("data/"):
        p = p[len("data/"):]
    return f"{DATA_BASE_URL}/data/{quote(p, safe='/')}"


def _kind_for(path: str) -> str | None:
    """按扩展名判断资产类型，非媒体文件返回 None。"""
    ext = os.path.splitext(path.strip())[1].lower()
    return _MEDIA_EXTS.get(ext)


def _walk_paths(data: Any, found: list) -> None:
    """递归遍历任意嵌套结构（dict/list/str），收集 (路径, 类型)。"""
    if isinstance(data, str):
        s = data.strip()
        # 字符串本身可能是被字符串化的 list/dict（如 serach_result）
        if s[:1] in "[{":
            try:
                _walk_paths(ast.literal_eval(s), found)
                return
            except Exception:
                pass
        kind = _kind_for(s)
        if kind:
            found.append((s, kind))
    elif isinstance(data, dict):
        for v in data.values():
            _walk_paths(v, found)
    elif isinstance(data, (list, tuple)):
        for v in data:
            _walk_paths(v, found)


def _extract_assets(text: str) -> list:
    """尝试把文本解析成结构化数据或从普通文本中提取媒体文件路径。

    支持两种模式：
    1. 结构化数据：tools step 产出的字符串化 dict/list（如 "{'success': True, ...}"）
    2. 普通文本：从自然语言回复中提取路径（如 "result_video\\clip_video\\video.mp4"）
    """
    text = (text or "").strip()
    if not text:
        return []

    assets = []
    seen = set()

    # 模式1：尝试解析结构化数据
    if text[0] in "{[":
        data: Any = None
        try:
            data = ast.literal_eval(text)
        except Exception:
            try:
                data = json.loads(text)
            except Exception:
                pass

        if data:
            found: list = []
            _walk_paths(data, found)

            for path, kind in found:
                url = _to_url(path)
                if url in seen:
                    continue
                seen.add(url)
                assets.append({
                    "name": os.path.basename(path.replace("\\", "/")) or path,
                    "url": url,
                    "kind": kind,
                })

    # 模式2：从普通文本中提取路径（使用正则匹配媒体文件扩展名）
    import re
    # 匹配类似 "result_video\clip_video\file.mp4" 或 "data/images/photo.jpg" 的路径
    pattern = r'(?:[\w\-]+[/\\])+[\w\-]+\.(' + '|'.join(
        ext.lstrip('.') for ext in _MEDIA_EXTS.keys()
    ) + r')'

    matches = re.findall(pattern, text, re.IGNORECASE)
    if matches:
        # 重新提取完整路径
        for match in re.finditer(pattern, text, re.IGNORECASE):
            path = match.group(0)
            kind = _kind_for(path)
            if not kind:
                continue

            url = _to_url(path)
            if url in seen:
                continue
            seen.add(url)
            assets.append({
                "name": os.path.basename(path.replace("\\", "/")) or path,
                "url": url,
                "kind": kind,
            })

    return assets


def _format_args(args: Any) -> str:
    """格式化 tool_call 的 args 为可读字符串。"""
    if args is None:
        return ""
    if isinstance(args, (dict, list)):
        try:
            return json.dumps(args, ensure_ascii=False, indent=2)
        except Exception:
            return str(args)
    return str(args)


# 工具名称到步骤的映射（用于进度跟踪）
_TOOL_STEP_MAPPING = {
    # 通用视频生成流程 (8步)
    "get_video_scripts": (1, 8, "📝 生成视频文案"),
    "text_to_speech_tool": (2, 8, "🎙️ 转换为语音"),
    "get_script_text_time": (3, 8, "⏱️ 分析时间轴"),
    "video_serach_and_clip_tools": (4, 8, "🔍 检索视频素材"),
    "merge_videos": (5, 8, "🎬 合并素材视频"),
    "audio2ass_tool": (6, 8, "💬 生成字幕文件"),
    "add_audio_to_video": (7, 8, "🔊 添加音频轨道"),
    "add_hardsub_with_offset": (8, 8, "✨ 嵌入字幕完成"),

    # 爆款视频仿写流程
    "ai_copywrite_tool": (1, 8, "📋 分析爆款视频"),
    "get_copywrite_scripts": (2, 8, "✍️ 仿写视频文案"),

    # 素材检索流程
    "img_search_tool_v2": (1, 3, "🖼️ 搜索图片素材"),
    "image_to_video_v2": (2, 3, "🎞️ 图片转视频"),
    "search_videos": (1, 2, "🎥 搜索视频素材"),

    # 视频剪辑流程
    "clip_video": (1, 2, "✂️ 裁剪视频片段"),
    "crop_video": (1, 2, "📐 裁剪视频画面"),

    # 音频处理流程
    "clip_audio": (1, 2, "🎵 裁剪音频片段"),

    # 字幕处理流程
    "asr_audio_file": (1, 2, "🎤 语音识别转字幕"),

    # 结构化输出
    "structure_tool_output": (0, 0, "✅ 完成处理"),
}


class State(rx.State):
    # 聊天消息：{role:'user'|'agent', kind:'text'|'tool'|'error',
    #          content:str, tool_name:str, args:str}
    chat_messages: list[dict] = []
    input_text: str = ""
    processing: bool = False

    # 视频资产：{name:str, url:str, kind:'video'|'audio'|'image'|'subtitle'|'file'}
    video_assets: list[dict] = []
    # 当前预览资产
    current_video_url: str = ""
    current_kind: str = ""

    # agent 连接状态
    agent_online: bool = False
    agents: list[dict] = []

    # 进度指示（拆分为单独字段以兼容 Reflex 的响应式系统）
    progress_current: int = 0
    progress_total: int = 0
    progress_step: str = ""
    progress_percentage: int = 0

    @rx.var
    def show_progress(self) -> bool:
        """计算属性：是否显示进度条"""
        return self.processing and self.progress_total > 0

    @rx.var
    def progress_text(self) -> str:
        """计算属性：进度文本 (如 3/8)"""
        return f"{self.progress_current}/{self.progress_total}"

    @rx.var
    def progress_width(self) -> str:
        """计算属性：进度条宽度百分比"""
        return f"{self.progress_percentage}%"

    # ---- 内部辅助：安全更新某条 agent 文本消息 ----
    def _set_msg_content(self, idx: int, content: str) -> None:
        msgs = list(self.chat_messages)
        if 0 <= idx < len(msgs):
            msgs[idx] = {**msgs[idx], "content": content}
        self.chat_messages = msgs

    # ---- 事件：输入框文本更新 ----
    def set_input_text(self, value: str):
        self.input_text = value

    # ---- 事件：键盘事件处理 ----
    @rx.event
    async def handle_key(self, key: str):
        # 只有在非处理状态、按 Enter、且输入框有内容时才发送
        if key == "Enter" and not self.processing and self.input_text.strip():
            # 必须把内部生成器的每次 yield 透传出去，
            # Reflex 才会在每一步把最新 state 推给前端（否则界面无任何反应）。
            async for _ in self._do_send():
                yield

    # ---- 内部方法：实际发送逻辑 ----
    async def _do_send(self):
        """内部发送方法，被 handle_key 和 send 调用"""
        query_text = self.input_text.strip()
        if not query_text or self.processing:
            return

        self.input_text = ""
        self.processing = True
        # 重置进度
        self.progress_current = 0
        self.progress_total = 0
        self.progress_step = "初始化..."
        self.progress_percentage = 0
        # 追加用户消息 + agent 占位消息
        self.chat_messages = self.chat_messages + [
            {"role": "user", "kind": "text", "content": query_text},
            {"role": "agent", "kind": "text", "content": ""},
        ]
        agent_idx = len(self.chat_messages) - 1
        yield

        try:
            async for event in api.stream_query(query_text):
                etype = event.get("type")

                if etype == "start":
                    self._set_msg_content(agent_idx, "思考中…")
                    self.progress_current = 0
                    self.progress_total = 0
                    self.progress_step = "分析任务中..."
                    self.progress_percentage = 0
                    yield

                elif etype == "text":
                    text = event.get("text", "")
                    assets = _extract_assets(text)
                    if assets:
                        # 工具结果：提取资产
                        self.video_assets = self.video_assets + assets
                        # 自动预览：优先视频，其次图片，最后音频
                        for kind_pref in ("video", "image", "audio"):
                            picked = next(
                                (a for a in reversed(assets) if a["kind"] == kind_pref),
                                None,
                            )
                            if picked:
                                self.current_video_url = picked["url"]
                                self.current_kind = picked["kind"]
                                break
                        yield
                    else:
                        # agent 正文：追加到当前 agent 文本消息
                        cur = self.chat_messages[agent_idx]["content"]
                        if cur == "思考中…":
                            cur = ""
                        self._set_msg_content(agent_idx, cur + text)
                        yield

                elif etype == "tool_call":
                    tool_name = event.get("tools_name", "")

                    # 更新进度
                    if tool_name in _TOOL_STEP_MAPPING:
                        current, total, step_name = _TOOL_STEP_MAPPING[tool_name]
                        percentage = int((current / total * 100)) if total > 0 else 0
                        self.progress_current = current
                        self.progress_total = total
                        self.progress_step = step_name
                        self.progress_percentage = percentage

                    self.chat_messages = self.chat_messages + [{
                        "role": "agent",
                        "kind": "tool",
                        "tool_name": tool_name,
                        "args": _format_args(event.get("args")),
                    }]
                    yield

                elif etype == "error":
                    self.chat_messages = self.chat_messages + [{
                        "role": "agent",
                        "kind": "error",
                        "content": event.get("error", "未知错误"),
                    }]
                    # 重置进度
                    self.progress_current = 0
                    self.progress_total = 0
                    self.progress_step = ""
                    self.progress_percentage = 0
                    yield

                elif etype == "done":
                    # 完成时设置进度为100%
                    if self.progress_total > 0:
                        self.progress_current = self.progress_total
                        self.progress_step = "✅ 处理完成"
                        self.progress_percentage = 100
                    yield
                # 其它：忽略

        except Exception as e:
            self.chat_messages = self.chat_messages + [{
                "role": "agent",
                "kind": "error",
                "content": f"请求失败: {e}",
            }]
            # 重置进度
            self.progress_current = 0
            self.progress_total = 0
            self.progress_step = ""
            self.progress_percentage = 0
            yield
        finally:
            self.processing = False
            yield

    # ---- 事件：发送按钮点击 ----
    @rx.event
    async def send(self):
        # 透传内部生成器的 yield，确保处理过程中界面实时更新
        async for _ in self._do_send():
            yield

    # ---- 事件：选择资产预览 ----
    @rx.event
    def select_video(self, url: str):
        self.current_video_url = url
        # 根据资产列表回填类型，供预览区选择正确的渲染方式
        for a in self.video_assets:
            if a["url"] == url:
                self.current_kind = a["kind"]
                break

    # ---- 事件：健康检查（页面加载时触发）----
    @rx.event
    async def check_health(self):
        self.agent_online = await api.health()
        if self.agent_online:
            self.agents = await api.list_agents()
