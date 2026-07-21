"""工具调用气泡：展示 agent 调用的子智能体名称与参数。"""
import reflex as rx


def tool_card(msg) -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.icon("wrench", size=14),
            rx.text("调用工具：", font_weight="bold", font_size="0.85em"),
            rx.text(msg["tool_name"], font_size="0.85em", color="#6366f1"),
            spacing="2",
            align_items="center",
        ),
        rx.cond(
            msg["args"] != "",
            rx.el.pre(
                msg["args"],
                font_size="0.72em",
                color="#475569",
                white_space="pre-wrap",
                margin_top="0.4em",
                max_height="180px",
                overflow_y="auto",
                font_family="monospace",
                margin="0.4em 0 0 0",
            ),
        ),
        bg="#eef2ff",
        border="1px solid #c7d2fe",
        border_radius="10px",
        padding="0.5em 0.8em",
        max_width="85%",
        width="fit-content",
        align_self="flex-start",
    )
