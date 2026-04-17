#!/usr/bin/env python3
"""
批量下载博主所有视频
Author: Claude
Date: 2026-04-17
"""

import subprocess
import sys
from pathlib import Path
import time

def batch_download(homepage_url, cookie_file="douyin_cookie.txt", output_dir="batch_output"):
    """
    批量下载博主主页的所有视频

    Args:
        homepage_url: 博主主页链接
        cookie_file: Cookie文件路径
        output_dir: 输出目录
    """

    # 检查Cookie文件
    cookie_path = Path(cookie_file)
    if not cookie_path.exists():
        print(f"❌ Cookie文件不存在: {cookie_file}")
        print("\n请先运行: python3 setup_cookie.py")
        return False

    # 读取Cookie
    with open(cookie_path, 'r', encoding='utf-8') as f:
        cookie = f.read().strip()

    if not cookie:
        print("❌ Cookie文件为空")
        return False

    print("=" * 60)
    print("🚀 批量下载博主视频")
    print("=" * 60)
    print(f"\n📌 博主主页: {homepage_url}")
    print(f"🔐 Cookie长度: {len(cookie)} 字符")
    print(f"📁 输出目录: {output_dir}")
    print("-" * 60)

    # F2批量下载命令
    cmd = [
        "python3", "-m", "f2", "dy",
        "-M", "post",  # 主页作品模式
        "-u", homepage_url,
        "-p", output_dir,
        "-d", "True",  # 保存文案
        "-v", "True",  # 保存封面
        "-m", "True",  # 保存音频
        "-k", cookie,
        "-o", "0",     # 0表示下载所有视频（不限制数量）
        "-s", "20",    # 每页获取20个视频
        "-e", "30",    # 超时30秒
        "-r", "5",     # 重试5次
        "-t", "5",     # 并发任务数5
        "-f", "True",  # 每个视频单独文件夹
        "-i", "all"    # 下载所有日期的视频
    ]

    print("\n🎬 开始下载...\n")
    print("💡 提示：")
    print("  - 下载可能需要较长时间（取决于视频数量）")
    print("  - 进度会实时显示")
    print("  - 可以按 Ctrl+C 暂停")
    print("\n" + "-" * 60 + "\n")

    try:
        # 实时显示输出
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        # 读取并打印输出
        for line in process.stdout:
            print(line, end='')

        process.wait()

        if process.returncode == 0:
            print("\n" + "=" * 60)
            print("✅ 批量下载完成！")
            print("=" * 60)

            # 统计下载的文件
            output_path = Path(output_dir)
            if output_path.exists():
                video_files = list(output_path.rglob("*.mp4"))
                desc_files = list(output_path.rglob("*.txt"))
                cover_files = list(output_path.rglob("*.jpg")) + list(output_path.rglob("*.png"))

                print(f"\n📊 下载统计:")
                print(f"  📹 视频: {len(video_files)} 个")
                print(f"  📄 文案: {len(desc_files)} 个")
                print(f"  🖼️  封面: {len(cover_files)} 个")

                # 计算总大小
                total_size = sum(f.stat().st_size for f in video_files if f.is_file())
                total_size_mb = total_size / (1024 * 1024)
                print(f"  💾 总大小: {total_size_mb:.2f} MB")

            return True
        else:
            print("\n❌ 下载失败")
            return False

    except KeyboardInterrupt:
        print("\n\n⏸️  用户中断下载")
        print("提示：部分视频可能已下载，可以继续运行此脚本恢复下载")
        return False
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        return False


def get_homepage_url():
    """获取博主主页链接"""

    print("\n📋 如何获取博主主页链接？")
    print("-" * 60)
    print("""
方法1：从抖音APP
  1. 打开抖音APP
  2. 进入博主主页（观棋有语·刘德超）
  3. 点击右上角"..."
  4. 点击"分享"
  5. 复制链接

方法2：从抖音网页版
  1. 访问 https://www.douyin.com
  2. 搜索"观棋有语·刘德超"
  3. 进入主页
  4. 复制浏览器地址栏链接
    """)

    print("=" * 60)
    homepage = input("请输入博主主页链接: ").strip()
    print("=" * 60)

    return homepage


def main():
    print("""
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║      🎬 抖音批量下载器                                   ║
║                                                          ║
║      一键下载博主所有视频                                 ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
    """)

    # 检查Cookie配置
    cookie_file = "douyin_cookie.txt"
    if not Path(cookie_file).exists():
        print("⚠️  未检测到Cookie配置")
        print("\n请先配置Cookie:")
        print("  python3 setup_cookie.py")
        print("\n配置完成后再运行此脚本")
        return

    print("✅ 检测到Cookie配置\n")

    # 获取博主链接
    if len(sys.argv) > 1:
        homepage_url = sys.argv[1]
        print(f"📌 使用参数提供的链接: {homepage_url}")
    else:
        homepage_url = get_homepage_url()

    if not homepage_url:
        print("❌ 未提供博主链接")
        return

    # 确认下载
    print("\n⚠️  即将开始批量下载")
    print(f"   博主: 观棋有语·刘德超（假设）")
    print(f"   链接: {homepage_url}")
    print(f"   模式: 下载所有视频")
    print("\n这可能需要较长时间（几百个视频可能需要数小时）")

    confirm = input("\n确认开始下载？(y/n): ").strip().lower()
    if confirm != 'y':
        print("❌ 用户取消")
        return

    # 开始下载
    success = batch_download(homepage_url, cookie_file)

    if success:
        print("\n" + "=" * 60)
        print("🎉 任务完成！")
        print("=" * 60)
        print("\n下一步：字幕提取")
        print("""
使用Whisper批量转录：
  python3 whisper_transcribe.py batch_output/ --batch
        """)


if __name__ == "__main__":
    main()
