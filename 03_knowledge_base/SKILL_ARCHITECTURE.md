# 🎓 从转录文本到Claude Code Skill - 完整架构

## ❌ 常见误解

### 错误方案：简单文本汇总

```python
# ❌ 这样做不行
all_text = ""
for transcript in transcripts:
    all_text += transcript['text']

skill_prompt = f"你是财经助手，参考以下内容回答：{all_text}"
```

**为什么不行？**
1. ❌ 文本太长（30万字）超过Claude的context限制
2. ❌ 无法精确检索相关内容
3. ❌ 没有时间信息
4. ❌ 响应慢、成本高
5. ❌ 无法引用来源

---

## ✅ 正确方案：RAG架构

### 架构图

```
┌─────────────────────────────────────────────────────────┐
│                     用户提问                              │
│         "刘德超对美联储降息的看法是什么？"                  │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ↓
┌─────────────────────────────────────────────────────────┐
│               Claude Code Skill                          │
│  - 理解用户意图                                            │
│  - 提取关键词（美联储、降息）                                │
│  - 调用Tool查询知识库                                       │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ↓ Tool Call
┌─────────────────────────────────────────────────────────┐
│              Lambda Function                             │
│  1. 接收查询参数                                           │
│  2. 向量化查询（Bedrock Embeddings）                       │
│  3. 查询OpenSearch（相似度搜索）                            │
│  4. 返回最相关的3-5个片段                                   │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ↓ Vector Search
┌─────────────────────────────────────────────────────────┐
│            OpenSearch向量数据库                           │
│  - 存储所有视频的分块文本                                   │
│  - 每个块包含：文本+向量+元数据                              │
│  - 支持语义搜索+时间过滤                                    │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ↓ 返回相关片段
┌─────────────────────────────────────────────────────────┐
│               Claude Code Skill                          │
│  基于检索结果生成回答：                                      │
│  "根据刘德超在2026-04-08的视频，他认为美联储降息..."        │
│  (来源: 2026-04-08_美联储议息会议分析.mp4)                  │
└─────────────────────────────────────────────────────────┘
```

---

## 📊 详细流程

### 阶段1：知识库构建（离线处理）

```
转录文本（S3）
    ↓ 1. 文本分块
分块文本
    ↓ 2. 向量化（Titan Embeddings）
向量 + 元数据
    ↓ 3. 索引到OpenSearch
OpenSearch知识库
```

#### 1.1 文本分块（Chunking）

**为什么要分块？**
- 每个视频5分钟，转录约1500字
- 直接存储整个视频文本不利于精确检索
- 分块后可以精确定位到具体段落

**分块策略**：

```python
class TextChunker:
    def chunk_transcript(self, transcript: dict, chunk_size: int = 500):
        """
        智能分块
        
        Args:
            transcript: 转录结果
            chunk_size: 每块约500字（2-3个段落）
        """
        segments = transcript['transcription']['segments']
        chunks = []
        
        current_chunk = {
            'text': '',
            'start_time': 0,
            'end_time': 0,
            'segment_ids': []
        }
        
        for seg in segments:
            # 累积文本直到达到chunk_size
            if len(current_chunk['text']) + len(seg['text']) > chunk_size:
                # 保存当前块
                chunks.append(current_chunk)
                
                # 开始新块
                current_chunk = {
                    'text': seg['text'],
                    'start_time': seg['start'],
                    'end_time': seg['end'],
                    'segment_ids': [seg['id']]
                }
            else:
                # 继续累积
                current_chunk['text'] += seg['text']
                current_chunk['end_time'] = seg['end']
                current_chunk['segment_ids'].append(seg['id'])
        
        # 添加最后一块
        if current_chunk['text']:
            chunks.append(current_chunk)
        
        return chunks
```

**分块结果示例**：

```python
# 原始：5分钟视频 = 1500字
# 分块后：3个chunk

[
    {
        'chunk_id': 0,
        'text': '人民币升值下，为什么出口暴涨？未来这个优势将会更大。首先我们要理解...',  # 500字
        'start_time': 0.0,
        'end_time': 95.3
    },
    {
        'chunk_id': 1,
        'text': '从数据来看，今年一季度中国出口增长了12.3%...',  # 500字
        'start_time': 95.3,
        'end_time': 187.6
    },
    {
        'chunk_id': 2,
        'text': '所以综合来看，人民币升值反而带来了...',  # 500字
        'start_time': 187.6,
        'end_time': 280.0
    }
]
```

