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
    req = RequirementsAgent(llm)
    req_result = await req.execute(user_input='开发一个待办事项应用')
    print('Requirements status:', req_result.status)
    print('Requirements data type:', type(req_result.data))
    print('Requirements data keys:', list(req_result.data.keys()))

    # 2. Technical - 用requirements的data作为输入
    tech = TechnicalAgent(llm)
    tech_result = await tech.execute(requirements=req_result.data)
    print('\nTechnical status:', tech_result.status)
    print('Technical error:', tech_result.error)
    if tech_result.data:
        print('Technical data keys:', list(tech_result.data.keys()))

asyncio.run(test())
