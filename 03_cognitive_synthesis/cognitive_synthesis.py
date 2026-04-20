#!/usr/bin/env python3
"""
认知框架合成器 - 借鉴Nuwa方法论

从所有视频转录中提取：
- 心智模型（三重验证：跨域复现、生成力、排他性）
- 决策启发式
- 表达DNA（量化风格特征）
- 价值观与反模式
- 诚实边界

输出：SKILL.md（可安装的Claude Skill）
"""

import os
import json
import boto3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from collections import Counter
import re

# ==================== 配置 ====================

# Bedrock模型ID（可通过环境变量覆盖）
BEDROCK_MODEL_ID = os.environ.get(
    'BEDROCK_MODEL_ID',
    'anthropic.claude-opus-4-20250514-v1:0'  # 默认使用标准区域模型
)

# ==================== 三重验证器 ====================

class MentalModelValidator:
    """心智模型三重验证"""

    def __init__(self):
        self.bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')

    def validate_candidate(self, candidate: Dict, all_transcripts: List[Dict]) -> Dict:
        """
        三重验证一个候选心智模型

        Args:
            candidate: {
                'pattern': '思维模式描述',
                'source_videos': ['video1.mp4', 'video2.mp4'],
                'quotes': ['引用1', '引用2']
            }
            all_transcripts: 所有转录结果

        Returns:
            {
                'is_mental_model': bool,
                'validation': {
                    'cross_domain': bool,  # 验证1：跨域复现
                    'generative': bool,    # 验证2：有生成力
                    'distinctive': bool    # 验证3：有排他性
                },
                'evidence': [...],
                'score': float
            }
        """

        prompt = f"""你是财经思维框架专家，负责验证一个候选心智模型。

候选模式：{candidate['pattern']}

来源视频：{len(candidate['source_videos'])}个
引用示例：{candidate['quotes'][:3]}

请进行三重验证：

## 验证1：跨域复现
这个思维模式是否在至少2个不同话题/领域中出现？

判断标准：
- 同一个框架用于分析不同的经济现象
- 例如：同样的逻辑既分析"降息"也分析"贬值"
- 不是碰巧用了相同的词，而是底层思维框架一致

## 验证2：有生成力
用这个模式能否推断此人对新问题的可能立场？

判断标准：
- 可以形成"如果遇到X情况，刘德超可能会..."
- 不是简单重复，而是能生成新的推理
- 有预测力

## 验证3：有排他性
这是刘德超独特的思维方式，还是所有财经分析师都这样想？

判断标准：
- 不是通用的财经常识
- 有个人特色
- 体现独特视角

请输出JSON：
{{
  "cross_domain": {{
    "passed": true/false,
    "evidence": "具体证据",
    "domains": ["领域1", "领域2"]
  }},
  "generative": {{
    "passed": true/false,
    "example": "可以生成的推断示例"
  }},
  "distinctive": {{
    "passed": true/false,
    "reasoning": "为什么独特/为什么不独特"
  }},
  "overall": "mental_model" / "heuristic" / "discard",
  "confidence": 0.0-1.0
}}

只输出JSON，不要额外解释。"""

        try:
            response = self.bedrock.invoke_model(
                modelId=BEDROCK_MODEL_ID,
                body=json.dumps({
                    'anthropic_version': 'bedrock-2023-05-31',
                    'max_tokens': 2048,
                    'messages': [
                        {'role': 'user', 'content': prompt}
                    ]
                })
            )

            result = json.loads(response['body'].read())
            content = result['content'][0]['text']

            # 提取JSON
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0].strip()
            elif '```' in content:
                content = content.split('```')[1].split('```')[0].strip()

            validation = json.loads(content)

            return {
                'is_mental_model': validation['overall'] == 'mental_model',
                'validation': {
                    'cross_domain': validation['cross_domain']['passed'],
                    'generative': validation['generative']['passed'],
                    'distinctive': validation['distinctive']['passed']
                },
                'evidence': validation,
                'score': validation['confidence']
            }

        except Exception as e:
            print(f"   ⚠️  验证失败: {e}")
            return {
                'is_mental_model': False,
                'validation': {'cross_domain': False, 'generative': False, 'distinctive': False},
                'evidence': {},
                'score': 0.0
            }

# ==================== 表达DNA提取器 ====================

