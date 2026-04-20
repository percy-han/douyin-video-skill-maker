#!/usr/bin/env python3
"""
检查AWS Bedrock可用的Claude模型

使用方法:
python check_bedrock_models.py
"""

import boto3
import json

def check_available_models():
    """列出所有可用的Claude模型"""

    print("🔍 检查AWS Bedrock可用的Claude模型...")
    print("="*80)

    try:
        bedrock = boto3.client('bedrock', region_name='us-east-1')

        # 列出所有基础模型
        response = bedrock.list_foundation_models()

        claude_models = []
        for model in response['modelSummaries']:
            model_id = model['modelId']

            # 只显示Claude模型
            if 'claude' in model_id.lower():
                claude_models.append({
                    'modelId': model_id,
                    'modelName': model.get('modelName', 'N/A'),
                    'providerName': model.get('providerName', 'N/A'),
                    'status': 'ACTIVE' if model.get('modelLifecycle', {}).get('status') == 'ACTIVE' else 'LEGACY'
                })

        if not claude_models:
            print("❌ 没有找到可用的Claude模型")
            print("\n可能原因:")
            print("1. AWS区域不正确（应该使用us-east-1）")
            print("2. 账户权限不足")
            print("3. Bedrock未启用")
            return

        # 按状态和名称排序
        claude_models.sort(key=lambda x: (x['status'], x['modelName']))

        print(f"找到 {len(claude_models)} 个Claude模型:\n")

        # 分组显示
        active_models = [m for m in claude_models if m['status'] == 'ACTIVE']
        legacy_models = [m for m in claude_models if m['status'] == 'LEGACY']

        if active_models:
            print("✅ **活跃模型** (推荐使用):")
            print("-" * 80)
            for model in active_models:
                print(f"  模型名: {model['modelName']}")
                print(f"  Model ID: {model['modelId']}")
                print(f"  提供商: {model['providerName']}")
                print()

        if legacy_models:
            print("⚠️  **过时模型** (需要重新激活):")
            print("-" * 80)
            for model in legacy_models:
                print(f"  模型名: {model['modelName']}")
                print(f"  Model ID: {model['modelId']}")
                print(f"  提供商: {model['providerName']}")
                print()

        # 推荐配置
        print("="*80)
        print("📝 **推荐配置**:\n")

        if active_models:
            # 找Opus 4
            opus_models = [m for m in active_models if 'opus' in m['modelName'].lower() and '4' in m['modelName']]
            if opus_models:
                recommended = opus_models[0]
                print(f"使用Claude Opus 4 (最强模型):")
                print(f"export BEDROCK_MODEL_ID={recommended['modelId']}")
            else:
                # 找Sonnet 4
                sonnet_models = [m for m in active_models if 'sonnet' in m['modelName'].lower() and '4' in m['modelName']]
                if sonnet_models:
                    recommended = sonnet_models[0]
                    print(f"使用Claude Sonnet 4 (次强模型):")
                    print(f"export BEDROCK_MODEL_ID={recommended['modelId']}")
                else:
                    recommended = active_models[0]
                    print(f"使用第一个可用模型:")
                    print(f"export BEDROCK_MODEL_ID={recommended['modelId']}")
        else:
            print("❌ 没有活跃模型可用！")
            print("\n请在AWS Bedrock控制台激活模型:")
            print("https://console.aws.amazon.com/bedrock/home?region=us-east-1#/modelaccess")

    except Exception as e:
        print(f"❌ 检查失败: {e}")
        print("\n可能的解决方案:")
        print("1. 检查AWS凭证: aws sts get-caller-identity")
        print("2. 检查区域配置: export AWS_DEFAULT_REGION=us-east-1")
        print("3. 检查IAM权限: bedrock:ListFoundationModels")

def test_model_access(model_id: str):
    """测试能否访问指定模型"""

    print(f"\n🧪 测试模型访问: {model_id}")
    print("-" * 80)

    try:
        bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-east-1')

        # 发送一个简单的测试请求
        response = bedrock_runtime.invoke_model(
            modelId=model_id,
            body=json.dumps({
                'anthropic_version': 'bedrock-2023-05-31',
                'max_tokens': 10,
                'messages': [
                    {'role': 'user', 'content': 'Hello'}
                ]
            })
        )

        result = json.loads(response['body'].read())
        print(f"✅ 模型可用！")
        print(f"   测试响应: {result['content'][0]['text'][:50]}...")
        return True

    except Exception as e:
        print(f"❌ 模型不可用: {e}")
        return False

if __name__ == '__main__':
    check_available_models()

    # 如果用户提供了model ID参数，测试访问
    import sys
    if len(sys.argv) > 1:
        model_id = sys.argv[1]
        test_model_access(model_id)

    print("\n" + "="*80)
    print("💡 提示:")
    print("   运行 'python check_bedrock_models.py <MODEL_ID>' 测试特定模型")
    print("   例如: python check_bedrock_models.py anthropic.claude-opus-4-20250514-v1:0")
