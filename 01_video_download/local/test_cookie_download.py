#!/usr/bin/env python3
"""
测试Cookie是否有效 - 简化版
Author: Claude
Date: 2026-04-17
"""

import subprocess
from pathlib import Path
import sys

def test_cookie():
    """测试Cookie文件"""

    print("=" * 60)
    print("🧪 Cookie测试")
    print("=" * 60)

    # 检查Cookie文件
    cookie_file = Path("douyin_cookie.txt")
    if not cookie_file.exists():
        print("\n❌ 错误：未找到 douyin_cookie.txt")
        print("\n请先创建Cookie文件：")
        print("  nano douyin_cookie.txt")
        print("  粘贴Cookie → Ctrl+O → Enter → Ctrl+X")
        return False

    # 读取Cookie
    with open(cookie_file, 'r', encoding='utf-8') as f:
        cookie = f.read().strip()

    # 验证Cookie
    print(f"\n✅ 找到Cookie文件")
    print(f"   长度: {len(cookie)} 字符")

    if len(cookie) < 100:
        print("\n⚠️  警告: Cookie太短，可能不完整")
        print(f"   当前: {len(cookie)} 字符")
        print(f"   预期: 500-2000 字符")

    # 检查关键字段
    key_fields = ['ttwid=', 'passport_csrf_token=', 'odin_tt=']
    missing_fields = [f for f in key_fields if f not in cookie]

    if missing_fields:
        print(f"\n⚠️  警告: 缺少关键字段: {', '.join(missing_fields)}")
        print("   Cookie可能不完整或未登录")
    else:
        print(f"\n✅ Cookie包含所有关键字段")

    # 显示Cookie前100字符
    print(f"\n📄 Cookie预览:")
    print(f"   {cookie[:100]}...")

    # 测试下载
    print("\n" + "=" * 60)
    print("🎬 测试下载单个视频")
    print("=" * 60)

    video_url = "https://v.douyin.com/ZH520PuJgeM/"
    print(f"\n🔗 测试链接: {video_url}")
    print("⏳ 正在下载...\n")

    cmd = [
        "python3", "-m", "f2", "dy",
        "-M", "one",
        "-u", video_url,
        "-p", "test_output",
        "-d", "True",
        "-k", cookie,
        "-e", "30",
        "-r", "3"
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )

        # 显示输出
        print(result.stdout)

        # 检查是否成功
        if result.returncode == 0:
            # 查找视频文件
            output_dir = Path("test_output")
            if output_dir.exists():
                video_files = list(output_dir.rglob("*.mp4"))

                if video_files:
                    print("\n" + "=" * 60)
                    print("✅ Cookie有效！下载成功！")
                    print("=" * 60)

                    for f in video_files:
                        size_mb = f.stat().st_size / (1024 * 1024)
                        print(f"\n📹 {f.name}")
                        print(f"   大小: {size_mb:.2f} MB")
                        print(f"   路径: {f}")

                    print("\n🎉 测试通过！可以开始批量下载了！")
                    print("\n下一步:")
                    print("  python3 batch_download.py")

                    return True

        # 失败处理
        print("\n" + "=" * 60)
        print("❌ Cookie无效或下载失败")
        print("=" * 60)

        # 分析错误
        output = result.stdout + result.stderr

        if "cookie" in output.lower():
            print("\n💡 可能的原因:")
            print("  1. Cookie已过期")
            print("  2. 未在浏览器中登录抖音")
            print("  3. Cookie复制不完整")

            print("\n🔧 解决方法:")
            print("  1. 重新登录抖音网页版")
            print("  2. 重新获取Cookie")
            print("  3. 确保Cookie包含所有字段（没有截断）")

        elif "响应内容为空" in output or "响应为空" in output:
            print("\n💡 可能的原因:")
            print("  1. 反爬虫限制（需要等待几分钟）")
            print("  2. Cookie不完整")

            print("\n🔧 解决方法:")
            print("  1. 等待5-10分钟后重试")
            print("  2. 检查Cookie是否完整")

        else:
            print("\n错误输出:")
            print(result.stderr[:500])

        return False

    except subprocess.TimeoutExpired:
        print("\n❌ 超时: 下载时间过长")
        return False

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        return False


def main():
    print("""
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║          🧪 Cookie测试工具                               ║
║                                                          ║
║          快速验证Cookie是否有效                           ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
    """)

    # 检查是否在正确目录
    if not Path("douyin_cookie.txt").exists():
        print("⚠️  提示: 未找到 douyin_cookie.txt")
        print("\n请先创建Cookie文件（任选一种方法）：\n")
        print("方法1 - 使用nano编辑器（推荐）:")
        print("  nano douyin_cookie.txt")
        print("  粘贴Cookie → Ctrl+O → Enter → Ctrl+X\n")
        print("方法2 - 使用echo命令:")
        print("  echo '你的Cookie' > douyin_cookie.txt\n")
        print("详细说明请查看: COOKIE_SETUP_SIMPLE.md")
        return

    success = test_cookie()

    if not success:
        print("\n📖 需要帮助？查看详细文档:")
        print("  cat COOKIE_SETUP_SIMPLE.md")


if __name__ == "__main__":
    main()
