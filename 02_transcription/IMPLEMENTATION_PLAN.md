# 🎤 Whisper转录模块 - 实现方案

## 📋 整体架构

```
S3视频文件
    ↓ 下载
GPU EC2实例 (g4dn.xlarge)
    ↓ Whisper转录
本地临时文件
    ↓ 上传
S3文本文件
    ↓ 清理
释放本地存储
```

## 🎯 设计目标

1. **高效**: GPU加速，1小时视频 → 3-5分钟转录
2. **经济**: 边下载边转录边删除，节省存储和成本
3. **准确**: 使用Large模型，准确率96-98%
4. **可恢复**: 支持断点续传，已转录的不重复
5. **易用**: 一键启动，自动化完整流程

## 📊 流程设计

### 方案对比

#### 方案A：批量下载 → 批量转录（不推荐）

```
1. 从S3下载所有视频（100GB+）
2. 逐个转录
3. 上传所有文本
4. 删除本地文件
```

**缺点**：
- ❌ 需要大量存储空间（100GB+）
- ❌ 如果中断，重新开始需要重新下载
- ❌ 成本高（需要更大的EBS）

#### 方案B：流式处理（推荐）⭐

```
for each video in S3:
    1. 下载单个视频
    2. 转录
    3. 上传文本
    4. 删除本地视频
    5. 继续下一个
```

**优点**：
- ✅ 存储需求小（只需5-10GB临时空间）
- ✅ 可随时中断恢复
- ✅ 节省成本

---

## 🏗️ 核心组件设计

### 1. S3管理器 (`S3Manager`)

**职责**：处理S3文件操作

```python
class S3Manager:
    def list_videos(bucket, prefix):
        """列出S3中所有视频文件"""
        
    def download_video(bucket, key, local_path):
        """下载单个视频到本地"""
        
    def upload_transcript(bucket, key, local_path):
        """上传转录文本到S3"""
        
    def check_exists(bucket, key):
        """检查文件是否已存在（避免重复）"""
```

### 2. Whisper转录器 (`WhisperTranscriber`)

**职责**：视频转文字

```python
class WhisperTranscriber:
    def __init__(model_size="large"):
        self.model = whisper.load_model(model_size)
        
    def transcribe(video_path):
        """转录视频，返回文本和字幕"""
        result = self.model.transcribe(
            video_path,
            language="zh",
            task="transcribe",
            temperature=0.0,
            best_of=5,
            beam_size=5
        )
        return result
        
    def save_outputs(result, output_dir):
        """保存多种格式：txt, srt, json"""
```

### 3. 批处理协调器 (`BatchProcessor`)

**职责**：协调整个流程

```python
class BatchProcessor:
    def __init__(s3_bucket, s3_prefix, output_prefix):
        self.s3_manager = S3Manager()
        self.transcriber = WhisperTranscriber()
        
    def process_all():
        """处理S3中所有视频"""
        videos = self.s3_manager.list_videos()
        
        for video in videos:
            if self.already_processed(video):
                continue
                
            # 下载
            local_path = self.download(video)
            
            # 转录
            result = self.transcriber.transcribe(local_path)
            
            # 保存
            self.save_and_upload(result, video)
            
            # 清理
            os.remove(local_path)
```

---

## 📂 输出格式设计

### 目录结构

**输入（S3）**：
```
s3://bucket/douyin_videos/20260417/
├── 视频1_标题/
│   ├── 视频1.mp4           # 输入
│   ├── 视频1.txt           # 文案
│   └── 视频1.jpg           # 封面
└── 视频2_标题/
    └── ...
```

**输出（S3）**：
```
s3://bucket/douyin_videos/20260417/
├── 视频1_标题/
│   ├── 视频1.mp4
│   ├── 视频1.txt
│   ├── 视频1.jpg
│   ├── 视频1_transcript.txt       # 纯文本转录 ⭐
│   ├── 视频1_transcript.srt       # SRT字幕 ⭐
│   └── 视频1_transcript.json      # 详细数据 ⭐
└── transcription_summary.json     # 转录总结 ⭐
```

### 文件格式

#### 1. 纯文本 (`*_transcript.txt`)

```
人民币升值下，为什么出口暴涨？未来这个优势将会更大。

首先我们要理解，人民币升值通常会降低出口竞争力，但是在当前的市场环境下...

（完整转录内容）
```

