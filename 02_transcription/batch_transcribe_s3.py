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
ENABLE_COGNITIVE_EXTRACTION = os.environ.get('ENABLE_COGNITIVE_EXTRACTION', 'false').lower() == 'true'
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
    """从转录文本提取认知框架 - 零清洗直接提取"""

    def __init__(self):
        self.bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')

    def extract_framework(self, transcript_result: Dict, metadata: Dict) -> Optional[Dict]:
        """
        从Whisper原始结果提取认知框架 (零清洗策略)

        Args:
            transcript_result: Whisper完整返回 {'text': '...', 'segments': [...], ...}
            metadata: 视频元数据

        Returns:
            认知框架 (JSON dict)
        """
        print(f"   🧠 提取认知框架 (零清洗策略)...")

        raw_text = transcript_result.get('text', '')

        # 简单的有效性检查 - 不做清洗，但跳过明显无效的内容
        if len(raw_text) < 100:
            print(f"   ⚠️  文本过短 ({len(raw_text)}字符)，可能无有效内容")
            return None

        # 构造prompt - 直接喂原始转录，让Claude处理一切噪音
        prompt = f"""# 原始语音转录 (Whisper输出，未清洗)

**视频信息**:
- 标题: {metadata.get('title', '未知')}
- 发布日期: {metadata.get('publish_date', '未知')}
- 文本长度: {len(raw_text)} 字符

**转录内容**:
{raw_text}

---

⚠️ **说明**: 这是Whisper转录的原始文本，可能包含语气词("嗯"、"啊")、停顿、重复、营销话术("记得点赞")等噪音。请忽略这些噪音，专注于提取说话者的**思维框架**。

---

# 提取任务

你的任务是**逆向工程说话者的认知操作系统** - 关注 **HOW they think**，不是 **WHAT they said**。

## 1. 心智模型识别 (最高优先级)

从这段内容中，识别说话者的**思考框架**:

### 1.1 独特视角
- 其他人怎么看这个问题？
- 他为什么不同意主流观点？
- 他的独特角度是什么？

**示例**:
- ❌ 不要提取: "他认为人民币会升值"
- ✅ 应该提取: "他习惯用博弈均衡点预测经济走向，而非线性外推当前趋势"

### 1.2 分析工具
- 他用什么框架拆解问题？(博弈论/供需分析/历史类比/系统思维...)
- 这个工具是通用的还是只适用于这个话题？

### 1.3 推理链
- 他的前提假设 → 推理步骤 → 结论
- **关键**: 他的推理跳跃在哪里？(显性逻辑 vs 隐性假设)

### 验证标准 (必须回答)
- **跨域复现**: 这个思维方式只在这个话题用，还是可能在其他场景也适用？
- **生成力**: 用这个框架能推测他对类似新事件的立场吗？
- **排他性**: 这是他独特的，还是常见观点？

---

## 2. 决策启发式 (快速判断规则)

他的"条件反射"式判断:
- 看到X → 立即想到Y
- 面对争议话题 → 默认立场是什么？
- 他的"警报信号"是什么？(什么情况下他会警觉)

**示例**:
- "看到货币升值 → 立即分析供应链博弈，不只看出口数据"
- "看到大众恐慌 → 默认立场是'不必恐慌'"

---

## 3. 认知信号 (从语言模式提取)

分析**怎么说**，不只是**说什么**:

### 3.1 确定性标记
- 哪些话说得斩钉截铁？哪些犹豫？
  - "我认为...嗯...利大于弊" → 可能不是强信念
  - "这一轮必然以升值结束" → 高确信度

### 3.2 强调模式
- 他重复了什么？(重复 = 核心观点)
- 他用什么方式强调？(提高音量/重复说/反问)

### 3.3 论证结构
- 结论先行 vs 铺垫后讲？
- 用数据说服 vs 用类比说服 vs 用反问引导？

---

## 4. 元认知线索 (对自己思维的反思)

- 他承认什么不确定？
- 他说"我以前认为...但现在..."？(观点演化)
- 他说"很多人(包括我)容易犯的错误是..."？(认知偏差自觉)

---

## 5. 视频分类

判断这个视频属于:
- **预测类**: 预言未来会发生什么
- **解读类**: 解释当前现象背后的逻辑
- **辩驳类**: 反驳某种主流观点
- **教学类**: 教授分析方法
- **其他**: 请注明

---

# 输出格式 (JSON)

{{
    "心智模型": [
        {{
            "模型名称": "简洁命名 (3-8字)",
            "描述": "这个模型的核心思想",
            "证据": "原文关键句 (保留原话，可以有语气词)",
            "应用场景": "他在什么情况下用这个模型",
            "验证": {{
                "跨域复现": "高/中/低 + 理由",
                "生成力": "高/中/低 + 能否预测他对新问题的立场",
                "排他性": "高/中/低 + 这是独特视角还是常见观点"
            }},
            "信心度": "高/中/低 + 理由"
        }}
    ],

    "决策启发式": [
        {{
            "触发条件": "看到X",
            "立即反应": "想到/做出Y",
            "证据": "原文句子"
        }}
    ],

    "认知信号": {{
        "高确定性论断": ["原文句子1", "原文句子2"],
        "犹豫不确定": ["原文句子"],
        "强调重复": ["反复说的核心观点"],
        "论证结构": "结论先行/数据驱动/类比为主/反问引导/..."
    }},

    "元认知线索": {{
        "承认的不确定性": ["原文"],
        "观点演化": ["以前...现在..."],
        "自我纠偏": ["容易犯的错误是..."]
    }},

    "视频分类": "预测类/解读类/辩驳类/教学类/其他",
    "信息密度": "高/中/低",
    "信息密度理由": "为什么是这个评级",
    "建议": "这个视频是否值得深入研究？为什么？"
}}

---

# ❌ 不要提取的内容

- 具体数据和时事细节 ("2026年4月出口增长8%")
- 纯描述性内容 ("最近人民币涨了")
- 营销话术 ("记得点赞关注")
- 闲聊和过渡语 ("今天我们来聊聊...")

# ✅ 要提取的内容

- **HOW he thinks** (他怎么思考)
- **WHY he believes** (为什么这么想)
- **HOW he differs** (他和别人的差异在哪里)

---

只输出JSON，不要额外解释。如果内容质量太低无法提取有价值框架，返回 {{"error": "内容质量不足，无法提取有效认知框架"}}"""

        try:
            # 调用Bedrock Claude Opus 4
            response = self.bedrock.invoke_model(
                modelId='us.anthropic.claude-opus-4-20250514-v1:0',
                body=json.dumps({
                    'anthropic_version': 'bedrock-2023-05-31',
                    'max_tokens': 8192,  # 增加token限制以获得更完整的分析
                    'temperature': 0.0,  # 确定性输出
                    'messages': [
                        {
                            'role': 'user',
                            'content': prompt
                        }
                    ]
                })
            )

            result = json.loads(response['body'].read())
            content = result['content'][0]['text']

            # 提取JSON（可能被```json或```包裹）
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0].strip()
            elif '```' in content:
                content = content.split('```')[1].split('```')[0].strip()

            framework = json.loads(content)

            # 检查是否是错误返回
            if 'error' in framework:
                print(f"   ⚠️  {framework['error']}")
                return None

            # 打印提取摘要
            models_count = len(framework.get('心智模型', []))
            heuristics_count = len(framework.get('决策启发式', []))
            video_type = framework.get('视频分类', '未知')

            print(f"   ✅ 框架提取完成:")
            print(f"      - 心智模型: {models_count}个")
            print(f"      - 决策启发式: {heuristics_count}个")
            print(f"      - 视频类型: {video_type}")
            print(f"      - 信息密度: {framework.get('信息密度', '未知')}")

            return framework

        except json.JSONDecodeError as e:
            print(f"   ❌ JSON解析失败: {e}")
            print(f"   原始返回: {content[:500]}...")
            return None
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

                # 提取认知框架（可选）
                framework = None
                if ENABLE_COGNITIVE_EXTRACTION:
                    framework = self.cognitive_extractor.extract_framework(
                        result,  # 传入完整的Whisper结果，包含text和segments
                        task['metadata']
                    )

                # 构建完整结果
                # 转换datetime对象为字符串
                metadata_serializable = {**task['metadata']}
                if 'publish_datetime' in metadata_serializable and metadata_serializable['publish_datetime']:
                    metadata_serializable['publish_datetime'] = metadata_serializable['publish_datetime'].isoformat()

                enhanced_result = {
                    'video_metadata': {
                        **metadata_serializable,
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
