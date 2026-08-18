"""
验收测试Agent —— 把验收标准（考卷）转成可执行 pytest 并真实运行

核心作用：需求阶段产出的 acceptance_criteria 是「考卷」，本 agent 在代码生成后，
把考卷逐条转成真实可跑的测试，核对「需求说返回 400，代码到底是不是 400」。

与 MVP 自带的测试不同：
- MVP 测试由生成代码的同一个 LLM 所写，可能与错误实现互相印证（自洽但错）；
- 验收测试由验收标准驱动，严格按需求断言，代码错了就必须让它失败。
"""

import os
import re
import sys
import time
import shutil
import tempfile
import subprocess
from typing import Dict, Any, List

from agents.base import BaseAgent, AgentResult
from llm.adapter import LLMAdapter


class AcceptanceAgent(BaseAgent):
    """验收测试Agent：真实执行验收标准"""

    name = "acceptance"

    def __init__(self, llm: LLMAdapter, timeout: int = 120):
        super().__init__(llm)
        self.timeout = timeout

    async def execute(self, **kwargs) -> AgentResult:
        criteria = kwargs.get("acceptance_criteria", []) or []
        code_files = kwargs.get("code_files", []) or []
        api_design = kwargs.get("api_design", {}) or {}

        if not criteria:
            return self._success({
                "results": [], "total": 0, "passed": 0, "failed": 0,
                "all_passed": True, "raw_output": "",
            })

        if not code_files:
            results = [{
                "criterion_id": c.get("id", ""),
                "description": c.get("description", ""),
                "passed": False, "detail": "无代码",
            } for c in criteria]
            return self._success({
                "results": results, "total": len(criteria), "passed": 0,
                "failed": len(criteria), "all_passed": False, "raw_output": "",
            })

        start = time.time()
        try:
            test_code = await self._generate_acceptance_tests(criteria, code_files, api_design)
            data = self._run_acceptance_tests(criteria, code_files, test_code)
            return self._success(data, time.time() - start)
        except Exception as e:
            return self._error(str(e), time.time() - start)

    # ------------------------------------------------------------------
    # 生成验收测试
    # ------------------------------------------------------------------
    async def _generate_acceptance_tests(self, criteria, code_files, api_design) -> str:
        system = """你是一位严格的验收测试工程师。请把「验收标准」逐条转成可执行的 pytest 测试。

要求：
1. 每个验收标准生成一个测试函数，函数名必须是 test_ac_<criterion_id>，其中 criterion_id 里的非字母数字字符替换为下划线（如 AC-001 → test_ac_AC_001）。
2. 测试从主模块 import FastAPI 实例（通常 `from main import app`），用 httpx 打真实接口：
   transport = ASGITransport(app=app) 然后 async with AsyncClient(transport=transport, base_url="http://test") as client。
3. 严格按验收标准里写明的期望来断言（状态码、返回内容），不要迁就代码的实际行为——代码错了就必须让它测失败。
4. 根据 api_design 和代码确定正确的 method、path、请求体字段名。
5. 只测验收标准明确要求的行为，不额外发挥。
6. 只输出纯 pytest 代码，不要输出 markdown 代码块标记，不要任何解释文字。"""
        user = f"""验收标准：
{criteria}

API设计：
{api_design}

代码文件（参考导入方式和接口签名）：
{code_files}"""
        code = await self.llm.generate(system, user)
        return self._strip_code_fences(code)

    @staticmethod
    def _strip_code_fences(code: str) -> str:
        code = (code or "").strip()
        m = re.search(r"```(?:python|py)?\s*\n(.*?)```", code, re.DOTALL)
        if m:
            return m.group(1).strip()
        return code

    # ------------------------------------------------------------------
    # 执行验收测试
    # ------------------------------------------------------------------
    def _run_acceptance_tests(self, criteria, code_files, test_code) -> Dict[str, Any]:
        sandbox = tempfile.mkdtemp(prefix="magent_accept_")
        try:
            self._write_files(sandbox, code_files)
            test_path = os.path.join(sandbox, "test_acceptance.py")
            with open(test_path, "w", encoding="utf-8") as f:
                f.write(test_code)

            env = dict(os.environ)
            env["PYTHONPATH"] = sandbox + os.pathsep + env.get("PYTHONPATH", "")
            env["PYTHONIOENCODING"] = "utf-8"

            try:
                proc = subprocess.run(
                    [sys.executable, "-m", "pytest", "-v", "--tb=line", "-p", "no:cacheprovider"],
                    cwd=sandbox, env=env, capture_output=True, text=True, timeout=self.timeout,
                )
            except subprocess.TimeoutExpired:
                return self._build_failed(criteria, "验收测试执行超时", "")

            output = (proc.stdout or "") + "\n" + (proc.stderr or "")
            return self._parse_results(criteria, output)
        finally:
            shutil.rmtree(sandbox, ignore_errors=True)

    def _parse_results(self, criteria, output) -> Dict[str, Any]:
        results = []
        for i, c in enumerate(criteria):
            cid = str(c.get("id") or "")
            sanitized = re.sub(r"[^0-9a-zA-Z_]", "_", cid) or f"criterion_{i + 1}"
            test_name = f"test_ac_{sanitized}"

            # 用 `::` 锚定 + 要求函数名后紧跟空白，避免前缀误匹配：
            # 如 AC-001 不能匹配到 AC-001_ERROR_EMPTY_TITLE（后者 FAILED 会污染前者）
            m = re.search(rf"::{re.escape(test_name)}\s+(PASSED|FAILED|ERROR)", output)
            status = m.group(1) if m else None

            if status is None:
                passed = False
                if "error" in output.lower() or "ERROR" in output:
                    detail = "验收测试收集/运行失败（见原始输出）"
                else:
                    detail = "未生成对应验收测试"
            else:
                passed = status == "PASSED"
                detail = {
                    "PASSED": "验收通过",
                    "FAILED": "验收失败（代码行为不符合需求）",
                    "ERROR": "验收测试运行错误",
                }[status]

            results.append({
                "criterion_id": cid,
                "description": c.get("description", ""),
                "passed": passed,
                "detail": detail,
            })

        passed = sum(1 for r in results if r["passed"])
        failed = len(results) - passed
        return {
            "results": results,
            "total": len(results),
            "passed": passed,
            "failed": failed,
            "all_passed": failed == 0,
            "raw_output": output,
        }

    def _build_failed(self, criteria, detail, output) -> Dict[str, Any]:
        results = [{
            "criterion_id": c.get("id", ""),
            "description": c.get("description", ""),
            "passed": False, "detail": detail,
        } for c in criteria]
        return {
            "results": results, "total": len(criteria), "passed": 0,
            "failed": len(criteria), "all_passed": False, "raw_output": output,
        }

    def _write_files(self, sandbox: str, files: List[Dict]) -> None:
        for f in files:
            path = (f.get("path") or "").strip().lstrip("/\\")
            content = f.get("content") or ""
            if not path or not content:
                continue
            clean = os.path.normpath(path)
            if clean.startswith("..") or os.path.isabs(clean):
                continue
            dest = os.path.join(sandbox, clean)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with open(dest, "w", encoding="utf-8") as fh:
                fh.write(content)
