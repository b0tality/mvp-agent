import sys, asyncio
sys.path.insert(0, r'C:\Users\MECHREV\agent\multi_agent_system_v2')

from dotenv import load_dotenv
load_dotenv(r'C:\Users\MECHREV\agent\multi_agent_system\.env', override=True)

import os
from llm import OpenAIAdapter
from agents.requirements import RequirementsAgent
from agents.technical import TechnicalAgent

async def test():
    llm = OpenAIAdapter(
        api_key=os.getenv('LOCAL_LLM_API_KEY'),
        base_url=os.getenv('LOCAL_LLM_BASE_URL'),
        model=os.getenv('LOCAL_LLM_MODEL')
    )

    # 1. Requirements
    print('=== Requirements ===')
    req_agent = RequirementsAgent(llm)
    req_result = await req_agent.execute(user_input='开发一个待办事项应用')
    print(f'Status: {req_result.status}, Duration: {req_result.duration_seconds:.1f}s')

    if req_result.status != 'success':
        print('Requirements failed:', req_result.error)
        return

    # 2. Technical
    print('\n=== Technical ===')
    tech_agent = TechnicalAgent(llm)
    tech_result = await tech_agent.execute(requirements=req_result.data)
    print(f'Status: {tech_result.status}, Duration: {tech_result.duration_seconds:.1f}s')

    if tech_result.status != 'success':
        print('Technical failed:', tech_result.error)
        return

    print('\nAll passed!')

asyncio.run(test())
