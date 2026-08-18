import sys, asyncio
sys.path.insert(0, r'C:\Users\MECHREV\agent\multi_agent_system_v2')

from dotenv import load_dotenv
load_dotenv(r'C:\Users\MECHREV\agent\multi_agent_system\.env', override=True)

import os
from llm import OpenAIAdapter
from agents.technical import TechnicalAgent

async def test():
    llm = OpenAIAdapter(
        api_key=os.getenv('LOCAL_LLM_API_KEY'),
        base_url=os.getenv('LOCAL_LLM_BASE_URL'),
        model=os.getenv('LOCAL_LLM_MODEL')
    )

    tech = TechnicalAgent(llm)
    result = await tech.execute(requirements={
        'functional_requirements': [{'id': 'FR-1', 'title': '待办事项CRUD', 'description': '支持增删改查'}]
    })

    print('Status:', result.status)
    print('Error:', result.error)
    if result.data:
        print('Data keys:', list(result.data.keys()))

asyncio.run(test())
