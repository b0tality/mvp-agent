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
        if not code_files:
            return self._success({"overall_score": 100, "approved": True, "issues": [], "summary": "无代码需要审查"})

        start = time.time()
        try:
            result = await self.llm.generate_structured(
                """你是一位资深代码审查专家。请审查代码质量。

检查以下方面：
1. 代码规范和风格
2. 潜在的安全问题
3. 性能问题
4. 代码复杂度
5. 重构建议""",
                f"代码文件：{code_files}",
                CodeReviewOutput
            )
            return self._success(result.model_dump(), time.time() - start)
        except Exception as e:
            return self._error(str(e), time.time() - start)
