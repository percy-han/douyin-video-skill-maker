# 📥 视频下载模块

批量下载抖音博主的所有视频、文案和封面。

## 🎯 功能特性

- ✅ 批量下载视频、文案、封面
- ✅ 自动Cookie管理
- ✅ 断点续传
- ✅ 错误自动重试
- ✅ 本地和EC2双模式
- ✅ 自动上传到S3

## 📂 目录结构

```
01_video_download/
├── local/              # 本地下载脚本
├── ec2/                # EC2部署脚本
├── docs/               # 详细文档
└── README.md
```

## 🚀 快速开始

### 本地下载（适合测试）

```bash
cd local
python3 setup_cookie.py          # 配置Cookie
python3 batch_download.py '链接'  # 下载视频
```

### EC2下载（适合批量）

```bash
cd ec2
# 1. 编辑 deploy_to_ec2.sh 配置EC2信息
# 2. 运行部署
./deploy_to_ec2.sh
```

## 📖 详细文档

- [完整使用指南](docs/BATCH_DOWNLOAD_GUIDE.md)
- [EC2部署教程](docs/EC2_DEPLOYMENT_GUIDE.md)
- [Cookie配置](docs/COOKIE_SETUP_SIMPLE.md)
- [常见问题](docs/EC2_FIX_GUIDE.md)

## 💰 成本

- **本地**: 免费
- **EC2**: ~$3/100个视频

详见: [文档](docs/EC2_DEPLOYMENT_GUIDE.md#成本预估)
