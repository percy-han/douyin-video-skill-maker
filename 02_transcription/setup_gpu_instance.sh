#!/bin/bash
# GPU实例环境配置脚本
# 适用于AWS Deep Learning AMI（PyTorch venv或conda）或已安装CUDA驱动的Ubuntu

set -e

echo "🔧 配置GPU实例环境"
echo "================================================"

# 检查并激活PyTorch环境
PYTORCH_ACTIVATED=false

# 方式1: 检查PyTorch venv (Deep Learning OSS Nvidia Driver AMI)
if [ -f /opt/pytorch/bin/activate ]; then
    echo "✅ 检测到PyTorch虚拟环境 (/opt/pytorch)"
    source /opt/pytorch/bin/activate
    PYTORCH_ACTIVATED=true
    PYTHON_CMD="python"
    PIP_CMD="pip"
    echo "   ✅ 已激活PyTorch虚拟环境"

# 方式2: 检查conda环境 (Deep Learning AMI with conda)
elif command -v conda &> /dev/null; then
    echo "✅ 检测到conda环境（Deep Learning AMI）"

    # 初始化conda
    if [ -f /opt/conda/etc/profile.d/conda.sh ]; then
        source /opt/conda/etc/profile.d/conda.sh
    fi

    # 激活pytorch环境
    if conda env list | grep -q "pytorch"; then
        conda activate pytorch
        PYTORCH_ACTIVATED=true
        PYTHON_CMD="python"
        PIP_CMD="pip"
        echo "   ✅ 已激活conda pytorch环境"
    else
        echo "   ⚠️  未找到pytorch环境，使用系统Python"
        PYTHON_CMD="python3"
        PIP_CMD="pip3"
    fi

# 方式3: 使用系统Python
else
    echo "✅ 使用系统Python"
    PYTHON_CMD="python3"
    PIP_CMD="pip3"
fi

# 检查GPU驱动
echo ""
echo "📊 检查GPU..."
if nvidia-smi &> /dev/null; then
    nvidia-smi
else
    echo "❌ 未检测到NVIDIA GPU驱动"
    echo ""
    echo "请使用以下方式之一："
    echo "  1. 使用AWS Deep Learning AMI（推荐）"
    echo "  2. 手动安装NVIDIA驱动："
    echo "     sudo apt update"
    echo "     sudo apt install -y nvidia-driver-535"
    echo "     sudo reboot"
    exit 1
fi

# 检查Python版本
echo ""
echo "🐍 检查Python版本..."
PYTHON_VERSION=$($PYTHON_CMD --version)
echo "   $PYTHON_VERSION"

# 检查并修复pip
echo ""
echo "🔧 检查pip..."
if ! $PIP_CMD --version &> /dev/null; then
    echo "   ⚠️  pip不可用，正在修复..."
    $PYTHON_CMD -m ensurepip --upgrade 2>/dev/null || {
        echo "   使用get-pip.py修复..."
        curl -sS https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py
        $PYTHON_CMD /tmp/get-pip.py
        rm -f /tmp/get-pip.py
    }
    echo "   ✅ pip已修复"
else
    echo "   ✅ pip可用"
fi

# 安装系统依赖（如果需要）
echo ""
echo "📦 检查系统依赖..."
if ! command -v ffmpeg &> /dev/null; then
    echo "   安装ffmpeg..."
    sudo apt update -qq
    sudo apt install -y ffmpeg git > /dev/null 2>&1
    echo "   ✅ 已安装: ffmpeg, git"
else
    echo "   ✅ ffmpeg已安装"
fi

# 检查PyTorch CUDA支持
echo ""
echo "🔥 检查PyTorch CUDA支持..."
CUDA_AVAILABLE=$($PYTHON_CMD -c "import torch; print(torch.cuda.is_available())" 2>/dev/null || echo "false")

if [ "$CUDA_AVAILABLE" = "True" ]; then
    echo "   ✅ PyTorch CUDA已可用"
    PYTORCH_VERSION=$($PYTHON_CMD -c "import torch; print(torch.__version__)")
    CUDA_VERSION=$($PYTHON_CMD -c "import torch; print(torch.version.cuda)")
    GPU_COUNT=$($PYTHON_CMD -c "import torch; print(torch.cuda.device_count())")
    GPU_NAME=$($PYTHON_CMD -c "import torch; print(torch.cuda.get_device_name(0))")
    echo "   📦 PyTorch版本: $PYTORCH_VERSION"
    echo "   🔧 CUDA版本: $CUDA_VERSION"
    echo "   🎮 GPU数量: $GPU_COUNT"
    echo "   💎 GPU型号: $GPU_NAME"
else
    echo "   ⚠️  PyTorch CUDA不可用"
    echo "   安装PyTorch（CUDA 12.1版本）..."
    $PIP_CMD install --upgrade pip --quiet
    $PIP_CMD install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121 --quiet

    # 再次验证
    CUDA_AVAILABLE=$($PYTHON_CMD -c "import torch; print(torch.cuda.is_available())")
    if [ "$CUDA_AVAILABLE" = "True" ]; then
        echo "   ✅ PyTorch CUDA安装成功"
        PYTORCH_VERSION=$($PYTHON_CMD -c "import torch; print(torch.__version__)")
        CUDA_VERSION=$($PYTHON_CMD -c "import torch; print(torch.version.cuda)")
        GPU_COUNT=$($PYTHON_CMD -c "import torch; print(torch.cuda.device_count())")
        GPU_NAME=$($PYTHON_CMD -c "import torch; print(torch.cuda.get_device_name(0))")
        echo "   📦 PyTorch版本: $PYTORCH_VERSION"
        echo "   🔧 CUDA版本: $CUDA_VERSION"
        echo "   🎮 GPU数量: $GPU_COUNT"
        echo "   💎 GPU型号: $GPU_NAME"
    else
        echo "   ❌ PyTorch CUDA安装失败"
        exit 1
    fi
