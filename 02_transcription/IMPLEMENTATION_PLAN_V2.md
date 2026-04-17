# 🎤 Whisper转录模块 - 实现方案 V2

## 🆕 更新内容（基于反馈）

1. ✅ **智能文件过滤**：只处理视频文件（.mp4, .webm, .mkv）
2. ✅ **文件名映射**：转录文件名与原视频严格对应
3. ✅ **时间戳解析**：从文件名提取发布时间，保存到元数据
4. ✅ **时间轴构建**：为Skill提供时间维度检索

---

## 📋 文件结构分析

### S3实际结构（多目录、多文件类型）

```
s3://bucket/douyin_videos/20260417_150000/
├── 2026-04-03 19-05-58_这活没法干_谁爱去谁去/
│   ├── 2026-04-03 19-05-58_这活没法干_谁爱去谁去_video.mp4     # ✅ 需要处理
│   ├── 2026-04-03 19-05-58_这活没法干_谁爱去谁去_desc.txt       # ❌ 跳过
│   ├── 2026-04-03 19-05-58_这活没法干_谁爱去谁去_cover.webp     # ❌ 跳过
│   └── 2026-04-03 19-05-58_这活没法干_谁爱去谁去_audio.m4a      # ❌ 跳过
├── 2026-04-08 19-38-59_人民币5_8_A股6124_哪个会先到来呢/
│   ├── 2026-04-08 19-38-59_xxx_video.mp4                        # ✅ 需要处理
│   └── ...
└── 2026-04-15 10-23-45_美联储降息预期分析/
    ├── 2026-04-15 10-23-45_xxx_video.mp4                        # ✅ 需要处理
    └── ...
```

### 文件名模式识别

**格式**: `YYYY-MM-DD HH-MM-SS_标题_video.mp4`

**示例**:
- `2026-04-03 19-05-58_这活没法干_谁爱去谁去_video.mp4`
- `2026-04-08 19-38-59_人民币5_8_A股6124_哪个会先到来呢_video.mp4`

**需要提取的信息**:
1. 发布时间：`2026-04-03 19:05:58`
2. 视频标题：`这活没法干_谁爱去谁去`
3. 文件类型：`video`
4. 扩展名：`.mp4`

---

## 🔍 智能文件过滤

### 1. 文件类型过滤

```python
import re
from pathlib import Path

class VideoFileFilter:
    """智能视频文件过滤器"""
    
    # 支持的视频格式
    VIDEO_EXTENSIONS = {'.mp4', '.webm', '.mkv', '.avi', '.mov', '.flv'}
    
    # 排除的文件类型
    EXCLUDE_PATTERNS = [
        '*_desc.txt',      # 描述文件
        '*_cover.*',       # 封面图片
        '*_audio.*',       # 音频文件
        '*.jpg', '*.png', '*.webp',  # 图片
        '*.json',          # 元数据
        '*_transcript.*'   # 已转录的（避免重复）
    ]
    
    def is_video_file(self, s3_key: str) -> bool:
        """判断是否为需要处理的视频文件"""
        path = Path(s3_key)
        
        # 检查扩展名
        if path.suffix.lower() not in self.VIDEO_EXTENSIONS:
            return False
        
        # 检查是否为排除模式
        for pattern in self.EXCLUDE_PATTERNS:
            if path.match(pattern):
                return False
        
        # 检查是否包含 _video 标记（可选）
        if '_video' in path.stem:
            return True
        
        # 默认：扩展名是视频格式就处理
        return True
    
    def list_videos_from_s3(self, bucket: str, prefix: str) -> list:
        """从S3列出所有需要处理的视频"""
        s3 = boto3.client('s3')
        
        videos = []
        paginator = s3.get_paginator('list_objects_v2')
        
        for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
            if 'Contents' not in page:
                continue
                
            for obj in page['Contents']:
                key = obj['Key']
                
                # 过滤视频文件
                if self.is_video_file(key):
                    videos.append({
                        'key': key,
                        'size': obj['Size'],
                        'modified': obj['LastModified']
                    })
        
        return videos
```