class ExpressionDNAExtractor:
    """表达风格量化提取"""

    def extract(self, all_transcripts: List[Dict]) -> Dict:
        """
        从所有转录中提取量化的表达特征

        Returns:
            {
                'sentence_patterns': {...},
                'vocabulary': {...},
                'style_labels': {...},
                'rhythm': {...}
            }
        """

        print("📊 提取表达DNA...")

        all_text = ""
        for t in all_transcripts:
            all_text += t['transcription']['text'] + "\n"

        # 句式特征
        sentences = self._split_sentences(all_text)
        questions = [s for s in sentences if '？' in s or '吗' in s]

        sentence_patterns = {
            'avg_length': sum(len(s) for s in sentences) / len(sentences) if sentences else 0,
            'question_ratio': len(questions) / len(sentences) if sentences else 0,
            'short_sentence_ratio': len([s for s in sentences if len(s) < 15]) / len(sentences) if sentences else 0,
            'metaphor_density': self._count_metaphors(all_text) / (len(all_text) / 1000)  # per 1000 chars
        }

        # 词汇特征
        vocabulary = self._extract_vocabulary(all_text)

        # 风格标签（需要Claude分析）
        style_labels = self._extract_style_labels(all_text)

        # 节奏特征
        rhythm = self._extract_rhythm(sentences)

        return {
            'sentence_patterns': sentence_patterns,
            'vocabulary': vocabulary,
            'style_labels': style_labels,
            'rhythm': rhythm
        }

    def _split_sentences(self, text: str) -> List[str]:
        """分句"""
        # 简单的中文分句
        sentences = re.split(r'[。！？\n]+', text)
        return [s.strip() for s in sentences if s.strip() and len(s.strip()) > 3]

    def _count_metaphors(self, text: str) -> int:
        """统计类比/比喻数量（简化版）"""
        metaphor_markers = ['就像', '好比', '类似', '相当于', '可以说是', '打个比方']
        count = 0
        for marker in metaphor_markers:
            count += text.count(marker)
        return count

    def _extract_vocabulary(self, text: str) -> Dict:
        """提取词汇特征"""
        # 高频词（排除停用词）
        stopwords = {'的', '了', '是', '在', '我', '有', '这', '个', '就', '不', '人', '都', '一', '和', '会'}
        words = re.findall(r'[\u4e00-\u9fa5]{2,}', text)
        word_counts = Counter(w for w in words if w not in stopwords)

        high_frequency = [w for w, c in word_counts.most_common(30)]

        # 确定性词汇
        certainty_words = ['显然', '必然', '一定', '肯定', '绝对', '毫无疑问', '明确']
        uncertainty_words = ['可能', '也许', '大概', '或许', '不确定', '未必']

        certainty_count = sum(text.count(w) for w in certainty_words)
        uncertainty_count = sum(text.count(w) for w in uncertainty_words)

        return {
            'high_frequency': high_frequency[:15],
            'certainty_ratio': certainty_count / (certainty_count + uncertainty_count + 1),
            'signature_phrases': self._find_signature_phrases(text)
        }

    def _find_signature_phrases(self, text: str) -> List[str]:
        """找口头禅/高频短语"""
        # 简化版：找3-5字的高频短语
        phrases = re.findall(r'[\u4e00-\u9fa5]{3,5}', text)
        phrase_counts = Counter(phrases)

        # 排除通用短语
        common_phrases = {'我们可以', '这个时候', '那么这个', '实际上', '也就是说'}

        return [p for p, c in phrase_counts.most_common(20)
                if c > 5 and p not in common_phrases][:10]

    def _extract_style_labels(self, text: str) -> Dict:
        """提取风格标签（简化版，完整版需要Claude分析）"""
        # 这里做简单判断，完整版应该用Claude

        # 正式 vs 口语
        formal_markers = ['因此', '综上所述', '换言之', '总而言之']
        colloquial_markers = ['说白了', '其实吧', '你看', '对吧', '嘛']

        formal_score = sum(text.count(m) for m in formal_markers)
        colloquial_score = sum(text.count(m) for m in colloquial_markers)

        # 断言 vs 谨慎
        assertive_markers = ['显然', '明确', '一定', '必须']
        cautious_markers = ['可能', '也许', '不确定', '需要观察']

        assertive_score = sum(text.count(m) for m in assertive_markers)
        cautious_score = sum(text.count(m) for m in cautious_markers)

        return {
            'formality': 'colloquial' if colloquial_score > formal_score else 'formal',
            'certainty': 'assertive' if assertive_score > cautious_score else 'cautious',
            'structure': 'conclusion_first'  # 财经分析通常结论先行
        }

    def _extract_rhythm(self, sentences: List[str]) -> Dict:
        """提取节奏特征"""
        return {
            'prefers_short_sentences': len([s for s in sentences if len(s) < 15]) > len(sentences) / 2,
            'uses_pauses': '，' in ''.join(sentences),  # 简化判断
            'builds_gradually': False  # 需要更复杂的分析
        }

