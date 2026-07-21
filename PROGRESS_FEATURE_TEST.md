# 进度指示功能测试指南

## 功能说明

已为 Video Agent Studio 添加实时进度指示功能，在视频生成过程中显示：
- 当前执行的步骤名称（带emoji图标）
- 进度百分比和步骤数（如 3/8）
- 可视化进度条

## 测试步骤

### 1. 启动服务

**终端1 - 启动后端：**
```bash
cd videocut_agent
python server.py
```

**终端2 - 启动前端：**
```bash
cd video_studio
reflex run
```

### 2. 访问界面

浏览器打开：http://localhost:3000

### 3. 测试场景

#### 场景1：通用视频生成（8步流程）
输入消息：
```
帮我生成一个关于如何学习的15秒视频
```

**预期进度步骤：**
1. 📝 生成视频文案 (1/8, 12.5%)
2. 🎙️ 转换为语音 (2/8, 25%)
3. ⏱️ 分析时间轴 (3/8, 37.5%)
4. 🔍 检索视频素材 (4/8, 50%)
5. 🎬 合并素材视频 (5/8, 62.5%)
6. 💬 生成字幕文件 (6/8, 75%)
7. 🔊 添加音频轨道 (7/8, 87.5%)
8. ✨ 嵌入字幕完成 (8/8, 100%)

#### 场景2：爆款视频仿写
输入消息：
```
仿照这个视频 https://www.youtube.com/shorts/xxx 生成一个15秒视频
```

**预期进度步骤：**
1. 📋 分析爆款视频 (1/8)
2. ✍️ 仿写视频文案 (2/8)
3. ...（后续步骤同通用流程）

#### 场景3：视频剪辑（2步流程）
输入消息：
```
帮我剪辑 videos/test.mp4，截取10到20秒
```

**预期进度步骤：**
1. ✂️ 裁剪视频片段 (1/2, 50%)
2. ✅ 处理完成 (2/2, 100%)

## 验证要点

### ✅ 正常情况
- [ ] 进度条在消息列表上方显示
- [ ] 步骤名称实时更新
- [ ] 进度百分比正确计算
- [ ] 进度条宽度平滑动画过渡
- [ ] 完成后进度条显示100%
- [ ] 处理完成后进度条自动隐藏

### ✅ 边界情况
- [ ] 未开始处理时不显示进度条
- [ ] 处理失败时进度条消失
- [ ] 多个任务串行执行时进度正确重置

### ✅ UI表现
- [ ] 进度条颜色为渐变紫色 (#6366f1 → #8b5cf6)
- [ ] 背景色为浅灰色 (#e2e8f0)
- [ ] 步骤文本带emoji前缀
- [ ] 显示 "当前步骤/总步骤" 格式

## 代码改动说明

### 修改文件
1. **video_studio/video_studio/state.py**
   - 新增 `progress` 字段存储进度状态
   - 新增 `_TOOL_STEP_MAPPING` 映射25个工具到具体步骤
   - 在 `_do_send()` 中监听 `tool_call` 事件更新进度
   - 在 `start`/`done`/`error` 事件中重置进度

2. **video_studio/video_studio/components/chat.py**
   - 新增 `_progress_bar()` 组件
   - 在聊天界面标题下方插入进度条
   - 使用条件渲染：仅在 `processing=True` 且 `total>0` 时显示

### 技术实现细节

**进度计算逻辑：**
```python
# 在接收到 tool_call 事件时
if tool_name in _TOOL_STEP_MAPPING:
    current, total, step_name = _TOOL_STEP_MAPPING[tool_name]
    percentage = int((current / total * 100)) if total > 0 else 0
    self.progress = {
        "current": current,
        "total": total,
        "step": step_name,
        "percentage": percentage
    }
```

**UI渲染逻辑：**
```python
# 仅在处理中且有明确总步骤数时显示
rx.cond(
    State.processing & (State.progress["total"] > 0),
    # 进度条组件
)
```

## 故障排查

### 问题1：进度条不显示
**可能原因：**
- 后端未返回 `tool_call` 事件
- 工具名称不在 `_TOOL_STEP_MAPPING` 中

**排查方法：**
```bash
# 在 state.py 的 _do_send 中添加调试输出
elif etype == "tool_call":
    tool_name = event.get("tools_name", "")
    print(f"DEBUG: tool_call received: {tool_name}")  # 添加这行
```

### 问题2：进度卡住不动
**可能原因：**
- Agent执行失败但未发送 `error` 事件
- 工具调用顺序与映射表不匹配

**解决方案：**
- 检查后端日志确认工具执行状态
- 使用浏览器开发者工具查看 WebSocket 消息

### 问题3：进度百分比不准确
**可能原因：**
- 不同流程使用了不同的工具组合
- 映射表中的 `total` 值设置不当

**解决方案：**
- 观察实际工具调用序列
- 调整 `_TOOL_STEP_MAPPING` 中的 `total` 值

## 性能影响

- **前端渲染**：每次进度更新触发一次 React 重渲染（~1ms）
- **WebSocket流量**：每个工具调用增加 ~100 字节进度数据
- **用户体验提升**：显著减少焦虑，提供明确反馈

## 后续优化建议

1. **动态步骤预测**：根据用户输入智能预测总步骤数
2. **时间估算**：基于历史数据显示预计剩余时间
3. **子任务展开**：显示每个工具的内部子步骤
4. **进度持久化**：刷新页面后恢复进度状态

## 更新日期
2026-07-17
