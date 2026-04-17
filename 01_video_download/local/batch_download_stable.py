#!/usr/bin/env python3
"""
稳定版批量下载 - 优化网络参数
Author: Claude
Date: 2026-04-17
"""

import subprocess
import sys
from pathlib import Path
import time

def batch_download_stable(homepage_url, cookie_file="douyin_cookie.txt", output_dir="batch_output"):
    """
    稳定版批量下载 - 优化网络参数

    优化：
    1. 增加重试次数（5→10）
    2. 增加超时时间（30→60秒）
    3. 降低并发数（5→3，减少服务器压力）
    4. 每页视频数减少（20→10，更稳定）
    """

    cookie_path = Path(cookie_file)
    if not cookie_path.exists():
        print(f"❌ Cookie文件不存在: {cookie_file}")
        return False

    with open(cookie_path, 'r', encoding='utf-8') as f:
        cookie = f.read().strip()

    print("=" * 60)
    print("🚀 稳定版批量下载")
    print("=" * 60)
    print(f"\n📌 博主主页: {homepage_url}")
    print(f"📁 输出目录: {output_dir}")
    print("\n⚙️  优化参数:")
    print("  - 重试次数: 10次")
    print("  - 超时时间: 60秒")
    print("  - 并发任务: 3个（降低服务器压力）")
    print("  - 每页数量: 10个（更稳定）")
    print("-" * 60)

    # 优化后的F2参数
    cmd = [
        "python3", "-m", "f2", "dy",
        "-M", "post",
        "-u", homepage_url,
        "-p", output_dir,
        "-d", "True",
        "-v", "True",
        "-m", "True",
        "-k", cookie,
        "-o", "0",      # 下载所有
        "-s", "10",     # 每页10个（降低）
        "-e", "60",     # 超时60秒（增加）
        "-r", "10",     # 重试10次（增加）
        "-t", "3",      # 并发3个（降低）
        "-f", "True",
        "-i", "all"
    ]

    print("\n🎬 开始下载...\n")

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        error_count = 0
        success_count = 0

        for line in process.stdout:
            print(line, end='')

            # 统计错误
            if 'ERROR' in line or '失败' in line:
                error_count += 1
            if '完成' in line or 'SUCCESS' in line:
                success_count += 1

        process.wait()

        print("\n" + "=" * 60)
        print("📊 下载统计")
        print("=" * 60)
        print(f"✅ 成功: {success_count}")
        print(f"❌ 错误: {error_count}")

        # 统计文件
        output_path = Path(output_dir)
        if output_path.exists():
            video_files = list(output_path.rglob("*.mp4"))
            print(f"\n📹 视频文件: {len(video_files)} 个")

            total_size = sum(f.stat().st_size for f in video_files if f.is_file())
            print(f"💾 总大小: {total_size / (1024**3):.2f} GB")

        if error_count > 0:
            print("\n⚠️  部分文件下载失败")
            print("这是正常现象（网络波动、服务器限流）")
            print("\n💡 建议:")
            print("  1. 等待5-10分钟后重新运行此脚本")
            print("  2. F2会自动跳过已下载的文件")
            print("  3. 只下载失败的文件")

        return True

    except KeyboardInterrupt:
        print("\n\n⏸️  用户中断")
        return False
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        return False


def check_failed_downloads(output_dir="batch_output"):
    """检查哪些视频可能下载失败"""

    print("\n" + "=" * 60)
    print("🔍 检查下载完整性")
    print("=" * 60)

    output_path = Path(output_dir)
    if not output_path.exists():
        print("未找到输出目录")
        return

    # 查找所有视频文件夹
    video_dirs = [d for d in output_path.iterdir() if d.is_dir()]

    incomplete = []
    for video_dir in video_dirs:
        # 检查是否有视频文件
        video_files = list(video_dir.glob("*.mp4"))

        if not video_files:
            incomplete.append(video_dir.name)
        else:
            # 检查文件大小是否异常（小于100KB可能不完整）
            for vf in video_files:
                if vf.stat().st_size < 100 * 1024:
                    incomplete.append(f"{video_dir.name} (文件过小)")

    if incomplete:
        print(f"\n⚠️  发现 {len(incomplete)} 个可能不完整的下载:")
        for i, item in enumerate(incomplete[:10], 1):
            print(f"  {i}. {item}")

        if len(incomplete) > 10:
            print(f"  ... 还有 {len(incomplete) - 10} 个")

        print("\n💡 解决方案: 重新运行下载脚本")
        print("   F2会自动跳过已完成的，只下载失败的")
    else:
        print("✅ 所有视频下载完整")


def main():
    print("""
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║      🎬 稳定版批量下载器                                  ║
║                                                          ║
║      优化网络参数，减少下载失败                            ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
    """)

    if len(sys.argv) < 2:
        print("用法:")
        print("  python3 batch_download_stable.py '博主主页链接'")
        print("\n或者检查已下载文件:")
        print("  python3 batch_download_stable.py --check")
        return

    if sys.argv[1] == '--check':
        check_failed_downloads()
        return

    homepage_url = sys.argv[1]

    # 下载
    batch_download_stable(homepage_url)

    # 下载完成后自动检查
    time.sleep(2)
    check_failed_downloads()


if __name__ == "__main__":
    main()
