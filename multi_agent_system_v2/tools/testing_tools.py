"""
测试工具集
"""

from typing import Dict, Any
from tools.base import BaseTool
from schemas import TestingOutput


class TestingTool(BaseTool):
    """测试工具"""
    name = "testing"
    description = "生成和运行测试"

    async def run(self, **kwargs) -> Dict[str, Any]:
        code_files = kwargs.get("code_files", [])
        result = await self.llm.generate_structured(
            "你是一位资深测试工程师。请为代码生成测试用例并评估覆盖率。",
            f"代码文件：{code_files}",
            TestingOutput
        )
        return result.model_dump()
