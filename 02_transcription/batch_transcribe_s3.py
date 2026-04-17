#!/usr/bin/env python3
"""
批量转录S3视频文件 - 带认知提取

工作流程：
1. 扫描S3，过滤视频文件（.mp4, .webm, .mkv）
2. 逐个下载 → Whisper转录 → 上传结果
3. 使用Claude提取分析框架（认知复刻）
4. 构建时间轴索引
"""

import os
import sys
import json
import time
import boto3
import whisper
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# ==================== 配置 ====================

S3_BUCKET = os.environ.get('S3_BUCKET', 'percyhan-douyin-video')
S3_PREFIX = os.environ.get('S3_PREFIX', 'douyin_videos/20260417_150000/')
WHISPER_MODEL = os.environ.get('WHISPER_MODEL', 'large')
TEMP_DIR = '/tmp/transcribe_temp'
OUTPUT_DIR = '/tmp/transcribe_output'

# ==================== 视频文件过滤器 ====================

class VideoFileFilter:
    """智能视频文件过滤器"""

    VIDEO_EXTENSIONS = {'.mp4', '.webm', '.mkv', '.avi', '.mov', '.flv'}
    EXCLUDE_PATTERNS = [
        '*_desc.txt',
        '*_cover.*',
        '*_audio.*',
        '*.jpg', '*.png', '*.webp',
        '*.json',
        '*_transcript.*'
    ]

    def is_video_file(self, s3_key: str) -> bool:
        """判断是否为需要处理的视频文件"""
        path = Path(s3_key)

        # 检查扩展名
        if path.suffix.lower() not in self.VIDEO_EXTENSIONS:
            return False

        # 检查是否为排除模式
        filename = path.name
        for pattern in self.EXCLUDE_PATTERNS:
            import fnmatch
            if fnmatch.fnmatch(filename, pattern):
                return False

        return True

    def list_videos_from_s3(self, bucket: str, prefix: str) -> List[Dict]:
        """从S3列出所有需要处理的视频"""
        s3 = boto3.client('s3')
        videos = []

        print(f"🔍 扫描S3视频文件: s3://{bucket}/{prefix}")

        paginator = s3.get_paginator('list_objects_v2')
        for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
            if 'Contents' not in page:
                continue

            for obj in page['Contents']:
                key = obj['Key']

                if self.is_video_file(key):
                    videos.append({
                        'key': key,
                        'size': obj['Size'],
                        'modified': obj['LastModified']
                    })

        print(f"   找到 {len(videos)} 个视频文件")
        return videos

# ==================== 文件名解析器 ====================

class VideoMetadataParser:
    """视频文件名解析器"""

    FILENAME_PATTERN = re.compile(
        r'^(?P<date>\d{4}-\d{2}-\d{2})\s+'
        r'(?P<time>\d{2}-\d{2}-\d{2})_'
        r'(?P<title>.+?)_'
        r'(?P<type>video|audio|cover|desc)'
        r'\.(?P<ext>\w+)$'
    )

    def parse_filename(self, s3_key: str) -> Optional[Dict]:
        """
        解析文件名，提取元数据

        Returns:
            {
                'publish_date': '2026-04-03',
                'publish_time': '19:05:58',
                'publish_datetime': datetime对象,
                'timestamp': Unix时间戳,
                'title': '标题',
                'file_type': 'video',
                'extension': 'mp4',
                'original_filename': '...'
            }
        """
        basename = Path(s3_key).name

        match = self.FILENAME_PATTERN.match(basename)
        if not match:
            # 如果不匹配标准格式，尝试提取日期
            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', basename)
            if date_match:
                return {
                    'publish_date': date_match.group(1),
                    'publish_time': None,
                    'publish_datetime': None,
                    'timestamp': None,
                    'title': Path(basename).stem,
                    'file_type': 'video',
                    'extension': Path(basename).suffix[1:],
                    'original_filename': basename
                }
            return None

        groups = match.groupdict()

        # 转换时间格式
        date_str = groups['date']
        time_str = groups['time'].replace('-', ':')

        try:
            publish_dt = datetime.strptime(
                f"{date_str} {time_str}",
                "%Y-%m-%d %H:%M:%S"
            )
            timestamp = publish_dt.timestamp()
        except ValueError:
            publish_dt = None
            timestamp = None

        return {
            'publish_date': date_str,
            'publish_time': time_str,
            'publish_datetime': publish_dt,
            'timestamp': timestamp,
            'title': groups['title'],
            'file_type': groups['type'],
            'extension': groups['ext'],
            'original_filename': basename
        }

    def generate_output_filename(self, video_metadata: Dict, output_type: str) -> str:
        """
        生成输出文件名（与原视频对应）

        Args:
            video_metadata: 解析的元数据
            output_type: 'transcript', 'srt', 'json'
        """
        date = video_metadata['publish_date']
        time = video_metadata.get('publish_time', '00-00-00')
        if time:
            time = time.replace(':', '-')
        title = video_metadata['title']

        ext_map = {
            'transcript': 'txt',
            'srt': 'srt',
            'json': 'json'
        }

        ext = ext_map.get(output_type, 'txt')

        return f"{date} {time}_{title}_transcript.{ext}"

