"""
MVP实现Agent
"""

import time
from typing import Dict, Any, List
from agents.base import BaseAgent, AgentResult
from llm.adapter import LLMAdapter
from schemas import MVPCodeOutput


class MVPAgent(BaseAgent):
    """
    MVP实现Agent
    
    支持迭代优化：
    - 首次生成：根据需求和技术方案生成代码
    - 改进生成：根据code_review/testing/编译的feedback修复代码
    """

    name = "mvp"

    def __init__(self, llm: LLMAdapter):
        super().__init__(llm)

    async def execute(self, **kwargs) -> AgentResult:
        technical_solution = kwargs.get("technical_solution", {})
        requirements = kwargs.get("requirements", {})
        feedback = kwargs.get("feedback", None)
        current_code = kwargs.get("current_code", [])
        iteration = kwargs.get("iteration", 0)

        if not technical_solution:
            return self._error("缺少 technical_solution 参数")

        start = time.time()
        try:
            tech_stack = technical_solution.get("tech_stack", {})
            api_design = technical_solution.get("api_design", {})
            db_design = technical_solution.get("database_design", {})

            if feedback and current_code:
                result = await self._improve_code(
                    current_code=current_code,
                    feedback=feedback,
                    requirements=requirements,
                    tech_stack=tech_stack,
                    iteration=iteration,
                )
            else:
                result = await self._generate_code(
                    requirements=requirements,
                    tech_stack=tech_stack,
                    api_design=api_design,
                    db_design=db_design,
                )

            data = result.model_dump()

            # 调试：检查LLM返回的数据
            code_files = data.get("code_files", [])
            if not code_files:
                # LLM返回了空code_files，可能是schema解析问题
                # 尝试直接从result获取
                if hasattr(result, 'code_files') and result.code_files:
                    data["code_files"] = [
                        {"path": f.path, "content": f.content, "language": f.language}
                        for f in result.code_files
                    ]

            if not data.get("code_files"):
                data["code_files"] = self._default_code_files()

            return self._success(data, time.time() - start)
        except Exception as e:
            return self._error(str(e), time.time() - start)

    async def _generate_code(
        self,
        requirements: Dict,
        tech_stack: Dict,
        api_design: Dict,
        db_design: Dict,
    ) -> MVPCodeOutput:
        """首次生成代码"""
        return await self.llm.generate_structured(
            """你是一位资深全栈开发工程师。请根据需求和技术栈生成MVP代码。

要求：
1. 必须生成至少2-3个代码文件（如main.py, models.py, routes.py）
2. 每个文件必须包含完整的可运行代码
3. 代码使用指定的技术栈
4. 生成requirements.txt或package.json等依赖文件
5. 项目名称使用小写字母和下划线
6. 确保代码语法正确，没有缩进错误""",
            f"""需求：{requirements}
技术栈：{tech_stack}
API设计：{api_design}
数据库设计：{db_design}

请生成完整的MVP代码，包含所有必要的文件。""",
            MVPCodeOutput,
        )

    async def _improve_code(
        self,
        current_code: List[Dict[str, Any]],
        feedback: Dict[str, Any],
        requirements: Dict,
        tech_stack: Dict,
        iteration: int,
    ) -> MVPCodeOutput:
        """根据反馈改进代码"""
        issues = feedback.get("issues", [])
        bugs = feedback.get("bugs", [])
        suggestions = feedback.get("suggestions", [])
        compile_errors = feedback.get("compile_errors", [])

        feedback_text = ""

        if compile_errors:
            feedback_text += "编译/语法错误（必须修复）：\n"
            for err in compile_errors:
                file_path = err.get("file", "unknown")
                err_type = err.get("type", "unknown")
                line = err.get("line", "")
                message = err.get("message", "")
                if line:
                    feedback_text += f"- {file_path}:{line} [{err_type}] {message}\n"
                else:
                    feedback_text += f"- {file_path} [{err_type}] {message}\n"
            feedback_text += "\n"

        if issues:
            feedback_text += "代码审查发现的问题：\n"
            for issue in issues:
                severity = issue.get("severity", "minor")
                desc = issue.get("description", "")
                suggestion = issue.get("suggestion", "")
                feedback_text += f"- [{severity}] {desc}\n  建议：{suggestion}\n"
            feedback_text += "\n"

        if bugs:
            feedback_text += "测试发现的Bug：\n"
            for bug in bugs:
                severity = bug.get("severity", "minor")
                desc = bug.get("description", "")
                feedback_text += f"- [{severity}] {desc}\n"
            feedback_text += "\n"

        if suggestions:
            feedback_text += "改进建议：\n"
            for s in suggestions:
                feedback_text += f"- {s}\n"

        return await self.llm.generate_structured(
            f"""你是一位资深全栈开发工程师。这是第{iteration}次代码改进。

请根据以下反馈修复代码中的问题：
1. 优先修复编译/语法错误（必须修复）
2. 修复所有标记为 critical 和 major 的问题
3. 修复所有Bug
4. 保留代码的正常功能
5. 确保修复后的代码语法正确、可编译""",
            f"""当前代码：
{current_code}

需要修复的问题：
{feedback_text}

技术栈：{tech_stack}
需求：{requirements}

请输出修复后的完整代码。""",
            MVPCodeOutput,
        )

    def _default_code_files(self) -> List[Dict[str, Any]]:
        return [
            {
                "path": "main.py",
                "content": '"""MVP主程序"""\nfrom fastapi import FastAPI\n\napp = FastAPI(title="MVP应用")\n\n@app.get("/")\ndef root():\n    return {"message": "Hello World"}\n\n@app.get("/health")\ndef health():\n    return {"status": "ok"}\n',
                "language": "python",
            },
            {
                "path": "requirements.txt",
                "content": "fastapi==0.104.1\nuvicorn==0.24.0\n",
                "language": "text",
            },
        ]
