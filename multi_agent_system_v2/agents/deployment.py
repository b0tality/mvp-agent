"""
部署Agent
"""

import time
from typing import Dict, Any
from agents.base import BaseAgent, AgentResult
from llm.adapter import LLMAdapter
from schemas import DeploymentOutput


class DeploymentAgent(BaseAgent):
    """部署Agent"""

    name = "deployment"

    def __init__(self, llm: LLMAdapter):
        super().__init__(llm)

    async def execute(self, **kwargs) -> AgentResult:
        code_files = kwargs.get("code_files", [])
        technical_solution = kwargs.get("technical_solution", {})

        start = time.time()
        try:
            result = await self.llm.generate_structured(
                """你是一位资深DevOps工程师。请生成部署方案和配置。

要求：
1. 设计部署策略
2. 生成Docker配置
3. 生成Kubernetes配置
4. 生成CI/CD配置
5. 生成监控配置""",
                f"代码文件：{code_files}\n技术方案：{technical_solution}",
                DeploymentOutput
            )
            return self._success(result.model_dump(), time.time() - start)
        except Exception as e:
            return self._error(str(e), time.time() - start)
