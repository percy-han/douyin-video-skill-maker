#!/bin/bash
# 创建干净的Python虚拟环境用于Whisper转录
set -e

echo "🔧 创建干净的Whisper虚拟环境"
echo "================================================"

# 检查系统Python 3.12
if command -v python3.12 &> /dev/null; then
    PYTHON_BIN="python3.12"
elif command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | awk '{print $2}' | cut -d. -f1,2)
    if [[ "$PYTHON_VERSION" == "3.12" ]] || [[ "$PYTHON_VERSION" == "3.11" ]] || [[ "$PYTHON_VERSION" == "3.10" ]]; then
        PYTHON_BIN="python3"
    else
        echo "❌ 需要Python 3.10-3.12，当前版本: $PYTHON_VERSION"
        exit 1
    fi
else
    echo "❌ 未找到Python 3"
    exit 1
fi

echo "✅ 使用Python: $($PYTHON_BIN --version)"

# 创建虚拟环境
VENV_PATH="$HOME/whisper_env"
if [ -d "$VENV_PATH" ]; then
    echo "⚠️  虚拟环境已存在: $VENV_PATH"
    read -p "是否删除并重建？(y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "$VENV_PATH"
    else
        echo "使用现有虚拟环境"
    fi
fi

if [ ! -d "$VENV_PATH" ]; then
    echo "📦 创建虚拟环境..."
    $PYTHON_BIN -m venv "$VENV_PATH"
    echo "   ✅ 虚拟环境已创建: $VENV_PATH"
fi

# 激活虚拟环境
echo ""
echo "🔄 激活虚拟环境..."
source "$VENV_PATH/bin/activate"

# 升级pip
echo ""
echo "⬆️  升级pip..."
pip install --upgrade pip setuptools wheel

# 检查GPU
echo ""
echo "📊 检查GPU..."
if nvidia-smi &> /dev/null; then
    nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader
else
    echo "❌ 未检测到NVIDIA GPU"
    exit 1
fi

# 安装PyTorch CUDA
echo ""
echo "🔥 安装PyTorch（CUDA 12.1）..."
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121

# 验证CUDA
echo ""
echo "✅ 验证PyTorch CUDA..."
python -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA available: {torch.cuda.is_available()}'); print(f'GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"N/A\"}')"

# 安装ffmpeg（如果需要）
echo ""
echo "📦 检查ffmpeg..."
if ! command -v ffmpeg &> /dev/null; then
    echo "   安装ffmpeg..."
    sudo apt update -qq
    sudo apt install -y ffmpeg
fi
echo "   ✅ ffmpeg已安装"

# 安装Whisper和依赖
echo ""
echo "🎤 安装Whisper..."
pip install git+https://github.com/openai/whisper.git boto3

# 验证安装
echo ""
echo "✅ 验证Whisper..."
python -c "import whisper; print(f'Whisper: OK')"

# 配置自动激活
echo ""
echo "🔧 配置环境自动激活..."
if ! grep -q "source $VENV_PATH/bin/activate" ~/.bashrc; then
    echo "source $VENV_PATH/bin/activate" >> ~/.bashrc
    echo "   ✅ 已添加自动激活到 ~/.bashrc"
else
    echo "   ✅ 已配置自动激活"
fi

# 完成
echo ""
echo "================================================"
echo "🎉 环境配置完成！"
echo "================================================"
echo ""
echo "环境信息:"
echo "  虚拟环境: $VENV_PATH"
echo "  Python: $(python --version)"
echo "  PyTorch: $(python -c 'import torch; print(torch.__version__)')"
echo "  CUDA: $(python -c 'import torch; print(torch.version.cuda)')"
echo "  GPU: $(python -c 'import torch; print(torch.cuda.get_device_name(0))')"
echo ""
echo "使用方法:"
echo "  1. 激活环境: source $VENV_PATH/bin/activate"
echo "  2. 配置S3:"
echo "     export S3_BUCKET=your-bucket-name"
echo "     export S3_PREFIX=douyin_videos/20260417/"
echo "  3. 执行转录:"
echo "     python batch_transcribe_s3.py"
echo ""
echo "💡 提示:"
echo "  - 下次登录时会自动激活虚拟环境"
echo "  - 如需停用: deactivate"
echo ""