# ==================== 单视频认知提取器 ====================

class SingleVideoCognitiveExtractor:
    """对单个视频提取认知框架（零清洗策略）"""

    def __init__(self):
        self.bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')

    def extract_from_transcript(self, transcript_data: Dict) -> Optional[Dict]:
        """
        从单个转录中提取认知框架（使用02的零清洗prompt）

        Args:
            transcript_data: 转录JSON（包含 video_metadata, transcription）

        Returns:
            认知框架 or None
        """
        raw_text = transcript_data['transcription']['text']
        metadata = transcript_data['video_metadata']

        if len(raw_text) < 100:
            return None

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
            response = self.bedrock.invoke_model(
                modelId=BEDROCK_MODEL_ID,
                body=json.dumps({
                    'anthropic_version': 'bedrock-2023-05-31',
                    'max_tokens': 8192,
                    'temperature': 0.0,
                    'messages': [{'role': 'user', 'content': prompt}]
                })
            )

            result = json.loads(response['body'].read())
            content = result['content'][0]['text']

            # 提取JSON
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0].strip()
            elif '```' in content:
                content = content.split('```')[1].split('```')[0].strip()

            framework = json.loads(content)

            # 检查是否是错误返回
            if 'error' in framework:
                return None

            return framework

        except Exception as e:
            print(f"      ⚠️ 提取失败: {e}")
            return None

# ==================== 认知合成器 ====================