**用途**：知识库构建、向量化

#### 2. SRT字幕 (`*_transcript.srt`)

```
1
00:00:00,000 --> 00:00:03,500
人民币升值下，为什么出口暴涨？

2
00:00:03,500 --> 00:00:07,200
未来这个优势将会更大。

3
00:00:07,200 --> 00:00:12,800
首先我们要理解，人民币升值通常会降低出口竞争力
```

**用途**：视频播放时显示字幕、精确定位

#### 3. JSON详细数据 (`*_transcript.json`)

```json
{
  "video_id": "7628595926097914212",
  "title": "人民币升值下，为什么出口暴涨",
  "duration": 324.5,
  "transcription": {
    "text": "完整文本...",
    "segments": [
      {
        "id": 0,
        "start": 0.0,
        "end": 3.5,
        "text": "人民币升值下，为什么出口暴涨？",
        "confidence": 0.98
      }
    ]
  },
  "metadata": {
    "model": "large-v3",
    "language": "zh",
    "duration": 324.5,
    "transcribed_at": "2026-04-17T16:30:00Z"
  }
}
```

**用途**：程序处理、分析统计

#### 4. 总结文件 (`transcription_summary.json`)

```json
{
  "batch_id": "20260417_163000",
  "total_videos": 156,
  "transcribed": 156,
  "failed": 0,
  "total_duration_seconds": 28080,
  "total_characters": 845230,
  "processing_time_seconds": 5640,
  "cost_estimate_usd": 3.2,
  "videos": [
    {
      "filename": "视频1.mp4",
      "status": "success",
      "duration": 180,
      "characters": 5420,
      "processing_time": 36
    }
  ]
}
```

---

## ⚙️ 关键参数配置

### Whisper参数优化（财经视频）

```python
transcribe_params = {
    "language": "zh",              # 中文
    "task": "transcribe",          # 转录任务
    "temperature": 0.0,            # 降低随机性
    "best_of": 5,                  # 多次采样取最佳
    "beam_size": 5,                # Beam search宽度
    "patience": 1.0,               # 搜索耐心
    "length_penalty": 1.0,         # 长度惩罚
    "compression_ratio_threshold": 2.4,  # 压缩比阈值
    "logprob_threshold": -1.0,     # 对数概率阈值
    "no_speech_threshold": 0.6,    # 无语音阈值
    "condition_on_previous_text": True,  # 上下文感知
    "initial_prompt": "这是一段关于财经、金融、经济的视频内容。" # 引导提示
}
```

**关键优化点**：
- `temperature=0.0`: 确保输出稳定，不随机
- `best_of=5`: 多次尝试取最佳，提高准确率
- `beam_size=5`: 平衡速度和质量
- `initial_prompt`: 引导模型识别财经术语

### 批处理参数

```python
batch_config = {
    "concurrent_downloads": 2,     # 同时下载2个视频（预加载）
    "max_retries": 3,              # 失败重试3次
    "retry_delay": 60,             # 重试延迟60秒
    "temp_storage_gb": 10,         # 临时存储10GB
    "chunk_size": 1024*1024*8,     # 下载块大小8MB
}
```

---

## 💰 成本估算

### GPU实例成本

**实例**: g4dn.xlarge
- GPU: NVIDIA T4 (16GB)
- vCPU: 4核
- 内存: 16GB
- 价格: $0.526/小时

**Spot价格**: $0.1578/小时（便宜70%）⭐

### 转录速度

- **实时因子**: 约10-15x（1小时视频 → 4-6分钟）
- **批处理**: 100小时视频 → 6-10小时

### 成本计算

**300个视频（每个5分钟，共25小时）**：

```
方案1: 按需实例
- 转录时间: 25小时 ÷ 12 = ~2小时
- 成本: 2小时 × $0.526 = $1.05

方案2: Spot实例（推荐）⭐
- 转录时间: ~2小时
- 成本: 2小时 × $0.158 = $0.32
```

**S3存储**：
- 文本文件：~50MB（可忽略）
- 成本: < $0.01/月

**总成本：~$0.32**（极低！）

---

## 🚀 执行流程

### 阶段1：环境准备

```bash
# 1. 启动GPU实例（Spot）
aws ec2 run-instances \
    --instance-type g4dn.xlarge \
    --instance-market-options "MarketType=spot"

# 2. 安装依赖
pip install openai-whisper boto3 torch

# 3. 验证GPU
python -c "import torch; print(torch.cuda.is_available())"
```

