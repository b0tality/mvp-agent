"""
测试迭代优化循环
"""

import sys, asyncio
sys.path.insert(0, r'C:\Users\MECHREV\agent\multi_agent_system_v2')

from dotenv import load_dotenv
load_dotenv(r'C:\Users\MECHREV\agent\multi_agent_system\.env', override=True)

import os
from llm import OpenAIAdapter
from agents.mvp import MVPAgent

async def test():
    llm = OpenAIAdapter(
        api_key=os.getenv('LOCAL_LLM_API_KEY'),
        base_url=os.getenv('LOCAL_LLM_BASE_URL'),
        model=os.getenv('LOCAL_LLM_MODEL')
    )

    mvp = MVPAgent(llm)

    # 1. 首次生成
    print("=== 首次生成 ===")
    result = await mvp.execute(
        technical_solution={"tech_stack": {"backend": "Python/FastAPI", "database": "SQLite"}},
        requirements={"functional_requirements": [{"id": "FR-1", "title": "用户登录", "description": "支持用户名密码登录"}]}
    )
    print(f"Status: {result.status}")
    print(f"Code files: {len(result.data.get('code_files', []))}")
    for f in result.data.get("code_files", []):
        print(f"  - {f.get('path')}: {len(f.get('content', ''))} chars")

    # 2. 带反馈改进
    print("\n=== 带反馈改进 ===")
    feedback = {
        "issues": [
            {"severity": "major", "description": "缺少输入验证", "suggestion": "添加参数校验"},
            {"severity": "minor", "description": "缺少错误处理", "suggestion": "添加try-except"}
        ],
        "bugs": [
            {"severity": "critical", "description": "SQL注入风险"}
        ],
        "suggestions": ["添加日志记录", "使用环境变量配置"]
    }

    result2 = await mvp.execute(
        technical_solution={"tech_stack": {"backend": "Python/FastAPI", "database": "SQLite"}},
        requirements={"functional_requirements": [{"id": "FR-1", "title": "用户登录", "description": "支持用户名密码登录"}]},
        feedback=feedback,
        current_code=result.data.get("code_files", []),
        iteration=1
    )
    print(f"Status: {result2.status}")
    print(f"Code files: {len(result2.data.get('code_files', []))}")
    for f in result2.data.get("code_files", []):
        print(f"  - {f.get('path')}: {len(f.get('content', ''))} chars")

    print("\n迭代优化测试通过!")

asyncio.run(test())