# ==================== Whisper转录器 ====================

class WhisperTranscriber:
    """Whisper转录引擎"""

    def __init__(self, model_size: str = 'large'):
        print(f"🎤 加载Whisper模型: {model_size}")
        self.model = whisper.load_model(model_size, device='cuda')
        print("   ✅ 模型加载完成")

    def transcribe(self, video_path: str) -> Dict:
        """
        转录视频

        Returns:
            {
                'text': '完整文本',
                'language': 'zh',
                'segments': [...]
            }
        """
        print(f"   🎤 开始转录...")
        start_time = time.time()

        result = self.model.transcribe(
            video_path,
            language='zh',
            task='transcribe',
            temperature=0.0,
            best_of=5,
            beam_size=5,
            condition_on_previous_text=True,
            initial_prompt="这是一段关于财经、金融、经济的视频内容。"
        )

        processing_time = time.time() - start_time
        result['processing_time'] = processing_time

        print(f"   ✅ 转录完成 ({processing_time:.1f}秒)")
        print(f"   📝 文本长度: {len(result['text'])} 字符")

        return result

# ==================== 认知提取器 ====================

class CognitiveExtractor:
    """从转录文本提取分析框架"""

    def __init__(self):
        self.bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')

    def extract_framework(self, transcript: str, metadata: Dict) -> Optional[Dict]:
        """
        使用Claude提取分析框架

        Args:
            transcript: 转录文本
            metadata: 视频元数据

        Returns:
            结构化的分析框架（YAML格式解析后的dict）
        """
        print(f"   🧠 提取认知框架...")

        # 如果文本太短，跳过
        if len(transcript) < 200:
            print(f"   ⚠️  文本过短（{len(transcript)}字符），跳过框架提取")
            return None

        prompt = f"""你是财经分析专家，擅长提取结构化的分析框架。

请分析以下视频转录内容，提取刘德超的分析思维：

标题：{metadata.get('title', '未知')}
发布日期：{metadata.get('publish_date', '未知')}

转录内容：
{transcript}

请提取：

1. **分析主题**：这个视频主要分析什么问题？

2. **推理链条**：从问题到结论的推理步骤
   - 每一步关注什么？
   - 使用什么逻辑？
   - 得出什么中间结论？

3. **关键变量**：
   - 涉及哪些经济指标？
   - 这些变量如何影响结论？
   - 有没有提到阈值？

4. **因果关系**：
   - X导致Y的逻辑是什么？
   - 有没有提到传导机制？

5. **判断模式**：
   - 在什么条件下得出什么结论？
   - if-then规则是什么？

6. **风险考虑**：
   - 提到了哪些风险或不确定性？

请以JSON格式输出，结构如下：
{{
  "topic": "主题",
  "reasoning_chain": [
    {{"step": 1, "question": "...", "variables": [], "logic": "...", "conclusion": "..."}}
  ],
  "key_variables": [
    {{"name": "变量名", "thresholds": {{}}, "impact": "影响描述"}}
  ],
  "causal_relations": [
    {{"cause": "原因", "effect": "结果", "mechanism": "机制", "strength": "strong/medium/weak"}}
  ],
  "decision_patterns": [
    {{"condition": "条件", "action": "结论", "confidence": "high/medium/low"}}
  ],
  "risks": ["风险1", "风险2"]
}}

只输出JSON，不要额外解释。"""

        try:
            response = self.bedrock.invoke_model(
                modelId='us.anthropic.claude-opus-4-20250514-v1:0',
                body=json.dumps({
                    'anthropic_version': 'bedrock-2023-05-31',
                    'max_tokens': 4096,
                    'messages': [
                        {'role': 'user', 'content': prompt}
                    ]
                })
            )

            result = json.loads(response['body'].read())
            content = result['content'][0]['text']

            # 提取JSON（可能被```json包裹）
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0].strip()
            elif '```' in content:
                content = content.split('```')[1].split('```')[0].strip()

            framework = json.loads(content)
            print(f"   ✅ 框架提取完成: {framework.get('topic', '未知主题')}")

            return framework

        except Exception as e:
            print(f"   ❌ 框架提取失败: {e}")
            return None

