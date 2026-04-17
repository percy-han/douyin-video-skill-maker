# 🚀 视频转录快速启动指南

## 前提条件

### 必需
- ✅ AWS账号（有权限启动EC2和访问S3）
- ✅ AWS CLI已配置
- ✅ SSH密钥对（用于连接EC2）
- ✅ 视频已上传到S3

### 可选
- GPU驱动和CUDA（如果使用Deep Learning AMI则不需要手动安装）

---

## 方案选择

### 方案A：使用Deep Learning AMI（推荐）⭐

**优势**：
- ✅ 开箱即用（预装NVIDIA驱动、CUDA、PyTorch）
- ✅ 版本匹配（AWS测试过的稳定组合）
- ✅ 节省时间（5分钟完成环境配置）

**成本**：
- g4dn.xlarge Spot: $0.158/小时
- 300个5分钟视频（25小时）→ 2小时转录 → **$0.32**

### 方案B：普通Ubuntu（不推荐）

**劣势**：
- ❌ 需要手动安装NVIDIA驱动（容易出错）
- ❌ 需要重启系统
- ❌ 版本兼容性问题

**仅在必须使用现有实例时选择此方案。**

---

## 🎯 完整流程（方案A：Deep Learning AMI）

### 步骤1：启动GPU实例

```bash
# 克隆仓库（本地）
git clone https://github.com/percy-han/douyin-video-skill-maker.git
cd douyin-video-skill-maker/02_transcription

# 启动GPU实例
./launch_gpu_instance.sh your-key-pair your-security-group

# 输出示例：
# ✅ GPU实例启动成功！
# SSH连接命令:
#   ssh -i ~/.ssh/your-key-pair.pem ubuntu@54.123.45.67
```

**脚本自动完成**：
- 查找最新的Deep Learning AMI（Ubuntu 22.04）
- 启动g4dn.xlarge Spot实例
- 等待实例就绪
- 显示SSH连接信息

**预计时间**：2-3分钟

---

### 步骤2：配置环境

SSH登录到GPU实例：

```bash
ssh -i ~/.ssh/your-key-pair.pem ubuntu@54.123.45.67
```

克隆仓库并配置：

```bash
# 克隆仓库
git clone https://github.com/percy-han/douyin-video-skill-maker.git
cd douyin-video-skill-maker/02_transcription

# 配置环境（一键完成）
./setup_gpu_instance.sh
```

**脚本自动完成**：
- 检测并激活PyTorch环境（venv或conda）
- 检查GPU驱动
- 验证CUDA和PyTorch
- 安装Whisper和依赖
- 验证AWS凭证
- 配置环境自动激活（下次登录自动激活）

**预计时间**：3-5分钟

**输出示例**：
```
🎉 环境配置完成！
================================================

环境信息:
  环境类型: PyTorch虚拟环境
  Python: Python 3.10.12
  PyTorch: 2.2.1+cu121
  CUDA: 12.1
  Whisper: 20231117
  Boto3: 1.34.69
  GPU: Tesla T4

⚠️  重要：
  - 当前使用虚拟环境中的python命令
  - 执行脚本时使用: python batch_transcribe_s3.py（不是python3）
  - 下次登录时会自动激活虚拟环境
```

---

### 步骤3：执行转录

配置环境变量：

```bash
export S3_BUCKET=your-bucket-name
export S3_PREFIX=douyin_videos/20260417_150000/
export WHISPER_MODEL=large  # 可选: large, medium, base
```

执行转录：

```bash
# 注意：如果使用PyTorch虚拟环境，使用python而非python3
python batch_transcribe_s3.py

# 如果使用系统Python，使用python3
# python3 batch_transcribe_s3.py
```

**处理流程**：
```
1. 扫描S3视频文件（只处理.mp4等视频）
   ↓
2. 逐个下载到本地临时目录
   ↓
3. Whisper转录（GPU加速）
   ↓
4. 保存TXT + SRT + JSON到S3
   ↓
5. 删除本地临时文件
   ↓
6. 继续下一个（断点续传）
```

**预计时间**：
- 单个5分钟视频：30-40秒
- 300个5分钟视频：2-3小时

**实时输出**：
```
🎬 批量视频转录 + 认知提取
============================================================
S3: s3://your-bucket/douyin_videos/20260417/

📥 从S3加载转录结果...
   找到 156 个视频文件

============================================================
[1/156] 处理: 人民币升值_为什么出口暴涨
发布时间: 2026-04-03 19:05:58
文件大小: 5.5 MB
============================================================
   📥 下载视频...
   ✅ 下载完成 (5.5 MB)
   🎤 开始转录...
   ✅ 转录完成 (36.5秒)
   📝 文本长度: 1520 字符
   💾 保存结果...
   ☁️  上传到S3...
   ✅ 处理完成

============================================================
[2/156] 处理: 美联储降息预期分析
...
```

---

### 步骤4：验证结果

检查S3输出：

