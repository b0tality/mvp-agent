import sys, asyncio
sys.path.insert(0, r'C:\Users\MECHREV\agent\multi_agent_system_v2')

from dotenv import load_dotenv
load_dotenv(r'C:\Users\MECHREV\agent\multi_agent_system\.env', override=True)

import os
from llm import OpenAIAdapter
from agents.requirements import RequirementsAgent
from agents.technical import TechnicalAgent
from agents.mvp import MVPAgent

async def test():
    llm = OpenAIAdapter(
        api_key=os.getenv('LOCAL_LLM_API_KEY'),
        base_url=os.getenv('LOCAL_LLM_BASE_URL'),
        model=os.getenv('LOCAL_LLM_MODEL')
    )

    # 1. Requirements
    print('=== Requirements ===')
    req = RequirementsAgent(llm)
    req_result = await req.execute(user_input='开发一个计算器')
    print(f'Status: {req_result.status}')
    print(f'Data keys: {list(req_result.data.keys())}')

    # 2. Technical
    print('\n=== Technical ===')
    tech = TechnicalAgent(llm)
    tech_result = await tech.execute(requirements=req_result.data)
    print(f'Status: {tech_result.status}')
    print(f'Data keys: {list(tech_result.data.keys())}')

    # 3. MVP
    print('\n=== MVP ===')
    mvp = MVPAgent(llm)
    mvp_result = await mvp.execute(
        technical_solution=tech_result.data,
        requirements=req_result.data
    )
    print(f'Status: {mvp_result.status}')
    print(f'Data keys: {list(mvp_result.data.keys())}')
    print(f'Code files: {len(mvp_result.data.get("code_files", []))}')
    print(f'Test files: {len(mvp_result.data.get("test_files", []))}')

    # 检查code_files内容
    for f in mvp_result.data.get("code_files", []):
        path = f.get("path", "?")
        content_len = len(f.get("content", ""))
        print(f'  - {path}: {content_len} chars')

asyncio.run(test())