# ==================== 输出保存器 ====================

class OutputSaver:
    """保存转录结果到多种格式"""

    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def save_txt(self, text: str, filename: str):
        """保存纯文本"""
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(text)
        return filepath

    def save_srt(self, segments: List[Dict], filename: str):
        """保存SRT字幕"""
        filepath = os.path.join(self.output_dir, filename)

        def format_timestamp(seconds: float) -> str:
            """转换为SRT时间格式 00:00:00,000"""
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = int(seconds % 60)
            millis = int((seconds % 1) * 1000)
            return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

        with open(filepath, 'w', encoding='utf-8') as f:
            for i, seg in enumerate(segments, 1):
                f.write(f"{i}\n")
                f.write(f"{format_timestamp(seg['start'])} --> {format_timestamp(seg['end'])}\n")
                f.write(f"{seg['text'].strip()}\n\n")

        return filepath

    def save_json(self, data: Dict, filename: str):
        """保存完整JSON数据"""
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return filepath

# ==================== S3管理器 ====================

class S3Manager:
    """S3文件操作"""

    def __init__(self, bucket: str):
        self.bucket = bucket
        self.s3 = boto3.client('s3')

    def download_video(self, s3_key: str, local_path: str):
        """下载视频到本地"""
        print(f"   📥 下载视频...")
        self.s3.download_file(self.bucket, s3_key, local_path)
        size_mb = os.path.getsize(local_path) / 1024 / 1024
        print(f"   ✅ 下载完成 ({size_mb:.1f} MB)")

    def upload_file(self, local_path: str, s3_key: str):
        """上传文件到S3"""
        self.s3.upload_file(local_path, self.bucket, s3_key)

    def check_exists(self, s3_key: str) -> bool:
        """检查S3文件是否存在"""
        try:
            self.s3.head_object(Bucket=self.bucket, Key=s3_key)
            return True
        except:
            return False

# ==================== 批处理协调器 ====================