class CognitiveSynthesizer:
    """从所有转录中合成认知框架"""

    def __init__(self):
        self.bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
        self.validator = MentalModelValidator()
        self.dna_extractor = ExpressionDNAExtractor()
        self.single_extractor = SingleVideoCognitiveExtractor()

    def synthesize(self, all_transcripts: List[Dict], output_dir: str) -> Dict:
        """
        完整的认知合成流程

        Returns:
            {
                'mental_models': [...],
                'heuristics': [...],
                'expression_dna': {...},
                'values': {...},
                'honest_boundaries': {...}
            }
        """

        print("\n" + "="*60)
        print("🧠 开始认知框架合成")
        print("="*60)

        # 步骤0：对每个视频单独提取认知框架（零清洗策略）
        print("\n步骤0/6：单视频认知提取（零清洗策略）...")
        print(f"   总共 {len(all_transcripts)} 个视频")

        video_frameworks = []
        for i, transcript in enumerate(all_transcripts, 1):
            title = transcript['video_metadata']['title']
            print(f"   [{i}/{len(all_transcripts)}] {title[:40]}...")

            framework = self.single_extractor.extract_from_transcript(transcript)

            if framework:
                models_count = len(framework.get('心智模型', []))
                heuristics_count = len(framework.get('决策启发式', []))
                video_type = framework.get('视频分类', '未知')
                density = framework.get('信息密度', '未知')

                print(f"      ✅ 模型:{models_count} 启发式:{heuristics_count} 类型:{video_type} 密度:{density}")

                video_frameworks.append({
                    'video_metadata': transcript['video_metadata'],
                    'framework': framework
                })
            else:
                print(f"      ⏭️  跳过（内容不足或提取失败）")

        print(f"\n   完成：成功提取 {len(video_frameworks)} / {len(all_transcripts)} 个视频")

        # 将单视频框架附加到转录数据上
        framework_map = {vf['video_metadata']['s3_key']: vf['framework'] for vf in video_frameworks}
        for transcript in all_transcripts:
            s3_key = transcript['video_metadata']['s3_key']
            if s3_key in framework_map:
                transcript['cognitive_framework'] = framework_map[s3_key]

        # 步骤1：跨视频聚合，提取候选模式
        print("\n步骤1/6：跨视频聚合候选思维模式...")
        candidates = self._aggregate_candidates_from_frameworks(video_frameworks)
        print(f"   找到 {len(candidates)} 个候选模式")

        # 步骤2：三重验证
        print("\n步骤2/6：三重验证（跨域、生成力、排他性）...")
        mental_models = []
        heuristics = []

        for i, candidate in enumerate(candidates, 1):
            print(f"   [{i}/{len(candidates)}] 验证: {candidate['pattern'][:50]}...")
            validation = self.validator.validate_candidate(candidate, all_transcripts)

            if validation['is_mental_model']:
                mental_models.append({
                    **candidate,
                    'validation': validation
                })
                print(f"      ✅ 心智模型（置信度: {validation['score']:.2f}）")
            elif validation['score'] > 0.3:
                heuristics.append(candidate)
                print(f"      📋 决策启发式")
            else:
                print(f"      ❌ 不通过验证")

        print(f"\n   结果：{len(mental_models)} 个心智模型，{len(heuristics)} 条决策启发式")

        # 步骤3：提取表达DNA
        print("\n步骤3/6：提取表达DNA...")
        expression_dna = self.dna_extractor.extract(all_transcripts)
        print(f"   ✅ 完成")

        # 步骤4：提取价值观
        print("\n步骤4/6：提取价值观与反模式...")
        values = self._extract_values(all_transcripts)
        print(f"   ✅ 完成")

        # 步骤5：构建诚实边界
        print("\n步骤5/6：构建诚实边界...")
        honest_boundaries = self._build_honest_boundaries(all_transcripts, mental_models)
        print(f"   ✅ 完成")

        # 步骤6：保存单视频框架（用于后续分析）
        print("\n步骤6/6：保存单视频框架...")
        self._save_video_frameworks(video_frameworks, output_dir)
        print(f"   ✅ 完成")

        return {
            'mental_models': mental_models,
            'heuristics': heuristics,
            'expression_dna': expression_dna,
            'values': values,
            'honest_boundaries': honest_boundaries,
            'metadata': {
                'total_videos': len(all_transcripts),
                'synthesis_date': datetime.now().isoformat(),
                'date_range': {
                    'start': min(t['video_metadata']['publish_date'] for t in all_transcripts),
                    'end': max(t['video_metadata']['publish_date'] for t in all_transcripts)
                }
            }
        }

    def _aggregate_candidates_from_frameworks(self, video_frameworks: List[Dict]) -> List[Dict]:
        """
        从单视频框架中聚合候选模式（新方法）

        策略：
        1. 收集所有单视频的心智模型
        2. 找出跨视频复现的模式
        3. 合并相似的模式
        """

        # 收集所有心智模型
        all_models = []
        for vf in video_frameworks:
            framework = vf['framework']
            video_title = vf['video_metadata']['title']

            for model in framework.get('心智模型', []):
                all_models.append({
                    'pattern': model['模型名称'] + ': ' + model['描述'],
                    'source_videos': [video_title],
                    'quotes': [model['证据']],
                    'model_name': model['模型名称'],
                    'description': model['描述'],
                    'cross_domain_score': model['验证'].get('跨域复现', '低')
                })

        # 简单聚合：找相似的模型名称
        candidates = []
        processed = set()

        for i, model1 in enumerate(all_models):
            if i in processed:
                continue

            # 找所有相似的模型
            similar_group = [model1]
            for j, model2 in enumerate(all_models[i+1:], i+1):
                if j in processed:
                    continue

                # 简单的相似度判断：模型名称包含相同关键词
                if self._are_similar_models(model1['model_name'], model2['model_name']):
                    similar_group.append(model2)
                    processed.add(j)

            # 合并相似模型
            if len(similar_group) >= 2:  # 至少2个视频复现才算候选
                merged = self._merge_similar_models(similar_group)
                candidates.append(merged)
                processed.add(i)

        # 也包含高信心度的单个模型
        for i, model in enumerate(all_models):
            if i not in processed and '高' in model['cross_domain_score']:
                candidates.append({
                    'pattern': model['pattern'],
                    'source_videos': model['source_videos'],
                    'quotes': model['quotes'],
                    'domains': [model['model_name']]
                })

        return candidates

    def _are_similar_models(self, name1: str, name2: str) -> bool:
        """判断两个模型名称是否相似"""
        # 简单版：如果有2个以上相同的字就认为相似
        common_chars = set(name1) & set(name2)
        return len(common_chars) >= 2

    def _merge_similar_models(self, models: List[Dict]) -> Dict:
        """合并相似的模型"""
        all_videos = []
        all_quotes = []
        for m in models:
            all_videos.extend(m['source_videos'])
            all_quotes.extend(m['quotes'])

        return {
            'pattern': models[0]['pattern'],
            'source_videos': list(set(all_videos)),
            'quotes': all_quotes[:5],  # 最多保留5个引用
            'domains': [m['model_name'] for m in models]
        }

    def _extract_candidates(self, all_transcripts: List[Dict]) -> List[Dict]:
        """提取候选思维模式（旧方法，保留作为备用）"""

        # 准备所有转录的摘要
        video_summaries = []
        for t in all_transcripts:
            video_summaries.append({
                'title': t['video_metadata']['title'],
                'date': t['video_metadata']['publish_date'],
                'text': t['transcription']['text'][:500]  # 只取前500字
            })

        prompt = f"""你是财经思维框架专家，分析刘德超（观棋有语）的视频转录。

你的任务：扫描所有视频，找出反复出现的思维模式。

注意：
- 不要提取具体观点（如"人民币会升值"）
- 要提取思维框架（如"汇率影响不是线性的"）
- 寻找跨多个视频、多个话题出现的分析逻辑

已有 {len(all_transcripts)} 个视频，涵盖话题：{self._summarize_topics(all_transcripts)}

请列出15-30个候选思维模式，每个包含：
1. 模式描述（一句话）
2. 出现的视频（标题）
3. 典型引用（原话）

输出JSON数组：
[
  {{
    "pattern": "思维模式描述",
    "source_videos": ["视频标题1", "视频标题2"],
    "quotes": ["引用1", "引用2"],
    "domains": ["降息", "贬值"]  // 出现在哪些话题
  }}
]

只输出JSON，不要额外解释。"""

        try:
            response = self.bedrock.invoke_model(
                modelId=BEDROCK_MODEL_ID,
                body=json.dumps({
                    'anthropic_version': 'bedrock-2023-05-31',
                    'max_tokens': 8192,
                    'messages': [
                        {'role': 'user', 'content': prompt}
                    ]
                })
            )

            result = json.loads(response['body'].read())
            content = result['content'][0]['text']

            # 提取JSON
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0].strip()
            elif '```' in content:
                content = content.split('```')[1].split('```')[0].strip()

            candidates = json.loads(content)
            return candidates

        except Exception as e:
            print(f"   ❌ 提取候选模式失败: {e}")
            return []

    def _save_video_frameworks(self, video_frameworks: List[Dict], output_dir: str):
        """保存单视频框架（用于后续分析）"""
        os.makedirs(output_dir, exist_ok=True)

        output_path = os.path.join(output_dir, 'video_frameworks.json')
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(video_frameworks, f, ensure_ascii=False, indent=2)

        print(f"   📄 保存到: {output_path}")

    def _summarize_topics(self, all_transcripts: List[Dict]) -> str:
        """总结涵盖的话题"""
        titles = [t['video_metadata']['title'] for t in all_transcripts[:20]]
        return ', '.join(titles)

    def _extract_values(self, all_transcripts: List[Dict]) -> Dict:
        """提取价值观与反模式（简化版）"""

        # 这里应该用Claude深度分析，暂时返回占位
        return {
            'core_values': [
                '数据驱动：基于经济数据分析，不是情绪判断',
                '系统思考：看整体而非局部',
                '独立思考：不盲从市场情绪'
            ],
            'anti_patterns': [
                '盲目跟风',
                '忽视数据',
                '线性外推'
            ],
            'tensions': [
                '短期波动 vs 长期趋势的平衡'
            ]
        }

    def _build_honest_boundaries(self, all_transcripts: List[Dict], mental_models: List[Dict]) -> Dict:
        """构建诚实边界"""

        latest_date = max(t['video_metadata']['publish_date'] for t in all_transcripts)

        return {
            'cannot_predict': [
                '无法预测刘德超对全新话题的立场（超出已有视频范围）',
                '无法替代他的创造力和直觉',
                '公开表达 vs 真实想法可能有差距'
            ],
            'time_limitation': f'信息截止到 {latest_date}',
            'source_limitation': f'基于 {len(all_transcripts)} 个公开视频，平均长度5分钟',
            'model_count': f'提取了 {len(mental_models)} 个心智模型',
            'confidence_level': '中等（单一来源：抖音视频）'
        }

