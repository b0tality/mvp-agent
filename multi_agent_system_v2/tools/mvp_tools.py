"""
MVP工具集
"""

import os
import sys
import tempfile
import subprocess
import ast
from typing import Dict, Any, List
from tools.base import BaseTool
from schemas import MVPCodeOutput


class CodeVerifierTool(BaseTool):
    """
    代码验证工具
    
    将生成的代码写入临时目录，尝试编译和运行，返回错误信息。
    """

    name = "code_verifier"
    description = "验证代码是否可编译运行"

    async def run(self, **kwargs) -> Dict[str, Any]:
        """
        验证代码文件
        
        kwargs:
            code_files: List[Dict] - 代码文件列表
            
        Returns:
            Dict with keys:
                - passed: bool - 是否通过
                - errors: List[Dict] - 错误列表
                - file_errors: Dict[str, List] - 按文件分组的错误
        """
        code_files = kwargs.get("code_files", [])
        if not code_files:
            return {"passed": True, "errors": [], "file_errors": {}}

        errors = []
        file_errors = {}

        # 创建临时目录
        with tempfile.TemporaryDirectory() as tmpdir:
            # 写入代码文件
            for cf in code_files:
                path = cf.get("path", "unknown.py")
                content = cf.get("content", "")
                if not content:
                    continue

                file_path = os.path.join(tmpdir, path)
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)

            # 验证每个Python文件
            for cf in code_files:
                path = cf.get("path", "")
                content = cf.get("content", "")

                if not path.endswith(".py") or not content:
                    continue

                file_path = os.path.join(tmpdir, path)
                file_errs = []

                # 1. 语法检查（AST解析）
                try:
                    ast.parse(content)
                except SyntaxError as e:
                    file_errs.append({
                        "type": "syntax",
                        "line": e.lineno,
                        "message": str(e.msg),
                        "text": e.text or "",
                    })

                # 2. 编译检查（py_compile）
                try:
                    result = subprocess.run(
                        [sys.executable, "-m", "py_compile", file_path],
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )
                    if result.returncode != 0:
                        file_errs.append({
                            "type": "compile",
                            "message": result.stderr.strip(),
                        })
                except subprocess.TimeoutExpired:
                    file_errs.append({
                        "type": "timeout",
                        "message": "编译超时",
                    })
                except Exception as e:
                    file_errs.append({
                        "type": "error",
                        "message": str(e),
                    })

                if file_errs:
                    file_errors[path] = file_errs
                    for err in file_errs:
                        errors.append({
                            "file": path,
                            **err,
                        })

        passed = len(errors) == 0
        return {
            "passed": passed,
            "errors": errors,
            "file_errors": file_errors,
        }


class ProjectGeneratorTool(BaseTool):
    """项目结构生成工具"""
    name = "project_generator"
    description = "生成项目目录结构"

    async def run(self, **kwargs) -> Dict[str, Any]:
        requirements = kwargs.get("requirements", {})
        tech_stack = kwargs.get("tech_stack", {})
        result = await self.llm.generate_structured(
            "你是一位资深项目架构师。请根据需求和技术栈生成项目结构。",
            f"需求：{requirements}\n技术栈：{tech_stack}",
            MVPCodeOutput
        )
        return result.model_dump()


class CodeGeneratorTool(BaseTool):
    """代码生成工具"""
    name = "code_generator"
    description = "生成代码文件"

    async def run(self, **kwargs) -> Dict[str, Any]:
        requirements = kwargs.get("requirements", {})
        tech_stack = kwargs.get("tech_stack", {})
        result = await self.llm.generate_structured(
            "你是一位资深全栈开发工程师。请根据需求和技术栈生成代码。",
            f"需求：{requirements}\n技术栈：{tech_stack}",
            MVPCodeOutput
        )
        return result.model_dump()
