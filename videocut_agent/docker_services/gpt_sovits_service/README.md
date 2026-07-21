# GPT-SoVITS Docker 服务

## 构建说明

该 Dockerfile 需要从 videocut_agent/models 目录构建，以便访问 gpt-sovits 源码：

```bash
cd videocut_agent/models
docker build -t gpt-sovits-service -f ../docker_services/gpt_sovits_service/Dockerfile .
```

## 环境变量

- `USE_GPU`: 是否使用 GPU (默认: true)
- `DEVICE`: 设备 (cuda/cpu，默认: cuda)

## 挂载目录

- `/app/GPT_SoVITS/pretrained_models`: 模型权重目录
- `/app/data/clone_voice`: 参考音频目录
