import reflex as rx

config = rx.Config(
    app_name="video_studio",
    backend_port=8001,  # 避开 agent server.py 的 8000
)
