# 抖音视频下载解决方案指南

由于抖音的反爬虫机制，自动化下载需要登录Cookie。以下是几种可行的解决方案：

## ✅ 方案1：使用yt-dlp + 浏览器Cookie（推荐）

### 步骤：

1. **在浏览器中登录抖音**
   - 打开 https://www.douyin.com
   - 登录你的抖音账号
   - 浏览一些视频（确保Cookie有效）

2. **导出Cookie文件**
   ```bash
   # Chrome用户：安装Get cookies.txt扩展
   # https://chrome.google.com/webstore/detail/get-cookiestxt/bgaddhkoddajcdgocldbbfleckgcbcid
   
   # 访问抖音网页后，点击扩展图标导出cookies.txt
   # 保存到: /Users/havpan/CC_Demo/finance/test_single_video/cookies.txt
   ```

3. **使用Cookie下载**
   ```bash
   cd /Users/havpan/CC_Demo/finance/test_single_video
   
   python3 -m yt_dlp \
     "https://v.douyin.com/ZH520PuJgeM/" \
     --cookies cookies.txt \
     --write-sub \
     --write-auto-sub \
     --sub-lang "zh-Hans,zh" \
     --write-description \
     --write-info-json \
     -o "output/%(title)s.%(ext)s"
   ```

---

## ✅ 方案2：手动下载 + Whisper转录（100%可行）

### 步骤：

1. **手动下载视频**
   - 使用抖音APP或网页版
   - 点击视频右下角"..."
   - 选择"保存本地"或使用第三方工具（如：Snaptik, SaveTok）

2. **使用Whisper转录**
   ```bash
   # 安装Whisper
   pip install openai-whisper
   
   # 转录音频（自动提取）
   whisper video.mp4 \
     --language Chinese \
     --model large \
     --output_format srt \
     --output_dir output/
   ```

3. **效果**
   - ✅ 准确率90-95%
   - ✅ 自动生成SRT字幕文件
   - ✅ 带时间戳

---

## ✅ 方案3：使用第三方下载服务（快速测试）

### 在线服务（无需Cookie）：

1. **SnapTik** - https://snaptik.app
   - 粘贴链接
   - 下载视频
   - 部分视频包含字幕

2. **SaveTok** - https://savetok.app
   - 同上

3. **Douyin Downloader** - https://douyin.wtf
   - 专门针对抖音
   - 支持批量下载

### 手动操作流程：
```
1. 在抖音APP复制视频链接
2. 打开上述任意网站
3. 粘贴链接 → 下载
4. 保存到本地
```

---

## ✅ 方案4：使用Playwright自动化（最完整）

如果需要批量下载，可以使用浏览器自动化：

```python
from playwright.sync_api import sync_playwright

def download_with_browser(video_url):
    """使用真实浏览器下载"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        # 1. 登录抖音（手动或自动）
        page.goto("https://www.douyin.com")
        input("请在浏览器中登录，然后按回车...")
        
        # 2. 访问视频页面
        page.goto(video_url)
        
        # 3. 提取视频URL和字幕
        # ... (需要分析页面结构)
        
        browser.close()
```

---

## 🎯 我的建议：混合方案

针对你的场景（构建财经知识库），我建议：

### 第一阶段：小规模测试（5-10个视频）
```bash
# 1. 手动下载几个视频（使用第三方网站）
# 2. 使用Whisper转录
whisper video1.mp4 --language Chinese --model large --output_format txt
whisper video2.mp4 --language Chinese --model large --output_format txt

# 3. 验证转录质量
# 4. 构建MVP知识库
```

### 第二阶段：规模化（所有视频）
```bash
# 1. 获取抖音Cookie（方案1）
# 2. 使用yt-dlp批量下载
# 3. 对无字幕视频使用Whisper补充
```

---

## 📋 Whisper转录脚本（推荐使用）

我已经为你准备了一个完整的转录脚本，即使无法自动下载视频，也可以手动下载后用这个脚本处理：

**创建文件：** `whisper_transcribe.py`

```python
#!/usr/bin/env python3
import whisper
import sys
from pathlib import Path

def transcribe_video(video_path, output_dir="output"):
    """使用Whisper转录视频"""
    
    print(f"🎤 加载Whisper模型（large）...")
    model = whisper.load_model("large")
    
    print(f"📹 处理视频: {video_path}")
    result = model.transcribe(
        str(video_path),
        language="zh",
        task="transcribe",
        verbose=True
    )
    
    # 保存文本
    txt_path = Path(output_dir) / f"{Path(video_path).stem}.txt"
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(result["text"])
    
    # 保存SRT字幕
    srt_path = Path(output_dir) / f"{Path(video_path).stem}.srt"
    with open(srt_path, 'w', encoding='utf-8') as f:
        for i, segment in enumerate(result["segments"]):
            start = segment["start"]
            end = segment["end"]
            text = segment["text"]
            
            f.write(f"{i+1}\n")
            f.write(f"{format_time(start)} --> {format_time(end)}\n")
            f.write(f"{text.strip()}\n\n")
    
    print(f"✅ 转录完成!")
    print(f"   文本: {txt_path}")
    print(f"   字幕: {srt_path}")

def format_time(seconds):
    """格式化时间为SRT格式"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{ms:03d}"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python whisper_transcribe.py video.mp4")
        sys.exit(1)
    
    transcribe_video(sys.argv[1])
```

**使用方法：**
```bash
# 1. 安装Whisper
pip install openai-whisper

# 2. 手动下载一个测试视频，保存为 test_video.mp4

# 3. 运行转录
python whisper_transcribe.py test_video.mp4

# 4. 检查输出
ls output/
```

---

## 🔍 下一步行动

请选择一个方案试试：

1. **快速验证（推荐）**：手动下载1个视频 → Whisper转录 → 看质量如何
2. **完整方案**：配置Cookie → 批量下载
3. **需要帮助**：告诉我你选哪个方案，我帮你详细设置
