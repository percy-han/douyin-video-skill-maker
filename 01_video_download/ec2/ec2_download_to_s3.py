#!/usr/bin/env python3
"""
EC2上运行的完整下载+上传S3脚本
Author: Claude
Date: 2026-04-17
"""

import subprocess
import sys
from pathlib import Path
import time
import boto3
from datetime import datetime

def install_dependencies():
    """安装必要依赖"""
    print("=" * 60)
    print("📦 安装依赖")
    print("=" * 60)

    packages = ['f2', 'openai-whisper', 'boto3']

    for pkg in packages:
        print(f"\n安装 {pkg}...")
        try:
            subprocess.run(
                ["pip3", "install", "--user", pkg],
                check=True,
                capture_output=True
            )
            print(f"✅ {pkg} 安装成功")
        except Exception as e:
            print(f"⚠️  {pkg} 安装失败: {e}")


def download_videos(homepage_url, cookie_file="douyin_cookie.txt", output_dir="batch_output"):
    """批量下载视频"""

    print("\n" + "=" * 60)
    print("🎬 批量下载视频")
    print("=" * 60)
    print(f"🔗 博主主页: {homepage_url}")
    print(f"📁 输出目录: {output_dir}")

    # 读取Cookie
    with open(cookie_file, 'r', encoding='utf-8') as f:
        cookie = f.read().strip()

    cmd = [
        "python3", "-m", "f2", "dy",
        "-M", "post",
        "-u", homepage_url,
        "-p", output_dir,
        "-d", "True",
        "-v", "True",
        "-m", "True",
        "-k", cookie,
        "-o", "0",
        "-s", "20",
        "-e", "30",
        "-r", "5",
        "-t", "5",
        "-f", "True",
        "-i", "all"
    ]

    print("\n⏳ 开始下载...\n")

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        for line in process.stdout:
            print(line, end='')

        process.wait()

        if process.returncode == 0:
            print("\n✅ 下载完成")
            return True
        else:
            print("\n❌ 下载失败")
            return False

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        return False


