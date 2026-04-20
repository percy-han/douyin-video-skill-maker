# 认知框架合成 - 快速开始

## 🎯 目标

从已有的视频转录中提取刘德超的认知框架，生成可安装的Claude Skill。

**无需重新转录！** 直接从S3的转录JSON提取。

---

## 🚀 快速运行

### 1. 设置环境变量

```bash
export S3_BUCKET=percyhan-douyin-video
export S3_PREFIX=post/刘德超/  # 你的转录文件所在目录
```

### 2. 运行合成器

```bash
cd 03_cognitive_synthesis
python cognitive_synthesis.py
```

---

## 📊 工作流程

```
步骤0: 单视频认知提取 (零清洗策略)
   ↓
   对每个视频的转录文本应用零清洗prompt
   提取: 心智模型、决策启发式、认知信号、元认知线索
   输出: video_frameworks.json

步骤1: 跨视频聚合
   ↓
   找出在多个视频中复现的思维模式
   合并相似模式

步骤2: 三重验证
   ↓
   验证1: 跨域复现 (至少2个不同话题)
   验证2: 有生成力 (可以推测对新问题的立场)
   验证3: 有排他性 (独特视角，非通用常识)

步骤3-5: 提取表达DNA、价值观、诚实边界

步骤6: 生成SKILL.md
```

---

## 📁 输出文件

运行完成后会生成：

### 本地 (`/tmp/skill_output/`)

- `SKILL.md` - 可安装的Claude Skill定义
- `cognitive_synthesis.json` - 完整的合成数据
- `video_frameworks.json` - 单视频认知框架（调试用）

### S3

```
s3://percyhan-douyin-video/post/刘德超/
├── SKILL.md
├── cognitive_synthesis.json
└── video_frameworks.json
```

---

## 🔍 预期输出示例

```
🧠 开始认知框架合成
============================================================

步骤0/6：单视频认知提取（零清洗策略）...
   总共 156 个视频
   [1/156] 印欧经济走廊大结局_1_4__#观棋有语_#g2...
      ✅ 模型:2 启发式:3 类型:辩驳类 密度:高
   [2/156] 印欧经济走廊大结局_2_4__#印度_#g20_...
      ✅ 模型:1 启发式:2 类型:解读类 密度:中
   ...
   完成：成功提取 145 / 156 个视频

步骤1/6：跨视频聚合候选思维模式...
   找到 23 个候选模式

步骤2/6：三重验证（跨域、生成力、排他性）...
   [1/23] 验证: 博弈均衡视角...
      ✅ 心智模型（置信度: 0.85）
   [2/23] 验证: 逆向共识思维...
      ✅ 心智模型（置信度: 0.78）
   ...
   结果：7 个心智模型，12 条决策启发式

步骤3/6：提取表达DNA...
   ✅ 完成

步骤4/6：提取价值观与反模式...
   ✅ 完成

步骤5/6：构建诚实边界...
   ✅ 完成

步骤6/6：保存单视频框架...
   ✅ 完成

============================================================
🎉 认知框架合成完成！
============================================================
心智模型：7 个
决策启发式：12 条
表达DNA：已量化
SKILL.md: s3://percyhan-douyin-video/post/刘德超/SKILL.md
单视频框架: s3://percyhan-douyin-video/post/刘德超/video_frameworks.json
```

---

## 🎨 关键特性

### ✅ 零清洗策略

不做文本清洗（去除"嗯啊"等），直接让Claude Opus 4处理原始转录。

**理由**: 大模型时代，传统正则清洗意义不大，Claude能自己识别噪音。

### ✅ 聚焦HOW而非WHAT

- ❌ 不提取: "他认为人民币会升值"
- ✅ 应该提取: "他习惯用博弈均衡点预测经济走向"

### ✅ 三重验证方法论（借鉴Nuwa）

只有通过三重验证的才算心智模型：

1. **跨域复现**: 同一思维方式在至少2个不同话题出现
2. **生成力**: 可以用来推测对新问题的立场
3. **排他性**: 独特视角，不是常见观点

---

## 🛠 调试

### 查看单视频提取结果

```bash
# 下载单视频框架
aws s3 cp s3://percyhan-douyin-video/post/刘德超/video_frameworks.json .

# 查看某个视频的提取结果
python3 -c "
import json
with open('video_frameworks.json') as f:
    data = json.load(f)
    
# 打印第一个视频
print(json.dumps(data[0], indent=2, ensure_ascii=False))
"
```

### 只提取单个视频（测试）

```python
from cognitive_synthesis import SingleVideoCognitiveExtractor
import json

extractor = SingleVideoCognitiveExtractor()

# 读取一个转录JSON
with open('sample_transcript.json') as f:
    transcript = json.load(f)

# 提取
framework = extractor.extract_from_transcript(transcript)
print(json.dumps(framework, indent=2, ensure_ascii=False))
```

---

## ⚠️ 注意事项

1. **首次运行很慢**: 需要对每个视频调用Claude API（156个视频约20-30分钟）
2. **Token成本**: 每个视频约3000-8000 tokens（输入+输出），总计约80万tokens
   - Opus 4成本: ~$12-15 USD (输入$0.015/1M, 输出$0.075/1M)
3. **失败重试**: 如果某个视频提取失败，会自动跳过，不影响其他视频

---

## 📚 生成的SKILL使用

```bash
# 下载SKILL.md
aws s3 cp s3://percyhan-douyin-video/post/刘德超/SKILL.md .

# 安装到Claude Code
mkdir -p ~/.claude/skills/liudechao-finance-perspective
cp SKILL.md ~/.claude/skills/liudechao-finance-perspective/

# 使用
# 在Claude Code中输入: /liudechao-finance-perspective
# 或触发词: "用刘德超的视角"、"刘德超会怎么看"
```

---

## 🔄 增量更新

如果添加了新视频转录：

1. 新转录会自动被检测（扫描S3_PREFIX下的所有`_transcript.json`）
2. 重新运行 `python cognitive_synthesis.py`
3. 会提取所有视频（包括新的），重新聚合

**优化**: 未来可以添加增量模式（只提取新视频，合并到已有框架）

---

## 🐛 常见问题

### Q: 为什么某些视频被跳过？

A: 可能原因：
- 转录文本太短（<100字符）
- Claude提取失败（内容质量不足）
- JSON解析错误

查看控制台输出了解详情。

### Q: 能否用其他模型替代Opus 4？

A: 可以，但不推荐：
- **Sonnet 4.5**: 可以，但认知提取质量会下降
- **Haiku**: 不推荐，太弱

修改 `modelId` 参数即可。

### Q: 如何调整prompt？

A: 修改 `SingleVideoCognitiveExtractor.extract_from_transcript()` 中的 `prompt` 变量。

---

## 📖 相关文档

- [Nuwa方法论](../nvwa/.agents/skills/huashu-nuwa/SKILL.md)
- [extraction-framework.md](../nvwa/.agents/skills/huashu-nuwa/references/extraction-framework.md)
- [02转录快速开始](../02_transcription/QUICKSTART.md)