**使用示例**:
```python
filter = VideoFileFilter()
videos = filter.list_videos_from_s3('bucket', 'douyin_videos/20260417/')

# 输出: 只包含 .mp4 等视频文件
# [
#   {'key': '.../video.mp4', 'size': 12345678},
#   ...
# ]
```

---

## 🏷️ 文件名解析和映射

### 2. 时间戳和标题提取

```python
import re
from datetime import datetime
from typing import Optional, Dict

class VideoMetadataParser:
    """视频文件名解析器"""
    
    # 文件名正则表达式
    # 匹配: YYYY-MM-DD HH-MM-SS_标题_video.mp4
    FILENAME_PATTERN = re.compile(
        r'^(?P<date>\d{4}-\d{2}-\d{2})\s+'
        r'(?P<time>\d{2}-\d{2}-\d{2})_'
        r'(?P<title>.+?)_'
        r'(?P<type>video|audio|cover|desc)'
        r'\.(?P<ext>\w+)$'
    )
    
    def parse_filename(self, filename: str) -> Optional[Dict]:
        """
        解析文件名，提取元数据
        
        Args:
            filename: 例如 "2026-04-03 19-05-58_标题_video.mp4"
            
        Returns:
            {
                'publish_date': '2026-04-03',
                'publish_time': '19:05:58',
                'publish_datetime': datetime对象,
                'title': '标题',
                'file_type': 'video',
                'extension': 'mp4',
                'original_filename': '...'
            }
        """
        # 从完整路径提取文件名
        basename = Path(filename).name
        
        match = self.FILENAME_PATTERN.match(basename)
        if not match:
            # 如果不匹配标准格式，尝试其他模式
            return self._parse_alternative_format(basename)
        
        groups = match.groupdict()
        
        # 转换时间格式
        date_str = groups['date']
        time_str = groups['time'].replace('-', ':')
        
        try:
            publish_dt = datetime.strptime(
                f"{date_str} {time_str}",
                "%Y-%m-%d %H:%M:%S"
            )
        except ValueError:
            publish_dt = None
        
        return {
            'publish_date': date_str,
            'publish_time': time_str,
            'publish_datetime': publish_dt,
            'timestamp': publish_dt.timestamp() if publish_dt else None,
            'title': groups['title'],
            'file_type': groups['type'],
            'extension': groups['ext'],
            'original_filename': basename
        }
    
    def _parse_alternative_format(self, filename: str) -> Optional[Dict]:
        """处理非标准格式的文件名"""
        # 尝试从文件名提取任何日期信息
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
        
        if date_match:
            return {
                'publish_date': date_match.group(1),
                'publish_time': None,
                'publish_datetime': None,
                'timestamp': None,
                'title': Path(filename).stem,
                'file_type': 'video',
                'extension': Path(filename).suffix[1:],
                'original_filename': filename
            }
        
        return None
    
    def generate_output_filename(self, video_metadata: Dict, output_type: str) -> str:
        """
        生成输出文件名（与原视频对应）
        
        Args:
            video_metadata: 解析的元数据
            output_type: 'transcript', 'srt', 'json'
            
        Returns:
            例如: "2026-04-03 19-05-58_标题_transcript.txt"
        """
        date = video_metadata['publish_date']
        time = video_metadata['publish_time'].replace(':', '-')
        title = video_metadata['title']
        
        # 扩展名映射
        ext_map = {
            'transcript': 'txt',
            'srt': 'srt',
            'json': 'json'
        }
        
        ext = ext_map.get(output_type, 'txt')
        
        return f"{date} {time}_{title}_transcript.{ext}"
```

**使用示例**:
```python
parser = VideoMetadataParser()

# 解析文件名
metadata = parser.parse_filename(
    "2026-04-03 19-05-58_这活没法干_video.mp4"
)

# 输出:
# {
#     'publish_date': '2026-04-03',
#     'publish_time': '19:05:58',
#     'publish_datetime': datetime(2026, 4, 3, 19, 5, 58),
#     'timestamp': 1775432758.0,
#     'title': '这活没法干',
#     'file_type': 'video',
#     'extension': 'mp4'
# }

# 生成转录文件名
transcript_name = parser.generate_output_filename(metadata, 'transcript')
# 输出: "2026-04-03 19-05-58_这活没法干_transcript.txt"
```

