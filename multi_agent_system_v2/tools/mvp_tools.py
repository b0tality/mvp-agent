"""
MVP工具集
"""

from typing import Dict, Any
from tools.base import BaseTool
from tools.executors import verify_code


class CodeVerifierTool(BaseTool):
    """
    代码验证工具：语法(AST)+编译(py_compile)检查

    具体逻辑委托 tools.executors.verify_code（与 function-calling 工具共享同一实现）。
    """

    name = "code_verifier"
    description = "验证代码是否可编译运行"

    async def run(self, **kwargs) -> Dict[str, Any]:
        code_files = kwargs.get("code_files", [])
        return await verify_code(code_files)