#### 1.2 向量化（Embeddings）

```python
import boto3

class EmbeddingGenerator:
    def __init__(self):
        self.bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
    
    def generate_embedding(self, text: str):
        """
        使用Amazon Titan Embeddings生成向量
        
        Returns:
            1536维的向量
        """
        response = self.bedrock.invoke_model(
            modelId='amazon.titan-embed-text-v1',
            body=json.dumps({
                'inputText': text
            })
        )
        
        result = json.loads(response['body'].read())
        return result['embedding']  # 1536维向量
```

#### 1.3 存储到OpenSearch

```python
from opensearchpy import OpenSearch

class KnowledgeBaseBuilder:
    def __init__(self):
        self.opensearch = OpenSearch(
            hosts=[{'host': 'your-opensearch-endpoint', 'port': 443}],
            http_auth=('admin', 'password'),
            use_ssl=True
        )
        self.embedding_generator = EmbeddingGenerator()
    
    def index_chunk(self, chunk: dict, video_metadata: dict):
        """索引一个文本块"""
        
        # 生成向量
        embedding = self.embedding_generator.generate_embedding(chunk['text'])
        
        # 构建文档
        document = {
            # 文本内容
            'text': chunk['text'],
            'chunk_id': chunk['chunk_id'],
            
            # 向量（用于相似度搜索）
            'text_embedding': embedding,
            
            # 视频元数据
            'video_title': video_metadata['title'],
            'video_filename': video_metadata['original_filename'],
            'publish_date': video_metadata['publish_date'],
            'publish_time': video_metadata['publish_time'],
            'publish_timestamp': video_metadata['publish_timestamp'],
            
            # 时间范围（在视频中的位置）
            'start_time': chunk['start_time'],
            'end_time': chunk['end_time'],
            
            # S3路径
            's3_video_key': video_metadata['s3_key'],
            's3_transcript_key': video_metadata['s3_key'].replace('_video.mp4', '_transcript.json'),
            
            # 索引时间
            'indexed_at': datetime.now().isoformat()
        }
        
        # 索引到OpenSearch
        self.opensearch.index(
            index='douyin-finance-kb',
            body=document
        )
    
    def build_knowledge_base(self, all_transcripts: list):
        """构建完整知识库"""
        
        chunker = TextChunker()
        
        for transcript in all_transcripts:
            # 分块
            chunks = chunker.chunk_transcript(transcript)
            
            # 索引每个块
            for chunk in chunks:
                self.index_chunk(chunk, transcript['video_metadata'])
        
        print(f"✅ 知识库构建完成！共索引 {total_chunks} 个文本块")
```

**OpenSearch索引结构**：

```json
{
  "mappings": {
    "properties": {
      "text": {"type": "text", "analyzer": "chinese"},
      "text_embedding": {
        "type": "knn_vector",
        "dimension": 1536
      },
      "video_title": {"type": "text"},
      "publish_date": {"type": "date"},
      "publish_timestamp": {"type": "long"},
      "start_time": {"type": "float"},
      "end_time": {"type": "float"}
    }
  }
}
```

---

### 阶段2：Lambda查询工具