---

## 📊 增强的输出格式（包含时间信息）

### JSON格式（完整元数据）

```json
{
  "video_metadata": {
    "original_filename": "2026-04-03 19-05-58_这活没法干_谁爱去谁去_video.mp4",
    "s3_key": "douyin_videos/20260417/2026-04-03 19-05-58_这活没法干_谁爱去谁去/2026-04-03 19-05-58_这活没法干_谁爱去谁去_video.mp4",
    "title": "这活没法干_谁爱去谁去",
    "publish_date": "2026-04-03",
    "publish_time": "19:05:58",
    "publish_timestamp": 1775432758,
    "duration_seconds": 324.5,
    "file_size_bytes": 5723705
  },
  "transcription": {
    "text": "完整转录文本...",
    "language": "zh",
    "model": "large-v3",
    "segments": [
      {
        "id": 0,
        "start": 0.0,
        "end": 3.5,
        "text": "人民币升值下，为什么出口暴涨？",
        "tokens": [1234, 5678, ...],
        "temperature": 0.0,
        "avg_logprob": -0.15,
        "compression_ratio": 1.8,
        "no_speech_prob": 0.02
      }
    ]
  },
  "processing": {
    "transcribed_at": "2026-04-17T16:30:00Z",
    "processing_time_seconds": 36.5,
    "gpu_used": "NVIDIA T4"
  }
}
```

**关键字段说明**:
- `publish_timestamp`: Unix时间戳，用于排序
- `publish_date/time`: 人类可读的时间
- `title`: 视频标题（用于检索）

---

## 🕐 时间轴构建（为Skill准备）

### 时间索引生成

```python
class TimelineBuilder:
    """构建视频时间轴，用于Skill时间检索"""
    
    def build_timeline(self, transcripts: list) -> dict:
        """
        构建时间轴索引
        
        Args:
            transcripts: 所有转录结果的列表
            
        Returns:
            时间轴数据结构
        """
        timeline = {
            'total_videos': len(transcripts),
            'date_range': {
                'start': None,
                'end': None
            },
            'by_date': {},      # 按日期分组
            'by_month': {},     # 按月份分组
            'by_topic': {},     # 按主题分组（后续可扩展）
            'chronological': [] # 时间顺序列表
        }
        
        # 按时间排序
        sorted_transcripts = sorted(
            transcripts,
            key=lambda x: x['video_metadata']['publish_timestamp']
        )
        
        if not sorted_transcripts:
            return timeline
        
        # 时间范围
        timeline['date_range']['start'] = sorted_transcripts[0]['video_metadata']['publish_date']
        timeline['date_range']['end'] = sorted_transcripts[-1]['video_metadata']['publish_date']
        
        # 按日期分组
        for transcript in sorted_transcripts:
            metadata = transcript['video_metadata']
            date = metadata['publish_date']
            month = date[:7]  # YYYY-MM
            
            # 按日期
            if date not in timeline['by_date']:
                timeline['by_date'][date] = []
            timeline['by_date'][date].append({
                'title': metadata['title'],
                'filename': metadata['original_filename'],
                'time': metadata['publish_time'],
                's3_key': metadata['s3_key']
            })
            
            # 按月份
            if month not in timeline['by_month']:
                timeline['by_month'][month] = []
            timeline['by_month'][month].append({
                'title': metadata['title'],
                'date': date,
                'filename': metadata['original_filename']
            })
            
            # 时间序列
            timeline['chronological'].append({
                'timestamp': metadata['publish_timestamp'],
                'date': date,
                'time': metadata['publish_time'],
                'title': metadata['title'],
                'filename': metadata['original_filename'],
                's3_key': metadata['s3_key']
            })
        
        return timeline
    
    def find_videos_by_date_range(self, timeline: dict, start_date: str, end_date: str) -> list:
        """
        根据日期范围查找视频
        
        Args:
            start_date: "2026-04-01"
            end_date: "2026-04-30"
        """
        results = []
        
        for entry in timeline['chronological']:
            if start_date <= entry['date'] <= end_date:
                results.append(entry)
        
        return results
    
    def find_recent_videos(self, timeline: dict, days: int = 7) -> list:
        """
        查找最近N天的视频
        
        Args:
            days: 天数
        """
        from datetime import datetime, timedelta
        
        now = datetime.now()
        cutoff = now - timedelta(days=days)
        cutoff_timestamp = cutoff.timestamp()
        
        return [
            entry for entry in timeline['chronological']
            if entry['timestamp'] >= cutoff_timestamp
        ]
```

