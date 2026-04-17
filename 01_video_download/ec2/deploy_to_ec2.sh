#!/bin/bash
# EC2部署脚本 - 将下载任务部署到AWS EC2
# Author: Claude
# Date: 2026-04-17

set -e  # 遇到错误立即退出

echo "=========================================="
echo "🚀 部署抖音下载器到AWS EC2"
echo "=========================================="

# 配置变量（请修改为你的实际值）
EC2_HOST=""              # EC2公网IP或域名（例如：3.88.123.45）
EC2_USER="ubuntu"      # EC2用户名（Amazon Linux用ec2-user，Ubuntu用ubuntu）
EC2_KEY=""               # SSH密钥路径（例如：~/.ssh/your-key.pem）
S3_BUCKET=""             # S3桶名称（例如：my-douyin-videos）
AWS_REGION="us-east-1"   # AWS区域

# 检查配置
if [ -z "$EC2_HOST" ]; then
    echo "❌ 错误: 请先配置EC2_HOST变量"
    echo ""
    echo "编辑此脚本，设置以下变量:"
    echo "  EC2_HOST='你的EC2公网IP'"
    echo "  EC2_KEY='~/.ssh/your-key.pem'"
    echo "  S3_BUCKET='your-bucket-name'"
    exit 1
fi

# 检查SSH密钥
if [ ! -f "$EC2_KEY" ]; then
    echo "❌ SSH密钥文件不存在: $EC2_KEY"
    exit 1
fi

# 检查Cookie文件
if [ ! -f "douyin_cookie.txt" ]; then
    echo "❌ 未找到Cookie文件: douyin_cookie.txt"
    echo "请先运行: python3 test_cookie_download.py"
    exit 1
fi

echo ""
echo "✅ 配置检查通过"
echo "   EC2: $EC2_USER@$EC2_HOST"
echo "   S3桶: $S3_BUCKET"
echo ""

# 创建部署包
echo "📦 创建部署包..."
DEPLOY_DIR="douyin_downloader"
rm -rf $DEPLOY_DIR
mkdir -p $DEPLOY_DIR

# 复制必要文件
cp douyin_cookie.txt $DEPLOY_DIR/
cp batch_download.py $DEPLOY_DIR/
cp whisper_transcribe.py $DEPLOY_DIR/
cp test_cookie_download.py $DEPLOY_DIR/

# 创建EC2上的运行脚本
cat > $DEPLOY_DIR/run_on_ec2.sh << 'EOF'
#!/bin/bash
# EC2上的执行脚本

set -e

echo "=========================================="
echo "🎬 在EC2上执行下载任务"
echo "=========================================="

# 1. 安装依赖
echo ""
echo "📦 安装依赖..."
sudo yum update -y 2>/dev/null || sudo apt-get update -y
sudo yum install -y python3 python3-pip git 2>/dev/null || sudo apt-get install -y python3 python3-pip git

# 安装Python包
pip3 install --user f2 openai-whisper boto3

# 2. 配置AWS CLI（如果还没配置）
if ! aws s3 ls >/dev/null 2>&1; then
    echo "⚠️  AWS CLI未配置，请运行: aws configure"
fi

# 3. 运行下载（传入主页链接作为参数）
if [ -z "$1" ]; then
    echo "用法: ./run_on_ec2.sh '博主主页链接'"
    exit 1
fi

HOMEPAGE_URL="$1"
S3_BUCKET="${2:-your-bucket-name}"

echo ""
echo "🔗 博主主页: $HOMEPAGE_URL"
echo "📦 S3桶: $S3_BUCKET"
echo ""

# 4. 批量下载
echo "⏳ 开始批量下载..."
python3 batch_download.py "$HOMEPAGE_URL"

# 5. 上传到S3
echo ""
echo "📤 上传到S3..."
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
S3_PATH="s3://$S3_BUCKET/douyin_videos/$TIMESTAMP/"

aws s3 sync batch_output/ "$S3_PATH" \
    --exclude "*.mp4" \
    --exclude "*.webm"

echo ""
echo "✅ 文案和元数据已上传到: $S3_PATH"

# 6. 上传视频文件（大文件，分开上传）
echo ""
echo "📤 上传视频文件..."
aws s3 sync batch_output/ "$S3_PATH" \
    --include "*.mp4" \
    --include "*.webm" \
    --storage-class INTELLIGENT_TIERING

echo ""
echo "✅ 视频文件已上传"

# 7. 生成下载清单
echo ""
echo "📋 生成文件清单..."
aws s3 ls "$S3_PATH" --recursive > s3_file_list.txt
echo "清单已保存: s3_file_list.txt"

echo ""
echo "=========================================="
echo "✨ 任务完成！"
echo "=========================================="
echo "S3路径: $S3_PATH"
echo "查看文件: aws s3 ls $S3_PATH --recursive"
EOF

chmod +x $DEPLOY_DIR/run_on_ec2.sh

echo "✅ 部署包已创建: $DEPLOY_DIR/"
echo ""

# 上传到EC2
echo "📤 上传文件到EC2..."
scp -i "$EC2_KEY" -r $DEPLOY_DIR/* "$EC2_USER@$EC2_HOST:~/douyin_downloader/"

echo ""
echo "✅ 文件已上传到EC2"
echo ""

# 显示后续步骤
echo "=========================================="
echo "📋 下一步操作"
echo "=========================================="
echo ""
echo "1. SSH登录到EC2:"
echo "   ssh -i $EC2_KEY $EC2_USER@$EC2_HOST"
echo ""
echo "2. 进入目录:"
echo "   cd ~/douyin_downloader"
echo ""
echo "3. 运行下载（替换为实际链接和S3桶名）:"
echo "   ./run_on_ec2.sh '博主主页链接' 'your-s3-bucket'"
echo ""
echo "4. 或者使用screen在后台运行（推荐）:"
echo "   screen -S douyin_download"
echo "   ./run_on_ec2.sh '博主主页链接' 'your-s3-bucket'"
echo "   # 按 Ctrl+A 然后按 D 分离会话"
echo "   # 重新连接: screen -r douyin_download"
echo ""
echo "=========================================="
