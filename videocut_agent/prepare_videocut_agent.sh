#!/bin/bash
set -e

echo "开始准备 videocut_agent 项目上传到 GitHub..."

# 设置源目录和目标目录
SOURCE_DIR="C:/Users/ddf/Desktop/zzc/code/seo_video_generate_main/seo_video_generate/videocut_agent"
TARGET_DIR="./videocut_agent_clean"

# 1. 创建清理后的目录
echo "[1/7] 创建目标目录..."
mkdir -p "$TARGET_DIR"

# 2. 复制源代码(排除敏感文件)
echo "[2/7] 复制源代码..."
rsync -av --progress "$SOURCE_DIR/" "$TARGET_DIR/" \
  --exclude=".env" \
  --exclude="__pycache__" \
  --exclude="*.pyc" \
  --exclude="*.log" \
  --exclude="output/" \
  --exclude="temp/"

# 3. 删除敏感文件
echo "[3/7] 清理敏感信息..."
cd "$TARGET_DIR"
rm -f .env
find . -name "*.pyc" -delete
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# 4. 替换硬编码的 API keys
echo "[4/7] 脱敏硬编码信息..."
# 替换 API key
find . -name "*.py" -type f -exec sed -i 's/sk-1623yFvhgqAtzr1ZUF3weA/your-api-key-here/g' {} +
# 替换内部域名
find . -name "*.py" -type f -exec sed -i 's|https://litellm.zuzuche.com|https://api.openai.com|g' {} +

# 5. 复制配置模板文件
echo "[5/7] 添加配置文件..."
cp ../videocut_agent/.env.example ./.env.example
cp ../videocut_agent/requirements.txt ./requirements.txt
cp ../videocut_agent/.gitignore ./.gitignore
cp ../videocut_agent/README.md ./README.md

# 6. 初始化 git 仓库
echo "[6/7] 初始化 Git 仓库..."
git init
git add .
git commit -m "Initial commit: Video AI Agent System

- 7个专业化智能体
- 完整视频制作流程
- Streamlit UI + FastAPI 服务
- 基于 LangGraph 构建"

# 7. 验证
echo "[7/7] 验证..."
echo "项目大小: $(du -sh . | cut -f1)"
echo "Python文件数: $(find . -name "*.py" | wc -l)"
echo "剩余 .env 文件: $(find . -name ".env" -not -name ".env.example" | wc -l)"

echo ""
echo "✅ 清理完成!"
echo ""
echo "下一步操作:"
echo "1. cd $TARGET_DIR"
echo "2. 检查代码是否正常"
echo "3. 创建 GitHub 仓库"
echo "4. git remote add origin <your-repo-url>"
echo "5. git push -u origin main"