```python
import boto3
import json
from opensearchpy import OpenSearch

def lambda_handler(event, context):
    """
    Lambda函数：查询知识库
    
    输入:
        {
            "query": "美联储降息",
            "date_range": {"start": "2026-04-01", "end": "2026-04-30"},  # 可选
            "top_k": 5
        }
    
    输出:
        {
            "results": [
                {
                    "text": "...",
                    "video_title": "...",
                    "publish_date": "...",
                    "relevance_score": 0.92
                }
            ]
        }
    """
    
    # 解析请求
    query = event.get('query', '')
    date_range = event.get('date_range', None)
    top_k = event.get('top_k', 5)
    
    # 1. 向量化查询
    bedrock = boto3.client('bedrock-runtime')
    response = bedrock.invoke_model(
        modelId='amazon.titan-embed-text-v1',
        body=json.dumps({'inputText': query})
    )
    query_embedding = json.loads(response['body'].read())['embedding']
    
    # 2. 构建OpenSearch查询
    opensearch = OpenSearch(...)
    
    search_body = {
        "size": top_k,
        "query": {
            "bool": {
                "must": [
                    {
                        # 向量相似度搜索
                        "knn": {
                            "text_embedding": {
                                "vector": query_embedding,
                                "k": top_k
                            }
                        }
                    }
                ]
            }
        }
    }
    
    # 可选：添加时间过滤
    if date_range:
        search_body["query"]["bool"]["filter"] = [
            {
                "range": {
                    "publish_date": {
                        "gte": date_range['start'],
                        "lte": date_range['end']
                    }
                }
            }
        ]
    
    # 3. 执行搜索
    response = opensearch.search(
        index='douyin-finance-kb',
        body=search_body
    )
    
    # 4. 格式化结果
    results = []
    for hit in response['hits']['hits']:
        source = hit['_source']
        results.append({
            'text': source['text'],
            'video_title': source['video_title'],
            'publish_date': source['publish_date'],
            'publish_time': source['publish_time'],
            'video_timestamp': f"{int(source['start_time']//60)}:{int(source['start_time']%60):02d}",
            's3_video_key': source['s3_video_key'],
            'relevance_score': hit['_score']
        })
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'query': query,
            'results': results
        }, ensure_ascii=False)
    }
```

---

### 阶段3：Claude Code Skill定义

```python
# ~/.claude/skills/finance-guru/skill.yaml
---
name: finance-guru
description: 查询刘德超财经视频内容的知识库
version: 1.0.0
author: percy-han

tools:
  - name: search_finance_videos
    description: |
      搜索刘德超财经视频的转录内容
      
      支持：
      - 语义搜索：理解问题含义，不需要精确匹配关键词
      - 时间过滤：可以查找特定时间段的内容
      - 相关度排序：自动返回最相关的内容
    
    parameters:
      query:
        type: string
        description: 用户的问题或关键词
        required: true
      
      date_range:
        type: object
        description: 可选的时间范围
        properties:
          start:
            type: string
            description: 开始日期 (YYYY-MM-DD)
          end:
            type: string
            description: 结束日期 (YYYY-MM-DD)
      
      top_k:
        type: integer
        description: 返回结果数量
        default: 5
    
    implementation:
      type: lambda
      function_arn: arn:aws:lambda:us-east-1:123456:function:finance-kb-search
---
```

```markdown
# ~/.claude/skills/finance-guru/prompt.md

你是财经知识助手，专门回答关于刘德超（观棋有语）财经视频内容的问题。

## 工作流程

1. **理解用户问题**
   - 提取关键词（如：美联储、降息、人民币、A股）
   - 识别时间范围（如：最近、4月初、上个月）

2. **调用search_finance_videos工具**
   - 传入用户问题作为query
   - 如果用户提到时间，设置date_range

3. **基于检索结果回答**
   - 引用具体视频作为来源
   - 显示发布时间
   - 如果有多个视频提到，综合回答

4. **回答格式**
   ```
   根据刘德超的视频：
   
   在 [2026-04-08] 发布的《美联储议息会议分析》中，他提到：
   "美联储在三月份维持利率不变，鲍威尔表示..."
   
   （来源：2026-04-08 19:38:59_美联储议息会议分析.mp4，时间戳 2:35）
   ```

## 示例对话

用户：刘德超对美联储降息怎么看？

助手：
我来查询刘德超关于美联储降息的观点...

[调用 search_finance_videos(query="美联储降息")]

根据检索结果，刘德超在多个视频中讨论了美联储降息：

**最新观点（2026-04-15）：**
在《美联储降息预期分析》中，刘德超认为："市场对降息的预期过于乐观，
从最新的通胀数据来看，美联储可能要到三季度才会开始降息..."

（来源：2026-04-15 10:23:45_美联储降息预期分析.mp4）

**早期观点（2026-04-03）：**
他在4月初的视频中提到："如果经济数据继续走弱，美联储可能在6月份
就开始降息..."

（来源：2026-04-03 19:05:58_美联储议息会议分析.mp4）

可以看到，刘德超的观点随着新数据的出现在调整，最新的判断更偏向于
降息时间会推迟。
```