class BatchProcessor:
    """批量转录协调器"""

    def __init__(self, s3_bucket: str, s3_prefix: str, model_size: str = 'large'):
        self.s3_bucket = s3_bucket
        self.s3_prefix = s3_prefix

        # 初始化组件
        self.file_filter = VideoFileFilter()
        self.metadata_parser = VideoMetadataParser()
        self.transcriber = WhisperTranscriber(model_size)
        self.cognitive_extractor = CognitiveExtractor()
        self.output_saver = OutputSaver(OUTPUT_DIR)
        self.s3_manager = S3Manager(s3_bucket)

        # 创建临时目录
        os.makedirs(TEMP_DIR, exist_ok=True)

    def process_all(self):
        """处理所有视频"""

        # 1. 列出所有视频
        videos = self.file_filter.list_videos_from_s3(self.s3_bucket, self.s3_prefix)

        if not videos:
            print("❌ 没有找到视频文件")
            return

        # 2. 解析元数据并排序
        print("\n📋 解析文件名和时间信息...")
        video_tasks = []
        for video in videos:
            metadata = self.metadata_parser.parse_filename(video['key'])
            if metadata:
                video_tasks.append({
                    's3_key': video['key'],
                    'metadata': metadata,
                    'size': video['size']
                })

        # 按时间排序
        video_tasks.sort(key=lambda x: x['metadata'].get('timestamp') or 0)

        print(f"   找到 {len(video_tasks)} 个有效视频")

        # 3. 逐个转录
        transcripts = []
        failed = []

        for i, task in enumerate(video_tasks, 1):
            try:
                print(f"\n{'='*60}")
                print(f"[{i}/{len(video_tasks)}] 处理: {task['metadata']['title']}")
                print(f"发布时间: {task['metadata']['publish_date']} {task['metadata'].get('publish_time', 'N/A')}")
                print(f"文件大小: {task['size'] / 1024 / 1024:.1f} MB")
                print(f"{'='*60}")

                # 检查是否已转录
                transcript_key = task['s3_key'].replace('_video.mp4', '_transcript.json')
                if self.s3_manager.check_exists(transcript_key):
                    print("   ⏭️  已存在转录文件，跳过")
                    continue

                # 下载视频
                local_video = os.path.join(TEMP_DIR, Path(task['s3_key']).name)
                self.s3_manager.download_video(task['s3_key'], local_video)

                # 转录
                result = self.transcriber.transcribe(local_video)

                # 提取认知框架
                framework = self.cognitive_extractor.extract_framework(
                    result['text'],
                    task['metadata']
                )

                # 构建完整结果
                enhanced_result = {
                    'video_metadata': {
                        **task['metadata'],
                        's3_key': task['s3_key'],
                        'file_size_bytes': task['size']
                    },
                    'transcription': {
                        'text': result['text'],
                        'language': result.get('language', 'zh'),
                        'segments': result['segments']
                    },
                    'cognitive_framework': framework,
                    'processing': {
                        'transcribed_at': datetime.now().isoformat(),
                        'processing_time_seconds': result.get('processing_time', 0),
                        'model': WHISPER_MODEL
                    }
                }

                # 保存多种格式
                print(f"   💾 保存结果...")
                txt_file = self.metadata_parser.generate_output_filename(task['metadata'], 'transcript')
                srt_file = self.metadata_parser.generate_output_filename(task['metadata'], 'srt')
                json_file = self.metadata_parser.generate_output_filename(task['metadata'], 'json')

                self.output_saver.save_txt(result['text'], txt_file)
                self.output_saver.save_srt(result['segments'], srt_file)
                self.output_saver.save_json(enhanced_result, json_file)

                # 上传到S3
                print(f"   ☁️  上传到S3...")
                video_dir = str(Path(task['s3_key']).parent)

                self.s3_manager.upload_file(
                    os.path.join(OUTPUT_DIR, txt_file),
                    f"{video_dir}/{txt_file}"
                )
                self.s3_manager.upload_file(
                    os.path.join(OUTPUT_DIR, srt_file),
                    f"{video_dir}/{srt_file}"
                )
                self.s3_manager.upload_file(
                    os.path.join(OUTPUT_DIR, json_file),
                    f"{video_dir}/{json_file}"
                )

                # 清理本地文件
                os.remove(local_video)
                os.remove(os.path.join(OUTPUT_DIR, txt_file))
                os.remove(os.path.join(OUTPUT_DIR, srt_file))
                os.remove(os.path.join(OUTPUT_DIR, json_file))

                transcripts.append(enhanced_result)
                print(f"   ✅ 处理完成")

            except Exception as e:
                print(f"   ❌ 处理失败: {e}")
                failed.append({
                    'video': task['s3_key'],
                    'error': str(e)
                })

        # 4. 生成总结
        print(f"\n{'='*60}")
        print("🎉 批量转录完成")
        print(f"{'='*60}")
        print(f"成功: {len(transcripts)}")
        print(f"失败: {len(failed)}")

        if failed:
            print("\n失败列表:")
            for f in failed:
                print(f"  - {f['video']}: {f['error']}")

        # 保存总结
        summary = {
            'batch_id': datetime.now().strftime('%Y%m%d_%H%M%S'),
            'total_videos': len(video_tasks),
            'transcribed': len(transcripts),
            'failed': len(failed),
            'failed_list': failed,
            'completed_at': datetime.now().isoformat()
        }

        summary_path = os.path.join(OUTPUT_DIR, 'transcription_summary.json')
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        summary_s3_key = f"{self.s3_prefix}transcription_summary.json"
        self.s3_manager.upload_file(summary_path, summary_s3_key)

        print(f"\n总结文件: s3://{self.s3_bucket}/{summary_s3_key}")

# ==================== 主函数 ====================

def main():
    """主入口"""
    print("🎬 批量视频转录 + 认知提取")
    print("="*60)

    processor = BatchProcessor(S3_BUCKET, S3_PREFIX, WHISPER_MODEL)
    processor.process_all()

if __name__ == '__main__':
    main()
