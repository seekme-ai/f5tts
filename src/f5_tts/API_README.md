# F5-TTS FastAPI服务

基于FastAPI框架的F5-TTS语音合成API服务，提供TTS语音合成、音频转录等功能。

## 功能特性

- 🎯 **语音合成**: 基于参考音频和文本生成目标语音
- 🎤 **音频转录**: 将音频文件转录为文本
- 🏥 **健康检查**: 监控服务状态和模型加载情况  
- 📊 **模型信息**: 获取当前加载模型的详细信息
- 🌐 **REST API**: 标准化的HTTP接口
- 📖 **自动文档**: 自动生成的API文档
- 🔧 **易于集成**: 支持多种编程语言调用

## 快速开始

### 1. 安装依赖

```bash
# 安装F5-TTS及其依赖
pip install -e .

# 或者只安装FastAPI相关依赖
pip install fastapi uvicorn python-multipart requests
```

### 2. 启动API服务器

```bash
# 使用命令行工具启动
f5-tts_api-server

# 或者直接运行Python模块
python -m f5_tts.api_server

# 自定义配置启动
f5-tts_api-server --host 0.0.0.0 --port 8000 --workers 1
```

### 3. 访问API文档

服务启动后，访问以下地址查看API文档：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API端点

### 1. 健康检查

```bash
GET /health
```

检查服务状态和模型加载情况。

**响应示例:**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "device": "cuda"
}
```

### 2. 获取模型信息

```bash
GET /model/info
```

获取当前加载模型的详细信息。

**响应示例:**
```json
{
  "model_name": "F5TTS_v1_Base",
  "device": "cuda",
  "mel_spec_type": "vocos",
  "target_sample_rate": 24000
}
```

### 3. 语音合成

```bash
POST /tts/synthesize
```

**请求参数:**
- `ref_audio`: 参考音频文件 (form-data文件上传)
- `request_data`: JSON格式的合成参数 (form-data字符串)

**request_data JSON结构:**
```json
{
  "ref_text": "参考音频对应的文本",
  "gen_text": "要生成的目标文本",
  "target_rms": 0.1,
  "cross_fade_duration": 0.15,
  "speed": 1.0,
  "nfe_step": 32,
  "cfg_strength": 2.0,
  "sway_sampling_coef": -1,
  "remove_silence": false,
  "seed": null
}
```

**响应:**
- 返回WAV格式的音频文件流
- 响应头包含音频信息：
  - `X-Audio-Duration`: 音频时长(秒)
  - `X-Sample-Rate`: 采样率
  - `X-Seed`: 使用的随机种子

### 4. 音频转录

```bash
POST /tts/transcribe
```

**请求参数:**
- `audio`: 要转录的音频文件 (form-data文件上传)
- `language`: 指定语言代码，可选 (form-data字符串)

**响应示例:**
```json
{
  "text": "转录得到的文本内容",
  "language": "zh"
}
```

## 使用示例

### Python客户端

使用内置的Python客户端：

```python
from f5_tts.api_client import F5TTSClient

# 创建客户端
client = F5TTSClient("http://localhost:8000")

# 健康检查
health = client.health_check()
print(f"服务状态: {health['status']}")

# 语音合成
result = client.synthesize_speech(
    ref_audio_path="reference_audio.wav",
    ref_text="这是参考音频的文本",
    gen_text="这是要生成的目标文本",
    output_path="output.wav",
    speed=1.0,
    seed=42
)
print(f"合成完成: {result['output_path']}")

# 音频转录
transcription = client.transcribe_audio("audio_file.wav")
print(f"转录结果: {transcription['text']}")
```

### 命令行客户端

```bash
# 运行演示
python -m f5_tts.api_client demo

# 健康检查
python -m f5_tts.api_client --action health

# 获取模型信息
python -m f5_tts.api_client --action info

# 语音合成
python -m f5_tts.api_client --action synthesize \
  --ref-audio reference.wav \
  --ref-text "参考音频文本" \
  --gen-text "要生成的文本" \
  --output output.wav \
  --speed 1.0 \
  --seed 42

# 音频转录
python -m f5_tts.api_client --action transcribe \
  --audio audio_file.wav \
  --language zh
```

### cURL示例

```bash
# 健康检查
curl http://localhost:8000/health

# 获取模型信息
curl http://localhost:8000/model/info

