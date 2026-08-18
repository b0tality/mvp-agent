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

    # 测试1: 简单prompt
    print("=== 测试1: 简单prompt ===")
    result1 = await llm.generate(
        "你是一位全栈开发工程师。请生成一个FastAPI应用的main.py文件内容。",
        "需求：待办事项API，支持增删改查"
    )
    print("Result length:", len(result1))
    print("Content:", result1[:300])

    # 测试2: 结构化输出（简短prompt）
    print("\n=== 测试2: 结构化输出 ===")
    
    from pydantic import BaseModel
    from typing import List
    
    class SimpleCodeOutput(BaseModel):
        code_files: List[dict]
    
    result2 = await llm.generate_structured(
        "生成代码文件，返回JSON格式",
        "需求：待办事项API",
        SimpleCodeOutput
    )
    print("Result:", result2)
    print("code_files:", len(result2.code_files))

asyncio.run(test())
