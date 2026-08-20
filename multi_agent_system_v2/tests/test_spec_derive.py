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


def test_query_params_accepts_int_values():
    """分页/区间查询参数（limit/offset/min/max）天然是整数，schema 必须接受数字值。

    回归：query_params 曾被定为 Dict[str,str]，LLM 给 {"min":10,"max":100} 会被拒，
    触发 generate_structured 重试（catalog_filter_sort 案例实测踩过）。
    """
    spec = ProjectSpec(project_name="products", endpoints=[
        EndpointSpec(method="GET", path="/products",
                     query_params={"min": 10, "max": 100}, response_status=200),
    ])
    assert spec.endpoints[0].query_params == {"min": 10, "max": 100}
    code = derive_acceptance_tests(spec)
    assert "params={'min': 10, 'max': 100}" in code, code


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


def test_derive_acceptance_409_rule_seeds_first():
    """唯一键冲突规则（409）必须先种资源再触发冲突，不能单次无状态请求。"""
    spec = ProjectSpec(project_name="counters", endpoints=[
        EndpointSpec(method="POST", path="/counters",
                     request_body={"name": "x"}, response_status=201),
    ], rules=[
        RuleSpec(description="名字唯一", method="POST", path="/counters",
                 request_body={"name": "x"}, expect_status=409),
    ])
    code = derive_acceptance_tests(spec)
    assert "先种资源" in code, code
    assert "assert r.status_code == 409" in code, code
    fn = code[code.index("def test_rule_0"):]
    assert fn.count("client.post('/counters'") == 2, fn  # 种子 + 触发


def test_derive_acceptance_non_conflict_rule_no_seed():
    """非 409 规则（如 422 校验）不该加种子请求。"""
    spec = ProjectSpec(project_name="todos", endpoints=[], rules=[
        RuleSpec(description="空标题 422", method="POST", path="/todos",
                 request_body={"title": ""}, expect_status=422),
    ])
    code = derive_acceptance_tests(spec)
    assert "先种资源" not in code
    assert code.count("client.post('/todos'") == 1, code


# ---------------------------------------------------------------------------
# request_body 支持 list（批量端点）+ 子资源路径参数端点覆盖
# ---------------------------------------------------------------------------

COURSES_MAIN = {
    "path": "main.py",
    "content": '''from fastapi import FastAPI

app = FastAPI()
courses = []
students = {}
_next = 1

@app.post("/courses", status_code=201)
def create_course(body: dict):
    global _next
    c = {"id": _next, "name": body["name"]}
    courses.append(c)
    students[_next] = []
    _next += 1
    return c

@app.get("/courses/{cid}/students")
def list_students(cid: int):
    return students.get(cid, [])
''',
}


def test_request_body_accepts_list():
    """批量端点的 request_body 应是 list 而非 dict，schema 必须接受。"""
    spec = ProjectSpec(project_name="bulk", endpoints=[
        EndpointSpec(method="POST", path="/items/bulk",
                     request_body=[{"name": "a"}, {"name": "b"}], response_status=201),
    ], rules=[
        RuleSpec(description="空名整体 422", method="POST", path="/items/bulk",
                 request_body=[{"name": ""}], expect_status=422),
    ])
    assert spec.endpoints[0].request_body == [{"name": "a"}, {"name": "b"}]
    assert spec.rules[0].request_body == [{"name": ""}]
    code = derive_acceptance_tests(spec)
    assert "json=[{'name': 'a'}, {'name': 'b'}]" in code, code


def test_derive_acceptance_seeds_path_param_endpoint():
    """带路径参数的子资源端点应生成「先种父资源再用 id 访问」的测试。"""
    spec = ProjectSpec(project_name="courses", endpoints=[
        EndpointSpec(method="POST", path="/courses",
                     request_body={"name": "math"}, response_status=201),
        EndpointSpec(method="GET", path="/courses/{cid}/students", response_status=200),
    ])
    code = derive_acceptance_tests(spec)
    assert "client.post('/courses', json={'name': 'math'})" in code, code
    assert "_rid_val = _rid(_r0)" in code, code
    assert ".replace('{cid}', str(_rid_val))" in code, code
    assert "def _rid(resp):" in code, code
    assert "test_endpoint_1_" in code, code


def test_derived_acceptance_path_param_runs_green():
    """子资源种子测试对正确实现应真实跑绿。"""
    spec = ProjectSpec(project_name="courses", endpoints=[
        EndpointSpec(method="POST", path="/courses",
                     request_body={"name": "math"}, response_status=201),
        EndpointSpec(method="GET", path="/courses/{cid}/students", response_status=200),
    ])
    code = derive_acceptance_tests(spec)
    data = asyncio.run(run_tests(
        [COURSES_MAIN],
        [{"path": "tests/test_acceptance.py", "content": code, "language": "python"}],
    ))
    assert data["all_passed"] is True, data


if __name__ == "__main__":
    test_derive_acceptance_deterministic()
    test_contract_check_matches()
    test_contract_check_detects_missing_endpoint()
    test_derived_acceptance_runs_green()
    test_derive_acceptance_emits_query_params()
    test_query_params_accepts_int_values()
    test_derive_acceptance_does_not_skip_query_path()
    test_contract_check_strips_query_from_path()
    test_derive_acceptance_409_rule_seeds_first()
    test_derive_acceptance_non_conflict_rule_no_seed()
    test_request_body_accepts_list()
    test_derive_acceptance_seeds_path_param_endpoint()
    test_derived_acceptance_path_param_runs_green()
    print("[PASS] spec_derive: 确定性验收推导 + 契约校验 + query 参数修复 + 409 种子 + list body + 子资源种子")
