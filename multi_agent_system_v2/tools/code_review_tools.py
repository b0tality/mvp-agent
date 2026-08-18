"""
代码审查工具集
"""

from typing import Dict, Any, List
from tools.base import BaseTool
from schemas import CodeReviewOutput


class CodeReviewTool(BaseTool):
    """代码审查工具"""
    name = "code_review"
    description = "审查代码质量"

    async def run(self, **kwargs) -> Dict[str, Any]:
        code_files = kwargs.get("code_files", [])
        result = await self.llm.generate_structured(
            "你是一位资深代码审查专家。请审查代码质量，检查问题并评分。",
            f"代码文件：{code_files}",
            CodeReviewOutput
        )
        return result.model_dump()
