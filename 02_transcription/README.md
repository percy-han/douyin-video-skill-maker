# 🎤 视频转录模块

将S3中的抖音视频转录为文本（使用Whisper）。

## ⚡ 快速开始

### 1. 启动GPU实例

**推荐配置**：
- 实例类型：`g4dn.xlarge`（NVIDIA T4 GPU）
- 操作系统：Ubuntu 22.04 LTS
- 磁盘：30GB EBS
- IAM角色：需要S3读写权限和Bedrock调用权限

**使用Spot实例节省70%成本**：
```bash
aws ec2 run-instances \
    --instance-type g4dn.xlarge \
    --image-id ami-0c55b159cbfafe1f0 \
    --instance-market-options "MarketType=spot" \
    --iam-instance-profile Name=EC2-S3-Bedrock-FullAccess \
    --key-name your-key-pair
```

### 2. 安装环境

SSH登录到实例后：

```bash
# 克隆仓库
git clone https://github.com/percy-han/douyin-video-skill-maker.git
cd douyin-video-skill-maker/02_transcription

# 安装依赖
./setup_gpu_instance.sh
```

### 3. 配置环境变量

```bash
export S3_BUCKET=your-bucket-name
export S3_PREFIX=douyin_videos/20260417_150000/
export WHISPER_MODEL=large  # 可选: large, medium, base
```

### 4. 执行转录

```bash
python3 batch_transcribe_s3.py
```

---

## 📊 处理流程

```
1. 扫描S3视频文件（只处理.mp4等视频）
2. 逐个下载 → Whisper转录
3. 保存txt/srt/json到S3
4. 删除本地临时文件，继续下一个
5. 生成transcription_summary.json总结
```

---

## 📂 输出格式

每个视频生成3个文件（文件名与原视频对应）：

### 1. 纯文本 (`*_transcript.txt`)

```
人民币升值下，为什么出口暴涨？未来这个优势将会更大。

首先我们要理解，人民币升值通常会降低出口竞争力...
```

**用途**：知识库构建、向量化

### 2. SRT字幕 (`*_transcript.srt`)

```
1
00:00:00,000 --> 00:00:03,500
人民币升值下，为什么出口暴涨？

2
00:00:03,500 --> 00:00:07,200
未来这个优势将会更大。
```

**用途**：视频播放字幕、精确定位

### 3. 完整JSON (`*_transcript.json`)

```json
{
  "video_metadata": {
    "original_filename": "2026-04-03 19-05-58_这活没法干_video.mp4",
    "s3_key": "douyin_videos/.../video.mp4",
    "title": "这活没法干",
    "publish_date": "2026-04-03",
    "publish_time": "19:05:58",
    "publish_timestamp": 1775432758
  },
  "transcription": {
    "text": "完整转录文本...",
    "language": "zh",
    "segments": [
      {
        "id": 0,
        "start": 0.0,
        "end": 3.5,
        "text": "人民币升值下，为什么出口暴涨？"
      }
    ]
  },
  "processing": {
    "transcribed_at": "2026-04-17T16:30:00Z",
    "processing_time_seconds": 36.5,
    "model": "large"
  }
}
```

**用途**：程序处理、后续认知提取

---

## 📋 智能文件过滤

脚本自动过滤S3文件，只处理视频：

**处理的文件**：
- ✅ `*_video.mp4`
- ✅ `*.webm`, `*.mkv`

**跳过的文件**：
- ❌ `*_desc.txt`（文案）
- ❌ `*_cover.webp`（封面）
- ❌ `*_audio.m4a`（音频）
- ❌ `*_transcript.*`（已转录的）

---

## 🔄 断点续传

脚本会检查S3中是否已存在 `*_transcript.json`：
- 如果存在 → 跳过
- 如果不存在 → 转录

**重新执行时会自动跳过已完成的视频**。

---

## 💰 成本估算

### GPU实例成本

**g4dn.xlarge**（NVIDIA T4）:
- 按需价格：$0.526/小时
- Spot价格：$0.158/小时（节省70%）⭐

### 转录速度

- 实时因子：10-15x（1小时视频 → 4-6分钟）
- 100小时视频 → 6-10小时处理时间

### 实际成本（300个5分钟视频）

```
总时长：25小时
转录时间：25小时 ÷ 12 = ~2小时

Spot实例成本：
  2小时 × $0.158 = $0.32

总成本：~$0.32（极低成本）
```

---

## 🐛 故障排查

### GPU不可用

```bash
# 检查NVIDIA驱动
nvidia-smi

# 检查PyTorch CUDA支持
python3 -c "import torch; print(torch.cuda.is_available())"
```

如果失败，重新安装CUDA驱动：
```bash
# Ubuntu
sudo apt install nvidia-driver-535
```

### S3权限错误

确保IAM角色包含：
```json
{
  "Effect": "Allow",
  "Action": [
    "s3:GetObject",
    "s3:PutObject",
    "s3:ListBucket"
  ],
  "Resource": [
    "arn:aws:s3:::your-bucket-name/*",
    "arn:aws:s3:::your-bucket-name"
  ]
}
```

### 内存不足

如果遇到 `OutOfMemoryError`：

```bash
# 改用medium模型（更省内存）
export WHISPER_MODEL=medium
python3 batch_transcribe_s3.py
```

---

## 📈 性能优化

### 使用FP16半精度

Whisper默认使用FP16（在CUDA上自动启用），速度提升30%。

### 预加载下一个视频

脚本按顺序处理视频，可以改进为：
- 主线程：转录当前视频
- 后台线程：预下载下一个视频

（暂未实现，后续可优化）

---

## 🎯 下一步

转录完成后：
1. ✅ S3中有完整的转录文本
2. ➡️ 执行认知合成（`../03_cognitive_synthesis/`）
3. ➡️ 生成SKILL.md

---

## 📄 相关文档

- 实现方案：`IMPLEMENTATION_PLAN.md`
- V2增强版：`IMPLEMENTATION_PLAN_V2.md`
- 认知合成：`../03_cognitive_synthesis/README.md`