### 阶段2：执行转录

```bash
# 一键执行
python3 batch_transcribe_s3.py \
    --s3-bucket percyhan-douyin-video \
    --s3-prefix douyin_videos/20260417/ \
    --model large \
    --output-bucket percyhan-douyin-video
```

### 阶段3：验证结果

```bash
# 检查转录文件
aws s3 ls s3://bucket/path/ --recursive | grep transcript

# 下载总结文件
aws s3 cp s3://bucket/path/transcription_summary.json .

# 查看统计
cat transcription_summary.json
```

---

## 🔄 断点续传设计

### 状态跟踪

创建 `transcription_state.json` 记录进度：

```json
{
  "started_at": "2026-04-17T16:00:00Z",
  "last_updated": "2026-04-17T17:30:00Z",
  "processed_videos": [
    "视频1.mp4",
    "视频2.mp4"
  ],
  "failed_videos": [
    {
      "filename": "视频3.mp4",
      "error": "FileNotFoundError",
      "retry_count": 2
    }
  ],
  "pending_videos": [
    "视频4.mp4",
    "视频5.mp4"
  ]
}
```

### 恢复机制

```python
def resume_transcription():
    """从上次中断处恢复"""
    state = load_state("transcription_state.json")
    
    # 跳过已处理的
    pending = state["pending_videos"]
    
    # 重试失败的（最多3次）
    retry = [v for v in state["failed_videos"] if v["retry_count"] < 3]
    
    # 继续处理
    process_videos(pending + retry)
```

---

## 📈 性能优化

### 1. 预加载机制

```python
# 当前视频转录时，后台下载下一个
with ThreadPoolExecutor(max_workers=2) as executor:
    # 主线程：转录
    transcribe(current_video)
    
    # 后台线程：预加载
    executor.submit(download, next_video)
```

### 2. 批量上传

```python
# 积累多个文本文件后批量上传
text_files = []
for video in videos:
    text_files.append(transcribe(video))
    
    if len(text_files) >= 10:
        batch_upload(text_files)
        text_files = []
```

### 3. GPU优化

```python
# 使用FP16半精度（速度提升30%）
model = whisper.load_model("large", device="cuda", fp16=True)
```

---

## 🐛 错误处理

### 常见错误和处理

```python
try:
    transcribe(video)
except OutOfMemoryError:
    # GPU内存不足：使用medium模型
    fallback_to_medium_model()
except FileNotFoundError:
    # S3文件不存在：跳过
    log_and_skip(video)
except Exception as e:
    # 其他错误：重试3次
    retry_with_backoff(video, max_retries=3)
```

---

## 📊 监控和日志

### 实时进度显示

```
========================================
🎤 批量转录进度
========================================
总视频: 156
已完成: 45 (28.8%)
进行中: 视频46.mp4 (42%)
失败: 2
预估剩余: 3小时15分

当前: 视频46_人民币升值分析.mp4
  时长: 5分23秒
  已处理: 2分16秒 (42%)
  预估完成: 3分钟后

========================================
```

### 日志文件

```
logs/
├── transcription.log           # 主日志
├── errors.log                  # 错误日志
└── performance.log             # 性能统计
```

---

## 🎯 最终交付物

运行完成后，你会得到：

```
S3完整结构：
s3://bucket/douyin_videos/20260417/
├── 视频1_标题/
│   ├── 视频1.mp4                       # 原视频
│   ├── 视频1.txt                       # 原文案
│   ├── 视频1.jpg                       # 封面
│   ├── 视频1_transcript.txt           # ⭐ 纯文本
│   ├── 视频1_transcript.srt           # ⭐ SRT字幕
│   └── 视频1_transcript.json          # ⭐ 详细数据
├── ... (所有视频)
└── transcription_summary.json         # ⭐ 总结
```

---

## 🤔 你的Review重点

请重点review以下设计：

1. **架构设计**：流式处理 vs 批量处理
2. **输出格式**：txt + srt + json 是否足够？
3. **成本估算**：~$0.32 是否可接受？
4. **错误处理**：重试机制是否完善？
5. **断点续传**：状态跟踪设计是否合理？

有任何疑问或建议都可以提！我会根据你的反馈调整后再写代码。🚀
