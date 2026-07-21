# Docker 服务部署测试记录

## 测试环境
- OS: Windows 11 Pro
- Docker Desktop: 需要运行中
- Python: 3.10+

## 测试计划

### 1. FunASR 服务测试
- [ ] 构建镜像
- [ ] 启动容器
- [ ] 健康检查
- [ ] API 功能测试
- [ ] 停止容器

### 2. GPT-SoVITS 服务测试
- [ ] 构建镜像
- [ ] 启动容器
- [ ] 健康检查
- [ ] API 功能测试
- [ ] 停止容器

### 3. Docker Compose 集成测试
- [ ] 使用 docker-compose 启动所有服务
- [ ] 验证服务间通信
- [ ] 运行完整测试脚本
- [ ] 检查日志

## 测试命令

### FunASR 单独测试
```bash
# 构建镜像
cd videocut_agent/docker_services/funasr_service
docker build -t funasr-service:test .

# 启动容器（CPU 模式）
docker run -d --name funasr-test \
  -p 8001:8001 \
  -v $(pwd)/../../models/funasr:/models/funasr:ro \
  -e USE_GPU=false \
  funasr-service:test

# 健康检查
curl http://localhost:8001/health

# 停止容器
docker stop funasr-test
docker rm funasr-test
```

### GPT-SoVITS 单独测试
```bash
# 构建镜像
cd videocut_agent/models
docker build -t gpt-sovits-service:test \
  -f ../docker_services/gpt_sovits_service/Dockerfile .

# 启动容器（CPU 模式）
docker run -d --name gpt-sovits-test \
  -p 9880:9880 \
  -v $(pwd)/gpt-sovits/GPT_SoVITS/pretrained_models:/app/GPT_SoVITS/pretrained_models:ro \
  -e USE_GPU=false \
  gpt-sovits-service:test

# 健康检查
curl http://localhost:9880/

# 停止容器
docker stop gpt-sovits-test
docker rm gpt-sovits-test
```

### Docker Compose 测试
```bash
cd videocut_agent/docker_services

# 启动所有服务
docker-compose up -d

# 查看状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

## 测试结果

### FunASR 测试结果
- 构建时间: 
- 镜像大小:
- 启动时间:
- 健康检查: 
- API 测试:
- 问题记录:

### GPT-SoVITS 测试结果
- 构建时间:
- 镜像大小:
- 启动时间:
- 健康检查:
- API 测试:
- 问题记录:

### 集成测试结果
- 服务启动:
- 服务通信:
- 完整测试:
- 问题记录:

## 问题和解决方案

记录测试过程中遇到的问题和解决方法。
