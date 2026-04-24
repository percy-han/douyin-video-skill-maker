# 🎬 Douyin Video Skill Maker

一键将抖音博主视频转换为Claude Code Skill的完整工具链。

> **核心理念**：不只提取"他说过什么"，而是复刻"他怎么想" - 提取思维框架、分析逻辑、表达风格，生成可复用的认知操作系统。

## 📋 项目简介

本项目用于批量下载抖音博主视频、转录文字内容、提取认知框架，并生成Claude Code Skill，让AI助手能够用博主的思维方式分析新问题。

**应用场景**：
- 📚 **财经博主** → 财经分析Skill（用他的框架分析当前经济）
- 🎓 **教育博主** → 教学方法Skill（用他的方式讲解新知识）
- 💼 **行业专家** → 专业咨询Skill（用他的视角做决策）

**与传统知识库的区别**：
- ❌ 传统：检索"他在X月说了什么"（过时信息，价值低）
- ✅ 本项目：提取"他的分析框架"，应用到新情况（可复用，价值高）

---

## 🚀 功能特性

### ✅ 阶段1：视频下载模块（已完成）

- 🔐 **Cookie管理**：自动配置和验证抖音Cookie
- 📥 **批量下载**：一键下载博主所有视频、文案、封面
- 🌐 **EC2部署**：支持部署到AWS EC2实现高速下载
- ☁️ **S3集成**：自动上传到S3存储
- 🔄 **断点续传**：支持中断恢复，自动跳过已下载文件

### ✅ 阶段2：视频转录模块（已完成）

- 🎤 **Whisper Large**：96-98%准确率的中文转录
- 🚀 **GPU加速**：g4dn.xlarge，1小时视频→4-6分钟
- 📂 **智能过滤**：只处理视频文件，跳过封面/文案
- 💾 **多格式输出**：TXT（纯文本）+ SRT（字幕）+ JSON（完整数据）
- 🔄 **断点续传**：自动跳过已转录的视频

### ✅ 阶段3：认知框架合成（已完成）⭐

