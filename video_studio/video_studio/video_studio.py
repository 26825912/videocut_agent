"""Video Agent Studio —— Reflex 应用入口。

布局：顶栏 + 左侧视频工作区 + 右侧聊天窗。
"""
import reflex as rx

from .state import State
from .styles import global_style
from .components.header import header
from .components.chat import chat
from .components.video_workspace import video_workspace


def index() -> rx.Component:
    return rx.vstack(
        header(),
        rx.hstack(
            rx.box(video_workspace(), flex="3", min_w="0", height="100%"),
            rx.box(width="1px", bg="#e2e8f0", height="100%"),
            rx.box(chat(), flex="2", min_w="0", height="100%"),
            width="100%",
            height="100%",
            spacing="0",
            align_items="stretch",
        ),
        width="100%",
        height="100vh",
        spacing="0",
        bg="#f8fafc",
    )


app = rx.App(style=global_style)
app.add_page(
    index,
    route="/",
    title="Video Agent Studio",
    on_load=State.check_health,
)
