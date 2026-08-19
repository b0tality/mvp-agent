"""
SpecReviewAgent —— 对 SpecAgent 产出的 ProjectSpec 做自动完备性评审（LLM 评审）。

为什么需要它：spec-driven 架构里「验证全部确定性」的前提是 Spec 本身对需求**没有遗漏**。
而「Spec 是否覆盖了自然语言需求里暗含的所有端点/校验」无法被确定性代码机械判定——
这正是全系统里唯一需要第二个 LLM 视角的地方：一个严格的「完备性批评者」。

它不做裁判级重写（那仍是 SpecAgent 的职责），只产出 approve / reject + 一条条可执行的
修复意见（issues），意见会作为 feedback 回灌 SpecAgent 重新生成——复用已经过测试的人工审阅回路。

评审失败（LLM 报错）时视为 approve（不阻塞），因为下游确定性硬门槛仍会兜底拦截真正的错误。
"""

from typing import List, Literal

from pydantic import BaseModel, Field

from agents.base import BaseAgent, AgentResult
from llm.adapter import LLMAdapter
from tools.spec_render import render_spec


class SpecReviewOutput(BaseModel):
    """自动评审的裁决 + 修复意见。"""
    verdict: Literal["approve", "reject"] = Field(
        description="approve=spec 完整且忠实；reject=存在遗漏/多余/字段或状态码错误"
    )
    issues: List[str] = Field(
        default_factory=list,
        description="每条都是一条可执行修复指令（如「缺少 POST /login 端点」）。approve 时为空。",
    )


_SPEC_REVIEW_SYSTEM = """你是一位极其严格的 API 规格评审员。把「原始需求」和「机器生成的 Spec」逐条比对，找出任何不一致。

你的唯一目标是：在 Spec 被拿去生成代码之前，拦截「遗漏」「多余」「字段/状态码错误」这三类缺陷。
因为下游所有测试都由这份 Spec 机械推导，Spec 一旦漏了某条规则，代码就会带着这个缺陷通过所有验证。

逐项检查：
1. 完备性：需求里每个动词（增/删/改/查/注册/登录/搜索/筛选/自增/标记完成…）是否都有对应的 endpoint？方法、路径、成功状态码是否合理？
2. 校验规则：需求里每条「约束」（必填、长度、唯一、非法输入、错误返回 401/403/404…）是否都成了 rule？expect_status 是否与需求一致？
3. 字段：每个 endpoint 的 request_body 是否恰好包含需求点名的字段（不多、不少）？
4. 忠实性：Spec 是否臆造了需求没提的端点/规则？有就指出。

裁决标准：只要存在**任何一条**上述缺陷 → verdict="reject"，并把每条缺陷写成一条具体的修复指令。
只有 Spec 完整、忠实、可验证时 → verdict="approve"。

修复指令要具体到「缺哪个端点 / 缺哪条规则 / 改哪个状态码」，让 SpecAgent 能直接照着改，不要泛泛而谈。
"""


class SpecReviewAgent(BaseAgent):
    """Spec 完备性评审员：比对需求 vs Spec，产出 approve/reject + 修复意见。"""

    name = "spec_review"

    def __init__(self, llm: LLMAdapter):
        super().__init__(llm)

    async def execute(self, **kwargs) -> AgentResult:
        user_input = kwargs.get("user_input", "")
        spec = kwargs.get("spec")
        if not user_input or spec is None:
            return self._error("缺少 user_input 或 spec 参数")

        readable = render_spec(spec)
        prompt = (
            f"【原始需求】\n{user_input}\n\n"
            f"【机器生成的 Spec（可读清单）】\n{readable}\n\n"
            f"请逐项比对，输出裁决。"
        )
        import time
        start = time.time()
        try:
            result = await self.llm.generate_structured(
                _SPEC_REVIEW_SYSTEM, prompt, SpecReviewOutput,
            )
            return self._success(result.model_dump(), time.time() - start)
        except Exception as e:
            return self._error(str(e), time.time() - start)

    def to_callback(self):
        """把 review agent 适配成 run_spec_pipeline 的自动评审回调协议：

        async (user_input, spec) -> "approve" / 修复意见字符串。
        """
        async def _review(user_input: str, spec) -> str:
            res = await self.execute(user_input=user_input, spec=spec)
            if res.status != "success":
                return "approve"  # 评审器自身失败不阻塞，下游硬门槛兜底
            data = res.data or {}
            if data.get("verdict") == "reject" and data.get("issues"):
                return "\n".join(data["issues"])
            return "approve"

        return _review
