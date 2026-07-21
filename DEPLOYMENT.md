# Video Agent Studio 部署指南

## 修复清单（已完成）

### 后端修复（videocut_agent/）
1. ✅ 添加 `/data` 静态文件挂载（server.py）
2. ✅ 复制缺失的 `asr_tools.py` 到 `videoscript_agent/tools/`
3. ✅ 迁移 moviepy 1.x → 2.x API：
   - `from moviepy.editor` → `from moviepy`
   - `.resize()` → `.resized()`
   - `.crop()` → `.cropped()`
   - 修复了 `tools/video_ops_v2.py` 和 `videocut_agent/tools/video_ops_v2.py`
4. ✅ 取消注释 `audiocut_agent/tools/asr_tools.py` 中的 `asr_audio_file`
5. ✅ 复制 `video_ops_v2.py` 到 `videogen_agent/tools/` 和 `videocopywrite_agent/tools/`
6. ✅ 修复 3 个 agent 的错误导入：`.method.video_ops_v2` → `.video_ops_v2`

### 前端创建（video_studio/）
- ✅ 完整的 Reflex 应用（13 个文件）
- ✅ 流式 SSE 聊天界面
- ✅ 视频预览 + 资产列表
- ✅ 自动提取生成的视频文件并预览

---

## 启动步骤

### 1. 启动 Agent 后端（终端1）
```bash
cd videocut_agent
python server.py
```
**预期输出**：
```
INFO:     Started server process [xxx]
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 2. 启动前端（终端2，首次需安装依赖）
```bash
cd video_studio

# 首次运行：安装依赖
pip install -r requirements.txt

# 启动 Reflex（首次会自动下载 Node.js 依赖，需几分钟）
reflex run
```
**预期输出**：
```
 ──────────────── Starting Reflex App ────────────────
 App running at: http://localhost:3000
```

### 3. 访问界面
打开浏览器访问 **http://localhost:3000**

- 顶栏应显示绿色"Agent 在线"
- 右侧聊天窗输入："帮我生成一个关于如何学习的15秒视频"
- 流式显示 agent 思考过程 + 工具调用
- 视频生成后左侧自动预览

---

## 架构说明
```
浏览器 (:3000)  ←WebSocket→  Reflex 后端 (:8001)  ←HTTP+SSE→  Agent (:8000)
                                                                    ↓
                                                              data/result_video/
浏览器 ←<video src>直接拉取←──────────────────────────────────────┘
```

**无需 CORS**：
- API 走 Reflex 后端→agent（服务器到服务器）
- 视频走 `<video>` 标签（媒体元素跨域播放免 CORS）

---

## 验证清单
- [ ] agent 后端启动无报错，端口 :8000
- [ ] 前端启动无报错，端口 :3000 + :8001
- [ ] 浏览器打开显示绿色"Agent 在线"
- [ ] 发送消息后右侧流式显示内容
- [ ] 工具调用显示蓝色卡片
- [ ] 视频生成后左侧播放器自动加载
- [ ] 点击资产列表可切换预览
- [ ] 点击下载按钮可下载视频

---

## 常见问题

**Q: reflex run 报错 "Node.js not found"**  
A: 需要先安装 Node.js 18+ (https://nodejs.org/)

**Q: 前端显示"Agent 离线"**  
A: 确认 agent 后端已启动在 :8000，检查 `video_studio/.env` 中的 `AGENT_API_URL`

**Q: 视频无法播放**  
A: 检查 agent 后端日志，确认 `/data` 静态目录挂载成功

**Q: 工具调用后无视频出现**  
A: agent 可能生成失败，查看右侧聊天的错误消息或 agent 后端日志