fi

# 安装Whisper和其他依赖
echo ""
echo "📦 安装Python依赖..."

# 清理损坏的包（如果存在）
if [ "$PYTORCH_ACTIVATED" = true ]; then
    echo "   清理损坏的包..."
    find /opt/pytorch/lib/python*/site-packages -name '~*' -type d 2>/dev/null | while read dir; do
        sudo rm -rf "$dir" 2>/dev/null || true
    done
fi

echo "   升级pip和构建工具..."
$PIP_CMD install --upgrade pip setuptools wheel --quiet --force-reinstall

if [ -f requirements.txt ]; then
    echo "   从requirements.txt安装..."
    $PIP_CMD install -r requirements.txt --quiet
else
    echo "   安装核心依赖..."
    $PIP_CMD install openai-whisper boto3 --quiet
fi

# 验证Whisper安装
echo ""
echo "🎤 验证Whisper安装..."
WHISPER_VERSION=$($PYTHON_CMD -c "import whisper; print(whisper.__version__)" 2>/dev/null || echo "未找到")
if [ "$WHISPER_VERSION" != "未找到" ]; then
    echo "   ✅ Whisper版本: $WHISPER_VERSION"
else
    echo "   ❌ Whisper安装失败"
    exit 1
fi

# 验证Boto3
echo ""
echo "☁️  验证AWS SDK..."
BOTO3_VERSION=$($PYTHON_CMD -c "import boto3; print(boto3.__version__)" 2>/dev/null || echo "未找到")
if [ "$BOTO3_VERSION" != "未找到" ]; then
    echo "   ✅ Boto3版本: $BOTO3_VERSION"
else
    echo "   ❌ Boto3安装失败"
    exit 1
fi

# 配置环境自动激活
if [ "$PYTORCH_ACTIVATED" = true ]; then
    echo ""
    echo "🔧 配置环境自动激活..."

    if [ -f /opt/pytorch/bin/activate ]; then
        # PyTorch venv
        if ! grep -q "source /opt/pytorch/bin/activate" ~/.bashrc; then
            echo 'source /opt/pytorch/bin/activate' >> ~/.bashrc
            echo "   ✅ 已设置：登录时自动激活PyTorch虚拟环境"
        else
            echo "   ✅ 已配置自动激活"
        fi
    elif command -v conda &> /dev/null; then
        # conda环境
        if ! grep -q "conda activate pytorch" ~/.bashrc; then
            echo 'conda activate pytorch' >> ~/.bashrc
            echo "   ✅ 已设置：登录时自动激活conda pytorch环境"
        else
            echo "   ✅ 已配置自动激活"
        fi
    fi
fi

# 配置AWS凭证（如果需要）
echo ""
if [ -n "$AWS_ACCESS_KEY_ID" ] && [ -n "$AWS_SECRET_ACCESS_KEY" ]; then
    echo "✅ 检测到AWS凭证（环境变量）"
elif aws sts get-caller-identity &> /dev/null; then
    echo "✅ 检测到AWS凭证（IAM角色或配置文件）"
else
    echo "⚠️  未检测到AWS凭证"
    echo ""
    echo "请配置AWS凭证（选择一种方式）："
    echo ""
    echo "方式1: 使用IAM角色（推荐，EC2实例）"
    echo "  在EC2控制台为实例关联IAM角色"
    echo ""
    echo "方式2: 配置AWS CLI"
    echo "  aws configure"
    echo ""
    echo "方式3: 设置环境变量"
    echo "  export AWS_ACCESS_KEY_ID=xxx"
    echo "  export AWS_SECRET_ACCESS_KEY=xxx"
    echo ""
fi

# 显示完整环境信息
echo ""
echo "================================================"
echo "🎉 环境配置完成！"
echo "================================================"
echo ""
echo "环境信息:"
if [ "$PYTORCH_ACTIVATED" = true ]; then
    echo "  环境类型: PyTorch虚拟环境"
else
    echo "  环境类型: 系统Python"
fi
echo "  Python: $PYTHON_VERSION"
echo "  PyTorch: $($PYTHON_CMD -c 'import torch; print(torch.__version__)')"
echo "  CUDA: $($PYTHON_CMD -c 'import torch; print(torch.version.cuda)')"
echo "  Whisper: $WHISPER_VERSION"
echo "  Boto3: $BOTO3_VERSION"
echo "  GPU: $($PYTHON_CMD -c 'import torch; print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else "无")')"
echo ""
echo "使用方法:"
echo "  export S3_BUCKET=your-bucket-name"
echo "  export S3_PREFIX=douyin_videos/20260417/"
echo "  export WHISPER_MODEL=large  # 可选: large, medium, base"
echo "  $PYTHON_CMD batch_transcribe_s3.py"
echo ""
if [ "$PYTHON_CMD" = "python" ]; then
    echo "⚠️  重要："
    echo "  - 当前使用虚拟环境中的python命令"
    echo "  - 执行脚本时使用: python batch_transcribe_s3.py（不是python3）"
    echo "  - 下次登录时会自动激活虚拟环境"
    echo ""
fi
echo "💡 提示:"
echo "  - large模型需要~10GB GPU内存（T4 16GB够用）"
echo "  - medium模型需要~5GB GPU内存（节省内存）"
echo "  - 转录速度: 1小时视频 → 4-6分钟（large）"
echo ""
