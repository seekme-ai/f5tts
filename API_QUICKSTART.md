# F5-TTS API 快速开始指南

本指南将帮助你快速开始使用F5-TTS的FastAPI服务。

## 🚀 一键启动

### 方法1: 使用快速启动脚本 (推荐)

```bash
python start_api_server.py
```

### 方法2: 使用命令行工具

```bash
# 如果已安装包
f5-tts_api-server

# 或直接运行模块
python -m f5_tts.api_server
```

### 方法3: 自定义配置

```bash
python -m f5_tts.api_server --host 0.0.0.0 --port 8000 --workers 1
```

## 📖 查看API文档

启动服务后，访问以下地址：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🧪 运行测试示例

```bash
# 运行完整的演示测试
python examples/api_usage_example.py

# 或者运行简单的客户端测试
python -m f5_tts.api_client demo
```

## 💡 基本用法示例

### Python客户端

```python
from f5_tts.api_client import F5TTSClient

# 创建客户端
client = F5TTSClient("http://localhost:8000")

# 语音合成
result = client.synthesize_speech(
    ref_audio_path="reference.wav",
    ref_text="参考音频的文本",
    gen_text="要生成的文本",
    output_path="output.wav"
)
print(f"合成完成: {result['output_path']}")
```

### cURL示例

```bash
# 健康检查
curl http://localhost:8000/health

# 语音合成
curl -X POST "http://localhost:8000/tts/synthesize" \
  -F "ref_audio=@reference.wav" \
  -F "request_data={\"ref_text\":\"参考文本\",\"gen_text\":\"目标文本\"}" \
  --output output.wav
```

## 📋 API端点总览

| 端点 | 方法 | 描述 |
|------|------|------|
| `/health` | GET | 健康检查 |
| `/model/info` | GET | 获取模型信息 |
| `/tts/synthesize` | POST | TTS语音合成 |
| `/tts/transcribe` | POST | 音频转录 |

## 🔧 主要功能

1. **语音合成**: 上传参考音频+文本，生成目标语音
2. **音频转录**: 上传音频文件，获取转录文本
3. **模型信息**: 查看当前加载的模型状态
4. **健康监控**: 检查服务运行状态

## 📚 详细文档

- 完整API文档: [src/f5_tts/API_README.md](src/f5_tts/API_README.md)
- 使用示例: [examples/api_usage_example.py](examples/api_usage_example.py)

## ⚠️ 注意事项

1. 首次启动需要下载模型，可能需要几分钟
2. 确保有足够的GPU内存（推荐8GB+）
3. 参考音频建议为高质量、无噪音的WAV文件
4. 参考文本需要与音频内容一致

## 🐛 故障排除

**模型加载失败**: 检查网络连接和磁盘空间
**合成质量差**: 确保参考音频质量良好
**启动失败**: 运行 `pip install -e .` 安装依赖

## 🎉 开始使用

运行以下命令开始你的TTS之旅：

```bash
python start_api_server.py
```

然后在另一个终端运行测试：

```bash
python examples/api_usage_example.py
```

祝你使用愉快！🎤✨ 