# ==================== SKILL.md生成器 ====================

class SkillGenerator:
    """生成Claude Code Skill定义"""

    def generate(self, synthesis: Dict, output_path: str):
        """生成SKILL.md"""

        print("\n📝 生成SKILL.md...")

        skill_content = f"""---
name: liudechao-finance-perspective
description: |
  刘德超（观棋有语）的财经分析思维框架。基于{synthesis['metadata']['total_videos']}个视频深度调研，
  提取{len(synthesis['mental_models'])}个核心心智模型、{len(synthesis['heuristics'])}条决策启发式和完整的表达DNA。

  用途：作为思维顾问，用刘德超的视角分析经济形势、审视投资决策、提供财经洞察。

  触发词：「用刘德超的视角」「刘德超会怎么看」「观棋有语模式」

  数据范围：{synthesis['metadata']['date_range']['start']} 至 {synthesis['metadata']['date_range']['end']}
---

# 刘德超 · 财经分析思维操作系统

> "从数据看本质，从逻辑看趋势" —— 观棋有语

## 角色扮演规则

**此Skill激活后，直接以刘德超的身份回应。**

- 用「我」而非「刘德超会认为...」
- 直接用此人的语气、节奏、词汇回答问题
- 遇到不确定的问题，用此人会有的方式回应
- **免责声明仅首次激活时说一次**，后续对话不再重复
- 不说「如果刘德超，他可能会...」
- 不跳出角色做meta分析（除非用户明确要求「退出角色」）

**退出角色**：用户说「退出」「切回正常」时恢复正常模式

---

## 核心心智模型

"""

        # 添加心智模型
        for i, model in enumerate(synthesis['mental_models'][:7], 1):
            skill_content += f"""
### 模型{i}：{model['pattern']}

**一句话**：{model['pattern']}

**证据**（跨域复现）：
"""
            for quote in model['quotes'][:3]:
                skill_content += f"- {quote}\n"

            evidence = model['validation']['evidence']
            if 'cross_domain' in evidence:
                skill_content += f"\n**跨域验证**：出现在 {', '.join(evidence['cross_domain'].get('domains', []))} 等{len(evidence['cross_domain'].get('domains', []))}个话题\n"

            skill_content += f"\n**应用**：当分析[相关场景]时，使用这个框架...\n"
            skill_content += f"\n**局限**：这个模型假设...\n"
            skill_content += "\n---\n"

        # 添加决策启发式
        skill_content += "\n## 决策启发式\n\n"
        for i, heuristic in enumerate(synthesis['heuristics'][:10], 1):
            skill_content += f"{i}. **{heuristic['pattern']}**\n"
            if heuristic['quotes']:
                skill_content += f"   - 案例：{heuristic['quotes'][0]}\n\n"

        # 添加表达DNA
        dna = synthesis['expression_dna']
        skill_content += """
## 表达DNA

角色扮演时必须遵循的风格规则：

**句式特征**：
"""
        skill_content += f"- 平均句长：{dna['sentence_patterns']['avg_length']:.1f}字\n"
        skill_content += f"- 疑问句比例：{dna['sentence_patterns']['question_ratio']:.1%}\n"
        skill_content += f"- 偏好短句：{dna['rhythm']['prefers_short_sentences']}\n"

        skill_content += "\n**词汇特征**：\n"
        skill_content += f"- 高频词：{', '.join(dna['vocabulary']['high_frequency'][:10])}\n"
        skill_content += f"- 口头禅：{', '.join(dna['vocabulary']['signature_phrases'][:5])}\n"
        skill_content += f"- 确定性比例：{dna['vocabulary']['certainty_ratio']:.1%}（{'断言型' if dna['vocabulary']['certainty_ratio'] > 0.5 else '谨慎型'}）\n"

        skill_content += "\n**风格标签**：\n"
        skill_content += f"- 正式度：{dna['style_labels']['formality']}\n"
        skill_content += f"- 确定性：{dna['style_labels']['certainty']}\n"
        skill_content += f"- 结构：{dna['style_labels']['structure']}\n"

        # 添加价值观
        skill_content += "\n## 价值观与反模式\n\n"
        skill_content += "**我追求的**：\n"
        for value in synthesis['values']['core_values']:
            skill_content += f"- {value}\n"

        skill_content += "\n**我拒绝的**：\n"
        for anti in synthesis['values']['anti_patterns']:
            skill_content += f"- {anti}\n"

        # 添加诚实边界
        boundaries = synthesis['honest_boundaries']
        skill_content += f"""
## 诚实边界

**这个Skill能做到的**：
- 用刘德超的分析框架解读当前经济形势
- 识别他关注的关键变量
- 模拟他的表达风格

**这个Skill做不到的**：
"""
        for limitation in boundaries['cannot_predict']:
            skill_content += f"- {limitation}\n"

        skill_content += f"""
**信息源说明**：
- 时间范围：{boundaries['time_limitation']}
- 数据来源：{boundaries['source_limitation']}
- 心智模型：{boundaries['model_count']}
- 置信度：{boundaries['confidence_level']}

**一个不告诉你局限在哪的Skill，不值得信任。**

---

## 元信息

- 生成时间：{synthesis['metadata']['synthesis_date']}
- 数据范围：{synthesis['metadata']['date_range']['start']} ~ {synthesis['metadata']['date_range']['end']}
- 视频数量：{synthesis['metadata']['total_videos']}
- 心智模型：{len(synthesis['mental_models'])}
- 决策启发式：{len(synthesis['heuristics'])}
"""

        # 保存文件
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(skill_content)

        print(f"   ✅ 已保存: {output_path}")
        print(f"   📄 文件大小: {len(skill_content)} 字符")

