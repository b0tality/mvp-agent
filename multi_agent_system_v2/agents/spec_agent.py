"""
SpecAgent —— 把自然语言需求转成一份机器可执行的 API 契约（ProjectSpec）。

这是 spec-driven 架构里「全系统唯一一次理解需求」的 LLM 调用，也是唯一需要人审阅的点：
Spec 是一份 30 秒能读完的小工件，人看一眼就知道「它漏了 400 这条吗」，错了能改、能重跑。

后续的验收测试、契约校验都由这份 Spec 确定性推导（tools/spec_derive.py），零 LLM。
"""

import time
from typing import Dict, Any

from agents.base import BaseAgent, AgentResult
from llm.adapter import LLMAdapter
from schemas.spec import ProjectSpec


_SPEC_SYSTEM = """你是一位严格的 API 规格编写器。把用户的自然语言需求转成一份机器可执行的 API 契约（ProjectSpec）。

这份 Spec 是整个系统的**唯一真相源**：后续所有测试都由它确定性生成，代码必须精确实现它。
因此你的输出必须精确、可验证、不臆造、不遗漏。

规则：
1. project_name：小写字母 + 下划线。
2. endpoints：列出**所有**后端 API 端点，每个给 method / path / request_body / response_status。
   - 路径用 REST 风格，路径参数用 {id} 形式（如 /todos/{id}）。
   - request_body 是「能成功触发该端点的合法 JSON 示例」（GET/DELETE 留空）。
   - response_status 是成功状态码（POST 常为 201，DELETE 常为 204，其余 200）。
   - 查询参数（筛选/搜索/分页，如「按优先级筛选」「按书名搜索」「limit/offset」）写进 query_params 字段
     （如 {"priority": "high"} 或 {"q": "python", "limit": "10"}），**绝对不要拼进 path**。
     path 只写资源路径本身（如 /tasks 或 /books），不含 ?query=...。
3. rules：列出**关键行为/校验规则**，每条必须能用一个 HTTP 请求客观判定，给 method / path / request_body / expect_status（必要时给 expect_contains 子串，必要时给 query_params）。
   - expect_contains 只能是字符串，不需要时**省略该字段**（不要写空数组 []、空对象 {} 或空字符串 ""）。
   - 必覆盖：必填字段缺失/非法 → 状态码；非法输入 → 422/400；唯一键冲突 → 409/400；资源不存在 → 404。
   - path **不要用 {id} 参数**（规则针对可无状态触发的校验，如 POST 校验、GET 列表）；资源级 404/删除 404 由系统的不变式测试覆盖。
4. 只写后端可验证的行为；不写 UI/前端行为。若用户需求有 UI 行为，转成对应的 API 行为。
5. 不要臆造用户没提的功能；宁可少而精确，不要多而模糊。
6. 实现细节（密码哈希、存储方式、框架内部）不写进 spec，只写 API 行为（方法+路径+状态码+响应）。

只输出 JSON，结构严格遵循 ProjectSpec。"""


class SpecAgent(BaseAgent):
    """Spec 编写器：NL → ProjectSpec（一次 LLM 调用）。"""

    name = "spec"

    def __init__(self, llm: LLMAdapter):
        super().__init__(llm)

    async def execute(self, **kwargs) -> AgentResult:
        user_input = kwargs.get("user_input", "")
        if not user_input:
            return self._error("缺少 user_input 参数")

        # 人工审阅反馈：附在原始需求后，让 SpecAgent 据此修正上一版 Spec
        feedback = kwargs.get("feedback", "")
        prompt = user_input
        if feedback:
            prompt = (
                f"{user_input}\n\n"
                f"【上一版 spec 的人工审阅反馈，请据此修正（其余保持不变）】\n{feedback}"
            )

        start = time.time()
        try:
            result = await self.llm.generate_structured(
                _SPEC_SYSTEM, prompt, ProjectSpec,
            )
            return self._success(result.model_dump(), time.time() - start)
        except Exception as e:
            return self._error(str(e), time.time() - start)
