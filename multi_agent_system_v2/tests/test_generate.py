import sys, asyncio
sys.path.insert(0, r'C:\Users\MECHREV\agent\multi_agent_system_v2')

from dotenv import load_dotenv
load_dotenv(r'C:\Users\MECHREV\agent\multi_agent_system\.env', override=True)

import os
from llm import OpenAIAdapter

async def test():
    llm = OpenAIAdapter(
        api_key=os.getenv('LOCAL_LLM_API_KEY'),
        base_url=os.getenv('LOCAL_LLM_BASE_URL'),
        model=os.getenv('LOCAL_LLM_MODEL')
    )

    # 测试generate
    print("测试 generate:")
    result = await llm.generate(
        "你是一位全栈开发工程师。",
        "生成一个FastAPI应用的main.py文件，支持待办事项CRUD。只输出代码，不要解释。"
    )
    print("Result length:", len(result))
    print("Content:")
    print(result[:500])

asyncio.run(test())
