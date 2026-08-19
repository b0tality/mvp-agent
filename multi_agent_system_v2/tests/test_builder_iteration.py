"""
BuilderAgent 迭代模式离线测试（fake client 脚本化 tool_calls，工具走真实执行器）

验证 ③b 新增的「修复迭代」路径：
1. 从上一版代码起跑（seed current_code/current_test_files/project_name）
2. LLM 只重传 code_files 时，test_files 不被清空（merge 语义）
3. 修完后 run_tests 真实跑出 all_passed=true
"""

import sys
import asyncio
import json

sys.path.insert(0, r'C:\Users\MECHREV\agent\multi_agent_system_v2')

from llm import OpenAIAdapter
from agents.builder import BuilderAgent


# ----------------------------------------------------------------------
# 假 OpenAI client（同 test_builder.py）
# ----------------------------------------------------------------------
class FakeTCFunction:
    def __init__(self, name, arguments):
        self.name = name
        self.arguments = arguments


class FakeToolCall:
    def __init__(self, call_id, name, arguments):
        self.id = call_id
        self.type = "function"
        self.function = FakeTCFunction(name, arguments)


class FakeMessage:
    def __init__(self, content=None, tool_calls=None):
        self.content = content
        self.tool_calls = tool_calls


class FakeChoice:
    def __init__(self, message):
        self.message = message


class FakeResponse:
    def __init__(self, message):
        self.choices = [FakeChoice(message)]


class FakeCompletions:
    def __init__(self, script):
        self.script = list(script)
        self.calls = []

    async def create(self, **kwargs):
        self.calls.append(kwargs)
        i = len(self.calls) - 1
        if i < len(self.script):
            return FakeResponse(self.script[i])
        return FakeResponse(FakeMessage(content="done"))


class FakeChat:
    def __init__(self, script):
        self.completions = FakeCompletions(script)


class FakeClient:
    def __init__(self, script):
        self.chat = FakeChat(script)


BROKEN_MAIN = {
    "path": "main.py",
    "language": "python",
    "content": '''from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "hello"}
''',  # 缺 /health → test_health 会失败
}

FIXED_MAIN = {
    "path": "main.py",
    "language": "python",
    "content": '''from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "hello"}

@app.get("/health")
def health():
    return {"status": "ok"}
''',
}

TEST_API = {
    "path": "tests/test_api.py",
    "language": "python",
    "content": '''from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_root():
    assert client.get("/").status_code == 200

def test_health():
    assert client.get("/health").json() == {"status": "ok"}
''',
}


async def main():
    # 脚本：run_tests(看现状，1 failed) → write_code(只改 code_files) → run_tests(全绿) → 总结
    script = [
        FakeMessage(tool_calls=[FakeToolCall("c1", "run_tests", "{}")]),
        FakeMessage(tool_calls=[FakeToolCall("c2", "write_code", json.dumps({"code_files": [FIXED_MAIN]}))]),
        FakeMessage(tool_calls=[FakeToolCall("c3", "run_tests", "{}")]),
        FakeMessage(content="已修复，测试全过"),
    ]

    llm = OpenAIAdapter(api_key="k", base_url="http://x", model="m")
    llm.client = FakeClient(script)
    builder = BuilderAgent(llm)

    feedback = {"issues": [{"severity": "major", "description": "缺少 /health 端点"}]}

    result = await builder.execute(
        user_input="待办事项 API",
        feedback=feedback,
        current_code=[BROKEN_MAIN],
        current_test_files=[TEST_API],
        project_name="demo",
        iteration=1,
    )

    assert result.status == "success", f"status={result.status} err={result.error}"
    # 1) 代码已被修复（content 含 /health）
    assert len(result.data["code_files"]) == 1, f"code_files={result.data['code_files']}"
    assert "/health" in result.data["code_files"][0]["content"], "修复后应包含 /health"
    # 2) 测试文件未被清空（merge 语义）
    assert len(result.data["test_files"]) == 1, f"test_files={result.data['test_files']}"
    # 3) project_name 保留
    assert result.data["project_name"] == "demo", result.data["project_name"]
    # 4) 修复后 run_tests 真实全绿
    tr = result.data["test_result"]
    assert tr["all_passed"] is True and tr["passed"] == 2, f"test_result={tr}"
    assert result.data["final_text"] == "已修复，测试全过"

    print("[PASS] BuilderAgent 迭代模式: seed 起跑 + merge 保测试 + 定点修复全绿")


if __name__ == "__main__":
    asyncio.run(main())
