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
    result = await mvp.execute(
        technical_solution={'tech_stack': {'backend': 'Python/FastAPI', 'database': 'SQLite'}},
        requirements={'functional_requirements': [{'id': 'FR-1', 'title': '待办事项CRUD', 'description': '支持增删改查'}]}
    )

    print('Status:', result.status)
    code_files = result.data.get('code_files', [])
    print('Code files:', len(code_files))
    for f in code_files:
        path = f.get('path', '?')
        content = f.get('content', '')
        print('  - %s: %d chars' % (path, len(content)))
        if len(content) < 500:
            print('    Content:', content[:200])

asyncio.run(test())
