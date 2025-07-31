#!/usr/bin/env python3
"""
F5-TTS FastAPI服务器
提供TTS语音合成、音频转录等功能的REST API接口
"""

import io
import os
import tempfile
import uuid
import wave
from pathlib import Path
from typing import Optional, List

import soundfile as sf
import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field

from f5_tts.api import F5TTS


# 数据模型定义
class TTSRequest(BaseModel):
    """TTS合成请求模型"""
    ref_text: str = Field(..., description="参考音频对应的文本")
    gen_text: str = Field(..., description="要生成的目标文本")
    target_rms: float = Field(0.1, description="目标音量RMS值", ge=0.0, le=1.0)
    cross_fade_duration: float = Field(0.15, description="交叉淡化时长", ge=0.0)
    speed: float = Field(1.0, description="语速倍率", ge=0.1, le=3.0)
    nfe_step: int = Field(32, description="NFE步数", ge=1, le=128)
    cfg_strength: float = Field(2.0, description="CFG强度", ge=0.0, le=10.0)
    sway_sampling_coef: float = Field(-1, description="摆动采样系数")
    remove_silence: bool = Field(False, description="是否移除静音部分")
    seed: Optional[int] = Field(None, description="随机种子")


class TTSResponse(BaseModel):
    """TTS合成响应模型"""
    message: str = Field(..., description="响应消息")
    audio_duration: float = Field(..., description="音频时长(秒)")
    sample_rate: int = Field(..., description="采样率")
    seed: Optional[int] = Field(None, description="使用的随机种子")


class TranscribeResponse(BaseModel):
    """转录响应模型"""
    text: str = Field(..., description="转录文本")
    language: Optional[str] = Field(None, description="检测到的语言")


class HealthResponse(BaseModel):
    """健康检查响应模型"""
    status: str = Field(..., description="服务状态")
    model_loaded: bool = Field(..., description="模型是否已加载")
    device: str = Field(..., description="运行设备")


class ModelInfo(BaseModel):
    """模型信息响应模型"""
    model_name: str = Field(..., description="模型名称")
    device: str = Field(..., description="运行设备")
    mel_spec_type: str = Field(..., description="梅尔频谱类型")
    target_sample_rate: int = Field(..., description="目标采样率")


# 全局变量
tts_model: Optional[F5TTS] = None


def create_app() -> FastAPI:
    """创建FastAPI应用"""
    app = FastAPI(
        title="F5-TTS API服务",
        description="基于F5-TTS的语音合成API服务，支持语音合成、音频转录等功能",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # 添加CORS中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app


app = create_app()


@app.on_event("startup")
async def startup_event():
    """应用启动时初始化模型"""
    global tts_model
    try:
        print("正在初始化F5-TTS模型...")
        tts_model = F5TTS()
        print(f"模型初始化完成，运行设备: {tts_model.device}")
    except Exception as e:
        print(f"模型初始化失败: {e}")
        tts_model = None


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时清理资源"""
    global tts_model
    if tts_model is not None:
        del tts_model
        tts_model = None
    print("应用已关闭")


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查端点"""
    global tts_model
    
    if tts_model is None:
        return HealthResponse(
            status="unhealthy",
            model_loaded=False,
            device="unknown"
        )
    
    return HealthResponse(
        status="healthy",
        model_loaded=True,
        device=tts_model.device
    )


@app.get("/model/info", response_model=ModelInfo)
async def get_model_info():
    """获取模型信息"""
    global tts_model
    
    if tts_model is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="模型未加载"
        )
    
    return ModelInfo(
        model_name="F5TTS_v1_Base",
        device=tts_model.device,
        mel_spec_type=tts_model.mel_spec_type,
        target_sample_rate=tts_model.target_sample_rate
    )


