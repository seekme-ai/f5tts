#!/usr/bin/env python3
"""
F5-TTS API使用示例
演示如何使用FastAPI服务进行TTS语音合成和音频转录
"""

import os
import time
import asyncio
from pathlib import Path
from importlib.resources import files

# 确保能导入F5-TTS模块
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from f5_tts.api_client import F5TTSClient


async def wait_for_server(client, max_wait=60):
    """等待服务器启动"""
    print("等待API服务器启动...")
    
    for i in range(max_wait):
        try:
            health = client.health_check()
            if health.get('model_loaded'):
                print(f"✅ 服务器已就绪，模型已加载在设备: {health.get('device')}")
                return True
        except Exception:
            pass
        
        print(f"⏳ 等待中... ({i+1}/{max_wait})")
        time.sleep(1)
    
    print("❌ 等待服务器启动超时")
    return False


def main():
    """主演示函数"""
    print("=" * 60)
    print("F5-TTS API使用示例演示")
    print("=" * 60)
    
    # 创建客户端实例
    client = F5TTSClient("http://localhost:8000")
    
    # 检查服务器是否可用
    try:
        if not wait_for_server(client):
            print("\n请先启动API服务器:")
            print("python -m f5_tts.api_server")
            return
    except Exception as e:
        print(f"无法连接到API服务器: {e}")
        print("\n请先启动API服务器:")
        print("python -m f5_tts.api_server")
        return
    
    print("\n" + "=" * 60)
    print("1. 健康检查测试")
    print("=" * 60)
    
    try:
        health = client.health_check()
        print(f"✅ 服务状态: {health['status']}")
        print(f"✅ 模型已加载: {health['model_loaded']}")
        print(f"✅ 运行设备: {health['device']}")
    except Exception as e:
        print(f"❌ 健康检查失败: {e}")
        return
    
    print("\n" + "=" * 60)
    print("2. 获取模型信息")
    print("=" * 60)
    
    try:
        info = client.get_model_info()
        print(f"📊 模型名称: {info['model_name']}")
        print(f"📊 运行设备: {info['device']}")
        print(f"📊 梅尔频谱类型: {info['mel_spec_type']}")
        print(f"📊 目标采样率: {info['target_sample_rate']} Hz")
    except Exception as e:
        print(f"❌ 获取模型信息失败: {e}")
        return
    
    print("\n" + "=" * 60)
    print("3. TTS语音合成测试")
    print("=" * 60)
    
    # 准备示例音频和文本
    try:
        ref_audio_path = str(files("f5_tts").joinpath("infer/examples/basic/basic_ref_en.wav"))
        
        if not os.path.exists(ref_audio_path):
            print(f"❌ 找不到示例音频文件: {ref_audio_path}")
            print("请检查F5-TTS安装是否完整")
            return
        
        # 测试参数
        test_cases = [
            {
                "name": "英文合成测试",
                "ref_text": "some call me nature, others call me mother nature.",
                "gen_text": "Hello, this is a test of the F5-TTS API service. The quality sounds amazing!",
                "output": "api_test_english.wav",
                "speed": 1.0
            },
            {
                "name": "中英混合测试", 
                "ref_text": "some call me nature, others call me mother nature.",
                "gen_text": "你好，这是F5-TTS API服务的测试。Hello world, mixed language test.",
                "output": "api_test_mixed.wav",
                "speed": 1.2
            },
            {
                "name": "快速语音测试",
                "ref_text": "some call me nature, others call me mother nature.",
                "gen_text": "This is a fast speech synthesis test using the F5-TTS API.",
                "output": "api_test_fast.wav",
                "speed": 1.5
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n🎤 测试 {i}: {test_case['name']}")
            print(f"   参考文本: {test_case['ref_text']}")
            print(f"   生成文本: {test_case['gen_text']}")
            print(f"   语速倍率: {test_case['speed']}")
            
            start_time = time.time()
            
            try:
                result = client.synthesize_speech(
                    ref_audio_path=ref_audio_path,
                    ref_text=test_case['ref_text'],
                    gen_text=test_case['gen_text'],
                    output_path=test_case['output'],
                    speed=test_case['speed'],
                    seed=42  # 固定种子确保结果一致
                )
                
                end_time = time.time()
                
                print(f"   ✅ 合成成功!")
                print(f"   📁 输出文件: {result['output_path']}")
                print(f"   ⏱️  音频时长: {result['duration']}秒")
                print(f"   🔢 采样率: {result['sample_rate']} Hz")
                print(f"   🎲 随机种子: {result['seed']}")
                print(f"   ⏰ 处理时间: {end_time - start_time:.2f}秒")
                
            except Exception as e:
                print(f"   ❌ 合成失败: {e}")
    
    except Exception as e:
        print(f"❌ 语音合成测试初始化失败: {e}")
    
    print("\n" + "=" * 60)
    print("4. 音频转录测试")
    print("=" * 60)
    
    # 使用刚才生成的音频文件进行转录测试
    test_files = ["api_test_english.wav", "api_test_mixed.wav"]
    
    for test_file in test_files:
        if os.path.exists(test_file):
            print(f"\n🎧 转录测试: {test_file}")
            
            try:
                start_time = time.time()
                result = client.transcribe_audio(test_file)
                end_time = time.time()
                
                print(f"   ✅ 转录成功!")
                print(f"   📝 转录文本: {result['text']}")
                print(f"   🌐 检测语言: {result.get('language', 'auto')}")
                print(f"   ⏰ 处理时间: {end_time - start_time:.2f}秒")
                
            except Exception as e:
                print(f"   ❌ 转录失败: {e}")
        else:
            print(f"\n⚠️  跳过转录测试: {test_file} 不存在")
    
    print("\n" + "=" * 60)
    print("5. 性能和压力测试")
    print("=" * 60)
    
    # 简单的性能测试
    print("\n⚡ 执行连续合成性能测试...")
    
    try:
        ref_audio_path = str(files("f5_tts").joinpath("infer/examples/basic/basic_ref_en.wav"))
        
        if os.path.exists(ref_audio_path):
            num_tests = 3
            total_time = 0
            
            for i in range(num_tests):
                start_time = time.time()
                
                result = client.synthesize_speech(
                    ref_audio_path=ref_audio_path,
                    ref_text="some call me nature, others call me mother nature.",
                    gen_text=f"Performance test number {i+1}. Testing API response time and consistency.",
                    output_path=f"perf_test_{i+1}.wav",
                    speed=1.0,
                    seed=i  # 不同的种子
                )
                
                end_time = time.time()
                duration = end_time - start_time
                total_time += duration
                
                print(f"   测试 {i+1}/{num_tests}: {duration:.2f}秒 (音频时长: {result['duration']}秒)")
            
            avg_time = total_time / num_tests
            print(f"\n📊 性能统计:")
            print(f"   平均处理时间: {avg_time:.2f}秒")
            print(f"   总处理时间: {total_time:.2f}秒")
            print(f"   处理效率: {avg_time:.2f}秒/请求")
            
    except Exception as e:
        print(f"❌ 性能测试失败: {e}")
    
    print("\n" + "=" * 60)
    print("✨ 演示完成!")
    print("=" * 60)
    
    # 清理测试文件
    print("\n🧹 清理测试文件...")
    test_files = [
        "api_test_english.wav", "api_test_mixed.wav", "api_test_fast.wav",
        "perf_test_1.wav", "perf_test_2.wav", "perf_test_3.wav"
    ]
    
    for file in test_files:
        if os.path.exists(file):
            os.remove(file)
            print(f"   删除: {file}")
    
    print("\n🎉 所有测试完成! API服务运行正常。")
    print("\n📚 更多使用方法请参考:")
    print("   - API文档: http://localhost:8000/docs")
    print("   - 详细说明: src/f5_tts/API_README.md")


if __name__ == "__main__":
    main() 