#!/usr/bin/env python3
"""
配置Cookie - 一次配置，批量下载
Author: Claude
Date: 2026-04-17
"""

import subprocess
from pathlib import Path

def setup_cookie():
    """配置Cookie的完整指南"""

    print("=" * 60)
    print("🔐 抖音Cookie配置指南")
    print("=" * 60)

    print("\n📋 步骤1：获取Cookie")
    print("-" * 60)
    print("""
1. 打开Chrome浏览器（或其他浏览器）
2. 访问 https://www.douyin.com
3. 登录你的抖音账号
4. 按 F12 打开开发者工具
5. 切换到 "Network" (网络) 标签
6. 刷新页面（F5）
7. 点击任意一个请求
8. 找到 "Request Headers" (请求头)
9. 找到 "Cookie:" 这一行
10. 复制完整的Cookie字符串
""")

    print("\n📋 Cookie长什么样？")
    print("-" * 60)
    print("示例（前100字符）：")
    print("ttwid=1%7C...; passport_csrf_token=...; odin_tt=...; ...")
    print("\n⚠️  完整Cookie通常有500-2000个字符")

    print("\n" + "=" * 60)
    print("请粘贴你的Cookie（粘贴后按回车）：")
    print("=" * 60)

    try:
        cookie = input().strip()
    except KeyboardInterrupt:
        print("\n❌ 用户取消")
        return None

    if not cookie:
        print("❌ Cookie不能为空")
        return None

    if len(cookie) < 100:
        print("⚠️  Cookie太短，可能不完整")
        print(f"   当前长度：{len(cookie)} 字符")
        print("   预期长度：500-2000 字符")

        confirm = input("\n是否继续？(y/n): ").strip().lower()
        if confirm != 'y':
            return None

    # 保存Cookie
    cookie_file = Path("douyin_cookie.txt")
    with open(cookie_file, 'w', encoding='utf-8') as f:
        f.write(cookie)

    print(f"\n✅ Cookie已保存到: {cookie_file}")
    print(f"   长度：{len(cookie)} 字符")

    return cookie


def test_cookie(cookie):
    """测试Cookie是否有效"""

    print("\n" + "=" * 60)
    print("🧪 测试Cookie有效性")
    print("=" * 60)

    video_url = "https://v.douyin.com/ZH520PuJgeM/"
    print(f"\n🔗 测试链接：{video_url}")
    print("⏳ 正在下载...\n")

    cmd = [
        "python3", "-m", "f2", "dy",
        "-M", "one",
        "-u", video_url,
        "-p", "output",
        "-d", "True",
        "-v", "True",
        "-k", cookie,  # 使用Cookie参数
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

        print(result.stdout)

        if result.returncode == 0:
            # 检查是否真的下载了文件
            files = list(Path("output").rglob("*.mp4"))
            if files:
                print("\n" + "=" * 60)
                print("✅ Cookie有效！下载成功！")
                print("=" * 60)
                for f in files:
                    size_mb = f.stat().st_size / (1024 * 1024)
                    print(f"📹 {f.name} ({size_mb:.2f} MB)")
                return True
            else:
                print("\n⚠️  命令执行成功但未找到视频文件")
                return False
        else:
            print("\n" + "=" * 60)
            print("❌ Cookie无效或已过期")
            print("=" * 60)

            if "cookie" in result.stderr.lower():
                print("错误信息提示Cookie问题")

            print("\n💡 请尝试：")
            print("1. 重新获取Cookie（确保已登录）")
            print("2. 使用无痕模式登录，避免Cookie冲突")

            return False

    except subprocess.TimeoutExpired:
        print("\n❌ 下载超时")
        return False
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        return False


def main():
    print("""
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║      🎬 抖音批量下载 - Cookie配置工具                    ║
║                                                          ║
║      配置一次，批量下载几百个视频                         ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
""")

    # 检查是否已有Cookie
    cookie_file = Path("douyin_cookie.txt")
    if cookie_file.exists():
        print(f"✅ 检测到已保存的Cookie文件")
        print(f"   文件：{cookie_file}")

        use_existing = input("\n是否使用已有Cookie？(y/n): ").strip().lower()
        if use_existing == 'y':
            with open(cookie_file, 'r', encoding='utf-8') as f:
                cookie = f.read().strip()
            print(f"✅ 已加载Cookie（{len(cookie)} 字符）")
        else:
            cookie = setup_cookie()
    else:
        cookie = setup_cookie()

    if not cookie:
        print("\n❌ 未配置Cookie，退出")
        return

    # 测试Cookie
    success = test_cookie(cookie)

    if success:
        print("\n" + "=" * 60)
        print("🎉 配置完成！")
        print("=" * 60)
        print("\n下一步：批量下载")
        print("""
使用方法：
  python3 batch_download.py --cookie douyin_cookie.txt

或者在F2命令中使用：
  python3 -m f2 dy -M post \\
    -u "博主主页链接" \\
    -k "$(cat douyin_cookie.txt)" \\
    -p output/
        """)
    else:
        print("\n❌ Cookie测试失败，请重新配置")


if __name__ == "__main__":
    main()
