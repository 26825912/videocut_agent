"""右侧聊天窗：消息列表（流式 + 工具卡片）+ 输入框。"""
import reflex as rx

from ..state import State
from .tool_card import tool_card


def _text_bubble(msg) -> rx.Component:
    """普通文本气泡，用户靠右、agent 靠左。"""
    is_user = msg["role"] == "user"
    return rx.box(
        rx.markdown(msg["content"]),
        bg=rx.cond(is_user, "#3b82f6", "#f1f5f9"),
        color=rx.cond(is_user, "white", "#0f172a"),
        padding="0.6em 0.9em",
        border_radius="12px",
        max_width="85%",
        align_self=rx.cond(is_user, "flex-end", "flex-start"),
    )


def _error_bubble(msg) -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.text("⚠", color="#dc2626", font_size="0.9em"),
            rx.text(msg["content"], color="#dc2626", font_size="0.9em"),
            spacing="1",
        ),
        bg="#fef2f2",
        border="1px solid #fecaca",
        border_radius="10px",
        padding="0.5em 0.8em",
        max_width="85%",
        align_self="flex-start",
    )


def message_bubble(msg) -> rx.Component:
    """单条消息渲染：按 kind 分发。"""
    return rx.cond(
        msg["kind"] == "tool",
        tool_card(msg),
        rx.cond(
            msg["kind"] == "error",
            _error_bubble(msg),
            _text_bubble(msg),
        ),
    )


def _progress_bar() -> rx.Component:
    """进度条组件：显示当前处理步骤和进度百分比"""
    return rx.cond(
        State.show_progress,
        rx.vstack(
            rx.hstack(
                rx.text(
                    State.progress_step,
                    font_size="0.85em",
                    font_weight="500",
                    color="#6366f1",
                ),
                rx.spacer(),
                rx.text(
                    State.progress_text,
                    font_size="0.8em",
                    color="#64748b",
                ),
                width="100%",
                align_items="center",
            ),
            rx.box(
                rx.box(
                    width=State.progress_width,
                    height="100%",
                    bg="linear-gradient(90deg, #6366f1 0%, #8b5cf6 100%)",
                    border_radius="4px",
                    transition="width 0.3s ease",
                ),
                width="100%",
                height="6px",
                bg="#e2e8f0",
                border_radius="4px",
                overflow="hidden",
            ),
            width="100%",
            spacing="1",
            padding="0.8em",
            bg="#f8fafc",
            border="1px solid #e2e8f0",
            border_radius="8px",
            margin_bottom="0.5em",
        ),
    )


def chat() -> rx.Component:
    return rx.vstack(
        rx.heading("💬 聊天", size="4"),
        rx.text(
            "描述你想创作的视频，Agent 会调用智能体完成创作与剪辑",
            font_size="0.8em",
            color="#94a3b8",
        ),
        # 进度条（仅在处理时显示）
        _progress_bar(),
        # 消息列表（可滚动）
        rx.scroll_area(
            rx.vstack(
                rx.foreach(State.chat_messages, message_bubble),
                width="100%",
                align_items="flex_start",
                spacing="2",
                padding="0.5em",
            ),
            width="100%",
            min_height="0",
            flex="1",
        ),
        # 输入区
        rx.hstack(
            rx.input(
                placeholder="例如：帮我生成一个关于如何学习的15秒视频",
                value=State.input_text,
                on_change=State.set_input_text,
                on_key_down=State.handle_key,
                disabled=State.processing,
                flex="1",
            ),
            rx.button(
                rx.cond(
                    State.processing,
                    rx.hstack(
                        rx.spinner(size="2"),
                        rx.text("处理中"),
                        spacing="2",
                        align_items="center",
                    ),
                    rx.hstack(
                        rx.icon("send", size=16),
                        rx.text("发送"),
                        spacing="2",
                        align_items="center",
                    ),
                ),
                on_click=State.send,
                disabled=State.processing,
            ),
            width="100%",
            align_items="center",
        ),
        width="100%",
        height="100%",
        padding="1em",
        spacing="3",
        align_items="start",
    )
