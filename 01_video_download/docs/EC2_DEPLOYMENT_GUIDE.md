# 🚀 EC2部署完整指南

## 为什么在EC2上运行？

✅ **快速**: AWS数据中心带宽远超家庭网络  
✅ **稳定**: 24小时不间断运行  
✅ **便宜**: 按需付费，用完即停  
✅ **集成**: 直接上传到S3，无需本地传输

---

## 📋 方案对比

| 方案 | 优点 | 缺点 | 推荐场景 |
|------|------|------|----------|
| 本地电脑 | 简单，无需配置 | 慢，占用本地资源 | 测试、少量视频 |
| EC2 | 快速，24小时运行 | 需要AWS配置 | ⭐ 批量下载（100+视频）|

---

## 🎯 完整部署流程

### 第1步：准备EC2实例

#### 1.1 启动EC2（如果还没有）

```bash
# 登录AWS Console
# EC2 → Launch Instance

推荐配置:
- AMI: Amazon Linux 2023 或 Ubuntu 22.04
- 实例类型: t3.medium (2vCPU, 4GB内存)
- 存储: 100GB EBS (gp3)
- 安全组: 允许SSH (22端口)
```

#### 1.2 配置IAM Role（重要！）

为EC2配置IAM Role，赋予S3权限：

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::your-bucket-name/*",
        "arn:aws:s3:::your-bucket-name"
      ]
    }
  ]
}
```

**附加到EC2实例：**
- EC2 → 实例 → Actions → Security → Modify IAM Role

---

### 第2步：上传文件到EC2

#### 2.1 自动部署（推荐）

编辑 `deploy_to_ec2.sh`，设置变量：

```bash
EC2_HOST="你的EC2公网IP"
EC2_USER="ec2-user"  # Amazon Linux用ec2-user，Ubuntu用ubuntu
EC2_KEY="~/.ssh/your-key.pem"
S3_BUCKET="your-bucket-name"
```

然后运行：

```bash
chmod +x deploy_to_ec2.sh
./deploy_to_ec2.sh
```

#### 2.2 手动部署

```bash
# 上传文件
scp -i ~/.ssh/your-key.pem \
    douyin_cookie.txt \
    ec2_download_to_s3.py \
    batch_download.py \
    ec2-user@YOUR_EC2_IP:~/

# 登录EC2
ssh -i ~/.ssh/your-key.pem ec2-user@YOUR_EC2_IP
```

---

### 第3步：在EC2上执行下载

#### 3.1 安装依赖

```bash
# 登录EC2后执行
sudo yum update -y  # Amazon Linux
# 或
sudo apt-get update -y  # Ubuntu

# 安装Python和pip
sudo yum install -y python3 python3-pip  # Amazon Linux
# 或
sudo apt-get install -y python3 python3-pip  # Ubuntu

# 安装Python包
pip3 install --user f2 boto3 openai-whisper
```

#### 3.2 运行下载+上传

```bash
# 使用完整脚本（推荐）
python3 ec2_download_to_s3.py \
    'https://www.douyin.com/user/博主ID' \
    'your-s3-bucket'

# 或分步执行
# 步骤1: 下载
python3 batch_download.py

# 步骤2: 上传到S3
aws s3 sync batch_output/ s3://your-bucket/douyin_videos/ \
    --storage-class INTELLIGENT_TIERING
```

#### 3.3 使用screen后台运行（推荐）

```bash
# 创建screen会话
screen -S douyin_download

# 运行下载
python3 ec2_download_to_s3.py \
    '博主主页链接' \
    'your-s3-bucket'

# 分离会话（让它在后台运行）
# 按 Ctrl+A，然后按 D

# 退出SSH（任务继续运行）
exit

# 稍后重新连接查看进度
ssh -i ~/.ssh/your-key.pem ec2-user@YOUR_EC2_IP
screen -r douyin_download
```

---

## 📊 预估成本

### EC2成本（按需实例）

| 实例类型 | vCPU | 内存 | 价格/小时 | 下载100个视频预估成本 |
|---------|------|------|----------|---------------------|
| t3.small | 2 | 2GB | $0.0208 | ~$0.21 (10小时) |
| t3.medium | 2 | 4GB | $0.0416 | ~$0.42 (10小时) |
| t3.large | 2 | 8GB | $0.0832 | ~$0.83 (10小时) |

**推荐**: t3.medium (性价比最高)

### S3存储成本

| 项目 | 价格 | 100个视频（每个5分钟）预估 |
|------|------|-------------------------|
| 存储（标准） | $0.023/GB/月 | ~$2.30/月 (100GB) |
| 存储（智能分层）| $0.021/GB/月 | ~$2.10/月 (自动优化) |
| PUT请求 | $0.005/1000请求 | <$0.01 |

**推荐**: INTELLIGENT_TIERING（智能分层）

### 总成本预估

**100个视频（每个5分钟，共500分钟）:**
- EC2运行10小时: ~$0.42
- S3存储首月: ~$2.10
- **总计首月**: ~$2.52

---

## 🔧 优化建议

### 1. 使用Spot实例（省70%）

```bash
# 启动Spot实例
aws ec2 request-spot-instances \
    --spot-price "0.0125" \
    --instance-count 1 \
    --type "one-time" \
    --launch-specification file://spot-spec.json
```

**优点**: 价格便宜70%  
**缺点**: 可能被中断（但可以恢复）

### 2. 只上传文本，视频本地处理

如果只需要文本内容构建知识库：

```bash
# 只上传文案和转录文本
aws s3 sync batch_output/ s3://your-bucket/texts/ \
    --exclude "*.mp4" \
    --exclude "*.webm" \
    --include "*.txt" \
    --include "*.srt"
```

**节省**: 90%以上的存储成本

### 3. 下载后立即转录（推荐）

修改脚本，下载完立即转录并上传文本：

```python
# 伪代码
for video in videos:
    download(video)
    transcript = whisper.transcribe(video)
    upload_to_s3(transcript)
    delete_local_video()  # 释放空间
```

---

## 📦 S3数据组织

推荐的S3目录结构：

```
s3://your-bucket/
├── douyin_videos/
│   ├── 20260417_150000/          # 时间戳批次
│   │   ├── 视频1/
│   │   │   ├── 视频.mp4           # 视频文件
│   │   │   ├── 视频.txt           # 文案
│   │   │   ├── 视频.jpg           # 封面
│   │   │   └── 视频_whisper.txt  # 转录文本
│   │   ├── 视频2/
│   │   └── manifest.txt           # 清单
│   └── 20260418_120000/
└── processed/                     # 处理后的数据
    └── knowledge_base/
        ├── embeddings.json
        └── index.json
```

---

## 🐛 常见问题

### Q1: EC2下载很慢？

**原因**: 
- EC2实例类型太小
- 网络限流

**解决**:
```bash
# 检查网络速度
curl -o /dev/null http://speedtest.tele2.net/100MB.zip

# 使用更大的实例类型（t3.large）
# 或增加并发数（修改batch_download.py中的 -t 参数）
```

### Q2: S3上传失败？

**检查IAM权限**:
```bash
# 测试S3访问
aws s3 ls s3://your-bucket/

# 如果失败，检查IAM Role是否正确附加
aws sts get-caller-identity
```

### Q3: 存储空间不足？

**清理本地文件**:
```bash
# 上传后删除本地视频
aws s3 sync batch_output/ s3://bucket/path/ && rm -rf batch_output/

# 或使用流式上传（边下载边上传边删除）
```

### Q4: 任务中断怎么办？

**恢复下载**:
```bash
# F2会自动跳过已下载的文件
python3 batch_download.py

# S3会自动跳过已上传的文件
aws s3 sync batch_output/ s3://bucket/path/
```

---

## 🎯 快速开始命令

```bash
# 1. 本地：部署到EC2
./deploy_to_ec2.sh

# 2. EC2：安装依赖
pip3 install --user f2 boto3

# 3. EC2：后台运行
screen -S download
python3 ec2_download_to_s3.py '博主链接' 'your-bucket'
# Ctrl+A, D 分离

# 4. 本地：查看进度
ssh -i key.pem ec2-user@IP
screen -r download

# 5. 完成后：验证S3
aws s3 ls s3://your-bucket/douyin_videos/ --recursive

# 6. 停止EC2节省成本
aws ec2 stop-instances --instance-ids i-xxxxx
```

---

## ✨ 下一步

下载完成后，你会在S3得到：
- ✅ 所有视频文件
- ✅ 所有文案文本
- ✅ 所有转录文本

接下来可以：
1. **构建知识库**: 向量化文本 → OpenSearch
2. **开发Skill**: 集成到Claude Code
3. **数据分析**: 提取主题、关键词

我可以继续帮你完成这些步骤！🚀
