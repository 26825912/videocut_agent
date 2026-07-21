# Video Agent Studio 运行指南

## 项目架构

```
浏览器 (:3000)  ←WebSocket→  Reflex 前端 (:8001)  ←HTTP+SSE→  Agent 后端 (:8000)
```

---

## 一、环境准备

### 1. 系统要求
- Python 3.10+
- Node.js 18+ (前端需要)
- FFmpeg (视频处理)

### 2. 安装 FFmpeg

**Windows:**
```bash
# 使用 chocolatey
choco install ffmpeg

# 或从官网下载: https://ffmpeg.org/download.html
```

**Linux:**
```bash
sudo apt-get install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

---

## 二、后端运行指令

### 后端项目路径
```
videocut_agent/
```

### 1. 安装后端依赖
```bash
cd videocut_agent
pip install -r requirements.txt
```

### 2. 配置环境变量
复制 `.env.example` 为 `.env` 并配置：
```bash
cp .env.example .env
```

编辑 `.env` 文件，填写必要的 API keys：
```env
GEMINI_API_KEY=your-api-key-here
GEMINI_API_BASE=https://api.openai.com/v1
```

### 3. 启动后端服务
```bash
cd videocut_agent
python server.py
```

**预期输出：**
```
INFO:     Started server process [xxx]
INFO:     Uvicorn running on http://0.0.0.0:8000
🚀 Agent 启动成功 (Async/Streaming Ready)...
```

**后端端口：** `8000`

**API 文档：** http://localhost:8000/docs

---

## 三、前端运行指令

### 前端项目路径
```
video_studio/
```

### 1. 安装前端依赖
```bash
cd video_studio
pip install -r requirements.txt
```

### 2. 配置前端环境变量
确保 `.env` 文件配置正确：
```env
AGENT_API_URL=http://localhost:8000
DATA_BASE_URL=http://localhost:8000
```

### 3. 启动前端服务
```bash
cd video_studio
reflex run
```

**首次运行说明：**
- Reflex 会自动下载 Node.js 依赖，需要几分钟时间
- 请确保已安装 Node.js 18+

**预期输出：**
```
──────────────── Starting Reflex App ────────────────
App running at: http://localhost:3000
```

**前端端口：**
- 前端页面：`3000`
- Reflex 后端：`8001`

---

## 四、访问应用

打开浏览器访问：**http://localhost:3000**

**正常状态：**
- 顶栏显示绿色"Agent 在线"
- 右侧聊天窗口可以输入消息
- 流式显示 agent 思考过程和工具调用
- 视频生成后左侧自动预览

---

## 五、启动顺序总结

### 终端1 - 后端
```bash
cd videocut_agent
python server.py
```

### 终端2 - 前端
```bash
cd video_studio
reflex run
```

### 访问
浏览器打开：http://localhost:3000

---

## 六、常见问题

### Q: reflex run 报错 "Node.js not found"
**A:** 需要先安装 Node.js 18+，下载地址：https://nodejs.org/

### Q: 前端显示"Agent 离线"
**A:** 
1. 确认后端已启动在端口 8000
2. 检查 `video_studio/.env` 中的 `AGENT_API_URL` 配置

### Q: 端口被占用
**A:**
- 后端端口可在 `.env` 中设置：`FASTAPI_PORT=你的端口`
- 前端端口可在 `rxconfig.py` 中修改 `backend_port`

### Q: 视频无法播放
**A:** 检查后端日志，确认 `/data` 静态目录挂载成功

---

## 七、端口说明

| 服务 | 端口 | 说明 |
|------|------|------|
| Agent 后端 | 8000 | FastAPI 服务 |
| Reflex 后端 | 8001 | 前端框架后端 |
| 前端页面 | 3000 | 浏览器访问地址 |

---

## 八、验证清单

- [ ] 后端启动无报错，端口 :8000
- [ ] 前端启动无报错，端口 :3000 + :8001
- [ ] 浏览器打开显示绿色"Agent 在线"
- [ ] 发送消息后右侧流式显示内容
- [ ] 工具调用显示蓝色卡片
- [ ] 视频生成后左侧播放器自动加载
- [ ] 点击资产列表可切换预览
- [ ] 点击下载按钮可下载视频