# 语音合成
curl -X POST "http://localhost:8000/tts/synthesize" \
  -F "ref_audio=@reference.wav" \
  -F "request_data={\"ref_text\":\"参考文本\",\"gen_text\":\"目标文本\"}" \
  --output output.wav

# 音频转录
curl -X POST "http://localhost:8000/tts/transcribe" \
  -F "audio=@audio_file.wav" \
  -F "language=zh"
```

### JavaScript (Node.js)

```javascript
const FormData = require('form-data');
const fs = require('fs');
const axios = require('axios');

// 语音合成
async function synthesizeSpeech() {
  const form = new FormData();
  form.append('ref_audio', fs.createReadStream('reference.wav'));
  form.append('request_data', JSON.stringify({
    ref_text: "参考音频文本",
    gen_text: "要生成的文本",
    speed: 1.0
  }));

  const response = await axios.post('http://localhost:8000/tts/synthesize', form, {
    headers: form.getHeaders(),
    responseType: 'stream'
  });

  response.data.pipe(fs.createWriteStream('output.wav'));
}
```

## 配置选项

### 服务器启动参数

```bash
f5-tts_api-server --help
```

**可用参数:**
- `--host`: 服务器主机地址 (默认: 0.0.0.0)
- `--port`: 服务器端口 (默认: 8000)
- `--workers`: 工作进程数 (默认: 1)
- `--reload`: 开发模式，代码变更时自动重载
- `--log-level`: 日志级别 (默认: info)

### TTS合成参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `ref_text` | string | - | 参考音频对应的文本 |
| `gen_text` | string | - | 要生成的目标文本 |
| `target_rms` | float | 0.1 | 目标音量RMS值 (0.0-1.0) |
| `cross_fade_duration` | float | 0.15 | 交叉淡化时长(秒) |
| `speed` | float | 1.0 | 语速倍率 (0.1-3.0) |
| `nfe_step` | int | 32 | NFE步数 (1-128) |
| `cfg_strength` | float | 2.0 | CFG强度 (0.0-10.0) |
| `sway_sampling_coef` | float | -1 | 摆动采样系数 |
| `remove_silence` | bool | false | 是否移除静音部分 |
| `seed` | int | null | 随机种子，null为随机 |

## 错误处理

API使用标准HTTP状态码：

- `200`: 请求成功
- `400`: 请求参数错误
- `422`: 请求数据验证失败
- `500`: 服务器内部错误
- `503`: 服务不可用(模型未加载)

**错误响应格式:**
```json
{
  "detail": "错误详细信息"
}
```

## 性能优化

1. **模型预加载**: 服务启动时自动加载模型，避免首次请求延迟
2. **GPU加速**: 自动检测并使用可用的GPU设备
3. **临时文件管理**: 自动清理处理过程中的临时文件
4. **流式响应**: 音频文件以流式方式返回，减少内存占用

## 注意事项

1. **文件格式**: 支持常见的音频格式 (WAV, MP3, FLAC等)
2. **文件大小**: 建议参考音频文件大小控制在10MB以内
3. **并发限制**: 默认使用单进程，高并发场景建议增加workers数量
4. **内存使用**: TTS模型占用较多显存，确保GPU内存充足
5. **网络超时**: 长文本合成可能需要较长时间，适当调整客户端超时设置

## 部署建议

### 生产环境

```bash
# 使用Gunicorn部署
pip install gunicorn
gunicorn f5_tts.api_server:app -w 2 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000

# 使用Docker (需要先创建Dockerfile)
docker build -t f5-tts-api .
docker run -p 8000:8000 --gpus all f5-tts-api
```

### 反向代理

```nginx
# Nginx配置示例
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        client_max_body_size 50M;
        proxy_read_timeout 300s;
    }
}
```

## 故障排除

### 常见问题

1. **模型加载失败**
   - 检查网络连接，确保能够下载Hugging Face模型
   - 检查磁盘空间是否充足
   - 检查CUDA环境是否正确配置

2. **合成质量问题**
   - 确保参考音频质量良好，无明显噪音
   - 参考文本与音频内容一致
   - 调整CFG强度和NFE步数参数

3. **性能问题**
   - 使用GPU加速
   - 调整batch size和worker数量
   - 监控CPU和内存使用情况

### 日志调试

```bash
# 启动时启用详细日志
f5-tts_api-server --log-level debug

# 查看模型加载日志
tail -f /path/to/log/file
```

## 贡献

欢迎提交Issues和Pull Requests来改进这个API服务！

## 许可证

MIT License - 详见LICENSE文件。 