借鉴[Nuwa](https://github.com/alchaincyf/nuwa-skill)方法论，提取认知框架：

- 🧠 **心智模型提取**：三重验证（跨域复现、生成力、排他性）
- 🗣️ **表达DNA量化**：句式、词汇、风格特征
- 📋 **决策启发式**：快速判断规则
- 🎯 **价值观提取**：追求什么、拒绝什么
- 🔍 **诚实边界**：明确Skill的局限

**输出**：可安装的Claude Code Skill（SKILL.md）

### 📅 阶段4：持续进化（TODO）

- 🔄 增量更新机制（新视频自动融入框架）
- 📈 质量自动评分
- 🔀 多人对比分析
- 📊 时间演化追踪

---

## 📂 项目结构

```
douyin-video-skill-maker/
├── 01_video_download/          # 视频下载模块 ✅
│   ├── local/                  # 本地下载脚本
│   │   ├── setup_cookie.py
│   │   ├── batch_download.py
│   │   └── douyin_cookie.txt.example
│   ├── ec2/                    # EC2部署脚本
│   │   ├── deploy_to_ec2.sh
│   │   ├── run_on_ubuntu.sh
│   │   └── ec2_download_to_s3.py
│   └── docs/                   # 完整文档
│       ├── COOKIE_SETUP_SIMPLE.md
│       ├── EC2_DEPLOYMENT_GUIDE.md
│       └── BATCH_DOWNLOAD_GUIDE.md
│
├── 02_transcription/           # 视频转录模块 ✅
│   ├── batch_transcribe_s3.py  # 主转录脚本（Whisper）
│   ├── setup_gpu_instance.sh   # GPU环境配置
│   ├── requirements.txt
│   ├── README.md               # 使用指南
│   ├── IMPLEMENTATION_PLAN.md  # 设计文档
│   └── IMPLEMENTATION_PLAN_V2.md
│
├── 03_cognitive_synthesis/     # 认知框架合成 ✅
│   ├── cognitive_synthesis.py  # 主合成脚本
│   ├── requirements.txt
│   └── README.md               # 方法论详解
│
├── 03_knowledge_base/          # 架构设计文档
│   ├── COGNITIVE_REPLICATION_ARCHITECTURE.md  # 认知复刻架构
│   ├── SKILL_ARCHITECTURE.md                  # Skill架构设计
│   └── ARCHITECTURE_COMPARISON.md             # 与Nuwa对比
│
└── README.md                   # 本文件
```

---

## 🎯 完整流程

### 第1步：视频下载

```bash
# EC2部署（推荐）
cd 01_video_download/ec2
./deploy_to_ec2.sh

# SSH登录EC2
ssh -i key.pem ubuntu@ec2-ip

# 下载所有视频到S3
./run_on_ubuntu.sh '博主主页链接' 's3-bucket-name'
```

**输出**：所有视频、封面、文案 → S3

### 第2步：视频转录

```bash
# 启动GPU实例（g4dn.xlarge Spot）
aws ec2 run-instances --instance-type g4dn.xlarge --instance-market-options "MarketType=spot"

# SSH登录GPU实例
ssh -i key.pem ubuntu@gpu-instance

# 克隆仓库并安装环境
git clone https://github.com/percy-han/douyin-video-skill-maker.git
cd douyin-video-skill-maker/02_transcription
./setup_gpu_instance.sh

# 配置并执行转录（根据实际S3路径修改）
export S3_BUCKET=percyhan-douyin-video
export S3_PREFIX=post/刘德超/
# 注意：如果脚本检测到PyTorch venv，使用python（不是python3）
python batch_transcribe_s3.py
```

**输出**：每个视频生成3个文件（TXT + SRT + JSON）

**成本**：300个5分钟视频（25小时）→ Spot实例2小时 → **$0.32**

### 第3步：认知框架合成

```bash
cd 03_cognitive_synthesis

# ⚠️ 配置环境变量（必须根据实际S3路径修改）
export S3_BUCKET=percyhan-douyin-video
export S3_PREFIX=post/刘德超/

# 执行认知合成
python3 cognitive_synthesis.py
```

**⚠️ 重要提示**：
- `S3_PREFIX` 必须设置为实际存放转录文件的路径
- 如果在 screen/tmux 中运行，重新连接后需要重新 export 环境变量
- 验证路径：`aws s3 ls s3://${S3_BUCKET}/${S3_PREFIX} --recursive | grep transcript.json`

**工作流程**：
1. 从S3加载所有转录JSON
2. 提取候选思维模式（15-30个）
3. 三重验证筛选真正的心智模型
4. 提取表达DNA（量化风格）
5. 生成SKILL.md（可安装的Skill）

**输出**：
- `SKILL.md` - Claude Code Skill定义
- `cognitive_synthesis.json` - 完整认知框架数据

**成本**：约$1.50（Claude Opus调用）

### 第4步：安装和使用Skill

**📥 快速开始**：

```bash
# 方法1：从GitHub下载（推荐）
wget https://raw.githubusercontent.com/percy-han/douyin-video-skill-maker/main/skills/SKILL_FULL.md

# 方法2：从S3下载
aws s3 cp s3://percyhan-douyin-video/post/刘德超/SKILL_FULL.md ./

# 安装到Claude Code
mkdir -p ~/.claude/skills/liudechao-finance
cp SKILL_FULL.md ~/.claude/skills/liudechao-finance/SKILL.md
```

**🎯 在Claude Code中使用**：
```
> 用刘德超的视角分析当前美联储降息的影响

> 刘德超会怎么看人民币汇率走势？

> 切换到观棋有语模式
```

**✨ Skill自动激活**（触发词）：
- "用刘德超的视角"
- "刘德超会怎么看"
- "观棋有语模式"

**📁 生成的文件**（位于 [`skills/`](skills/) 目录）：
- `SKILL_FULL.md` - 可直接安装的Skill文件（176KB）
- `SKILL_APPENDIX.md` - 深度研究附录，完整123个心智模型（177KB）
- `cognitive_synthesis.json` - 机器可读的结构化数据（850KB）
- `video_frameworks.json` - 单视频提取结果（4.1MB）

详见：[skills/README.md](skills/README.md)

---

## 💡 认知复刻 vs 传统检索

### 传统方案的问题 ❌

```
用户："当前美联储可能降息，对A股有什么影响？"

传统RAG：
→ 检索"美联储降息"相关视频
→ 返回："刘德超在2026-04-03说：'如果降息，A股可能...'"
→ 问题：这是3个月前的观点，经济环境已变化
→ 价值：低（过时信息）
```

### 认知复刻方案 ✅

```
用户："当前美联储可能降息，对A股有什么影响？"

认知复刻：
→ 提取他分析"降息→股市"的思维框架
→ 识别他关注的关键变量（通胀、汇率、估值）
→ 应用他的分析逻辑到当前数据
→ 输出："基于刘德超的分析方法，当前情况下..."

价值：高（可应用于新情况）
```

**核心差异**：
- 传统：回放历史观点（价值随时间衰减）
- 认知复刻：提取思维框架（可复用到新情况）

---

## 🧠 三重验证机制（Nuwa方法论）

一个观点要被认定为「心智模型」而非「随口一说」，必须通过三重验证：

### 验证1：跨域复现
同一思维框架出现在至少2个不同话题/领域。

**示例**：
```
候选："汇率影响不是线性的"

扫描所有视频：
- 视频A："人民币升值对出口" → "升值不一定削弱出口"
- 视频B："中美贸易定价权" → "汇率影响取决于产业链位置"
- 视频C："产业升级指标" → "不能简单用汇率解释"

结果：✅ 3个不同话题，同一框架 → 通过
```

### 验证2：有生成力
用这个模型可以推断此人对新问题的可能立场。

**示例**：
```
模式："汇率影响不是线性的"

问题：人民币贬值5%，对进口企业有什么影响？

推断：
→ 不能简单说"成本上升5%"
→ 要看：产业链位置、定价权、替代品
→ 有定价权→转嫁成本；无定价权→利润挤压

结果：✅ 能生成新推理 → 通过
```

### 验证3：有排他性
不是所有财经分析师都这样想，体现独特视角。

**示例**：
```
通用常识："汇率升值不利出口"（所有人都知道）

刘德超独特视角：
- "汇率影响取决于竞争力来源"
- 强调技术优势可以抵消汇率劣势

结果：✅ 有区分度 → 通过
```

**验证结果分类**：
- 三重通过 → **心智模型**（3-7个）
- 1-2重通过 → **决策启发式**（5-10条）
- 0重通过 → 丢弃

---

## 💰 总成本预估

### 300个5分钟视频（25小时）的完整流程

| 阶段 | 成本 |
|------|------|
| **视频下载**（EC2 t3.medium × 10h） | $0.42 |
| **S3存储**（100GB） | $2.3/月 |
| **视频转录**（g4dn.xlarge Spot × 2h） | $0.32 |
| **认知合成**（Claude Opus调用） | $1.50 |
| **总计** | **~$5** |

**性价比**：
- 传统RAG：每次查询$0.001，但价值低（过时信息）
- 认知复刻：一次性$5，生成可复用的Skill
- **价值提升10倍+，成本极低**

---

## 📖 详细文档

### 各模块文档
- [视频下载指南](01_video_download/README.md)
- [视频转录指南](02_transcription/README.md)
- [认知合成指南](03_cognitive_synthesis/README.md)

### 架构设计文档
- [认知复刻架构](03_knowledge_base/COGNITIVE_REPLICATION_ARCHITECTURE.md)
- [与Nuwa方法论对比](03_knowledge_base/ARCHITECTURE_COMPARISON.md)
- [Skill架构设计](03_knowledge_base/SKILL_ARCHITECTURE.md)

---

## 🛠️ 技术栈

- **视频下载**: [F2](https://github.com/Johnserf-Seed/f2)
- **语音转录**: [OpenAI Whisper](https://github.com/openai/whisper)
- **认知提取**: Claude Opus 4（Bedrock）
- **存储**: AWS S3
- **计算**: AWS EC2（视频下载）+ g4dn.xlarge（GPU转录）
- **方法论**: 借鉴[Nuwa](https://github.com/alchaincyf/nuwa-skill)三重验证

---

## 📊 示例：财经博主Skill

### 输入
- 博主：刘德超（观棋有语）
- 视频：300个财经分析视频
- 内容：降息、汇率、股市、产业升级等

### 输出：SKILL.md

```markdown
---
name: liudechao-finance-perspective
description: 刘德超财经分析思维框架
---

## 核心心智模型（5个）

### 模型1：汇率影响不是线性的
**一句话**：汇率变化对经济的影响取决于竞争力来源
**证据**：出现在出口分析、贸易定价、产业升级等3个领域
**应用**：分析货币政策对实体经济的影响时...
**局限**：假设产业结构稳定...

## 决策启发式（8条）

1. **看数据，不看情绪**：...
2. **关注结构，不只总量**：...

## 表达DNA

**句式特征**：
- 平均句长：18.5字
- 短句为主，断言型语气

**词汇特征**：
- 高频词：显然、数据、其实、关键
- 口头禅：从数据来看、说白了、这个很明确

**风格标签**：
- 口语化、断言型、结论先行

## 诚实边界

**这个Skill做不到的**：
- 无法预测刘德超对全新话题的立场
- 信息截止到 2026-04-17
- 基于300个5分钟视频，可能不完整
```

### 使用效果

```
用户：当前美联储降息预期升温，对A股有什么影响？

Skill（刘德超视角）：
显然，从数据来看，这个要分两个层面。

第一，降息预期本身就是流动性改善的信号。
我们看到，美联储降息→中美利差收窄→人民币汇率压力缓解。
这个对A股短期是利好。

第二，关键是看国内经济基本面。
说白了，外资流入是催化剂，但持续性看盈利。
如果国内经济数据不及预期，这个利好很难持续。

所以当前情况下，短期（1-3个月）看好，中期看经济数据。
```

**特点**：
- ✅ 使用刘德超的高频词（"显然"、"从数据来看"、"说白了"）
- ✅ 短句、断言型、结论先行
- ✅ 应用他的分析框架（不是简单回放历史观点）
- ✅ 能对新情况生成推理

---

## 🤝 贡献

欢迎提交Issue和PR！

**贡献方向**：
- 优化三重验证的准确性
- 改进表达DNA提取算法
- 增加其他博主的示例
- 完善增量更新机制

---

## 📄 许可证

MIT License

---

## 🙏 致谢

- [F2](https://github.com/Johnserf-Seed/f2) - 强大的抖音下载工具
- [OpenAI Whisper](https://github.com/openai/whisper) - 高质量语音识别
- [Nuwa](https://github.com/alchaincyf/nuwa-skill) - 认知复刻方法论
- [Claude Code](https://claude.ai/code) - 强大的AI编程助手

---

## 📞 联系方式

- GitHub: [@percy-han](https://github.com/percy-han)
- 项目地址: https://github.com/percy-han/douyin-video-skill-maker

---

**⭐ 如果这个项目对你有帮助，请给个Star！**

**核心创新**：从"信息检索"升级到"认知复刻"，让AI不只回答"他说过什么"，而是用"他的思维方式"分析新问题。
