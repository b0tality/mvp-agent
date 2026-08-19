"""
需求分析Agent —— 生成 + 对抗评审 + 修订

在原有「解析→故事→验收标准→优先级」之后，新增一步：
5. 对抗评审：让 LLM 以 red-team 评审员身份攻击刚生成的需求（歧义/不可验证/漏不变式/矛盾）。
6. 若有 critical/major 缺陷，把批评喂回，修订验收标准（必要时也修订功能需求）。

这样需求不再是「跑一次就信」，而是一个「作者 → 对手 → 作者修订」的对抗闭环，
正对之前归因里「需求漏了 id 唯一性」这类 40% 根因——不变式由 agent 自己推导并补上，无需人工清单。
"""

import time
from typing import Dict, Any, List

from pydantic import BaseModel, Field

from agents.base import BaseAgent, AgentResult
from llm.adapter import LLMAdapter
from schemas import AcceptanceCriterion, RequirementItem
from tools.requirements_tools import (
    RequirementParserTool,
    UserStoryGeneratorTool,
    AcceptanceCriteriaTool,
    PriorityCalculatorTool,
)


class CritiqueIssue(BaseModel):
    severity: str = Field(default="major", description="缺陷等级: critical/major/minor")
    description: str = Field(default="", description="缺陷描述")
    suggestion: str = Field(default="", description="修复建议")


class RequirementsCritique(BaseModel):
    issues: List[CritiqueIssue] = Field(default_factory=list, description="发现的缺陷列表")
    approved: bool = Field(default=True, description="是否无明显缺陷")


class RevisedRequirements(BaseModel):
    acceptance_criteria: List[AcceptanceCriterion] = Field(
        default_factory=list, description="修订后的验收标准"
    )
    functional_requirements: List[RequirementItem] = Field(
        default_factory=list, description="修订后的功能需求（仅当有遗漏/错误时输出）"
    )


_CRITIC_SYSTEM = """你是一位严苛的需求评审员（red-team）。原始用户需求已给出，下面是一份由另一位分析师生成的需求文档。你的职责是找它的缺陷，而不是肯定它。宁可按 major/critical 报，也不要漏报。

重点找：
1. 是否误解或遗漏了用户的原始意图。
2. 验收标准是否每条都「可被一个 HTTP 请求客观判定通过/失败」——有没有用模糊词（如"合理""友好""快速""适当"）而没有具体可验证细节（状态码/字段名/边界值）。
3. 【致命】验收标准是否是纯 UI 行为（点击按钮、勾选复选框、颜色标签、页面跳转、前端通知），而下游只会生成后端 API（FastAPI），无法验证 UI。若是，报 critical 并建议改写成对应 API 行为（状态码 + 响应体字段 + 列表长度/数据一致性）。
4. 【致命】是否臆造了用户没提的功能（标签/优先级/提醒/通知/统计等），把「待办事项应用」膨胀成别的产品。若是，报 critical 并建议删除这些过度设计、只保留用户明确要求的核心。
5. 是否漏了该领域「隐含不变式」的验收标准，例如：资源标识唯一性/递增、幂等性、删除后不可再引用、状态与计数一致性、边界值（空/超长/负数/0）。
6. 功能需求之间有没有矛盾或重复。

只输出 JSON。issues 里每条给 severity(critical/major/minor)、description、suggestion。只要存在上述第 3/4 条任一问题，就必须报 critical 且 approved=false。"""


_REVISE_SYSTEM = """你是一位资深需求分析师。下面是你之前生成的需求文档，以及评审员指出的缺陷。请修订。

要求：
1. 针对每一条 critical/major 缺陷修订：补上缺失的验收标准、把模糊描述改成可验证（含状态码/字段/边界值）、消除歧义。
2. 若评审指出验收标准是纯 UI 行为，把它们改写为 API 行为（POST/GET/PUT/PATCH/DELETE + 状态码 + 响应体字段 + 列表长度/数据一致性）。
3. 若评审指出功能需求过度设计（臆造了用户没要的标签/优先级/提醒/通知等），直接删掉这些功能及其对应的验收标准，只保留用户明确要求的核心。
4. 若评审指出功能需求有遗漏或错误，也一并修订 functional_requirements，否则保留原样。
5. 保留原有正确、且在用户意图内的验收标准和功能需求，不要删减、不要重写与缺陷无关的部分。

只输出 JSON：{"acceptance_criteria": [...], "functional_requirements": [...]}。"""