@app.post("/tts/synthesize")
async def synthesize_speech(
    ref_audio: UploadFile = File(..., description="参考音频文件"),
    request_data: str = Form(..., description="TTS请求参数的JSON字符串")
):
    """
    TTS语音合成端点
    
    上传参考音频文件和文本，生成目标语音
    """
    global tts_model
    
    if tts_model is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="模型未加载"
        )
    
    try:
        # 解析请求参数
        import json
        request_dict = json.loads(request_data)
        request = TTSRequest(**request_dict)
        
        # 验证音频文件格式（宽松检查）
        is_audio_content_type = (
            not ref_audio.content_type or 
            ref_audio.content_type.startswith("audio/") or
            ref_audio.content_type == "application/octet-stream"
        )
        is_audio_filename = (
            not ref_audio.filename or 
            ref_audio.filename.lower().endswith(('.wav', '.mp3', '.flac', '.m4a', '.ogg'))
        )
        
        if not (is_audio_content_type or is_audio_filename):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="上传文件必须是音频格式"
            )
        
        # 保存临时音频文件
        temp_dir = tempfile.mkdtemp()
        ref_audio_path = os.path.join(temp_dir, f"ref_{uuid.uuid4()}.wav")
        
        with open(ref_audio_path, "wb") as f:
            f.write(await ref_audio.read())
        
        # 执行TTS合成
        wav, sr, spec = tts_model.infer(
            ref_file=ref_audio_path,
            ref_text=request.ref_text,
            gen_text=request.gen_text,
            target_rms=request.target_rms,
            cross_fade_duration=request.cross_fade_duration,
            speed=request.speed,
            nfe_step=request.nfe_step,
            cfg_strength=request.cfg_strength,
            sway_sampling_coef=request.sway_sampling_coef,
            remove_silence=request.remove_silence,
            seed=request.seed,
        )
        
        # 将音频数据转换为WAV格式的字节流
        output_buffer = io.BytesIO()
        sf.write(output_buffer, wav, sr, format='WAV')
        output_buffer.seek(0)
        
        # 计算音频时长
        duration = len(wav) / sr
        
        # 读取音频数据
        audio_data = output_buffer.read()
        
        # 清理临时文件
        os.unlink(ref_audio_path)
        os.rmdir(temp_dir)
        
        # 返回音频流
        return StreamingResponse(
            io.BytesIO(audio_data),
            media_type="audio/wav",
            headers={
                "Content-Disposition": "attachment; filename=synthesized_audio.wav",
                "X-Audio-Duration": str(duration),
                "X-Sample-Rate": str(sr),
                "X-Seed": str(tts_model.seed) if hasattr(tts_model, 'seed') else "null"
            }
        )
        
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"请求参数JSON格式错误: {str(e)}"
        )
    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        # 记录详细错误信息用于调试
        import traceback
        error_trace = traceback.format_exc()
        print(f"TTS合成错误: {error_trace}")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"TTS合成失败: {str(e)}"
        )


@app.post("/tts/transcribe", response_model=TranscribeResponse)
async def transcribe_audio(
    audio: UploadFile = File(..., description="要转录的音频文件"),
    language: Optional[str] = Form(None, description="指定语言代码，留空自动检测")
):
    """
    音频转录端点
    
    上传音频文件，返回转录文本
    """
    global tts_model
    
    if tts_model is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="模型未加载"
        )
    
    try:
        # 验证音频文件格式（宽松检查）
        is_audio_content_type = (
            not audio.content_type or 
            audio.content_type.startswith("audio/") or
            audio.content_type == "application/octet-stream"
        )
        is_audio_filename = (
            not audio.filename or 
            audio.filename.lower().endswith(('.wav', '.mp3', '.flac', '.m4a', '.ogg'))
        )
        
        if not (is_audio_content_type or is_audio_filename):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="上传文件必须是音频格式"
            )
        
        # 保存临时音频文件
        temp_dir = tempfile.mkdtemp()
        audio_path = os.path.join(temp_dir, f"audio_{uuid.uuid4()}.wav")
        
        with open(audio_path, "wb") as f:
            f.write(await audio.read())
        
        # 执行转录
        transcribed_text = tts_model.transcribe(audio_path, language)
        
        # 清理临时文件
        os.unlink(audio_path)
        os.rmdir(temp_dir)
        
        return TranscribeResponse(
            text=transcribed_text,
            language=language
        )
        
    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        # 记录详细错误信息用于调试
        import traceback
        error_trace = traceback.format_exc()
        print(f"音频转录错误: {error_trace}")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"音频转录失败: {str(e)}"
        )


@app.get("/")
async def root():
    """根路径，提供API信息"""
    return {
        "message": "F5-TTS API服务",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "endpoints": {
            "health": "/health",
            "model_info": "/model/info",
            "synthesize": "/tts/synthesize",
            "transcribe": "/tts/transcribe"
        }
    }


def main():
    """启动FastAPI服务器"""
    import argparse
    
    parser = argparse.ArgumentParser(description="F5-TTS FastAPI服务器")
    parser.add_argument("--host", default="0.0.0.0", help="服务器主机地址")
    parser.add_argument("--port", type=int, default=8000, help="服务器端口")
    parser.add_argument("--workers", type=int, default=1, help="工作进程数")
    parser.add_argument("--reload", action="store_true", help="开发模式，代码变更时自动重载")
    parser.add_argument("--log-level", default="info", help="日志级别")
    
    args = parser.parse_args()
    
    print(f"启动F5-TTS API服务器...")
    print(f"地址: http://{args.host}:{args.port}")
    print(f"API文档: http://{args.host}:{args.port}/docs")
    
    uvicorn.run(
        "f5_tts.api_server:app",
        host=args.host,
        port=args.port,
        workers=args.workers,
        reload=args.reload,
        log_level=args.log_level
    )


if __name__ == "__main__":
    main() 