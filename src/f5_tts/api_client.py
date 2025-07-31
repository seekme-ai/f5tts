#!/usr/bin/env python3
"""
F5-TTS API客户端
用于测试FastAPI服务的示例客户端
"""

import json
import os
import argparse
from pathlib import Path
from typing import Optional

import requests
from importlib.resources import files


class F5TTSClient:
    """F5-TTS API客户端"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        初始化客户端
        
        Args:
            base_url: API服务的基础URL
        """
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        
    def health_check(self) -> dict:
        """健康检查"""
        response = self.session.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()
    
    def get_model_info(self) -> dict:
        """获取模型信息"""
        response = self.session.get(f"{self.base_url}/model/info")
        response.raise_for_status()
        return response.json()
    
    def synthesize_speech(
        self,
        ref_audio_path: str,
        ref_text: str,
        gen_text: str,
        output_path: str,
        target_rms: float = 0.1,
        cross_fade_duration: float = 0.15,
        speed: float = 1.0,
        nfe_step: int = 32,
        cfg_strength: float = 2.0,
        sway_sampling_coef: float = -1,
        remove_silence: bool = False,
        seed: Optional[int] = None
    ) -> dict:
        """
        语音合成
        
        Args:
            ref_audio_path: 参考音频文件路径
            ref_text: 参考音频对应的文本
            gen_text: 要生成的目标文本
            output_path: 输出音频文件路径
            target_rms: 目标音量RMS值
            cross_fade_duration: 交叉淡化时长
            speed: 语速倍率
            nfe_step: NFE步数
            cfg_strength: CFG强度
            sway_sampling_coef: 摆动采样系数
            remove_silence: 是否移除静音部分
            seed: 随机种子
            
        Returns:
            包含响应信息的字典
        """
        # 准备请求参数
        request_data = {
            "ref_text": ref_text,
            "gen_text": gen_text,
            "target_rms": target_rms,
            "cross_fade_duration": cross_fade_duration,
            "speed": speed,
            "nfe_step": nfe_step,
            "cfg_strength": cfg_strength,
            "sway_sampling_coef": sway_sampling_coef,
            "remove_silence": remove_silence,
            "seed": seed
        }
        
        # 准备文件和数据
        with open(ref_audio_path, "rb") as audio_file:
            files = {"ref_audio": audio_file}
            data = {"request_data": json.dumps(request_data)}
            
            response = self.session.post(
                f"{self.base_url}/tts/synthesize",
                files=files,
                data=data
            )
        
        response.raise_for_status()
        
        # 保存音频文件
        with open(output_path, "wb") as f:
            f.write(response.content)
        
        # 返回响应头信息
        return {
            "output_path": output_path,
            "duration": response.headers.get("X-Audio-Duration"),
            "sample_rate": response.headers.get("X-Sample-Rate"),
            "seed": response.headers.get("X-Seed")
        }
    
    def transcribe_audio(self, audio_path: str, language: Optional[str] = None) -> dict:
        """
        音频转录
        
        Args:
            audio_path: 音频文件路径
            language: 指定语言代码，留空自动检测
            
        Returns:
            转录结果
        """
        with open(audio_path, "rb") as audio_file:
            files = {"audio": audio_file}
            data = {"language": language} if language else {}
            
            response = self.session.post(
                f"{self.base_url}/tts/transcribe",
                files=files,
                data=data
            )
        
        response.raise_for_status()
        return response.json()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="F5-TTS API客户端测试")
    parser.add_argument("--url", default="http://localhost:8000", help="API服务URL")
    parser.add_argument("--action", choices=["health", "info", "synthesize", "transcribe"], 
                       default="health", help="要执行的操作")
    
    # 语音合成参数
    parser.add_argument("--ref-audio", help="参考音频文件路径")
    parser.add_argument("--ref-text", help="参考音频对应的文本")
    parser.add_argument("--gen-text", help="要生成的目标文本")
    parser.add_argument("--output", help="输出音频文件路径")
    parser.add_argument("--speed", type=float, default=1.0, help="语速倍率")
    parser.add_argument("--seed", type=int, help="随机种子")
    
    # 转录参数
    parser.add_argument("--audio", help="要转录的音频文件路径")
    parser.add_argument("--language", help="指定语言代码")
    
    args = parser.parse_args()
    
    # 创建客户端
    client = F5TTSClient(args.url)
    
    try:
        if args.action == "health":
            # 健康检查
            result = client.health_check()
            print("健康检查结果:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
        elif args.action == "info":
            # 获取模型信息
            result = client.get_model_info()
            print("模型信息:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
        elif args.action == "synthesize":
            # 语音合成
            if not all([args.ref_audio, args.ref_text, args.gen_text, args.output]):
                print("错误: 语音合成需要 --ref-audio, --ref-text, --gen-text, --output 参数")
                return
            
            result = client.synthesize_speech(
                ref_audio_path=args.ref_audio,
                ref_text=args.ref_text,
                gen_text=args.gen_text,
                output_path=args.output,
                speed=args.speed,
                seed=args.seed
            )
            print("语音合成完成:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
        elif args.action == "transcribe":
            # 音频转录
            if not args.audio:
                print("错误: 音频转录需要 --audio 参数")
                return
            
            result = client.transcribe_audio(args.audio, args.language)
            print("转录结果:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
    except requests.exceptions.RequestException as e:
        print(f"请求错误: {e}")
    except Exception as e:
        print(f"执行失败: {e}")


def demo():
    """演示功能"""
    print("F5-TTS API客户端演示")
    print("=" * 50)
    
    client = F5TTSClient()
    
    try:
        # 1. 健康检查
        print("1. 健康检查...")
        health = client.health_check()
        print(f"服务状态: {health['status']}")
        print(f"模型已加载: {health['model_loaded']}")
        print(f"运行设备: {health['device']}")
        print()
        
        # 2. 获取模型信息
        print("2. 获取模型信息...")
        info = client.get_model_info()
        print(f"模型名称: {info['model_name']}")
        print(f"采样率: {info['target_sample_rate']}")
        print(f"梅尔频谱类型: {info['mel_spec_type']}")
        print()
        
        # 3. 使用示例音频进行合成
        print("3. 语音合成示例...")
        ref_audio = str(files("f5_tts").joinpath("infer/examples/basic/basic_ref_en.wav"))
        
        if os.path.exists(ref_audio):
            result = client.synthesize_speech(
                ref_audio_path=ref_audio,
                ref_text="some call me nature, others call me mother nature.",
                gen_text="Hello, this is a test of the F5-TTS API service.",
                output_path="api_test_output.wav",
                seed=42
            )
            print(f"合成完成: {result['output_path']}")
            print(f"音频时长: {result['duration']}秒")
            print(f"使用种子: {result['seed']}")
        else:
            print("示例音频文件不存在，跳过合成测试")
        
        print("\n演示完成！")
        
    except Exception as e:
        print(f"演示失败: {e}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) == 1 or (len(sys.argv) == 2 and sys.argv[1] == "demo"):
        demo()
    else:
        main() 