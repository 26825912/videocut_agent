"""左侧视频工作区：播放器 + 下载 + 资产列表。"""
import reflex as rx

from ..state import State


def _asset_icon(kind) -> rx.Component:
    return rx.cond(kind == "video", "🎬",
        rx.cond(kind == "audio", "🎵",
            rx.cond(kind == "image", "🖼",
                rx.cond(kind == "subtitle", "📝", "📄"))))


def _asset_row(asset) -> rx.Component:
    # 视频/图片/音频均可点击预览
    previewable = (asset["kind"] == "video") | (asset["kind"] == "image") | (asset["kind"] == "audio")
    return rx.hstack(
        rx.text(_asset_icon(asset["kind"]), font_size="1.1em"),
        rx.text(
            asset["name"],
            no_of_lines=1,
            flex="1",
            font_size="0.85em",
        ),
        rx.cond(
            previewable,
            rx.icon("eye", size=12, color="#6366f1"),
            rx.box(),
        ),
        cursor="pointer",
        on_click=State.select_video(asset["url"]),
        padding="0.4em 0.6em",
        border_radius="6px",
        width="100%",
        align_items="center",
        spacing="2",
        _hover={"bg": "#f1f5f9"},
    )


def _empty_state() -> rx.Component:
    return rx.center(
        rx.vstack(
            rx.icon("clapperboard", size=44, color="#94a3b8"),
            rx.text("生成的视频将显示在这里", color="#475569", font_weight="bold"),
            rx.text(
                "通过右侧聊天让 Agent 创作 / 剪辑视频",
                color="#94a3b8",
                font_size="0.85em",
            ),
            spacing="2",
            align_items="center",
        ),
        width="100%",
        min_height="300px",
        bg="#f8fafc",
        border="1px dashed #cbd5e1",
        border_radius="12px",
    )


def _preview() -> rx.Component:
    """根据当前资产类型选择渲染方式：视频 / 图片 / 音频。"""
    return rx.cond(
        State.current_kind == "image",
        rx.image(
            src=State.current_video_url,
            width="100%",
            max_height="480px",
            object_fit="contain",
            border_radius="8px",
        ),
        rx.cond(
            State.current_kind == "audio",
            rx.audio(
                src=State.current_video_url,
                controls=True,
                width="100%",
                height="54px",
            ),
            rx.video(src=State.current_video_url, controls=True, width="100%"),
        ),
    )


def _player() -> rx.Component:
    return rx.vstack(
        _preview(),
        rx.hstack(
            rx.spacer(),
            rx.link(
                rx.button(
                    rx.icon("download", size=14),
                    "下载",
                    variant="soft",
                    size="1",
                ),
                href=State.current_video_url,
                is_external=True,
            ),
            width="100%",
        ),
        width="100%",
        spacing="2",
    )


def video_workspace() -> rx.Component:
    return rx.vstack(
        rx.heading("🎞 视频工作区", size="4"),
        rx.cond(
            State.current_video_url == "",
            _empty_state(),
            _player(),
        ),
        rx.divider(margin="0.5em 0"),
        rx.hstack(
            rx.heading("资产列表", size="3"),
            rx.spacer(),
            rx.text(
                State.video_assets.length(),
                font_size="0.8em",
                color="#94a3b8",
            ),
            width="100%",
            align_items="center",
        ),
        rx.cond(
            State.video_assets.length() == 0,
            rx.text(
                "暂无资产，让 Agent 创作视频后这里会显示生成的文件",
                color="#94a3b8",
                font_size="0.85em",
            ),
            rx.scroll_area(
                rx.vstack(
                    rx.foreach(State.video_assets, _asset_row),
                    width="100%",
                    spacing="1",
                ),
                width="100%",
                max_height="220px",
            ),
        ),
        width="100%",
        height="100%",
        padding="1em",
        spacing="3",
        align_items="start",
    )
