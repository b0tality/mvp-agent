"""
Builder Agent —— 用 function-calling 自主完成「生成→编译→测试→修复」闭环

与旧 MVPAgent 的差别：
- 旧 MVP 只负责生成代码，编译/测试/修复的循环由 orchestrator 硬编码驱动；
- BuilderAgent 用 LLM 的 tool_calls 自己决定何时写代码、何时编译、何时测试、何时停。

关键设计：工具是「带状态」的——代码存在 builder 实例里，LLM 调 verify_code()/run_tests()
时只传空参数，由闭包从状态读代码，避免 LLM 在工具参数里搬运整份代码（费 token 且不可靠）。
"""

import time
from typing import Dict, Any, List

from agents.base import BaseAgent, AgentResult
from llm.adapter import LLMAdapter
from tools.executors import verify_code, run_tests


_FILE_SCHEMA = {
    "type": "object",
    "properties": {
        "path": {"type": "string", "description": "文件路径，如 main.py"},
        "content": {"type": "string", "description": "文件内容"},
        "language": {"type": "string", "description": "语言，如 python"},
    },
    "required": ["path", "content"],
}


class BuilderAgent(BaseAgent):
    """Builder Agent：带状态的 agentic 代码生成与修复循环"""

    name = "builder"

    def __init__(self, llm: LLMAdapter, max_rounds: int = 8):
        super().__init__(llm)
        self.max_rounds = max_rounds
        self.code_files: List[Dict] = []
        self.test_files: List[Dict] = []
        self.project_name: str = ""
        self.last_verify: Dict[str, Any] = {}
        self.last_tests: Dict[str, Any] = {}

    async def execute(self, **kwargs) -> AgentResult:
        user_input = kwargs.get("user_input", "")
        requirements = kwargs.get("requirements", {})
        technical_solution = kwargs.get("technical_solution", {})
        feedback = kwargs.get("feedback")
        current_code = kwargs.get("current_code") or []
        current_test_files = kwargs.get("current_test_files") or []
        project_name = kwargs.get("project_name", "")
        iteration = kwargs.get("iteration", 0)

        if not user_input and not technical_solution:
            return self._error("缺少 user_input 或 technical_solution 参数")

        start = time.time()
        try:
            # 重置状态；迭代模式（feedback + 上一版代码）则从现有代码起跑，定点修复而非从零重写
            self.code_files = list(current_code)
            self.test_files = list(current_test_files)
            self.project_name = project_name
            self.last_verify = {}
            self.last_tests = {}

            iterating = bool(feedback and current_code)
            final_text = await self.llm.generate_with_tools(
                self._system_prompt(iterating=iterating),
                self._user_prompt(user_input, requirements, technical_solution, feedback, iteration),
                self._tool_schemas(),
                self._build_handlers(),
                max_rounds=self.max_rounds,
            )

            if not self.code_files:
                return self._error("Builder 未产出任何代码（LLM 未调用 write_code）", time.time() - start)

            data = {
                "code_files": self.code_files,
                "test_files": self.test_files,
                "project_name": self.project_name or "builder_project",
                "verify_result": self.last_verify,
                "test_result": self.last_tests,
                "final_text": final_text,
            }
            return self._success(data, time.time() - start)
        except Exception as e:
            return self._error(str(e), time.time() - start)

    # ------------------------------------------------------------------
    # 工具 handlers（闭包捕获 self，读写工作区状态）
    # ------------------------------------------------------------------
    def _build_handlers(self) -> Dict[str, Any]:
        async def _write_code(args):
            # 只覆盖「明确传入」的字段：迭代修复时 LLM 若只改了代码没重传测试，
            # 已 seed 的测试文件不会被清空。
            if "code_files" in args:
                self.code_files = args.get("code_files") or []
            if "test_files" in args:
                self.test_files = args.get("test_files") or []
            if args.get("project_name"):
                self.project_name = args["project_name"]
            return {
                "written": len(self.code_files) + len(self.test_files),
                "code_files": len(self.code_files),
                "test_files": len(self.test_files),
            }

        async def _verify_code(args):
            self.last_verify = await verify_code(self.code_files)
            return self.last_verify

        async def _run_tests(args):
            r = await run_tests(self.code_files, self.test_files)
            # 截断原始输出，避免 traceback 撑爆回灌上下文
            r = dict(r)
            r["raw_output"] = (r.get("raw_output") or "")[:4000]
            self.last_tests = r
            return r

        return {
            "write_code": _write_code,
            "verify_code": _verify_code,
            "run_tests": _run_tests,
        }

    # ------------------------------------------------------------------
    # 工具 schema（带状态的最小参数版本）
    # ------------------------------------------------------------------
    @staticmethod
    def _tool_schemas() -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "write_code",
                    "description": "把生成的代码和测试写入工作区（覆盖旧代码）。这是你产出代码的唯一方式。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "code_files": {"type": "array", "items": _FILE_SCHEMA},
                            "test_files": {"type": "array", "items": _FILE_SCHEMA},
                            "project_name": {"type": "string", "description": "项目名，小写字母+下划线"},
                        },
                        "required": ["code_files"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "verify_code",
                    "description": "对工作区当前代码做语法(AST)+编译(py_compile)检查，返回错误列表。",
                    "parameters": {"type": "object", "properties": {}},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "run_tests",
                    "description": "真实运行工作区代码的 pytest + 覆盖率 + 冒烟探活，返回通过/失败数和 bug。",
                    "parameters": {"type": "object", "properties": {}},
                },
            },
        ]

    # ------------------------------------------------------------------
    # prompt
    # ------------------------------------------------------------------
    @staticmethod
    def _system_prompt(iterating: bool = False) -> str:
        base = """你是一位资深全栈开发工程师。目标是产出一个「编译通过 + 测试全过」的可运行 FastAPI MVP。

你有一个工作区，通过调用工具操作它：
- write_code：把生成的代码和测试写入工作区（覆盖旧代码）。这是你产出代码的唯一方式。
- verify_code：对工作区当前代码做编译/语法检查。
- run_tests：真实运行 pytest + 覆盖率 + 冒烟探活。

工作流程（用工具自主推进，不要问问题）：
1. 先 write_code 写入完整的代码 + 测试。
2. 调 verify_code 检查编译；有错误就 write_code 定点修复。
3. 调 run_tests 真实跑测试；有失败就根据 traceback/断言差异 write_code 修复，只改有问题的部分，不要重写已通过的代码。
4. 重复直到 run_tests 返回 all_passed=true，然后停（不再调用工具，只给一句简短总结）。

硬性要求：
- 后端用 FastAPI，主入口 main.py 且包含 `app = FastAPI(...)`。
- 测试文件放 tests/test_api.py，用 pytest + httpx 的 AsyncClient + ASGITransport 或 fastapi.testclient.TestClient 打内存中的 app；覆盖核心功能（含正常与异常用例）。
- 必须生成 requirements.txt（fastapi、uvicorn、pytest、httpx 等）。
- 功能要真实实现，不能是 TODO 占位。
- 代码语法正确、可编译、可运行。"""

        if iterating:
            base += """

【本轮是修复迭代】工作区里已放有上一版的代码和测试（不是你新写的，是历史版本）。
请按下面顺序推进，只做针对性修复：
1. 先调 run_tests 看当前失败状态（或直接 write_code 定点修复）。
2. 根据「需要修复的问题」里列出的 code_review 问题、验收标准差距、测试失败，write_code 定点修改。
3. 只改有问题的部分；不要删除已有端点/功能，不要重写已通过的测试，不要引入与需求无关的新功能。
4. 修完调 verify_code + run_tests 验证，直到 all_passed=true 再停。"""
        return base

    @staticmethod
    def _user_prompt(
        user_input: str,
        requirements: Dict,
        technical_solution: Dict,
        feedback: Dict = None,
        iteration: int = 0,
    ) -> str:
        parts = []
        if iteration:
            parts.append(f"【第 {iteration} 次修复迭代】")
        if user_input:
            parts.append(f"需求：{user_input}")
        if technical_solution:
            parts.append(f"技术方案：{technical_solution}")
        if requirements:
            parts.append(f"结构化需求：{requirements}")
        if feedback:
            parts.append(BuilderAgent._format_feedback(feedback))
        return "\n\n".join(parts) if parts else "请生成一个 FastAPI MVP。"

    @staticmethod
    def _format_feedback(feedback: Dict) -> str:
        """把外部反馈（code_review/testing/acceptance）格式化成 LLM 能据以修复的文本。"""
        lines = ["需要修复的问题（务必全部处理）："]

        compile_errors = feedback.get("compile_errors") or []
        if compile_errors:
            lines.append("编译/语法错误（必须修复）：")
            for err in compile_errors:
                file_path = err.get("file", "unknown")
                err_type = err.get("type", "unknown")
                line = err.get("line", "")
                message = err.get("message", "")
                loc = f"{file_path}:{line}" if line else file_path
                lines.append(f"- {loc} [{err_type}] {message}")

        issues = feedback.get("issues") or []
        if issues:
            lines.append("代码审查发现的问题：")
            for issue in issues:
                severity = issue.get("severity", "minor")
                desc = issue.get("description", "")
                suggestion = issue.get("suggestion", "")
                lines.append(f"- [{severity}] {desc}" + (f"\n  建议：{suggestion}" if suggestion else ""))

        bugs = feedback.get("bugs") or []
        if bugs:
            lines.append("测试发现的 Bug：")
            for bug in bugs:
                severity = bug.get("severity", "minor")
                desc = bug.get("description", "")
                lines.append(f"- [{severity}] {desc}")

        acceptance_failures = feedback.get("acceptance_failures") or []
        if acceptance_failures:
            lines.append("验收标准未满足（需求 vs 实现的差距，按需求修复，不要迁就代码现有行为）：")
            for a in acceptance_failures:
                cid = a.get("criterion_id", "")
                desc = a.get("description", "")
                detail = a.get("detail", "")
                lines.append(f"- [{cid}] {desc} — {detail}")

        hints = feedback.get("hints") or []
        if hints:
            lines.append("修复提示（针对性技术要点，务必照做）：")
            for h in hints:
                lines.append(f"- {h}")

        test_output = feedback.get("test_output") or ""
        if test_output:
            lines.append("真实测试运行输出（看 traceback 定位）：\n" + test_output[:4000])

        acceptance_raw = feedback.get("acceptance_raw_output") or ""
        if acceptance_raw:
            lines.append("验收测试原始输出（看具体断言差异）：\n" + acceptance_raw[:3000])

        suggestions = feedback.get("suggestions") or []
        if suggestions:
            lines.append("改进建议：")
            for s in suggestions:
                lines.append(f"- {s}")

        return "\n".join(lines)
