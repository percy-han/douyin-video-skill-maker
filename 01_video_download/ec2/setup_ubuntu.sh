#!/bin/bash
# Ubuntu EC2快速设置脚本
# Author: Claude
# Date: 2026-04-17

set -e

echo "=========================================="
echo "🚀 Ubuntu EC2环境设置"
echo "=========================================="

# 检查Python版本
echo ""
echo "📋 当前环境:"
python3 --version
echo ""

# 更新系统
echo "📦 更新系统包..."
sudo apt-get update -y

# 安装基础依赖
echo ""
echo "📦 安装基础依赖..."
sudo apt-get install -y python3-pip git curl

# 升级pip
echo ""
echo "📦 升级pip..."
python3 -m pip install --upgrade pip

# 安装Python包
echo ""
echo "📦 安装F2和依赖..."
pip3 install --user f2 boto3 openai-whisper

# 添加pip用户路径到PATH
echo ""
echo "📦 配置环境变量..."
if ! grep -q "/.local/bin" ~/.bashrc; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
    echo "✅ PATH已添加到 ~/.bashrc"
fi

# 立即应用PATH
export PATH="$HOME/.local/bin:$PATH"

# 验证安装
echo ""
echo "=========================================="
echo "✅ 验证安装"
echo "=========================================="

# 检查F2
if command -v f2 &> /dev/null; then
    echo "✅ F2已安装"
    f2 --version 2>/dev/null || python3 -m f2 --version
else
    echo "⚠️  f2命令不可用，使用 python3 -m f2"
    python3 -m f2 --version
fi

# 检查boto3
python3 -c "import boto3; print('✅ boto3已安装')" || echo "❌ boto3未安装"

echo ""
echo "=========================================="
echo "🎉 设置完成！"
echo "=========================================="
echo ""
echo "请运行以下命令使环境生效:"
echo "  source ~/.bashrc"
echo ""
echo "然后可以开始下载:"
echo "  cd ~/douyin_downloader"
echo "  python3 batch_download.py '博主链接'"
echo ""
