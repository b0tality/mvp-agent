import sys, asyncio
sys.path.insert(0, r'C:\Users\MECHREV\agent\multi_agent_system_v2')

from dotenv import load_dotenv
load_dotenv(r'C:\Users\MECHREV\agent\multi_agent_system\.env', override=True)

import os
from llm import OpenAIAdapter
from schemas import MVPCodeOutput

async def test():
    llm = OpenAIAdapter(
        api_key=os.getenv('LOCAL_LLM_API_KEY'),
        base_url=os.getenv('LOCAL_LLM_BASE_URL'),
        model=os.getenv('LOCAL_LLM_MODEL')
    )

    # 测试generate_structured
    print("测试 generate_structured:")
    try:
        result = await llm.generate_structured(
            "你是一位全栈开发工程师。请生成一个简单的FastAPI应用代码。",
            "需求：待办事项API，支持增删改查",
            MVPCodeOutput
        )
        print("Result type:", type(result))
        print("code_files count:", len(result.code_files))
        for f in result.code_files:
            print("  - %s: %d chars" % (f.path, len(f.content)))
            if len(f.content) < 300:
                print("    Content:", f.content[:200])
    except Exception as e:
        print("Error:", e)
        import traceback
        traceback.print_exc()

asyncio.run(test())
