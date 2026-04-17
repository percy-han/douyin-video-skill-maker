#!/usr/bin/env python3
"""
使用Whisper转录视频音频
适用于手动下载的抖音视频
Author: Claude
Date: 2026-04-17
"""

import sys
from pathlib import Path

def check_whisper():
    """检查Whisper是否安装"""
    try:
        import whisper
        print(f"✅ Whisper 已安装")
        return True
    except ImportError:
        print("❌ Whisper 未安装")
        print("安装命令: pip install openai-whisper")
        return False


def transcribe_video(video_path, output_dir="output", model_size="large"):
    """
    使用Whisper转录视频

    Args:
        video_path: 视频文件路径
        output_dir: 输出目录
        model_size: 模型大小 (tiny, base, small, medium, large)
                    - tiny: 最快，准确率最低
                    - base: 快速，准确率一般
                    - small: 平衡
                    - medium: 较慢，准确率较高
                    - large: 最慢，准确率最高（推荐用于财经视频）
    """
    import whisper

    video_path = Path(video_path)
    if not video_path.exists():
        print(f"❌ 文件不存在: {video_path}")
        return False

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print(f"🎤 Whisper 音频转录")
    print("=" * 60)
    print(f"📹 视频: {video_path.name}")
    print(f"📁 输出: {output_dir}")
    print(f"🧠 模型: {model_size}")
    print("-" * 60)

    try:
        # 加载模型
        print(f"\n⏳ 加载Whisper模型（{model_size}）...")
        model = whisper.load_model(model_size)

        # 转录
        print(f"⏳ 开始转录（这可能需要几分钟）...")
        result = model.transcribe(
            str(video_path),
            language="zh",  # 中文
            task="transcribe",
            verbose=False,  # 不显示详细输出
            # 优化参数
            temperature=0.0,  # 降低随机性
            best_of=5,  # 多次采样取最佳
            beam_size=5,  # beam search
            patience=1.0
        )

        # 保存纯文本
        txt_path = output_path / f"{video_path.stem}.txt"
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(result["text"])
        print(f"\n✅ 纯文本已保存: {txt_path.name}")

        # 保存SRT字幕（带时间戳）
        srt_path = output_path / f"{video_path.stem}.srt"
        with open(srt_path, 'w', encoding='utf-8') as f:
            for i, segment in enumerate(result["segments"]):
                start = segment["start"]
                end = segment["end"]
                text = segment["text"].strip()

                f.write(f"{i+1}\n")
                f.write(f"{format_time(start)} --> {format_time(end)}\n")
                f.write(f"{text}\n\n")
        print(f"✅ SRT字幕已保存: {srt_path.name}")

        # 保存详细JSON（包含每句的置信度）
        import json
        json_path = output_path / f"{video_path.stem}_segments.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(result["segments"], f, ensure_ascii=False, indent=2)
        print(f"✅ 详细数据已保存: {json_path.name}")

        # 显示预览
        print("\n" + "=" * 60)
        print("📄 转录内容预览")
        print("=" * 60)
        text = result["text"]
        print(text[:500] + ("..." if len(text) > 500 else ""))

        # 统计信息
        print("\n" + "=" * 60)
        print("📊 统计信息")
        print("=" * 60)
        print(f"总字数: {len(text)}")
        print(f"总时长: {result['segments'][-1]['end']:.2f} 秒")
        print(f"片段数: {len(result['segments'])}")

        return True

    except Exception as e:
        print(f"\n❌ 转录失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def format_time(seconds):
    """格式化时间为SRT格式 (HH:MM:SS,mmm)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{ms:03d}"


def batch_transcribe(video_dir, output_dir="output"):
    """批量转录目录下的所有视频"""
    video_dir = Path(video_dir)
    video_files = []

    # 支持的视频格式
    extensions = ['.mp4', '.mov', '.avi', '.mkv', '.flv', '.webm']

    for ext in extensions:
        video_files.extend(video_dir.glob(f"*{ext}"))

    if not video_files:
        print(f"❌ 在 {video_dir} 中没有找到视频文件")
        return

    print(f"📂 找到 {len(video_files)} 个视频文件")
    print("-" * 60)

    success_count = 0
    for i, video_file in enumerate(video_files, 1):
        print(f"\n[{i}/{len(video_files)}] 处理: {video_file.name}")
        if transcribe_video(video_file, output_dir):
            success_count += 1

    print("\n" + "=" * 60)
    print(f"✨ 批量处理完成！")
    print(f"   成功: {success_count}/{len(video_files)}")
    print("=" * 60)


def main():
    """主函数"""
    if not check_whisper():
        print("\n请先安装Whisper:")
        print("  pip install openai-whisper")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("🎬 Whisper 视频转录工具")
    print("=" * 60)

    if len(sys.argv) < 2:
        print("\n用法:")
        print("  单个文件: python whisper_transcribe.py video.mp4")
        print("  批量处理: python whisper_transcribe.py video_dir/ --batch")
        print("\n模型选择:")
        print("  --model tiny|base|small|medium|large")
        print("  默认: large (推荐)")
        sys.exit(1)

    # 解析参数
    target = sys.argv[1]
    is_batch = "--batch" in sys.argv

    # 模型大小
    model_size = "large"
    if "--model" in sys.argv:
        idx = sys.argv.index("--model")
        if idx + 1 < len(sys.argv):
            model_size = sys.argv[idx + 1]

    # 处理
    if is_batch:
        batch_transcribe(target, output_dir="output")
    else:
        transcribe_video(target, output_dir="output", model_size=model_size)


if __name__ == "__main__":
    main()
