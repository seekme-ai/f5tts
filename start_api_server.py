#!/usr/bin/env python3
"""
F5-TTS API服务器快速启动脚本
"""

import sys
import subprocess
import time
import webbrowser
import os
from pathlib import Path

# 添加src目录到Python路径
project_root = Path(__file__).parent
src_path = project_root / "src"
if src_path.exists():
    sys.path.insert(0, str(src_path))

def check_dependencies():
    """检查必要的依赖"""
    try:
        import fastapi
        import uvicorn
        # 尝试导入本地的f5_tts模块
        import f5_tts
        return True
    except ImportError as e:
        print(f"❌ 缺少必要依赖: {e}")
        print("\n请安装FastAPI相关依赖:")
        print("pip install fastapi uvicorn python-multipart requests")
        return False


def main():
    """主函数"""
    print("=" * 60)
    print("🚀 F5-TTS API服务器启动器")
    print("=" * 60)
    
    # 检查依赖
    if not check_dependencies():
        return 1
    
    print("✅ 依赖检查通过")
    
    # 启动服务器
    print("\n🔄 正在启动API服务器...")
    print("   地址: http://localhost:8000")
    print("   API文档: http://localhost:8000/docs")
    print("   停止服务: Ctrl+C")
    
    try:
        # 使用uvicorn直接启动API服务器
        import uvicorn
        
        # 延迟一秒后自动打开浏览器
        def open_browser():
            time.sleep(3)
            try:
                webbrowser.open("http://localhost:8000/docs")
                print("\n🌐 已自动打开API文档页面")
            except:
                pass
        
        import threading
        browser_thread = threading.Thread(target=open_browser, daemon=True)
        browser_thread.start()
        
        # 启动API服务器
        uvicorn.run(
            "f5_tts.api_server:app",
            host="0.0.0.0",
            port=8000,
            log_level="info"
        )
        
    except KeyboardInterrupt:
        print("\n\n👋 API服务器已停止")
        return 0
    except Exception as e:
        print(f"\n❌ 启动失败: {e}")
        print("\n💡 尝试手动运行:")
        print("cd src && python -m f5_tts.api_server")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 