# ==================== 主函数 ====================

def main():
    """主入口：从S3加载转录，合成认知框架"""

    S3_BUCKET = os.environ.get('S3_BUCKET', 'percyhan-douyin-video')
    S3_PREFIX = os.environ.get('S3_PREFIX', 'douyin_videos/20260417_150000/')
    OUTPUT_DIR = '/tmp/skill_output'

    print("🧠 认知框架合成器")
    print("="*60)
    print(f"S3: s3://{S3_BUCKET}/{S3_PREFIX}")
    print()

    # 1. 从S3加载所有转录的JSON文件
    print("📥 从S3加载转录结果...")
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
                except Exception as e:
                    print(f"   ⚠️  跳过 {key}: {e}")

    print(f"   加载了 {len(all_transcripts)} 个转录文件")

    if not all_transcripts:
        print("❌ 没有找到转录文件")
        return

    # 2. 执行认知合成
    synthesizer = CognitiveSynthesizer()
    synthesis = synthesizer.synthesize(all_transcripts, OUTPUT_DIR)

    # 3. 生成SKILL.md
    skill_generator = SkillGenerator()
    skill_path = os.path.join(OUTPUT_DIR, 'SKILL.md')
    skill_generator.generate(synthesis, skill_path)

    # 4. 保存完整的synthesis JSON
    synthesis_path = os.path.join(OUTPUT_DIR, 'cognitive_synthesis.json')
    with open(synthesis_path, 'w', encoding='utf-8') as f:
        json.dump(synthesis, f, ensure_ascii=False, indent=2)
    print(f"\n💾 完整数据已保存: {synthesis_path}")

    # 5. 上传到S3
    print(f"\n☁️  上传到S3...")
    s3.upload_file(skill_path, S3_BUCKET, f"{S3_PREFIX}SKILL.md")
    s3.upload_file(synthesis_path, S3_BUCKET, f"{S3_PREFIX}cognitive_synthesis.json")

    # 上传单视频框架
    video_frameworks_path = os.path.join(OUTPUT_DIR, 'video_frameworks.json')
    if os.path.exists(video_frameworks_path):
        s3.upload_file(video_frameworks_path, S3_BUCKET, f"{S3_PREFIX}video_frameworks.json")

    print("\n" + "="*60)
    print("🎉 认知框架合成完成！")
    print("="*60)
    print(f"心智模型：{len(synthesis['mental_models'])} 个")
    print(f"决策启发式：{len(synthesis['heuristics'])} 条")
    print(f"表达DNA：已量化")
    print(f"SKILL.md: s3://{S3_BUCKET}/{S3_PREFIX}SKILL.md")
    print(f"单视频框架: s3://{S3_BUCKET}/{S3_PREFIX}video_frameworks.json")

if __name__ == '__main__':
    main()
