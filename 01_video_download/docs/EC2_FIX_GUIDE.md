# 🔧 EC2错误修复指南

## ❌ 错误信息

```
RuntimeError: There is no current event loop in thread 'MainThread'.
```

## 🔍 问题原因

**Python 3.9的asyncio兼容性问题**

- EC2上默认安装的是Python 3.9
- F2使用asyncio，在Python 3.9上有事件循环初始化问题
- Python 3.10+修复了这个问题

---

## ✅ 解决方案（3个选择）

### 方案1：升级Python到3.11+（推荐）⭐

#### Amazon Linux 2023

```bash
# 安装Python 3.11
sudo yum install -y python3.11 python3.11-pip

# 设置别名
echo "alias python3=python3.11" >> ~/.bashrc
echo "alias pip3=pip3.11" >> ~/.bashrc
source ~/.bashrc

# 重新安装依赖
pip3 install --user f2 boto3

# 验证版本
python3 --version  # 应该显示 3.11.x
```

#### Ubuntu

```bash
# 安装Python 3.11
sudo apt-get update
sudo apt-get install -y software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt-get update
sudo apt-get install -y python3.11 python3.11-pip python3.11-venv

# 设置为默认
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

# 重新安装依赖
pip3 install --user f2 boto3

# 验证版本
python3 --version
```

---

### 方案2：使用修复版脚本（临时方案）

我已经创建了一个修复版的脚本：`batch_download_fixed.py`

这个脚本在启动时自动初始化事件循环，兼容Python 3.9。

**重新部署**（在本地执行）：

```bash
# 1. 上传修复版脚本
cd /Users/havpan/CC_Demo/finance/test_single_video

scp -i /Users/havpan/AWS/key-pair/tokyo.pem \
    batch_download_fixed.py \
    ec2-user@13.230.31.116:~/douyin_downloader/

# 2. SSH登录EC2
ssh -i /Users/havpan/AWS/key-pair/tokyo.pem ec2-user@13.230.31.116

# 3. 使用修复版脚本
cd ~/douyin_downloader
python3 batch_download_fixed.py '博主主页链接'
```

---

### 方案3：使用虚拟环境（干净环境）

```bash
# 在EC2上执行
cd ~/douyin_downloader

# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install f2 boto3

# 运行下载
python batch_download.py '博主主页链接'
```

---

## 🎯 推荐流程

### 快速解决（5分钟）

```bash
# 1. 在EC2上安装Python 3.11
sudo yum install -y python3.11 python3.11-pip

# 2. 创建软链接
sudo ln -sf /usr/bin/python3.11 /usr/bin/python3

# 3. 重新安装F2
pip3.11 install --user f2 boto3

# 4. 运行下载（使用python3.11）
python3.11 -m f2 dy -M post \
    -u '博主主页链接' \
    -k "$(cat douyin_cookie.txt)" \
    -p batch_output \
    -o 0 \
    -s 20 \
    -d True \
    -v True \
    -m True \
    -f True
```

---

## 📋 完整操作步骤

### 步骤1：登录EC2

```bash
ssh -i /Users/havpan/AWS/key-pair/tokyo.pem ec2-user@13.230.31.116
```

### 步骤2：检查Python版本

```bash
python3 --version

# 如果是3.9，需要升级
```

### 步骤3：升级Python

```bash
# Amazon Linux
sudo yum install -y python3.11 python3.11-pip

# 设置Python 3.11为默认
sudo alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1
```

### 步骤4：重新安装依赖

```bash
# 清理旧安装
rm -rf ~/.local/lib/python3.9/

# 安装新依赖
pip3 install --user f2 boto3

# 验证安装
python3 -m f2 --version
```

### 步骤5：运行下载

```bash
cd ~/douyin_downloader

# 方法1: 使用修复版脚本
python3 batch_download_fixed.py '博主主页链接'

# 方法2: 直接使用F2
python3 -m f2 dy -M post \
    -u '博主主页链接' \
    -k "$(cat douyin_cookie.txt)" \
    -p batch_output \
    -o 0
```

---

## 🐛 验证修复

运行以下测试命令：

```bash
# 测试1: Python版本
python3 --version
# 应该显示 >= 3.10

# 测试2: F2是否正常
python3 -m f2 --version
# 应该显示版本号，无报错

# 测试3: asyncio是否正常
python3 -c "import asyncio; print('asyncio OK')"
# 应该输出: asyncio OK

# 测试4: F2帮助
python3 -m f2 dy -h
# 应该显示帮助信息，无报错
```

---

## 💡 如果升级Python仍有问题

### Plan B: 使用Docker

```bash
# 在EC2上安装Docker
sudo yum install -y docker
sudo systemctl start docker
sudo usermod -aG docker ec2-user

# 使用Python 3.11镜像
docker run -it --rm \
    -v ~/douyin_downloader:/app \
    python:3.11 bash

# 在容器内
cd /app
pip install f2 boto3
python3 batch_download.py '博主链接'
```

---

## 📞 还是不行？

如果以上方案都不行，可以：

1. **本地下载**: 回到本地电脑下载（虽然慢但稳定）
2. **更换EC2 AMI**: 使用Ubuntu 22.04（自带Python 3.10+）
3. **联系我**: 贴出完整错误信息，我帮你调试

---

## 🚀 快速命令（复制粘贴）

```bash
# 一键修复脚本（在EC2上执行）
sudo yum install -y python3.11 python3.11-pip && \
sudo alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1 && \
pip3 install --user f2 boto3 && \
python3 --version && \
echo "✅ 修复完成！"
```

执行后重新运行下载脚本即可！
