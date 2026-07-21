# 贡献指南

感谢你考虑为 Video AI Agent System 做出贡献!

## 如何贡献

### 报告 Bug

如果发现 bug,请创建一个 issue 并包含:
- Bug 的详细描述
- 重现步骤
- 期望行为
- 实际行为
- 环境信息(OS, Python版本等)

### 提出新功能

如果有新功能建议,请创建一个 issue 并说明:
- 功能描述
- 使用场景
- 为什么这个功能有用

### 提交代码

1. Fork 这个仓库
2. 创建你的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交你的修改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启一个 Pull Request

### 代码规范

- 遵循 PEP 8 Python 代码规范
- 为新功能添加测试
- 更新相关文档
- 确保所有测试通过

### Pull Request 流程

1. 更新 README.md,说明你的修改
2. 更新 CHANGELOG.md(如果有)
3. PR 会被审查,可能需要修改
4. 审查通过后会被合并

## 开发环境设置

```bash
# 克隆仓库
git clone https://github.com/yourusername/videocut_agent_system.git
cd videocut_agent_system

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装开发依赖
pip install -r requirements.txt
pip install -r requirements-dev.txt  # 如果有开发专用依赖

# 运行测试
pytest
```

## 提交信息格式

使用清晰的提交信息:

```
类型: 简短描述(不超过50个字符)

详细描述(可选,72个字符换行)

- 列出主要修改点
- 解释为什么做这个修改
```

类型可以是:
- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式修改
- `refactor`: 重构
- `test`: 测试相关
- `chore`: 构建过程或辅助工具的变动

## 行为准则

- 尊重所有贡献者
- 接受建设性批评
- 关注什么对社区最好
- 展现同理心

## 问题?

如有任何问题,请开启一个 issue 或发送邮件到 your-email@example.com
