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

    # 测试_generate_code的逻辑
    requirements = {'functional_requirements': [{'id': 'FR-1', 'title': '待办事项CRUD', 'description': '支持增删改查'}]}
    tech_stack = {'backend': 'Python/FastAPI', 'database': 'SQLite'}
    api_design = {}
    db_design = {}

    print("调用 generate_structured:")
    try:
        result = await llm.generate_structured(
            """你是一位资深全栈开发工程师。请根据需求和技术栈生成MVP代码。

要求：
1. 必须生成至少2-3个代码文件（如main.py, models.py, routes.py）
2. 每个文件必须包含完整的可运行代码
3. 代码使用指定的技术栈
4. 生成requirements.txt或package.json等依赖文件
5. 项目名称使用小写字母和下划线
6. 确保代码语法正确，没有缩进错误""",
            f"""需求：{requirements}
技术栈：{tech_stack}
API设计：{api_design}
数据库设计：{db_design}

请生成完整的MVP代码，包含所有必要的文件。""",
            MVPCodeOutput,
        )
        
        print("Result type:", type(result))
        print("code_files:", len(result.code_files))
        for f in result.code_files:
            print("  - %s: %d chars" % (f.path, len(f.content)))
        
        data = result.model_dump()
        print("data[code_files]:", len(data.get("code_files", [])))
        
    except Exception as e:
        print("Error:", e)
        import traceback
        traceback.print_exc()

asyncio.run(test())
