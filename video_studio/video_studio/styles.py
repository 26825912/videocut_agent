"""全局共享样式。"""
import reflex as rx

# 主题色
COLORS = {
    "primary": "#6366f1",
    "bg": "#f8fafc",
    "border": "#e2e8f0",
    "user_bubble": "#3b82f6",
    "agent_bubble": "#f1f5f9",
}

global_style: dict = {
    "body": {
        "font_family": "system-ui, -apple-system, 'Segoe UI', sans-serif",
        "background_color": COLORS["bg"],
    },
}
