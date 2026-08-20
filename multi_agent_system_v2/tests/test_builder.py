"""
BuilderAgent 离线测试（fake client 脚本化 LLM 的 tool_calls，但工具 handler 走真实执行器）

验证 agentic 循环的状态流转：
write_code → verify_code → run_tests（真实 pytest）→ 最终回答，
且 builder 的 code_files/test_files/project_name/test_result 都正确落位。
"""

import sys
import asyncio
import json

sys.path.insert(0, r'C:\Users\MECHREV\agent\multi_agent_system_v2')

from llm import OpenAIAdapter
from agents.builder import BuilderAgent


# ----------------------------------------------------------------------
# 假 OpenAI client
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


MAIN_PY = {
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

REQ_TXT = {
    "path": "requirements.txt",
    "language": "text",
    "content": "fastapi>=0.104\nuvicorn>=0.24\npytest>=7\nhttpx>=0.24\n",
}

TEST_API_PY = {
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
    write_args = json.dumps({
        "code_files": [MAIN_PY, REQ_TXT],
        "test_files": [TEST_API_PY],
        "project_name": "demo",
    })
    script = [
        FakeMessage(tool_calls=[FakeToolCall("c1", "write_code", write_args)]),
        FakeMessage(tool_calls=[FakeToolCall("c2", "verify_code", "{}")]),
        FakeMessage(tool_calls=[FakeToolCall("c3", "run_tests", "{}")]),
        FakeMessage(content="完成，测试全过"),
    ]

    llm = OpenAIAdapter(api_key="k", base_url="http://x", model="m")
    llm.client = FakeClient(script)
    builder = BuilderAgent(llm)

    result = await builder.execute(user_input="待办事项 API")

    assert result.status == "success", f"status={result.status} err={result.error}"
    assert len(result.data["code_files"]) == 2, f"code_files={len(result.data['code_files'])}"
    assert len(result.data["test_files"]) == 1, f"test_files={len(result.data['test_files'])}"
    assert result.data["project_name"] == "demo", result.data["project_name"]
    assert result.data["verify_result"].get("passed") is True, result.data["verify_result"]
    tr = result.data["test_result"]
    assert tr["all_passed"] is True and tr["passed"] == 2, f"test_result={tr}"
    assert result.data["final_text"] == "完成，测试全过"

    print("[PASS] BuilderAgent: write_code → verify_code → run_tests(真实执行) 状态流转正确")


def test_empty_output_fallback():
    """第一轮 LLM 只吐文字不调 write_code（DeepSeek 偶发）→ 兜底重试一次并勒令调用工具。"""
    write_args = json.dumps({
        "code_files": [MAIN_PY, REQ_TXT],
        "test_files": [TEST_API_PY],
        "project_name": "demo",
    })
    script = [
        FakeMessage(content="好的，我来实现这个接口。"),  # 第 1 轮：空产出（未调 write_code）
        FakeMessage(tool_calls=[FakeToolCall("c1", "write_code", write_args)]),  # 兜底重试 → 产出
        FakeMessage(content="完成"),
    ]

    llm = OpenAIAdapter(api_key="k", base_url="http://x", model="m")
    llm.client = FakeClient(script)
    builder = BuilderAgent(llm)

    async def run():
        return await builder.execute(user_input="待办事项 API")

    result = asyncio.run(run())

    assert result.status == "success", f"status={result.status} err={result.error}"
    assert len(result.data["code_files"]) == 2, result.data.get("code_files")
    # 确认兜底真的走了第二轮 generate_with_tools，且 user prompt 里带了勒令调工具的提醒
    second_user = llm.client.chat.completions.calls[1]["messages"][1]["content"]
    assert "上一轮你没有调用 write_code" in second_user, second_user
    print("[PASS] BuilderAgent: 空产出兜底——第一轮未调 write_code 时重试并勒令调用工具")


if __name__ == "__main__":
    asyncio.run(main())
    test_empty_output_fallback()
