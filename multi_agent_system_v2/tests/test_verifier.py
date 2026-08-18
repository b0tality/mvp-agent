import sys, asyncio
sys.path.insert(0, r'C:\Users\MECHREV\agent\multi_agent_system_v2')

from tools.mvp_tools import CodeVerifierTool

async def test():
    verifier = CodeVerifierTool(llm=None)

    # 测试1: 语法正确的代码
    print("=== 测试1: 语法正确 ===")
    result1 = await verifier.run(code_files=[
        {"path": "main.py", "content": "from fastapi import FastAPI\napp = FastAPI()\n@app.get('/')\ndef root():\n    return {'msg': 'ok'}\n", "language": "python"}
    ])
    print(f"Passed: {result1['passed']}")
    print(f"Errors: {len(result1['errors'])}")

    # 测试2: 语法错误的代码
    print("\n=== 测试2: 语法错误 ===")
    result2 = await verifier.run(code_files=[
        {"path": "main.py", "content": "from fastapi import FastAPI\napp = FastAPI()\ndef root(\n    return {'msg': 'ok'}\n", "language": "python"}
    ])
    print(f"Passed: {result2['passed']}")
    print(f"Errors: {len(result2['errors'])}")
    for err in result2['errors']:
        print(f"  - {err['file']}:{err.get('line', '?')} [{err['type']}] {err['message']}")

    # 测试3: 缩进错误
    print("\n=== 测试3: 缩进错误 ===")
    result3 = await verifier.run(code_files=[
        {"path": "main.py", "content": "def foo():\nprint('hello')\n", "language": "python"}
    ])
    print(f"Passed: {result3['passed']}")
    print(f"Errors: {len(result3['errors'])}")
    for err in result3['errors']:
        print(f"  - {err['file']}:{err.get('line', '?')} [{err['type']}] {err['message']}")

    print("\n编译验证工具测试通过!")

asyncio.run(test())