### 时间轴输出示例

```json
{
  "total_videos": 156,
  "date_range": {
    "start": "2026-03-15",
    "end": "2026-04-17"
  },
  "by_date": {
    "2026-04-03": [
      {
        "title": "这活没法干_谁爱去谁去",
        "time": "19:05:58",
        "filename": "2026-04-03 19-05-58_xxx_video.mp4"
      }
    ],
    "2026-04-08": [
      {
        "title": "人民币5_8_A股6124",
        "time": "19:38:59",
        "filename": "2026-04-08 19-38-59_xxx_video.mp4"
      }
    ]
  },
  "by_month": {
    "2026-03": [/*...*/],
    "2026-04": [/*...*/]
  },
  "chronological": [
    {
      "timestamp": 1775432758,
      "date": "2026-04-03",
      "time": "19:05:58",
      "title": "这活没法干",
      "s3_key": "..."
    }
  ]
}
```

---

## 🎯 Skill时间检索场景

### 场景1：查找特定时间段的内容

```python
# 用户问题: "刘德超在4月初对美联储的看法是什么？"

# Skill逻辑:
timeline = load_timeline()
videos = timeline_builder.find_videos_by_date_range(
    timeline, 
    "2026-04-01", 
    "2026-04-10"
)

# 然后在这些视频的转录中搜索 "美联储"
for video in videos:
    transcript = load_transcript(video['s3_key'])
    if "美联储" in transcript['text']:
        # 返回相关内容
        ...
```

### 场景2：查找最新观点

```python
# 用户问题: "刘德超最近对A股的最新看法？"

# Skill逻辑:
recent_videos = timeline_builder.find_recent_videos(timeline, days=7)

for video in recent_videos:
    transcript = load_transcript(video['s3_key'])
    if "A股" in transcript['text']:
        # 返回最新内容
        ...
```

### 场景3：时间趋势分析

```python
# 用户问题: "刘德超对人民币汇率的观点是如何变化的？"

# Skill逻辑:
all_videos = timeline['chronological']
rmb_videos = []

for video in all_videos:
    transcript = load_transcript(video['s3_key'])
    if "人民币" in transcript['text'] or "汇率" in transcript['text']:
        rmb_videos.append({
            'date': video['date'],
            'title': video['title'],
            'content': extract_relevant_paragraph(transcript, "人民币")
        })

# 按时间排序展示观点演变
rmb_videos.sort(key=lambda x: x['date'])
```

---

## 🔄 更新后的完整流程

