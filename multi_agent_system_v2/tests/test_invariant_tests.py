"""
确定性不变式测试生成器（非 LLM）离线验证

用带 response_model 的 FastAPI 待办应用，复现评估里发现的 next_id bug：
作者自测只断言列表长度，漏了「id 唯一」。验证：
1. generate_invariant_tests 能从 OpenAPI 契约机械推导出 id 唯一性测试（不含 LLM）。
2. 该测试真实运行时能抓到 next_id bug（相对断言，不受状态累积影响）。
3. 修复后通过。
"""

import sys
import asyncio

sys.path.insert(0, r'C:\Users\MECHREV\agent\multi_agent_system_v2')

from tools.invariant_tests import generate_invariant_tests
from tools.executors import run_tests


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


def test_generator_derives_id_unique_without_llm():
    inv = generate_invariant_tests([BUGGY_MAIN])
    assert "test_invariant_id_unique" in inv, inv
    # 确定性生成，不含 LLM 的自由发挥：一定包含计数一致性，且不含任何解释文字
    assert "test_invariant_count_consistent" in inv, inv
    assert "```" not in inv


AUTH_MAIN = {
    "path": "main.py", "language": "python",
    "content": '''from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI()
users = {}
next_id = 1

class Register(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=8)
    email: str = Field(pattern=r".+@.+\\..+")

@app.post("/api/register", status_code=201)
def register(r: Register):
    global next_id
    if r.username in users:
        return {"detail": "exists"}
    users[r.username] = {"id": next_id, "username": r.username}
    next_id += 1
    return users[r.username]

@app.get("/api/users/me")
def me():
    return {"id": 1}
''',
}


def test_invariant_skips_non_collection_resource():
    """无「GET 列表」的端点（register/login/auth）不套不变式——宁可少测，不误报。

    这类端点有唯一键约束（重复注册返回 409 而非新 id）、无列表、无 DELETE，
    强套 id 唯一/计数一致会误报。generate_invariant_tests 应整体跳过返回空串。
    """
    inv = generate_invariant_tests([AUTH_MAIN])
    assert inv == "", f"auth 风格端点应跳过不变式，却生成了：{inv!r}"


def test_invariant_catches_id_bug():
    inv = generate_invariant_tests([BUGGY_MAIN])
    data = asyncio.run(run_tests(
        [BUGGY_MAIN],
        [{"path": "tests/test_invariants.py", "content": inv, "language": "python"}],
    ))
    assert data["all_passed"] is False, data
    assert any("test_invariant_id_unique" in (b.get("description") or "") for b in data["bugs"]), data["bugs"]


def test_invariant_passes_fixed_code():
    inv = generate_invariant_tests([FIXED_MAIN])
    data = asyncio.run(run_tests(
        [FIXED_MAIN],
        [{"path": "tests/test_invariants.py", "content": inv, "language": "python"}],
    ))
    assert data["all_passed"] is True, data


if __name__ == "__main__":
    test_generator_derives_id_unique_without_llm()
    test_invariant_catches_id_bug()
    test_invariant_passes_fixed_code()
    test_invariant_skips_non_collection_resource()
    print("[PASS] 确定性不变式测试: 从 OpenAPI 机械推导 + 抓到 next_id bug + 修复后通过 + auth 端点跳过")
