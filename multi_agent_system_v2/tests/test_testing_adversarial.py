"""
TestingAgent 集成测试：确定性不变式测试已接入（非 LLM）

复现评估里发现的 next_id bug，验证 TestingAgent.execute 现在会：
1. 自动从 OpenAPI 契约生成不变式测试（无需 LLM 调用）。
2. 真实运行时抓到 id 唯一性 bug（all_passed=False）。
3. 修复后通过（all_passed=True）。

（原「LLM 对抗测试」已移除，被这条确定性路径取代；见 tools/invariant_tests.py）
"""

import sys
import asyncio

sys.path.insert(0, r'C:\Users\MECHREV\agent\multi_agent_system_v2')

from agents.testing import TestingAgent


BUGGY_MAIN = {
    "path": "main.py", "language": "python",
    "content": '''from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()
todos = []
next_id = 1

class TodoCreate(BaseModel):
    title: str

class TodoResponse(BaseModel):
    id: int
    title: str

@app.post("/todo", status_code=201, response_model=TodoResponse)
def create(todo: TodoCreate):
    todos.append({"id": next_id, "title": todo.title})  # BUG: 没有 next_id += 1
    return todos[-1]

@app.get("/todo", response_model=list[TodoResponse])
def list_todos():
    return todos
''',
}

FIXED_MAIN = {
    "path": "main.py", "language": "python",
    "content": '''from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()
todos = []
next_id = 1

class TodoCreate(BaseModel):
    title: str

class TodoResponse(BaseModel):
    id: int
    title: str

@app.post("/todo", status_code=201, response_model=TodoResponse)
def create(todo: TodoCreate):
    global next_id
    todos.append({"id": next_id, "title": todo.title})
    next_id += 1
    return todos[-1]

@app.get("/todo", response_model=list[TodoResponse])
def list_todos():
    return todos
''',
}


class DummyLLM:
    """不变式测试是确定性的，不应再调用 LLM；一旦调用即视为回归。"""
    async def generate(self, system, user):
        raise AssertionError("LLM 对抗测试已移除，TestingAgent 不应调用 generate")


async def _run(code_files):
    agent = TestingAgent(DummyLLM())
    result = await agent.execute(code_files=code_files, test_files=[])
    assert result.status == "success", result.error
    return result.data


def test_invariant_catches_id_bug():
    data = asyncio.run(_run([BUGGY_MAIN]))
    assert data["all_passed"] is False, data
    assert any("test_invariant_id_unique" in (b.get("description") or "") for b in data["bugs"]), data["bugs"]


def test_invariant_passes_fixed_code():
    data = asyncio.run(_run([FIXED_MAIN]))
    assert data["all_passed"] is True, data
    assert data.get("invariants_generated") is True, data


if __name__ == "__main__":
    test_invariant_catches_id_bug()
    test_invariant_passes_fixed_code()
    print("[PASS] TestingAgent 集成: 确定性不变式测试接入 + 抓 next_id bug + 修复后通过")