class RequirementsAgent(BaseAgent):
    """
    需求分析Agent

    职责：
    1. 解析用户需求
    2. 生成用户故事
    3. 生成验收标准
    4. 优先级排序
    5. 对抗评审 + 修订（新增）
    """

    name = "requirements"

    def __init__(self, llm: LLMAdapter):
        super().__init__(llm)
        self.parser = RequirementParserTool(llm)
        self.story_gen = UserStoryGeneratorTool(llm)
        self.criteria_gen = AcceptanceCriteriaTool(llm)
        self.priority_calc = PriorityCalculatorTool(llm)

    async def execute(self, **kwargs) -> AgentResult:
        user_input = kwargs.get("user_input", "")
        if not user_input:
            return self._error("缺少 user_input 参数")

        start = time.time()

        try:
            # 1. 解析需求
            parsed = await self.parser.run(user_input=user_input)
            # 2. 生成用户故事
            stories = await self.story_gen.run(requirements=parsed)
            # 3. 生成验收标准（锚定原始需求，保留可验证细节）
            criteria = await self.criteria_gen.run(
                user_stories=stories.get("user_stories", []),
                requirements=parsed,
                user_input=user_input,
            )
            # 4. 优先级排序
            priority = await self.priority_calc.run(requirements=parsed)

            # 合并结果
            data = {
                **parsed,
                "user_stories": stories.get("user_stories", []),
                "acceptance_criteria": criteria.get("acceptance_criteria", []),
                "priority_matrix": priority,
            }

            # 5. 对抗评审 + 修订（agent 自己找缺陷、自己补，无需人工清单）
            data = await self._critique_and_revise(data, user_input)

            return self._success(data, time.time() - start)

        except Exception as e:
            return self._error(str(e), time.time() - start)

    # ------------------------------------------------------------------
    # 对抗评审 + 修订
    # ------------------------------------------------------------------
    async def _critique_and_revise(self, data: Dict[str, Any], user_input: str) -> Dict[str, Any]:
        # 评审失败/修订失败都不应拖垮整个需求阶段，降级为「跳过评审」并保留原样
        try:
            critique = await self._critique(data, user_input)
        except Exception:
            return data

        issues = critique.get("issues", []) or []
        blocking = [i for i in issues if i.get("severity") in ("critical", "major")]
        if not blocking:
            data["critique"] = {"issues": issues, "revised": False}
            return data

        try:
            revised = await self._revise(data, critique, user_input)
        except Exception:
            data["critique"] = {"issues": issues, "revised": False}
            return data

        if revised.get("acceptance_criteria"):
            data["acceptance_criteria"] = revised["acceptance_criteria"]
        if revised.get("functional_requirements"):
            data["functional_requirements"] = revised["functional_requirements"]
        data["critique"] = {"issues": issues, "revised": True}
        return data

    async def _critique(self, data: Dict[str, Any], user_input: str) -> Dict[str, Any]:
        focus = {
            "functional_requirements": data.get("functional_requirements", []),
            "non_functional_requirements": data.get("non_functional_requirements", []),
            "user_stories": data.get("user_stories", []),
            "acceptance_criteria": data.get("acceptance_criteria", []),
        }
        result = await self.llm.generate_structured(
            _CRITIC_SYSTEM,
            f"原始用户需求：{user_input}\n\n需求文档：{focus}",
            RequirementsCritique,
        )
        return result.model_dump()

    async def _revise(self, data: Dict[str, Any], critique: Dict[str, Any], user_input: str) -> Dict[str, Any]:
        focus = {
            "functional_requirements": data.get("functional_requirements", []),
            "acceptance_criteria": data.get("acceptance_criteria", []),
        }
        result = await self.llm.generate_structured(
            _REVISE_SYSTEM,
            f"原始用户需求：{user_input}\n\n需求文档：{focus}\n\n评审缺陷：{critique}",
            RevisedRequirements,
        )
        return result.model_dump()