```python
class EnhancedBatchProcessor:
    """增强的批处理器（包含文件过滤和时间解析）"""
    
    def __init__(self, s3_bucket, s3_prefix):
        self.s3_bucket = s3_bucket
        self.s3_prefix = s3_prefix
        self.file_filter = VideoFileFilter()
        self.metadata_parser = VideoMetadataParser()
        self.timeline_builder = TimelineBuilder()
        self.transcriber = WhisperTranscriber()
    
    def process_all(self):
        """完整处理流程"""
        
        # 1. 列出所有视频文件（只过滤.mp4等）
        print("🔍 扫描S3视频文件...")
        videos = self.file_filter.list_videos_from_s3(
            self.s3_bucket, 
            self.s3_prefix
        )
        print(f"   找到 {len(videos)} 个视频文件")
        
        # 2. 解析每个视频的元数据
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
        
        # 3. 按时间排序处理
        video_tasks.sort(key=lambda x: x['metadata']['publish_timestamp'] or 0)
        
        # 4. 逐个转录
        transcripts = []
        for i, task in enumerate(video_tasks, 1):
            print(f"\n[{i}/{len(video_tasks)}] 处理: {task['metadata']['title']}")
            print(f"   发布时间: {task['metadata']['publish_date']} {task['metadata']['publish_time']}")
            
            # 下载
            local_path = self.download_video(task['s3_key'])
            
            # 转录
            result = self.transcriber.transcribe(local_path)
            
            # 增强结果（添加时间信息）
            enhanced_result = {
                'video_metadata': {
                    **task['metadata'],
                    's3_key': task['s3_key'],
                    'file_size_bytes': task['size']
                },
                'transcription': result,
                'processing': {
                    'transcribed_at': datetime.now().isoformat(),
                    'processing_time_seconds': result.get('processing_time', 0)
                }
            }
            
            # 保存多种格式（文件名对应）
            self.save_all_formats(enhanced_result)
            
            # 上传到S3
            self.upload_to_s3(enhanced_result)
            
            # 清理本地文件
            os.remove(local_path)
            
            transcripts.append(enhanced_result)
        
        # 5. 构建时间轴
        print("\n🕐 构建时间轴索引...")
        timeline = self.timeline_builder.build_timeline(transcripts)
        
        # 保存时间轴
        self.save_timeline(timeline)
        
        print("\n✅ 全部完成！")
        return {
            'transcripts': transcripts,
            'timeline': timeline
        }
```

---

## 📦 最终输出结构

```
s3://bucket/douyin_videos/20260417_150000/
├── 2026-04-03 19-05-58_这活没法干/
│   ├── 2026-04-03 19-05-58_这活没法干_video.mp4
│   ├── 2026-04-03 19-05-58_这活没法干_desc.txt
│   ├── 2026-04-03 19-05-58_这活没法干_cover.webp
│   ├── 2026-04-03 19-05-58_这活没法干_transcript.txt      # ⭐ 新增
│   ├── 2026-04-03 19-05-58_这活没法干_transcript.srt      # ⭐ 新增
│   └── 2026-04-03 19-05-58_这活没法干_transcript.json     # ⭐ 新增
├── 2026-04-08 19-38-59_人民币分析/
│   └── ...（同上）
├── transcription_summary.json                              # ⭐ 转录总结
└── timeline_index.json                                     # ⭐ 时间轴索引
```

**文件名严格对应**：
- 视频：`2026-04-03 19-05-58_标题_video.mp4`
- 转录：`2026-04-03 19-05-58_标题_transcript.txt`
- 字幕：`2026-04-03 19-05-58_标题_transcript.srt`
- 元数据：`2026-04-03 19-05-58_标题_transcript.json`

---

## ✅ 新增功能总结

| 功能 | 实现方式 | 用途 |
|------|---------|------|
| **文件过滤** | `VideoFileFilter` | 只处理.mp4等视频，跳过图片、文本 |
| **时间解析** | `VideoMetadataParser` | 从文件名提取发布时间 |
| **文件名映射** | `generate_output_filename()` | 确保转录文件名与视频对应 |
| **时间轴构建** | `TimelineBuilder` | 为Skill提供时间检索能力 |
| **元数据增强** | JSON中保存时间戳 | 支持按时间、按月、按日查询 |

---

## 🎯 为Skill准备的数据

转录完成后，Skill可以实现：

1. ✅ **按时间查询**："4月初刘德超说了什么？"
2. ✅ **最新观点**："刘德超最近对A股的看法？"
3. ✅ **趋势分析**："刘德超对人民币的观点如何变化？"
4. ✅ **精确定位**：返回结果时显示视频发布时间
5. ✅ **时间轴可视化**：按时间排列所有视频

---

这个更新后的方案解决了你提出的所有问题！你觉得如何？有其他需要调整的吗？🚀
