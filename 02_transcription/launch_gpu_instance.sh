#!/bin/bash
# 启动GPU实例用于视频转录

set -e

echo "🚀 启动GPU实例（g4dn.xlarge Spot）"
echo "================================================"

# 配置参数
INSTANCE_TYPE="g4dn.xlarge"
KEY_NAME="${1:-your-key-pair}"  # 第一个参数：密钥名称
SECURITY_GROUP="${2:-default}"  # 第二个参数：安全组

# 查找最新的Deep Learning AMI（Ubuntu 22.04）
echo ""
echo "📋 查找最新的Deep Learning AMI..."
AMI_INFO=$(aws ec2 describe-images \
  --owners amazon \
  --filters "Name=name,Values=Deep Learning Base OSS Nvidia Driver GPU AMI (Ubuntu 22.04)*" \
  --query 'Images | sort_by(@, &CreationDate) | [-1].[ImageId,Name]' \
  --output text \
  --region us-east-1)

AMI_ID=$(echo "$AMI_INFO" | awk '{print $1}')
AMI_NAME=$(echo "$AMI_INFO" | awk '{$1=""; print $0}' | xargs)

if [ -z "$AMI_ID" ]; then
    echo "❌ 未找到Deep Learning AMI"
    exit 1
fi

echo "   ✅ 找到AMI: $AMI_ID"
echo "   📦 名称: $AMI_NAME"

# 启动Spot实例
echo ""
echo "🎯 启动Spot实例..."
INSTANCE_INFO=$(aws ec2 run-instances \
  --image-id "$AMI_ID" \
  --instance-type "$INSTANCE_TYPE" \
  --key-name "$KEY_NAME" \
  --security-group-ids "$SECURITY_GROUP" \
  --instance-market-options '{
    "MarketType": "spot",
    "SpotOptions": {
      "SpotInstanceType": "one-time",
      "InstanceInterruptionBehavior": "terminate"
    }
  }' \
  --block-device-mappings '[
    {
      "DeviceName": "/dev/sda1",
      "Ebs": {
        "VolumeSize": 50,
        "VolumeType": "gp3",
        "DeleteOnTermination": true
      }
    }
  ]' \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=whisper-transcription}]' \
  --region us-east-1 \
  --query 'Instances[0].[InstanceId,PrivateIpAddress]' \
  --output text)

INSTANCE_ID=$(echo "$INSTANCE_INFO" | awk '{print $1}')
PRIVATE_IP=$(echo "$INSTANCE_INFO" | awk '{print $2}')

echo "   ✅ 实例ID: $INSTANCE_ID"
echo "   📍 私有IP: $PRIVATE_IP"

# 等待实例运行
echo ""
echo "⏳ 等待实例启动..."
aws ec2 wait instance-running --instance-ids "$INSTANCE_ID" --region us-east-1

# 获取公网IP
PUBLIC_IP=$(aws ec2 describe-instances \
  --instance-ids "$INSTANCE_ID" \
  --query 'Reservations[0].Instances[0].PublicIpAddress' \
  --output text \
  --region us-east-1)

echo "   ✅ 实例正在运行"
echo "   🌐 公网IP: $PUBLIC_IP"

# 等待SSH可用
echo ""
echo "⏳ 等待SSH服务就绪（约30秒）..."
sleep 30

# 显示连接信息
echo ""
echo "================================================"
echo "✅ GPU实例启动成功！"
echo "================================================"
echo ""
echo "SSH连接命令:"
echo "  ssh -i ~/.ssh/${KEY_NAME}.pem ubuntu@${PUBLIC_IP}"
echo ""
echo "实例信息:"
echo "  实例ID: $INSTANCE_ID"
echo "  公网IP: $PUBLIC_IP"
echo "  实例类型: $INSTANCE_TYPE"
echo "  AMI: $AMI_ID"
echo ""
echo "下一步操作:"
echo "  1. SSH登录到实例"
echo "  2. 克隆仓库:"
echo "     git clone https://github.com/percy-han/douyin-video-skill-maker.git"
echo "  3. 执行转录:"
echo "     cd douyin-video-skill-maker/02_transcription"
echo "     ./setup_gpu_instance.sh"
echo "     export S3_BUCKET=your-bucket"
echo "     export S3_PREFIX=douyin_videos/20260417/"
echo "     python3 batch_transcribe_s3.py"
echo ""
echo "💡 查看实例成本:"
echo "   aws ec2 describe-spot-instance-requests --region us-east-1"
echo ""
echo "🛑 完成后记得终止实例:"
echo "   aws ec2 terminate-instances --instance-ids $INSTANCE_ID --region us-east-1"
echo ""
