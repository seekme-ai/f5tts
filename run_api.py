#!/usr/bin/env python3
"""
简单的F5-TTS API服务器启动脚本
直接运行，无需安装包
"""

import sys
import os
from pathlib import Path

# 确保能找到src目录
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

# 切换到src目录运行
os.chdir(src_path)

print("🚀 启动F5-TTS API服务器...")
print("📍 地址: http://localhost:8000")
print("📖 API文档: http://localhost:8000/docs")
print("⏹️  停止服务: Ctrl+C")
print()

try:
    # 直接执行api_server模块
    exec(open("f5_tts/api_server.py").read())
except KeyboardInterrupt:
    print("\n👋 服务器已停止")
except Exception as e:
    print(f"❌ 启动失败: {e}")
    print("\n尝试手动运行:")
    print("cd src && python f5_tts/api_server.py") 