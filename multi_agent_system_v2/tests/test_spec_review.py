"""
spec 人工审阅节点 + 可读化渲染的离线验证（零 LLM、零联网）

验证：
1. render_spec 把 ProjectSpec 渲染成中文可读清单（端点 + 规则 + 请求体示例）。
2. run_spec_pipeline 的审阅回调协议：
   - "reject" → 立即中止，builder 不执行；
   - "approve" → 通过 spec 阶段，继续到 builder；
   - 其它字符串（修改意见）→ 重新生成 Spec 并把意见附给 SpecAgent。
"""

import sys
import asyncio

sys.path.insert(0, r'C:\Users\MECHREV\agent\multi_agent_system_v2')

from agents.base import AgentResult
from agents.builder import BuilderAgent
from agents.spec_review_agent import SpecReviewAgent
from schemas.spec import ProjectSpec, EndpointSpec, RuleSpec
from pipeline.spec_pipeline import run_spec_pipeline
from tools.spec_render import render_spec


def make_spec() -> ProjectSpec:
    return ProjectSpec(
        project_name="todo_app",
        description="待办事项",
        endpoints=[
            EndpointSpec(method="POST", path="/todos",
                         request_body={"title": "x"}, response_status=201),
            EndpointSpec(method="GET", path="/todos", response_status=200),
        ],
        rules=[
            RuleSpec(description="标题为空应返回 422", method="POST", path="/todos",
                     request_body={"title": ""}, expect_status=422),
        ],
    )


class FakeSpecAgent:
    def __init__(self, spec: ProjectSpec):
        self.spec = spec
        self.calls = []

    async def execute(self, **kwargs) -> AgentResult:
        self.calls.append(kwargs)
        return AgentResult(status="success", data=self.spec.model_dump())


class FakeBuilder:
    def __init__(self):
        self.called = False

    async def execute(self, **kwargs) -> AgentResult:
        self.called = True
        return AgentResult(status="success", data={"code_files": []})


def test_render_spec_readable():
    out = render_spec(make_spec())
    assert "API 端点" in out, out
    assert "校验规则" in out, out
    assert "POST /todos" in out, out
    assert "todo_app" in out, out
    assert "{" in out, "应有请求体示例"  # 示例请求体 JSON


def test_render_spec_accepts_dict():
    out = render_spec(make_spec().model_dump())
    assert "API 端点" in out and "GET /todos" in out


def test_review_reject_aborts_before_builder():
    agent = FakeSpecAgent(make_spec())
    builder = FakeBuilder()

    async def review(spec):
        return "reject"

    r = asyncio.run(run_spec_pipeline("开发待办", agent, builder, spec_review=review))
    assert r["status"] == "rejected", r
    assert len(agent.calls) == 1, "reject 应立即中止，不再重新生成"
    assert builder.called is False, "reject 后 builder 不应执行"


def test_review_approve_proceeds_to_builder():
    agent = FakeSpecAgent(make_spec())
    builder = FakeBuilder()

    async def review(spec):
        return "approve"

    r = asyncio.run(run_spec_pipeline("开发待办", agent, builder, spec_review=review))
    assert builder.called is True, "approve 后应继续到 builder"
    assert len(agent.calls) == 1, "approve 后不应重新生成 spec"


def test_review_feedback_regenerates_spec():
    agent = FakeSpecAgent(make_spec())
    builder = FakeBuilder()
    verdicts = iter(["加一个 PUT /todos/{id} 端点", "reject"])

    async def review(spec):
        return next(verdicts)

    r = asyncio.run(run_spec_pipeline("开发待办", agent, builder, spec_review=review))
    assert r["status"] == "rejected", r
    assert len(agent.calls) == 2, "第一轮给意见后应重新生成一次 spec"
    # 第二次生成时，意见应作为 feedback 附给 SpecAgent
    assert "PUT" in agent.calls[1].get("feedback", ""), agent.calls[1]
    assert builder.called is False


# ---------------------------------------------------------------------------
# 外层重试：builder 没过硬门槛时，把失败信息回灌重跑
# ---------------------------------------------------------------------------

CODE_MISSING_GET = {
    "path": "main.py", "language": "python",
    "content": '''from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()
todos = []
next_id = 1

class TodoCreate(BaseModel):
    title: str

class TodoOut(BaseModel):
    id: int
    title: str

@app.post("/todos", status_code=201, response_model=TodoOut)
def create(todo: TodoCreate):
    global next_id
    todos.append({"id": next_id, "title": todo.title})
    next_id += 1
    return todos[-1]
''',
}

CODE_FULL = {
    "path": "main.py", "language": "python",
    "content": CODE_MISSING_GET["content"] + '''

@app.get("/todos", response_model=list[TodoOut])
def list_todos():
    return todos
''',
}


