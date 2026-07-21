"""
FunASR 语音识别服务
提供 HTTP API 接口
"""
import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
import tempfile
import shutil

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="FunASR Service", version="1.0.0")

# 全局模型实例
funasr_model = None
model_loaded = False


def get_model_path(model_name: str) -> str:
    """获取模型路径"""
    model_base = os.getenv("FUNASR_MODEL_DIR", "/models/funasr")

    model_mapping = {
        "paraformer_zh": f"{model_base}/speech_seaco_paraformer_large_asr_nat-zh-cn-16k-common-vocab8404-pytorch",
        "vad_zh": f"{model_base}/speech_fsmn_vad_zh-cn-16k-common-pytorch",
        "punc_zh": f"{model_base}/punc_ct-transformer_zh-cn-common-vocab272727-pytorch",
        "paraformer_en": f"{model_base}/speech_paraformer-large_asr_nat-en-16k-common-vocab10020"
    }

    path = model_mapping.get(model_name)

    # 如果本地模型不存在，使用 HuggingFace 模型 ID
    if path and not os.path.exists(path):
        logger.warning(f"本地模型 {path} 不存在，将使用在线模型")
        online_models = {
            "paraformer_zh": "iic/speech_seaco_paraformer_large_asr_nat-zh-cn-16k-common-vocab8404-pytorch",
            "vad_zh": "damo/speech_fsmn_vad_zh-cn-16k-common-pytorch",
            "punc_zh": "damo/punc_ct-transformer_zh-cn-common-vocab272727-pytorch",
            "paraformer_en": "iic/speech_paraformer-large_asr_nat-en-16k-common-vocab10020"
        }
        return online_models.get(model_name, path)

    return path


def load_funasr_model(language: str = "zh", use_gpu: bool = True):
    """加载 FunASR 模型"""
    global funasr_model, model_loaded

    if model_loaded:
        return funasr_model

    try:
        from funasr import AutoModel

        logger.info(f"加载 FunASR 模型 (language={language}, gpu={use_gpu})...")

        # 根据语言选择模型
        if language in ["zh", "zh-cn"]:
            asr_model = get_model_path("paraformer_zh")
            vad_model = get_model_path("vad_zh")
            punc_model = get_model_path("punc_zh")
        else:
            asr_model = get_model_path("paraformer_en")
            vad_model = get_model_path("vad_zh")
            punc_model = None

        model_kwargs = {
            "model": asr_model,
            "device": "cuda" if use_gpu else "cpu"
        }

        if vad_model:
            model_kwargs["vad_model"] = vad_model

        if punc_model:
            model_kwargs["punc_model"] = punc_model

        logger.info(f"模型配置: {model_kwargs}")

        funasr_model = AutoModel(**model_kwargs)
        model_loaded = True

        logger.info("FunASR 模型加载成功")
        return funasr_model

    except Exception as e:
        logger.error(f"加载模型失败: {e}")
        raise


def convert_audio_to_wav(input_path: str) -> str:
    """转换音频为标准 WAV 格式"""
    from pydub import AudioSegment

    output_path = input_path.replace(Path(input_path).suffix, "_converted.wav")

    try:
        audio = AudioSegment.from_file(input_path)
        audio = audio.set_channels(1)
        audio = audio.set_frame_rate(16000)
        audio.export(output_path, format="wav", codec="pcm_s16le")
        return output_path
    except Exception as e:
        logger.error(f"音频转换失败: {e}")
        return input_path


@app.on_event("startup")
async def startup_event():
    """启动时加载模型"""
    try:
        use_gpu = os.getenv("USE_GPU", "true").lower() == "true"
        language = os.getenv("LANGUAGE", "zh")
        load_funasr_model(language=language, use_gpu=use_gpu)
        logger.info("服务启动完成")
    except Exception as e:
        logger.warning(f"启动时加载模型失败（将在首次请求时重试）: {e}")


@app.get("/")
async def root():
    """健康检查"""
    return {
        "service": "FunASR Service",
        "status": "running",
        "model_loaded": model_loaded
    }


@app.post("/asr")
async def speech_to_text(
    file: UploadFile = File(...),
    language: str = Form("zh"),
    provider: str = Form("funasr")
):
    """
    语音识别接口

    Args:
        file: 音频文件
        language: 语言代码 (zh, en, ja, ko)
        provider: 提供商（保留兼容性，目前只支持 funasr）

    Returns:
        识别结果列表
    """
    temp_input = None
    temp_converted = None

    try:
        # 保存上传的文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp:
            temp_input = tmp.name
            shutil.copyfileobj(file.file, tmp)

        logger.info(f"收到识别请求: {file.filename}, language={language}")

        # 转换音频格式
        temp_converted = convert_audio_to_wav(temp_input)

        # 加载模型
        model = load_funasr_model(language=language)

        # 执行识别
        generation_kwargs = {
            "return_raw_text": True,
            "is_final": True,
            "sentence_timestamp": True,
            "word_timestamp": True,
            "batch_size": 1
        }

        result = model.generate(input=temp_converted, **generation_kwargs)

        # 解析结果
        segments = []

        if result and len(result) > 0:
            for item in result:
                text = item.get('text', '')
                timestamps = item.get('timestamp', [])

                if timestamps and isinstance(timestamps, list) and len(timestamps) > 0:
                    if isinstance(timestamps[0], (list, tuple)) and len(timestamps[0]) == 2:
                        # 字符级时间戳格式
                        if timestamps and text.strip():
                            start_time = float(timestamps[0][0]) / 1000.0
                            end_time = float(timestamps[-1][1]) / 1000.0

                            segments.append({
                                "text": text.strip(),
                                "start_time": round(start_time, 2),
                                "end_time": round(end_time, 2),
                                "duration": round(end_time - start_time, 2)
                            })
                else:
                    # 句级时间戳
                    sentence_start = item.get('sentence_start', 0) / 1000.0 if item.get('sentence_start') else 0
                    sentence_end = item.get('sentence_end', 0) / 1000.0 if item.get('sentence_end') else 0

                    if sentence_end == 0 and text:
                        estimated_duration = len(text) * 0.15
                        sentence_end = sentence_start + estimated_duration

                    segments.append({
                        "text": text,
                        "start_time": round(sentence_start, 2),
                        "end_time": round(sentence_end, 2),
                        "duration": round(sentence_end - sentence_start, 2)
                    })

        logger.info(f"识别完成，共 {len(segments)} 个片段")

        return JSONResponse(content={
            "success": True,
            "segments": segments,
            "count": len(segments)
        })

    except Exception as e:
        logger.error(f"识别失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        # 清理临时文件
        if temp_input and os.path.exists(temp_input):
            try:
                os.remove(temp_input)
            except:
                pass
        if temp_converted and os.path.exists(temp_converted) and temp_converted != temp_input:
            try:
                os.remove(temp_converted)
            except:
                pass


@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "model_loaded": model_loaded
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
