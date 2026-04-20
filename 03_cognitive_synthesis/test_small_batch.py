#!/usr/bin/env python3
"""
测试版：只处理前N个视频（避免高成本）

使用方法:
export S3_BUCKET=percyhan-douyin-video
export S3_PREFIX=post/刘德超/
export TEST_VIDEO_COUNT=10  # 只处理10个视频

python test_small_batch.py
"""

import os
import sys

# 修改环境变量，限制处理数量
TEST_VIDEO_COUNT = int(os.environ.get('TEST_VIDEO_COUNT', 10))

print(f"🧪 测试模式：只处理前 {TEST_VIDEO_COUNT} 个视频")
print("="*60)

# 修改main函数，添加限制
import cognitive_synthesis as cs

# Monkey patch main函数
original_main = cs.main

def test_main():
    """测试版main - 限制视频数量"""

    S3_BUCKET = os.environ.get('S3_BUCKET', 'percyhan-douyin-video')
    S3_PREFIX = os.environ.get('S3_PREFIX', 'post/刘德超/')
    OUTPUT_DIR = '/tmp/skill_output'

    print("🧠 认知框架合成器（测试模式）")
    print("="*60)
    print(f"S3: s3://{S3_BUCKET}/{S3_PREFIX}")
    print(f"⚠️  限制: 只处理前 {TEST_VIDEO_COUNT} 个视频")
    print()

    # 1. 从S3加载转录文件（限制数量）
    print("📥 从S3加载转录结果...")
    import boto3
    import json

    s3 = boto3.client('s3')
    all_transcripts = []
    paginator = s3.get_paginator('list_objects_v2')

    for page in paginator.paginate(Bucket=S3_BUCKET, Prefix=S3_PREFIX):
        if 'Contents' not in page:
            continue

        for obj in page['Contents']:
            key = obj['Key']

            # 只加载 transcript.json 文件
            if key.endswith('_transcript.json'):
                try:
                    response = s3.get_object(Bucket=S3_BUCKET, Key=key)
                    content = response['Body'].read().decode('utf-8')
                    transcript = json.loads(content)
                    all_transcripts.append(transcript)

                    # 达到限制就停止
                    if len(all_transcripts) >= TEST_VIDEO_COUNT:
                        print(f"   ⚠️  已达到测试限制 ({TEST_VIDEO_COUNT}个)，停止加载")
                        break

                except Exception as e:
                    print(f"   ⚠️  跳过 {key}: {e}")

        # 外层循环也要检查
        if len(all_transcripts) >= TEST_VIDEO_COUNT:
            break

    print(f"   加载了 {len(all_transcripts)} 个转录文件")

    if not all_transcripts:
        print("❌ 没有找到转录文件")
        return

    # 2. 执行认知合成
    synthesizer = cs.CognitiveSynthesizer()
    synthesis = synthesizer.synthesize(all_transcripts, OUTPUT_DIR)

    # 3. 生成SKILL.md
    skill_generator = cs.SkillGenerator()
    skill_path = os.path.join(OUTPUT_DIR, 'SKILL.md')
    skill_generator.generate(synthesis, skill_path)

    # 4. 保存完整的synthesis JSON
    synthesis_path = os.path.join(OUTPUT_DIR, 'cognitive_synthesis.json')
    with open(synthesis_path, 'w', encoding='utf-8') as f:
        json.dump(synthesis, f, ensure_ascii=False, indent=2)
    print(f"\n💾 完整数据已保存: {synthesis_path}")

    # 5. 上传到S3（测试模式加后缀）
    print(f"\n☁️  上传到S3...")
    test_suffix = f"_test_{TEST_VIDEO_COUNT}"
    s3.upload_file(skill_path, S3_BUCKET, f"{S3_PREFIX}SKILL{test_suffix}.md")
    s3.upload_file(synthesis_path, S3_BUCKET, f"{S3_PREFIX}cognitive_synthesis{test_suffix}.json")

    # 上传单视频框架
    video_frameworks_path = os.path.join(OUTPUT_DIR, 'video_frameworks.json')
    if os.path.exists(video_frameworks_path):
        s3.upload_file(video_frameworks_path, S3_BUCKET, f"{S3_PREFIX}video_frameworks{test_suffix}.json")

    print("\n" + "="*60)
    print("🎉 认知框架合成完成（测试模式）！")
    print("="*60)
    print(f"心智模型：{len(synthesis['mental_models'])} 个")
    print(f"决策启发式：{len(synthesis['heuristics'])} 条")
    print(f"表达DNA：已量化")
    print(f"SKILL.md: s3://{S3_BUCKET}/{S3_PREFIX}SKILL{test_suffix}.md")
    print(f"单视频框架: s3://{S3_BUCKET}/{S3_PREFIX}video_frameworks{test_suffix}.json")
    print()
    print(f"⚠️  注意：这是基于 {len(all_transcripts)} 个视频的测试结果")
    print(f"   如果满意，删除 TEST_VIDEO_COUNT 环境变量，运行完整版")

if __name__ == '__main__':
    test_main()
