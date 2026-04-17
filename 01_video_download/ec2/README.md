# ☁️ EC2部署脚本

在AWS EC2上运行，实现高速下载并自动上传到S3。

## 📋 文件说明

| 文件 | 用途 |
|------|------|
| `deploy_to_ec2.sh` | 一键部署脚本 |
| `run_on_ubuntu.sh` | Ubuntu EC2上的执行脚本 |
| `ec2_download_to_s3.py` | Python版完整脚本 |
| `setup_ubuntu.sh` | Ubuntu环境配置 |
| `batch_download_fixed.py` | Python 3.9兼容版 |

## 🚀 快速部署

### 前置条件

1. ✅ 一个运行中的EC2实例（推荐Ubuntu）
2. ✅ SSH密钥文件（.pem）
3. ✅ S3存储桶
4. ✅ EC2附加了S3写入权限的IAM Role

### 步骤1：配置部署脚本

编辑 `deploy_to_ec2.sh`：

```bash
EC2_HOST="your-ec2-ip"
EC2_KEY="/path/to/your-key.pem"
S3_BUCKET="your-bucket-name"
```

### 步骤2：运行部署

```bash
./deploy_to_ec2.sh
```

这会自动上传所有必要文件到EC2。

### 步骤3：在EC2上执行

SSH登录到EC2：

```bash
ssh -i your-key.pem ubuntu@your-ec2-ip
cd ~/douyin_downloader
./run_on_ubuntu.sh '博主主页链接' 'your-s3-bucket'
```

## 💰 成本优化

### 使用Spot实例

比按需实例便宜70%：

```bash
aws ec2 run-instances \
    --instance-type t3.medium \
    --instance-market-options "MarketType=spot"
```

### 推荐实例类型

| 实例 | vCPU | 内存 | 价格/小时 | 适用场景 |
|------|------|------|----------|---------|
| t3.small | 2 | 2GB | $0.0208 | 少量视频 |
| t3.medium | 2 | 4GB | $0.0416 | **推荐** |
| t3.large | 2 | 8GB | $0.0832 | 大量视频 |

### 成本预估

100个视频（每个5分钟）：
- EC2运行10小时: $0.42
- S3存储100GB: $2.30/月
- **总计**: ~$3

## 🔧 配置IAM Role

EC2需要S3写入权限：

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
        "arn:aws:s3:::your-bucket/*",
        "arn:aws:s3:::your-bucket"
      ]
    }
  ]
}
```

在EC2控制台：
Actions → Security → Modify IAM Role

## 🐛 常见问题

**Q: "No module named f2"**
A: 运行 `pip3 install --user f2`

**Q: Python版本问题？**
A: 参考 [EC2_FIX_GUIDE.md](../docs/EC2_FIX_GUIDE.md)

**Q: 下载到一半断了？**
A: 重新运行脚本，会自动续传

## 📖 详细文档

- [完整部署教程](../docs/EC2_DEPLOYMENT_GUIDE.md)
- [故障排查](../docs/EC2_FIX_GUIDE.md)
