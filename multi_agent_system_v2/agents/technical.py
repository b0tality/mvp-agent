"""
技术架构Agent
"""

import time
from typing import Dict, Any
from agents.base import BaseAgent, AgentResult
from llm.adapter import LLMAdapter
from schemas import TechnicalOutput


class TechnicalAgent(BaseAgent):
    """技术架构Agent"""

    name = "technical"

    def __init__(self, llm: LLMAdapter):
        super().__init__(llm)

    async def execute(self, **kwargs) -> AgentResult:
        requirements = kwargs.get("requirements", {})
        if not requirements:
            return self._error("缺少 requirements 参数")

        start = time.time()
        try:
            # 一次调用生成完整技术方案
            result = await self.llm.generate_structured(
                """你是一位资深技术架构师。请根据需求设计完整的技术方案。

要求：
1. 设计系统架构（选择合适的架构模式）
2. 选择技术栈（后端、前端、数据库）
3. 设计RESTful API
4. 设计数据库schema
5. 设计安全方案
6. 估算开发成本""",
                f"需求：{requirements}",
                TechnicalOutput
            )

            data = result.model_dump()
            return self._success(data, time.time() - start)
        except Exception as e:
            return self._error(str(e), time.time() - start)
