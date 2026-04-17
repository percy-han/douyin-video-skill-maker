#!/bin/bash
# Ubuntu上的一键运行脚本
# 自动安装依赖 + 下载 + 上传S3

set -e

echo "=========================================="
echo "🎬 Ubuntu EC2 - 一键执行"
echo "=========================================="

# 检查参数
if [ -z "$1" ]; then
    echo "用法: ./run_on_ubuntu.sh '博主主页链接' 'S3桶名'"
    exit 1
fi

HOMEPAGE_URL="$1"
S3_BUCKET="${2:-percyhan-douyin-video}"

echo ""
echo "🔗 博主主页: $HOMEPAGE_URL"
echo "📦 S3桶: $S3_BUCKET"
echo ""

# 1. 检查并安装依赖
echo "=========================================="
echo "📦 步骤1: 检查依赖"
echo "=========================================="

if ! python3 -m f2 --version &>/dev/null; then
    echo "⚠️  F2未安装，开始安装..."

    echo "更新系统..."
    sudo apt-get update -y

    echo "安装pip..."
    sudo apt-get install -y python3-pip

    echo "安装F2和boto3..."
    pip3 install --user f2 boto3

    # 添加到PATH
    export PATH="$HOME/.local/bin:$PATH"

    echo "✅ 依赖安装完成"
else
    echo "✅ F2已安装"
fi

# 验证boto3
python3 -c "import boto3" 2>/dev/null || pip3 install --user boto3

echo ""

# 2. 检查Cookie
echo "=========================================="
echo "📦 步骤2: 检查Cookie"
echo "=========================================="

if [ ! -f "douyin_cookie.txt" ]; then
    echo "❌ 未找到Cookie文件"
    echo "请先上传Cookie文件:"
    echo "  scp -i key.pem douyin_cookie.txt ubuntu@IP:~/douyin_downloader/"
    exit 1
fi

echo "✅ Cookie文件存在"
COOKIE=$(cat douyin_cookie.txt)
echo "   长度: ${#COOKIE} 字符"
echo ""

# 3. 批量下载
echo "=========================================="
echo "📦 步骤3: 批量下载"
echo "=========================================="

python3 -m f2 dy \
    -M post \
    -u "$HOMEPAGE_URL" \
    -k "$COOKIE" \
    -p batch_output \
    -d True \
    -v True \
    -m True \
    -o 0 \
    -s 20 \
    -e 30 \
    -r 5 \
    -t 5 \
    -f True \
    -i all

if [ $? -ne 0 ]; then
    echo "❌ 下载失败"
    exit 1
fi

echo ""
echo "✅ 下载完成"
echo ""

# 4. 统计文件
echo "=========================================="
echo "📊 步骤4: 统计下载"
echo "=========================================="

if [ -d "batch_output" ]; then
    VIDEO_COUNT=$(find batch_output -name "*.mp4" -type f | wc -l)
    TXT_COUNT=$(find batch_output -name "*.txt" -type f | wc -l)
    TOTAL_SIZE=$(du -sh batch_output | cut -f1)

    echo "📹 视频: $VIDEO_COUNT 个"
    echo "📄 文案: $TXT_COUNT 个"
    echo "💾 总大小: $TOTAL_SIZE"
else
    echo "⚠️  未找到batch_output目录"
fi

echo ""

# 5. 上传到S3
echo "=========================================="
echo "📦 步骤5: 上传到S3"
echo "=========================================="

# 检查AWS CLI
if ! command -v aws &> /dev/null; then
    echo "安装AWS CLI..."
    sudo apt-get install -y awscli
fi

# 生成时间戳
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
S3_PATH="s3://$S3_BUCKET/douyin_videos/$TIMESTAMP/"

echo "📤 上传路径: $S3_PATH"
echo ""

# 先上传小文件（文案、封面）
echo "上传文案和元数据..."
aws s3 sync batch_output/ "$S3_PATH" \
    --exclude "*.mp4" \
    --exclude "*.webm" \
    --exclude "*.mkv"

echo ""
echo "✅ 文案已上传"
echo ""

# 再上传视频文件（大文件）
echo "上传视频文件..."
aws s3 sync batch_output/ "$S3_PATH" \
    --include "*.mp4" \
    --include "*.webm" \
    --include "*.mkv" \
    --storage-class INTELLIGENT_TIERING

echo ""
echo "✅ 视频已上传"
echo ""

# 6. 生成清单
echo "=========================================="
echo "📦 步骤6: 生成清单"
echo "=========================================="

aws s3 ls "$S3_PATH" --recursive > s3_file_list.txt
echo "✅ 清单已保存: s3_file_list.txt"

# 显示前10个文件
echo ""
echo "前10个文件:"
head -10 s3_file_list.txt

echo ""
echo "=========================================="
echo "✨ 全部完成！"
echo "=========================================="
echo ""
echo "📊 结果:"
echo "   S3路径: $S3_PATH"
echo "   本地清单: s3_file_list.txt"
echo ""
echo "查看S3文件:"
echo "   aws s3 ls $S3_PATH --recursive"
echo ""
echo "下载到本地:"
echo "   aws s3 sync $S3_PATH ./downloads/"
echo ""
