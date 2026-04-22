#!/usr/bin/env python3
"""
仅生成SKILL_APPENDIX.md（从已有的cognitive_synthesis.json）

使用方法:
python generate_appendix_only.py /path/to/cognitive_synthesis.json /path/to/output_SKILL_APPENDIX.md
"""

import json
import sys
import os


def generate_appendix(synthesis: dict, output_path: str):
    """生成深度研究补充文档（完整验证细节）"""

    print("\n📚 生成深度研究补充文档...")

    appendix = f"""# 刘德超认知框架 - 深度研究补充文档

> 本文档包含所有心智模型和决策启发式的完整验证细节、置信度评分、视频溯源

**生成时间**: {synthesis['metadata']['synthesis_date']}
**数据范围**: {synthesis['metadata']['date_range']['start']} ~ {synthesis['metadata']['date_range']['end']}
**视频总数**: {synthesis['metadata']['total_videos']}

---

## 📊 统计概览

- **心智模型**: {len(synthesis['mental_models'])} 个
- **决策启发式**: {len(synthesis['heuristics'])} 条
- **平均置信度**: {sum(m['validation'].get('confidence', 0) for m in synthesis['mental_models'])/len(synthesis['mental_models']):.3f}

---

## 🧠 完整心智模型列表（按置信度排序）

"""

    # 按置信度排序
    sorted_models = sorted(
        synthesis['mental_models'],
        key=lambda x: x['validation'].get('confidence', 0),
        reverse=True
    )

    for i, model in enumerate(sorted_models, 1):
        validation = model['validation']
        evidence = validation.get('evidence', {})

        appendix += f"""
### {i}. {model['pattern']}

**置信度**: {validation.get('confidence', 0):.3f}

**三重验证详情**:

1. **跨域复现** (Cross-Domain)
   - 复现次数: {evidence.get('cross_domain', {}).get('occurrence_count', 0)} 次
   - 涉及领域: {', '.join(evidence.get('cross_domain', {}).get('domains', [])[:10])}
   - 领域数量: {len(evidence.get('cross_domain', {}).get('domains', []))}

2. **生成力** (Generative Power)
   - 预测能力: {evidence.get('generative_power', {}).get('can_predict_stance', False)}
   - 应用场景: {evidence.get('generative_power', {}).get('example_predictions', '未提供')}

3. **排他性** (Distinctiveness)
   - 独特视角: {evidence.get('distinctiveness', {}).get('is_unique_perspective', False)}
   - 差异说明: {evidence.get('distinctiveness', {}).get('differentiation', '未提供')}

**典型引用**:
"""
        for j, quote in enumerate(model['quotes'][:10], 1):
            appendix += f"{j}. {quote}\n"

        appendix += "\n---\n"

    # 决策启发式部分
    appendix += "\n## 📋 完整决策启发式列表\n\n"

    sorted_heuristics = sorted(
        synthesis['heuristics'],
        key=lambda x: x.get('validation', {}).get('confidence', 0),
        reverse=True
    )

    for i, heuristic in enumerate(sorted_heuristics, 1):
        validation = heuristic.get('validation', {})

        appendix += f"""
### {i}. {heuristic['pattern']}

**置信度**: {validation.get('confidence', 0):.3f}

**验证证据**:
- 复现次数: {validation.get('evidence', {}).get('cross_domain', {}).get('occurrence_count', 0)}
- 涉及领域: {', '.join(validation.get('evidence', {}).get('cross_domain', {}).get('domains', [])[:5])}

**案例引用**:
"""
        for j, quote in enumerate(heuristic.get('quotes', [])[:5], 1):
            appendix += f"{j}. {quote}\n"

        appendix += "\n---\n"

    # 元数据部分
    appendix += f"""
## 📁 元数据与溯源

### 视频框架统计

- 成功提取: {synthesis['metadata'].get('successful_extractions', 0)} 个
- 提取失败: {synthesis['metadata'].get('failed_extractions', 0)} 个

### 方法论

本框架基于零清洗策略（Zero-Cleaning Strategy）:
- 直接处理原始转录文本（包含口语化表达、停顿词等）
- 使用 Claude Opus 4.7 进行认知信号提取
- 三重验证方法论（跨域、生成力、排他性）

### 数据溯源

完整单视频框架数据: `video_frameworks.json`
完整合成数据: `cognitive_synthesis.json`

---

**文档生成**: {synthesis['metadata']['synthesis_date']}
"""

    # 保存文件
    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(appendix)

    print(f"   ✅ 已保存补充文档: {output_path}")
    print(f"   📄 文件大小: {len(appendix)} 字符")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python generate_appendix_only.py <cognitive_synthesis.json> [output_path]")
        print("\n示例:")
        print("  python generate_appendix_only.py /tmp/skill_output/cognitive_synthesis.json")
        print("  python generate_appendix_only.py cognitive_synthesis.json SKILL_APPENDIX.md")
        sys.exit(1)

    input_file = sys.argv[1]

    if len(sys.argv) >= 3:
        output_file = sys.argv[2]
    else:
        # 默认输出到同目录
        output_file = os.path.join(os.path.dirname(input_file), 'SKILL_APPENDIX.md')

    print(f"📥 加载: {input_file}")
    with open(input_file, 'r', encoding='utf-8') as f:
        synthesis = json.load(f)

    generate_appendix(synthesis, output_file)

    print("\n✅ 完成！")
