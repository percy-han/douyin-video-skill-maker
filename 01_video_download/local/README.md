# 💻 本地下载脚本

在本地电脑上运行的下载脚本。

## 📋 文件说明

| 文件 | 用途 | 优先级 |
|------|------|--------|
| `setup_cookie.py` | 配置抖音Cookie | ⭐⭐⭐ 必需 |
| `test_cookie_download.py` | 测试Cookie是否有效 | ⭐⭐⭐ 推荐 |
| `batch_download.py` | 标准批量下载 | ⭐⭐⭐ 主要 |
| `batch_download_stable.py` | 稳定版（网络优化） | ⭐⭐ 备用 |
| `whisper_transcribe.py` | Whisper转录脚本 | ⭐ 可选 |

## 🚀 使用流程

### 第1步：安装依赖

```bash
pip install f2
```

### 第2步：配置Cookie

```bash
python3 setup_cookie.py
```

按提示操作：
1. 在浏览器登录抖音
2. F12 → Console → 运行 `document.cookie`
3. 复制Cookie粘贴到脚本

### 第3步：测试Cookie

```bash
python3 test_cookie_download.py
```

如果成功下载测试视频，说明Cookie有效。

### 第4步：批量下载

```bash
python3 batch_download.py '博主主页链接'
```

输出会保存到 `batch_output/` 目录。

## 💡 使用技巧

### 如果下载很慢

本地下载速度取决于你的网络。如果下载100+视频，建议使用EC2部署。

### 如果遇到网络错误

使用稳定版脚本：

```bash
python3 batch_download_stable.py '博主链接'
```

### 后台运行（Mac/Linux）

```bash
# 使用screen
screen -S download
python3 batch_download.py '链接'
# Ctrl+A, D 分离

# 重新连接
screen -r download
```

## 🐛 常见问题

**Q: Cookie粘贴后没反应？**
A: 使用nano编辑器：`nano douyin_cookie.txt`，粘贴后保存

**Q: 下载失败？**
A: 重新运行脚本，F2会自动跳过已下载的文件

**Q: 想只下载前10个视频？**
A: 修改脚本中的 `-o 0` 为 `-o 10`

## 📖 更多文档

- [Cookie配置详解](../docs/COOKIE_SETUP_SIMPLE.md)
- [完整使用指南](../docs/BATCH_DOWNLOAD_GUIDE.md)