def upload_to_s3(local_dir, s3_bucket, s3_prefix=None):
    """
    上传文件到S3

    Args:
        local_dir: 本地目录
        s3_bucket: S3桶名
        s3_prefix: S3前缀（可选）
    """

    print("\n" + "=" * 60)
    print("📤 上传到S3")
    print("=" * 60)

    # 生成时间戳前缀
    if not s3_prefix:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        s3_prefix = f"douyin_videos/{timestamp}"

    print(f"📦 S3桶: {s3_bucket}")
    print(f"📁 S3路径: s3://{s3_bucket}/{s3_prefix}/")

    local_path = Path(local_dir)
    if not local_path.exists():
        print(f"❌ 本地目录不存在: {local_dir}")
        return False

    try:
        s3 = boto3.client('s3')

        # 收集所有文件
        all_files = list(local_path.rglob("*"))
        total_files = len([f for f in all_files if f.is_file()])

        print(f"\n📊 找到 {total_files} 个文件")

        # 分类上传
        video_files = []
        other_files = []

        for file in all_files:
            if not file.is_file():
                continue

            if file.suffix.lower() in ['.mp4', '.webm', '.mkv', '.avi']:
                video_files.append(file)
            else:
                other_files.append(file)

        print(f"   📹 视频文件: {len(video_files)}")
        print(f"   📄 其他文件: {len(other_files)}")

        # 先上传小文件（文案、封面等）
        print("\n⏳ 上传文案和元数据...")
        for i, file in enumerate(other_files, 1):
            relative_path = file.relative_to(local_path)
            s3_key = f"{s3_prefix}/{relative_path}"

            print(f"  [{i}/{len(other_files)}] {file.name}...", end='')

            try:
                s3.upload_file(
                    str(file),
                    s3_bucket,
                    s3_key,
                    ExtraArgs={'ContentType': get_content_type(file)}
                )
                print(" ✅")
            except Exception as e:
                print(f" ❌ {e}")

        # 上传视频文件（使用INTELLIGENT_TIERING存储类）
        print("\n⏳ 上传视频文件...")
        for i, file in enumerate(video_files, 1):
            relative_path = file.relative_to(local_path)
            s3_key = f"{s3_prefix}/{relative_path}"

            size_mb = file.stat().st_size / (1024 * 1024)
            print(f"  [{i}/{len(video_files)}] {file.name} ({size_mb:.2f}MB)...", end='')

            try:
                # 使用分段上传（适合大文件）
                s3.upload_file(
                    str(file),
                    s3_bucket,
                    s3_key,
                    ExtraArgs={
                        'ContentType': 'video/mp4',
                        'StorageClass': 'INTELLIGENT_TIERING'  # 智能分层存储
                    }
                )
                print(" ✅")
            except Exception as e:
                print(f" ❌ {e}")

        print("\n✅ 上传完成")
        print(f"\nS3路径: s3://{s3_bucket}/{s3_prefix}/")

        return f"s3://{s3_bucket}/{s3_prefix}/"

    except Exception as e:
        print(f"\n❌ 上传失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def get_content_type(file):
    """根据文件后缀返回Content-Type"""
    suffix_map = {
        '.txt': 'text/plain',
        '.json': 'application/json',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.webp': 'image/webp',
        '.mp4': 'video/mp4',
        '.webm': 'video/webm',
        '.srt': 'text/plain',
    }
    return suffix_map.get(file.suffix.lower(), 'application/octet-stream')


def generate_manifest(s3_bucket, s3_prefix, output_file="s3_manifest.txt"):
    """生成S3文件清单"""

    print("\n📋 生成文件清单...")

    try:
        s3 = boto3.client('s3')

        # 列出所有文件
        paginator = s3.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=s3_bucket, Prefix=s3_prefix)

        files = []
        total_size = 0

        for page in pages:
            if 'Contents' in page:
                for obj in page['Contents']:
                    files.append({
                        'key': obj['Key'],
                        'size': obj['Size'],
                        'modified': obj['LastModified']
                    })
                    total_size += obj['Size']

        # 保存清单
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write(f"S3文件清单 - s3://{s3_bucket}/{s3_prefix}/\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"总文件数: {len(files)}\n")
            f.write(f"总大小: {total_size / (1024**3):.2f} GB\n\n")
            f.write("-" * 80 + "\n\n")

            for file in files:
                size_mb = file['size'] / (1024 * 1024)
                f.write(f"{file['key']}\n")
                f.write(f"  大小: {size_mb:.2f} MB\n")
                f.write(f"  修改时间: {file['modified']}\n\n")

        print(f"✅ 清单已保存: {output_file}")
        print(f"   总文件: {len(files)}")
        print(f"   总大小: {total_size / (1024**3):.2f} GB")

        # 上传清单到S3
        manifest_key = f"{s3_prefix}/manifest.txt"
        s3.upload_file(output_file, s3_bucket, manifest_key)
        print(f"✅ 清单已上传: s3://{s3_bucket}/{manifest_key}")

        return True

    except Exception as e:
        print(f"❌ 生成清单失败: {e}")
        return False


def main():
    print("""
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║      🚀 EC2批量下载器 + S3上传                            ║
║                                                          ║
║      完整的下载、转录、上传流程                            ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
    """)

    # 检查参数
    if len(sys.argv) < 3:
        print("用法:")
        print("  python3 ec2_download_to_s3.py <博主主页链接> <S3桶名>")
        print("\n示例:")
        print("  python3 ec2_download_to_s3.py 'https://www.douyin.com/user/xxx' 'my-bucket'")
        return

    homepage_url = sys.argv[1]
    s3_bucket = sys.argv[2]
    s3_prefix = sys.argv[3] if len(sys.argv) > 3 else None

    # 检查Cookie
    if not Path("douyin_cookie.txt").exists():
        print("❌ 未找到Cookie文件: douyin_cookie.txt")
        print("\n请先将Cookie文件上传到EC2")
        return

    print("\n配置:")
    print(f"  博主: {homepage_url}")
    print(f"  S3桶: {s3_bucket}")
    print(f"  S3前缀: {s3_prefix or '自动生成'}")

    # 确认
    confirm = input("\n继续？(y/n): ").strip().lower()
    if confirm != 'y':
        print("已取消")
        return

    start_time = time.time()

    # 1. 下载视频
    if not download_videos(homepage_url):
        print("\n❌ 下载失败，停止")
        return

    # 2. 上传到S3
    s3_path = upload_to_s3("batch_output", s3_bucket, s3_prefix)

    if not s3_path:
        print("\n❌ 上传失败")
        return

    # 3. 生成清单
    if s3_prefix:
        generate_manifest(s3_bucket, s3_prefix)
    else:
        # 从返回的路径提取prefix
        prefix = s3_path.replace(f"s3://{s3_bucket}/", "").rstrip('/')
        generate_manifest(s3_bucket, prefix)

    # 完成
    elapsed = time.time() - start_time
    hours = int(elapsed // 3600)
    minutes = int((elapsed % 3600) // 60)

    print("\n" + "=" * 60)
    print("✨ 全部完成！")
    print("=" * 60)
    print(f"\n⏱️  总耗时: {hours}小时{minutes}分钟")
    print(f"📦 S3路径: {s3_path}")
    print(f"\n查看文件:")
    print(f"  aws s3 ls {s3_path} --recursive")


if __name__ == "__main__":
    main()
