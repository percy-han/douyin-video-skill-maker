# 🎬 Douyin Video Skill Maker

一键将抖音博主视频转换为Claude Code Skill的完整工具链。

## 📋 项目简介

本项目用于批量下载抖音博主视频、提取文字内容，并构建知识库，最终生成Claude Code Skill，让AI助手能够回答关于视频内容的问题。

**应用场景**：
- 📚 将财经博主内容转为财经知识库
- 🎓 将教育博主内容转为学习助手
- 💼 将行业专家内容转为专业咨询工具

## 🚀 功能特性

### ✅ 已完成：视频下载模块

- 🔐 **Cookie管理**：自动配置和验证抖音Cookie
- 📥 **批量下载**：一键下载博主所有视频、文案、封面
- 🌐 **EC2部署**：支持部署到AWS EC2实现高速下载
- ☁️ **S3集成**：自动上传到S3存储
- 🔄 **断点续传**：支持中断恢复，自动跳过已下载文件
- 🐛 **错误重试**：智能重试机制，应对网络波动

### 🚧 开发中：文字提取模块

- 🎤 使用Whisper或AWS Transcribe提取视频文字
- 📊 批量处理视频转录

### 📅 规划中：知识库构建

- 向量化文本内容
- 构建OpenSearch索引
- 开发Claude Code Skill

## 📂 项目结构

```
douyin-video-skill-maker/
├── 01_video_download/          # 视频下载模块
│   ├── local/                  # 本地下载脚本
│   ├── ec2/                    # EC2部署脚本
│   ├── docs/                   # 文档
│   └── README.md
├── 02_transcription/           # 文字提取模块（开发中）
├── 03_knowledge_base/          # 知识库构建（规划中）
├── 04_skill_generator/         # Skill生成器（规划中）
└── README.md
```

## 🎯 快速开始

### 方案A：本地下载（适合测试）

```bash
# 1. 安装依赖
pip install f2

# 2. 配置Cookie
cd 01_video_download/local
python3 setup_cookie.py

# 3. 下载视频
python3 batch_download.py '博主主页链接'
```

### 方案B：EC2下载（适合批量，推荐）

```bash
# 1. 配置部署脚本
cd 01_video_download/ec2
# 编辑 deploy_to_ec2.sh，设置EC2信息

# 2. 部署到EC2
./deploy_to_ec2.sh

# 3. SSH登录EC2并运行
ssh -i your-key.pem ubuntu@your-ec2-ip
cd ~/douyin_downloader
./run_on_ubuntu.sh '博主链接' 'your-s3-bucket'
```

## 📖 详细文档

- [视频下载完整指南](01_video_download/docs/GUIDE.md)
- [EC2部署指南](01_video_download/docs/EC2_DEPLOYMENT.md)
- [Cookie配置指南](01_video_download/docs/COOKIE_SETUP.md)
- [常见问题](01_video_download/docs/FAQ.md)

## 💰 成本预估

### 本地下载
- 免费（仅消耗带宽和存储）

### EC2下载（推荐）
- **EC2**: t3.medium × 10小时 ≈ $0.42
- **S3存储**: 100GB ≈ $2.3/月
- **总计**: ~$3/100个视频

## 🔐 安全说明

**重要：请勿泄露以下文件**
- ❌ `douyin_cookie.txt` - 你的抖音登录凭证
- ❌ `*.pem` - AWS SSH密钥
- ❌ `.env` - 环境变量配置

这些文件已在 `.gitignore` 中排除，不会被提交到GitHub。

## 🛠️ 技术栈

- **下载**: F2 (抖音下载工具)
- **转录**: Whisper / AWS Transcribe
- **存储**: AWS S3
- **计算**: AWS EC2
- **向量化**: Amazon Titan Embeddings
- **索引**: OpenSearch

## 📊 使用示例

### 财经知识库（观棋有语·刘德超）

1. 下载300个财经分析视频
2. 提取文字内容（约30万字）
3. 构建财经知识库
4. 生成Claude Skill：回答财经问题

### 预期效果

```
用户: 美联储最近的货币政策是什么？
Skill: 根据刘德超在2026-04-10的视频，美联储在三月份维持利率不变...
      (来源: 2026-04-10_美联储议息会议分析.mp4)
```

## 🤝 贡献

欢迎提交Issue和PR！

## 📄 许可证

MIT License

## 🙏 致谢

- [F2](https://github.com/Johnserf-Seed/f2) - 强大的抖音下载工具
- [OpenAI Whisper](https://github.com/openai/whisper) - 高质量语音识别
- [Claude Code](https://claude.ai/code) - 强大的AI编程助手

## 📞 联系方式

- GitHub: [@percy-han](https://github.com/percy-han)
- 项目地址: https://github.com/percy-han/douyin-video-skill-maker

---

**⭐ 如果这个项目对你有帮助，请给个Star！**
