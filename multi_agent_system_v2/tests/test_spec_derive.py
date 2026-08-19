"""
spec-driven 确定性推导的离线验证（零 LLM、零联网）

验证 tools/spec_derive.py 两条确定性链：
1. derive_acceptance_tests：从 Spec 机械生成 pytest，纯代码、可复现、不放水。
2. contract_check：真实 import 生成的 app，比对 spec 端点 vs app.openapi() 路径，
   能抓到「builder 漏实现端点」这类设计偏离。
"""

import sys
import asyncio

sys.path.insert(0, r'C:\Users\MECHREV\agent\multi_agent_system_v2')

from schemas.spec import ProjectSpec, EndpointSpec, RuleSpec
from tools.spec_derive import derive_acceptance_tests, contract_check
from tools.executors import run_tests


TODO_MAIN = {
    "path": "main.py",
    "content": '''from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()
todos = []
_next = 1

class Todo(BaseModel):
    title: str

class TodoOut(BaseModel):
    id: int
    title: str

@app.post("/todos", status_code=201, response_model=TodoOut)
def create(t: Todo):
    global _next
    todos.append({"id": _next, "title": t.title})
    _next += 1
    return todos[-1]

@app.get("/todos", response_model=list[TodoOut])
def list_todos():
    return todos

@app.delete("/todos/{todo_id}", status_code=204)
def delete(todo_id: int):
    global todos
    todos = [t for t in todos if t["id"] != todo_id]
    return None
''',
}


def make_spec() -> ProjectSpec:
    return ProjectSpec(
        project_name="todo_spec",
        description="待办事项",
        endpoints=[
            EndpointSpec(method="POST", path="/todos",
                         request_body={"title": "buy milk"}, response_status=201),
            EndpointSpec(method="GET", path="/todos", response_status=200),
            EndpointSpec(method="DELETE", path="/todos/{id}", response_status=204),
        ],
        rules=[
            RuleSpec(description="缺少 title 返回 422", method="POST", path="/todos",
                     request_body={}, expect_status=422),
        ],
    )


def test_derive_acceptance_deterministic():
    spec = make_spec()
    code = derive_acceptance_tests(spec)
    assert "test_endpoint_0_" in code, code
    assert "test_rule_0" in code, code
    assert "```" not in code, "纯代码，不应有 markdown"
    # 确定性：再生成一次应逐字节一致（这是「推导」而非「翻译」的判据）
    assert derive_acceptance_tests(spec) == code


def test_contract_check_matches():
    spec = make_spec()
    r = contract_check(spec, [TODO_MAIN])
    assert r["match"] is True, r
    assert r["missing"] == [] and r["extra"] == [], r


def test_contract_check_detects_missing_endpoint():
    spec = make_spec()
    # builder 漏实现了 spec 里的 PUT 端点 → 契约校验必须抓到
    spec.endpoints.append(EndpointSpec(
        method="PUT", path="/todos/{id}",
        request_body={"title": "x"}, response_status=200,
    ))
    r = contract_check(spec, [TODO_MAIN])
    assert r["match"] is False, r
    assert any("PUT" in m for m in r["missing"]), r


def test_derived_acceptance_runs_green():
    """推导出的验收测试对正确实现应真实跑绿。"""
    spec = make_spec()
    acc = derive_acceptance_tests(spec)
    data = asyncio.run(run_tests(
        [TODO_MAIN],
        [{"path": "tests/test_acceptance.py", "content": acc, "language": "python"}],
    ))
    assert data["all_passed"] is True, data


# ---------------------------------------------------------------------------
# query 参数修复：查询参数走 query_params 字段，不拼进 path
# ---------------------------------------------------------------------------

TASKS_MAIN = {
    "path": "main.py",
    "content": '''from fastapi import FastAPI
from typing import Optional

app = FastAPI()

@app.get("/tasks")
def list_tasks(priority: Optional[str] = None):
    return []
''',
}


def test_derive_acceptance_emits_query_params():
    """query_params 字段应生成 client.get(path, params=...) 而非拼进 path。"""
    spec = ProjectSpec(project_name="tasks", endpoints=[
        EndpointSpec(method="GET", path="/tasks",
                     query_params={"priority": "high"}, response_status=200),
    ])
    code = derive_acceptance_tests(spec)
    assert "client.get('/tasks'" in code, code
    assert "params={'priority': 'high'}" in code, code
    assert "?priority" not in code, "查询参数不该拼进 path"


def test_derive_acceptance_does_not_skip_query_path():
    """path 里偶发混入 ?query={x} 时，不该被误判为路径参数而跳过测试。"""
    spec = ProjectSpec(project_name="tasks", endpoints=[
        EndpointSpec(method="GET", path="/tasks?priority={priority}", response_status=200),
    ])
    code = derive_acceptance_tests(spec)
    assert "test_endpoint_0_" in code, "带查询串的端点不应被跳过"
    assert "client.get('/tasks'" in code, code


def test_contract_check_strips_query_from_path():
    """契约校验应把 path 里的查询串剥掉再比（/tasks?priority=x 与 /tasks 视为同一端点）。"""
    spec = ProjectSpec(project_name="tasks", endpoints=[
        EndpointSpec(method="GET", path="/tasks?priority={priority}", response_status=200),
    ])
    r = contract_check(spec, [TASKS_MAIN])
    assert r["match"] is True, r
    assert r["missing"] == [] and r["extra"] == [], r


if __name__ == "__main__":
    test_derive_acceptance_deterministic()
    test_contract_check_matches()
    test_contract_check_detects_missing_endpoint()
    test_derived_acceptance_runs_green()
    test_derive_acceptance_emits_query_params()
    test_derive_acceptance_does_not_skip_query_path()
    test_contract_check_strips_query_from_path()
    print("[PASS] spec_derive: 确定性验收推导 + 契约校验(抓到漏端点) + query 参数修复")
