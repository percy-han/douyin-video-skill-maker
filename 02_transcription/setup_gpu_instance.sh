#!/bin/bash
# GPU实例环境配置脚本

set -e

echo "🔧 配置GPU实例环境"

# 检查CUDA
echo "📊 检查CUDA..."
if ! command -v nvidia-smi &> /dev/null; then
    echo "❌ 未检测到NVIDIA GPU或驱动"
    exit 1
fi

nvidia-smi
echo "✅ GPU检测成功"

# 安装Python依赖
echo ""
echo "📦 安装Python依赖..."
pip3 install --upgrade pip
pip3 install -r requirements.txt

# 验证Whisper
echo ""
echo "🎤 验证Whisper安装..."
python3 -c "import whisper; print('✅ Whisper版本:', whisper.__version__)"

# 验证PyTorch CUDA
echo ""
echo "🔥 验证PyTorch CUDA支持..."
python3 -c "import torch; print('✅ PyTorch版本:', torch.__version__); print('✅ CUDA可用:', torch.cuda.is_available()); print('✅ GPU数量:', torch.cuda.device_count())"

# 验证Boto3
echo ""
echo "☁️  验证AWS SDK..."
python3 -c "import boto3; print('✅ Boto3版本:', boto3.__version__)"

echo ""
echo "🎉 环境配置完成"
echo ""
echo "使用方法："
echo "  export S3_BUCKET=your-bucket-name"
echo "  export S3_PREFIX=douyin_videos/20260417_150000/"
echo "  python3 batch_transcribe_s3.py"
