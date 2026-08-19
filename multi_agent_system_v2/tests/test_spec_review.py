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


if __name__ == "__main__":
    test_render_spec_readable()
    test_render_spec_accepts_dict()
    test_review_reject_aborts_before_builder()
    test_review_approve_proceeds_to_builder()
    test_review_feedback_regenerates_spec()
    print("[PASS] spec 审阅节点 + 可读化渲染")
