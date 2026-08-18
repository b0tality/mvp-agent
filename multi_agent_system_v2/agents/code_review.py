"""
代码审查Agent
"""

import time
from typing import Dict, Any
from agents.base import BaseAgent, AgentResult
from llm.adapter import LLMAdapter
from schemas import CodeReviewOutput


class CodeReviewAgent(BaseAgent):
    """代码审查Agent"""

    name = "code_review"

    def __init__(self, llm: LLMAdapter):
        super().__init__(llm)

    async def execute(self, **kwargs) -> AgentResult:
        code_files = kwargs.get("code_files", [])
        test_results = kwargs.get("test_results") or {}
        if not code_files:
            return self._success({"overall_score": 100, "approved": True, "issues": [], "summary": "无代码需要审查"})

        start = time.time()
        try:
            result = await self.llm.generate_structured(
                """你是一位资深代码审查专家。请结合「真实测试结果」审查代码质量，与测试形成互相监督。

检查以下方面：
1. 测试失败是否反映了真实代码缺陷（结合 raw_output 里的 traceback 定位到具体代码行）
2. 潜在的安全问题（注入、越权、缺少输入校验、硬编码密钥）
3. 逻辑正确性（边界条件、类型、异常处理、除零/空值）
4. 性能问题（不必要的循环、重复查询、O(n²)）
5. 可维护性（命名、结构、重复代码、TODO 占位）

评分标准（严格）：
- 90-100：代码健壮、测试全过、无明显问题
- 80-89：有少量 minor 问题但不影响功能
- 70-79：有需要修复的设计/健壮性问题
- <70：存在影响正确性或安全的问题

critical/major 只用于：测试失败对应的真实缺陷、安全问题、影响正确性的逻辑错误。""",
                f"""代码文件：{code_files}

真实测试结果（testing agent 实际执行 pytest/冒烟/覆盖率）：{test_results}""",
                CodeReviewOutput,
            )
            return self._success(result.model_dump(), time.time() - start)
        except Exception as e:
            return self._error(str(e), time.time() - start)
