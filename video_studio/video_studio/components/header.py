"""顶栏：标题 + agent 连接状态 + 刷新。"""
import reflex as rx

from ..state import State


def header() -> rx.Component:
    return rx.hstack(
        rx.heading("🎬 Video Agent Studio", size="6"),
        rx.spacer(),
        rx.hstack(
            rx.box(
                width="10px",
                height="10px",
                border_radius="50%",
                bg=rx.cond(State.agent_online, "#22c55e", "#ef4444"),
            ),
            rx.text(
                rx.cond(State.agent_online, "Agent 在线", "Agent 离线"),
                font_size="0.9em",
                color="#64748b",
            ),
            rx.button(
                "刷新",
                on_click=State.check_health,
                variant="soft",
                size="1",
            ),
            spacing="2",
            align_items="center",
        ),
        width="100%",
        padding="0.8em 1.2em",
        bg="white",
        border_bottom="1px solid #e2e8f0",
        align_items="center",
    )
