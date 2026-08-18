"""
部署工具集
"""

from typing import Dict, Any
from tools.base import BaseTool
from schemas import DeploymentOutput


class DeploymentTool(BaseTool):
    """部署工具"""
    name = "deployment"
    description = "生成部署方案和配置"

    async def run(self, **kwargs) -> Dict[str, Any]:
        code_files = kwargs.get("code_files", [])
        technical_solution = kwargs.get("technical_solution", {})
        result = await self.llm.generate_structured(
            "你是一位资深DevOps工程师。请生成部署方案和Docker配置。",
            f"代码文件：{code_files}\n技术方案：{technical_solution}",
            DeploymentOutput
        )
        return result.model_dump()
