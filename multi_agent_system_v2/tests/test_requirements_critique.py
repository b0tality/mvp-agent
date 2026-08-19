"""
RequirementsAgent 对抗评审离线测试（fake LLM）

验证「生成 → 对抗评审 → 修订」闭环的机制：
1. critic 报 critical/major 缺陷 → 触发修订，验收标准被补全（如补上 id 唯一性）
2. critic 无实质缺陷 → 不修订，原样保留
"""

import sys
import asyncio

sys.path.insert(0, r'C:\Users\MECHREV\agent\multi_agent_system_v2')

from agents.requirements import (
    RequirementsAgent,
    RequirementsCritique,
    RevisedRequirements,
    CritiqueIssue,
)
from schemas import AcceptanceCriterion


class CriticFakeLLM:
    """critic 报一个 major 缺陷，revise 返回「原标准 + 补上的 id 唯一性标准」"""
    async def generate_structured(self, system, user, output_schema, max_retries=2):
        if output_schema.__name__ == "RequirementsCritique":
            return RequirementsCritique(
                issues=[CritiqueIssue(
                    severity="major",
                    description="验收标准漏了「创建多个待办时 id 必须唯一」这一隐含不变式",
                    suggestion="补上 id 唯一性的验收标准",
                )],
                approved=False,
            )
        if output_schema.__name__ == "RevisedRequirements":
            return RevisedRequirements(
                acceptance_criteria=[
                    AcceptanceCriterion(id="AC-1", story_id="US-1", description="POST /todo 返回 201"),
                    AcceptanceCriterion(id="AC-2", story_id="US-1", description="连续创建多个待办，每个 id 必须唯一且递增"),
                ],
                functional_requirements=[],
            )
        raise AssertionError(f"unexpected schema: {output_schema.__name__}")


class ApproveFakeLLM:
    """critic 认为无明显缺陷 → 不应触发修订"""
    async def generate_structured(self, system, user, output_schema, max_retries=2):
        if output_schema.__name__ == "RequirementsCritique":
            return RequirementsCritique(issues=[], approved=True)
        raise AssertionError("不应调用 revise")


def _base_data():
    return {
        "functional_requirements": [{"id": "FR-1", "title": "创建待办", "description": "用户能创建待办"}],
        "acceptance_criteria": [
            {"id": "AC-1", "story_id": "US-1", "description": "POST /todo 返回 201"},
        ],
    }


def test_critique_triggers_revise_and_completes_criteria():
    async def run():
        agent = RequirementsAgent(CriticFakeLLM())
        out = await agent._critique_and_revise(_base_data(), "开发一个待办事项应用")
        return out

    out = asyncio.run(run())
    assert out["critique"]["revised"] is True, out["critique"]
    # 修订后补上了 id 唯一性的验收标准
    assert any("唯一" in c["description"] for c in out["acceptance_criteria"]), out["acceptance_criteria"]
    assert len(out["acceptance_criteria"]) == 2, out["acceptance_criteria"]


def test_no_blocking_issue_skips_revise():
    async def run():
        agent = RequirementsAgent(ApproveFakeLLM())
        out = await agent._critique_and_revise(_base_data(), "开发一个待办事项应用")
        return out

    out = asyncio.run(run())
    assert out["critique"]["revised"] is False, out["critique"]
    assert len(out["acceptance_criteria"]) == 1, out["acceptance_criteria"]


if __name__ == "__main__":
    test_critique_triggers_revise_and_completes_criteria()
    test_no_blocking_issue_skips_revise()
    print("[PASS] RequirementsAgent 对抗评审: 有缺陷→修订补全 / 无缺陷→不修订")