class FlakyBuilder:
    """第一轮漏实现 GET 端点（契约不符），第二轮补上——模拟「重试后修复」。"""
    def __init__(self):
        self.calls = []

    async def execute(self, **kwargs):
        self.calls.append(kwargs)
        code = CODE_MISSING_GET if len(self.calls) == 1 else CODE_FULL
        return AgentResult(status="success", data={"code_files": [code]})


def test_outer_retry_fixes_gate_failure():
    spec = ProjectSpec(
        project_name="todo_retry",
        endpoints=[
            EndpointSpec(method="POST", path="/todos",
                         request_body={"title": "x"}, response_status=201),
            EndpointSpec(method="GET", path="/todos", response_status=200),
        ],
    )
    agent = FakeSpecAgent(spec)
    builder = FlakyBuilder()
    r = asyncio.run(run_spec_pipeline("开发待办", agent, builder))
    assert r["gate_ok"] is True, r
    assert len(builder.calls) == 2, f"第一轮漏 GET 应触发重试，实际调用 {len(builder.calls)} 次"
    assert builder.calls[1].get("current_code"), "重试应带上上一版代码"
    assert builder.calls[1].get("feedback"), "重试应带上失败反馈"


def test_builder_spec_iteration_prompt():
    """builder 在 spec 模式 + 修复迭代时，系统提示与用户提示都应含失败反馈。"""
    sp = BuilderAgent._system_prompt(iterating=True, spec_mode=True)
    assert "修复迭代" in sp
    up = BuilderAgent._user_prompt(
        "", {}, {},
        feedback={"test_output": "E assert 404 == 200"},
        spec={"project_name": "x", "endpoints": [], "rules": []},
    )
    assert "404" in up and "200" in up, "失败反馈应喂进 user prompt"


# ---------------------------------------------------------------------------
# 自动完备性评审（SpecReviewAgent）+ 回调适配
# ---------------------------------------------------------------------------

def test_auto_review_approve_single_pass():
    agent = FakeSpecAgent(make_spec())
    builder = FakeBuilder()

    async def review(user_input, spec):
        return "approve"

    r = asyncio.run(run_spec_pipeline("开发待办", agent, builder, spec_auto_review=review))
    assert len(agent.calls) == 1, "自动评审 approve 后不应重新生成 spec"
    assert builder.called is True, "自动评审通过后应继续到 builder"


def test_auto_review_feedback_regenerates():
    agent = FakeSpecAgent(make_spec())
    builder = FakeBuilder()
    verdicts = iter(["缺少 POST /todos/{id} 端点", "approve"])

    async def review(user_input, spec):
        return next(verdicts)

    r = asyncio.run(run_spec_pipeline("开发待办", agent, builder, spec_auto_review=review))
    assert len(agent.calls) == 2, "第一轮给意见后应重新生成一次 spec"
    assert "POST /todos/{id}" in agent.calls[1].get("feedback", ""), agent.calls[1]
    assert builder.called is True


class _FakeReviewAgent:
    def __init__(self, data):
        self.data = data

    async def execute(self, **kwargs):
        return AgentResult(status="success", data=self.data)


def test_review_agent_callback_approve():
    cb = SpecReviewAgent.to_callback(_FakeReviewAgent({"verdict": "approve", "issues": []}))
    assert asyncio.run(cb("req", {})) == "approve"


def test_review_agent_callback_feedback_joins_issues():
    cb = SpecReviewAgent.to_callback(
        _FakeReviewAgent({"verdict": "reject", "issues": ["缺 A", "缺 B"]})
    )
    assert asyncio.run(cb("req", {})) == "缺 A\n缺 B"


def test_review_agent_callback_error_degrades_to_approve():
    """评审器自身报错不应阻塞流水线（下游确定性硬门槛兜底）。"""
    async def execute(self, **kwargs):
        return AgentResult(status="error", error="boom")

    agent = type("BrokenReviewAgent", (), {"execute": execute})()
    cb = SpecReviewAgent.to_callback(agent)
    assert asyncio.run(cb("req", {})) == "approve"


if __name__ == "__main__":
    test_render_spec_readable()
    test_render_spec_accepts_dict()
    test_review_reject_aborts_before_builder()
    test_review_approve_proceeds_to_builder()
    test_review_feedback_regenerates_spec()
    test_outer_retry_fixes_gate_failure()
    test_builder_spec_iteration_prompt()
    test_auto_review_approve_single_pass()
    test_auto_review_feedback_regenerates()
    test_review_agent_callback_approve()
    test_review_agent_callback_feedback_joins_issues()
    test_review_agent_callback_error_degrades_to_approve()
    print("[PASS] spec 审阅节点 + 可读化渲染 + 外层重试 + 自动评审")
