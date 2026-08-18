import sys, asyncio
sys.path.insert(0, r'C:\Users\MECHREV\agent\multi_agent_system_v2')

from dotenv import load_dotenv
load_dotenv(r'C:\Users\MECHREV\agent\multi_agent_system\.env', override=True)

import os
from llm import OpenAIAdapter
from agents.requirements import RequirementsAgent

async def test():
    llm = OpenAIAdapter(
        api_key=os.getenv('LOCAL_LLM_API_KEY'),
        base_url=os.getenv('LOCAL_LLM_BASE_URL'),
        model=os.getenv('LOCAL_LLM_MODEL')
    )

    req = RequirementsAgent(llm)
    result = await req.execute(user_input='开发一个待办事项应用')

    print('Status:', result.status)
    print('Error:', result.error)
    print('Data keys:', list(result.data.keys()))

asyncio.run(test())