```bash
# 查看转录文件
aws s3 ls s3://your-bucket/douyin_videos/20260417/ --recursive | grep transcript

# 下载查看
aws s3 cp s3://your-bucket/douyin_videos/20260417/transcription_summary.json ./
cat transcription_summary.json
```

**输出结构**：
```
s3://bucket/douyin_videos/20260417/
├── 2026-04-03 19-05-58_这活没法干/
│   ├── 2026-04-03 19-05-58_这活没法干_video.mp4
│   ├── 2026-04-03 19-05-58_这活没法干_transcript.txt      # ⭐ 纯文本
│   ├── 2026-04-03 19-05-58_这活没法干_transcript.srt      # ⭐ 字幕
│   └── 2026-04-03 19-05-58_这活没法干_transcript.json     # ⭐ 完整数据
├── ...（所有视频）
└── transcription_summary.json                              # ⭐ 总结
```

---

### 步骤5：清理资源

**转录完成后，记得终止实例**：

```bash
# 获取实例ID
aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=whisper-transcription" \
  --query 'Reservations[0].Instances[0].InstanceId' \
  --output text

# 终止实例
aws ec2 terminate-instances --instance-ids i-xxxxx
```

---

## 🐛 常见问题

### Q1: GPU不可用

**检查GPU**：
```bash
nvidia-smi
```

**如果报错**：
```bash
# 检查是否使用了Deep Learning AMI
cat /etc/os-release

# 如果不是DL AMI，手动安装驱动
sudo apt update
sudo apt install -y nvidia-driver-535
sudo reboot  # 必须重启
```

### Q2: PyTorch CUDA不可用

**检查PyTorch**：
```bash
python3 -c "import torch; print(torch.cuda.is_available())"
```

**如果输出False**：
```bash
# 重新安装PyTorch（CUDA版本）
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### Q3: 内存不足

**错误信息**：`OutOfMemoryError`

**解决方案**：
```bash
# 改用medium模型（省内存）
export WHISPER_MODEL=medium
python3 batch_transcribe_s3.py
```

### Q4: S3权限错误

**错误信息**：`AccessDenied`

**解决方案**：
```bash
# 检查IAM角色权限
aws sts get-caller-identity

# 确保有S3读写权限：
# - s3:GetObject
# - s3:PutObject
# - s3:ListBucket
```

### Q5: 转录速度慢

**检查是否使用GPU**：
```bash
# 转录时运行nvidia-smi
nvidia-smi

# 应该看到Python进程使用GPU
```

**如果GPU利用率低**：
- 可能网络慢（下载视频）
- 可能磁盘慢（使用gp3而非gp2）

---

## 💰 成本控制

### 实时查看成本

```bash
# 查看Spot实例价格
aws ec2 describe-spot-price-history \
  --instance-types g4dn.xlarge \
  --product-descriptions "Linux/UNIX" \
  --query 'SpotPriceHistory[0].SpotPrice'

# 查看实例运行时间
aws ec2 describe-instances \
  --instance-ids i-xxxxx \
  --query 'Reservations[0].Instances[0].LaunchTime'
```

### 成本优化建议

1. **使用Spot实例**：节省70%（$0.526 → $0.158）
2. **及时终止实例**：转录完成后立即终止
3. **批量处理**：避免频繁启停实例
4. **使用medium模型**：如果large太慢

**300个5分钟视频的成本**：
- GPU实例（2小时）：$0.32
- S3存储（100GB）：$2.30/月
- **总计：~$3**

---

## 📊 性能参考

### GPU性能对比

| GPU型号 | 实例类型 | Spot价格 | 转录速度 | 推荐 |
|---------|---------|---------|---------|------|
| Tesla T4 | g4dn.xlarge | $0.158/h | 10-15x | ⭐ 推荐 |
| Tesla V100 | p3.2xlarge | $0.918/h | 20-30x | 💰 太贵 |
| CPU | t3.2xlarge | $0.133/h | 1-2x | 🐌 太慢 |

**结论**：g4dn.xlarge性价比最高

### 模型对比

| 模型 | GPU内存 | 准确率 | 速度 | 推荐 |
|------|---------|--------|------|------|
| large | 10GB | 96-98% | 10-15x | ⭐ 推荐 |
| medium | 5GB | 93-95% | 15-20x | ✅ 可选 |
| base | 1GB | 85-90% | 30-40x | ❌ 太差 |

**结论**：财经内容用large，通用内容用medium

---

## 🎯 下一步

转录完成后，执行认知框架合成：

```bash
cd ../03_cognitive_synthesis
export S3_BUCKET=your-bucket
export S3_PREFIX=douyin_videos/20260417/
python3 cognitive_synthesis.py
```

详见：[认知框架合成指南](../03_cognitive_synthesis/README.md)

---

## 📚 相关文档

- [完整README](README.md)
- [实现方案](IMPLEMENTATION_PLAN.md)
- [V2增强版](IMPLEMENTATION_PLAN_V2.md)
- [认知合成](../03_cognitive_synthesis/README.md)
