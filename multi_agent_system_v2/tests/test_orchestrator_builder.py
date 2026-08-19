"""
PipelineOrchestrator + BuilderAgent 集成测试（离线，不联网）

验证 ③b：orchestrator 把 BuilderAgent 接进 mvp 阶段，且其产物（code_files/test_files）
正确落到 state 并流向下游阶段。requirements/technical/code_review/testing/acceptance/deployment
都用 stub，只有 mvp 用真实的 BuilderAgent（fake client 脚本化 tool_calls）。
"""

import sys
import asyncio
import json

sys.path.insert(0, r'C:\Users\MECHREV\agent\multi_agent_system_v2')

from agents.base import BaseAgent, AgentResult
from agents.builder import BuilderAgent
from llm import OpenAIAdapter
from pipeline.orchestrator import PipelineOrchestrator


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


# ----------------------------------------------------------------------
# stub agents
# ----------------------------------------------------------------------
class StubAgent(BaseAgent):
    """返回固定 data 的桩 agent，用于隔离 builder 之外的阶段。"""

    name = "stub"

    def __init__(self, data):
        self._data = data

    async def execute(self, **kwargs):
        return self._success(dict(self._data))


MAIN_PY = {
    "path": "main.py", "language": "python",
    "content": "from fastapi import FastAPI\napp = FastAPI()\n\n@app.get('/')\ndef root():\n    return {'ok': True}\n",
}
TEST_API = {
    "path": "tests/test_api.py", "language": "python",
    "content": "from fastapi.testclient import TestClient\nfrom main import app\nclient = TestClient(app)\n\ndef test_root():\n    assert client.get('/').status_code == 200\n",
}


async def main():
    write_args = json.dumps({
        "code_files": [MAIN_PY],
        "test_files": [TEST_API],
        "project_name": "integ",
    })
    script = [
        FakeMessage(tool_calls=[FakeToolCall("c1", "write_code", write_args)]),
        FakeMessage(content="完成"),
    ]

    llm = OpenAIAdapter(api_key="k", base_url="http://x", model="m")
    llm.client = FakeClient(script)
    builder = BuilderAgent(llm)

    agents = {
        "requirements": StubAgent({
            "functional_requirements": [{"id": "FR-1", "title": "根接口"}],
            "acceptance_criteria": [{"id": "AC-001", "description": "GET / 返回 200"}],
        }),
        "technical": StubAgent({
            "tech_stack": {"backend": "Python/FastAPI"},
            "api_design": {"endpoints": [{"method": "GET", "path": "/"}]},
        }),
        "mvp": builder,
        "code_review": StubAgent({"overall_score": 95, "approved": True, "issues": []}),
        "testing": StubAgent({"all_passed": True, "passed": 1, "failed": 0,
                              "coverage": {"line": 90}, "bugs": [], "raw_output": ""}),
        "acceptance": StubAgent({"all_passed": True, "passed": 1, "total": 1, "failed": 0, "results": []}),
        "deployment": StubAgent({"deployment_plan": {"strategy": "rolling"}}),
    }

    orch = PipelineOrchestrator(agents, max_iterations=3)
    result = await orch.run("待办事项应用")

    assert result.status == "success", f"status={result.status}, failed={result.failed_stages}"
    # mvp 阶段由 BuilderAgent 产出代码
    assert result.stages["mvp"].status == "success", result.stages["mvp"]
    assert len(result.stages["mvp"].data.get("code_files", [])) == 1
    assert len(result.stages["mvp"].data.get("test_files", [])) == 1
    # 产物落到共享 state，供下游使用
    assert orch.state.get("mvp").get("project_name") == "integ"
    assert len(orch.state.get("mvp").get("code_files", [])) == 1
    # 下游阶段正常跑到 deployment（验收门通过）
    assert result.stages["deployment"].status == "success", result.stages["deployment"]

    print("[PASS] orchestrator + BuilderAgent: mvp 接进流水线，产物流向下游，验收门通过")


if __name__ == "__main__":
    asyncio.run(main())
