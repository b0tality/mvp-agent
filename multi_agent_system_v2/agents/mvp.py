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
            """你是一位资深全栈开发工程师。请生成一个可运行的 Web MVP（后端 FastAPI + 极简前端）。

硬性要求：
1. 后端用 FastAPI，主入口必须是 main.py，且包含 `app = FastAPI(...)`（这样能 `uvicorn main:app` 启动）。
2. 所有代码文件放在项目根目录（扁平结构，模块间用相对导入，如 `from models import X`）。
3. 只生成一个测试文件 tests/test_api.py（放入 test_files 字段，不是 code_files），用 pytest + httpx 的 AsyncClient + ASGITransport（或 fastapi.testclient.TestClient）打内存中的 app；
   覆盖每个核心功能（含正常用例和异常/边界用例）。禁止生成用 requests 打真实服务器（127.0.0.1）的测试，禁止生成 test_acceptance.py。
4. 必须生成 requirements.txt（列出 fastapi、uvicorn、pytest、httpx 等依赖）。
   尽量用标准库实现，减少外部依赖。密码哈希**必须用标准库** hashlib（如 pbkdf2_hmac 或 sha256+随机盐），
   **禁止引入 passlib/bcrypt**（passlib 1.7.4 与 bcrypt>=4.1 不兼容，会报
   "password cannot be longer than 72 bytes" 或 "bcrypt has no attribute __about__"）。
   JWT 可用 PyJWT（import jwt as pyjwt），或手写 HMAC 签名；不要从 main 里 import jwt 别名。
5. 功能要真实实现，不能是 TODO 占位；接口要返回正确数据。
6. 项目名称放在 project_name 字段，小写字母+下划线。
7. 若生成前端静态页面（如 index.html），必须在 main.py 里用 StaticFiles 或路由把它服务出来；否则不要生成前端文件。
8. 代码语法正确、可编译、无缩进错误。""",
            f"""需求：{requirements}
技术栈：{tech_stack}
API设计：{api_design}
数据库设计：{db_design}

请生成完整的、可直接运行的 Web MVP 代码和测试。""",
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

        test_output = feedback.get("test_output", "")
        if test_output:
            feedback_text += "真实测试运行输出（务必让所有测试通过，看 traceback 定位）：\n"
            feedback_text += test_output[:4000]
            feedback_text += "\n\n"

        acceptance_failures = feedback.get("acceptance_failures", [])
        if acceptance_failures:
            feedback_text += "验收标准未满足（需求 vs 实现的差距，必须按需求修复，不要迁就代码现有行为）：\n"
            for a in acceptance_failures:
                cid = a.get("criterion_id", "")
                desc = a.get("description", "")
                detail = a.get("detail", "")
                feedback_text += f"- [{cid}] {desc} — {detail}\n"
            feedback_text += "\n"

        acceptance_raw = feedback.get("acceptance_raw_output", "")
        if acceptance_raw:
            feedback_text += "验收测试原始输出（看具体断言差异，按需求修正）：\n"
            feedback_text += acceptance_raw[:3000]
            feedback_text += "\n\n"

        if suggestions:
            feedback_text += "改进建议：\n"
            for s in suggestions:
                feedback_text += f"- {s}\n"

        return await self.llm.generate_structured(
            f"""你是一位资深全栈开发工程师。这是第{iteration}次代码改进。

请根据以下反馈修复代码，目标是让真实测试全部通过：
1. 优先修复编译/语法错误（必须修复）
2. 修复所有 critical 和 major 的问题
3. 修复所有失败的测试（参考「真实测试运行输出」里的 traceback 和断言差异）
4. 只做针对性最小修改，不要重写已通过测试的代码，不要删除已有端点/功能
5. 若验收要求某类输入返回特定状态码（如 400），而当前返回的是框架默认值（如 FastAPI 的 422 校验错误），需显式处理（添加 RequestValidationError 异常处理器返回 400，或改为手动校验），而不是让框架兜底返回 422
6. 确保修复后的代码语法正确、可编译、可运行
7. 必须输出 test_files 字段：重新生成测试文件 tests/test_api.py，用 pytest + httpx 覆盖所有核心功能（含正常与异常/边界用例）。不要把测试文件放进 code_files。""",
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
