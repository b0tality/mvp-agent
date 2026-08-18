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
    
    agent = RequirementsAgent(llm)
    result = await agent.execute(user_input='开发一个待办事项应用')
    
    print('Status:', result.status)
    print('Agent used:', result.agent_used)
    print('Duration:', round(result.duration_seconds, 1), 's')
    print('Error:', result.error)
    print()
    print('Data keys:', list(result.data.keys()))
    print('Functional requirements:', len(result.data.get('functional_requirements', [])))
    print('User stories:', len(result.data.get('user_stories', [])))
    print('Acceptance criteria:', len(result.data.get('acceptance_criteria', [])))
    
    print()
    print('--- Sample requirements ---')
    for req in result.data.get('functional_requirements', [])[:3]:
        rid = req.get('id', '?')
        title = req.get('title', '?')
        desc = req.get('description', '')[:60]
        print('  [%s] %s: %s...' % (rid, title, desc))

asyncio.run(test())
