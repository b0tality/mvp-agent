"""
诊断MVP code_files为空的根本原因
"""
import sys, asyncio, json
sys.path.insert(0, r'C:\Users\MECHREV\agent\multi_agent_system_v2')

from dotenv import load_dotenv
load_dotenv(r'C:\Users\MECHREV\agent\multi_agent_system\.env', override=True)

import os
from openai import AsyncOpenAI
from schemas import MVPCodeOutput, CodeFile

API_KEY = os.getenv('LOCAL_LLM_API_KEY')
BASE_URL = os.getenv('LOCAL_LLM_BASE_URL')
MODEL = os.getenv('LOCAL_LLM_MODEL')

async def test_raw_json_schema():
    """测试1: 直接调用API，看json_schema模式返回什么"""
    print("=" * 60)
    print("测试1: 直接调用API (json_schema模式)")
    print("=" * 60)

    client = AsyncOpenAI(api_key=API_KEY, base_url=BASE_URL)
    schema = MVPCodeOutput.model_json_schema()

    try:
        response = await client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "生成一个FastAPI待办事项应用的代码。"},
                {"role": "user", "content": "需求：支持增删改查"}
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {"name": "MVPCodeOutput", "schema": schema}
            }
        )
        content = response.choices[0].message.content
        print("Raw response:", content[:1000])
        parsed = json.loads(content)
        print("\nparsed keys:", list(parsed.keys()))
        print("code_files count:", len(parsed.get("code_files", [])))
    except Exception as e:
        print("json_schema FAILED:", e)

async def test_json_object():
    """测试2: 用json_object模式"""
    print("\n" + "=" * 60)
    print("测试2: json_object模式")
    print("=" * 60)

    client = AsyncOpenAI(api_key=API_KEY, base_url=BASE_URL)

    try:
        response = await client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "生成一个FastAPI待办事项应用。返回JSON格式，包含code_files列表，每个元素有path和content字段。"},
                {"role": "user", "content": "需求：支持增删改查"}
            ],
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        print("Raw response:", content[:1000])
        parsed = json.loads(content)
        print("\nparsed keys:", list(parsed.keys()))
        if "code_files" in parsed:
            print("code_files count:", len(parsed["code_files"]))
            for f in parsed["code_files"][:2]:
                print("  - %s: %d chars" % (f.get("path", "?"), len(f.get("content", ""))))
    except Exception as e:
        print("json_object FAILED:", e)

async def test_pydantic_validate():
    """测试3: 用pydantic验证json_object的输出"""
    print("\n" + "=" * 60)
    print("测试3: json_object + pydantic验证")
    print("=" * 60)

    client = AsyncOpenAI(api_key=API_KEY, base_url=BASE_URL)

    try:
        response = await client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": """生成一个FastAPI待办事项应用的代码。
返回JSON格式：
{
  "code_files": [
    {"path": "main.py", "content": "完整代码内容", "language": "python"},
    {"path": "requirements.txt", "content": "依赖内容", "language": "text"}
  ],
  "test_files": [],
  "docker_config": {},
  "project_name": "todo_app"
}"""},
                {"role": "user", "content": "需求：支持增删改查"}
            ],
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        print("Raw response length:", len(content))

        # 用pydantic验证
        result = MVPCodeOutput.model_validate_json(content)
        print("code_files count:", len(result.code_files))
        for f in result.code_files[:2]:
            print("  - %s: %d chars" % (f.path, len(f.content)))

    except Exception as e:
        print("FAILED:", e)

asyncio.run(test_raw_json_schema())
asyncio.run(test_json_object())
asyncio.run(test_pydantic_validate())