---

## 🔄 完整工作流程

### 用户提问："刘德超最近对A股的看法？"

```
1. Claude Code Skill接收问题

2. Skill分析：
   - 关键词：A股
   - 时间：最近（最近7天）
   
3. 调用Lambda Tool:
   search_finance_videos(
       query="A股",
       date_range={"start": "2026-04-10", "end": "2026-04-17"}
   )

4. Lambda处理：
   - 向量化"A股" → embedding
   - OpenSearch搜索：
     * 语义相似度匹配
     * 时间范围过滤
     * 返回top 5结果

5. 返回结果：
   [
       {
           "text": "最近A股市场出现了调整，主要原因是...",
           "video_title": "A股调整原因分析",
           "publish_date": "2026-04-15",
           "relevance_score": 0.94
       },
       {...}
   ]

6. Claude生成回答：
   "根据刘德超在2026-04-15的最新视频《A股调整原因分析》，
   他认为：'最近A股市场出现了调整，主要原因是...'
   
   （来源：2026-04-15 10:23:45_A股调整原因分析.mp4）"
```

---

## 💰 成本优化

### 方案对比

#### 方案A：每次传入全部文本（错误）
```
成本：每次查询传入30万字 → $0.015/次
响应时间：5-10秒
准确性：一般（信息过载）
```

#### 方案B：RAG检索（正确）⭐
```
成本：
  - 知识库构建（一次性）：$0.50
  - 每次查询：向量化查询($0.0001) + OpenSearch($0.0001) = $0.0002/次
响应时间：1-2秒
准确性：高（精确检索）
```

**1000次查询成本对比**：
- 方案A：$15
- 方案B：$0.20
- **节省98.7%！**

---

## 📊 知识库统计

假设300个视频，每个5分钟：

```
总视频数：300
总时长：25小时
总字数：约45万字

分块后：
  - 每块500字
  - 总块数：900个
  - 向量数：900个
  - OpenSearch文档：900个

存储：
  - 文本：~1MB
  - 向量（1536维 × 900）：~10MB
  - 总计：~11MB

OpenSearch成本：
  - t3.small.search实例：$0.036/小时 = $26/月
  - 或使用Serverless：$0.24/OCU-hour（按需）
```

---

## 🚀 与你现有项目的集成

我注意到你的 `aws-omni-support-agent` 项目已经有类似架构：

```python
# 你已有的组件（可复用）
- Amazon Bedrock（Claude Opus 4.5）
- OpenSearch（向量数据库）
- Lambda（工具实现）
- Titan Embeddings
- RAG知识库（01_create_support_knowledegbase_rag/）
```

**可以直接复用！**只需：
1. 创建新的OpenSearch索引（douyin-finance-kb）
2. 部署新的Lambda函数（查询财经知识库）
3. 创建新的Skill定义

---

## 🎯 总结：不是简单汇总！

| 错误方案 | 正确方案 |
|---------|---------|
| ❌ 汇总所有文本到Prompt | ✅ RAG：检索相关片段 |
| ❌ 超过context限制 | ✅ 只传入相关的500-1000字 |
| ❌ 无法引用来源 | ✅ 返回视频标题、时间 |
| ❌ 成本高（$0.015/次） | ✅ 成本低（$0.0002/次） |
| ❌ 响应慢（5-10秒） | ✅ 响应快（1-2秒） |
| ❌ 无时间检索 | ✅ 支持时间维度查询 |

---

## 📋 完整Pipeline

```
1️⃣ 视频下载 (已完成)
   ↓
2️⃣ Whisper转录 (即将开发)
   ↓
3️⃣ 文本分块 + 向量化
   ↓
4️⃣ 存入OpenSearch
   ↓
5️⃣ 部署Lambda查询工具
   ↓
6️⃣ 创建Claude Skill定义
   ↓
7️⃣ 测试和优化
   ↓
✅ 上线使用！
```

现在清楚了吗？需要我详细解释哪个部分？🚀
