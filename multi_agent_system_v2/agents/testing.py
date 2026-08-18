"""
测试Agent
"""

import time
from typing import Dict, Any
from agents.base import BaseAgent, AgentResult
from llm.adapter import LLMAdapter
from schemas import TestingOutput


class TestingAgent(BaseAgent):
    """测试Agent"""

    name = "testing"

    def __init__(self, llm: LLMAdapter):
        super().__init__(llm)

    async def execute(self, **kwargs) -> AgentResult:
        code_files = kwargs.get("code_files", [])
        if not code_files:
            return self._success({"test_cases": [], "bugs": [], "coverage": {"line": 0, "branch": 0, "function": 0}, "summary": "无代码需要测试"})

        start = time.time()
        try:
            result = await self.llm.generate_structured(
                """你是一位资深测试工程师。请为代码生成测试用例。

要求：
1. 生成单元测试用例
2. 评估测试覆盖率
3. 识别潜在的Bug
4. 提供测试总结""",
                f"代码文件：{code_files}",
                TestingOutput
            )
            return self._success(result.model_dump(), time.time() - start)
        except Exception as e:
            return self._error(str(e), time.time() - start)
