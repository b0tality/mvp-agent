"""
测试Agent —— 真实执行验证

不再让LLM"假装"测试，而是把生成的代码真实跑起来：
1. 把代码 + 测试写入沙箱
2. 真实运行 pytest（含集成测试，用 TestClient 打真实接口）
3. 启动应用做冒烟探活（导入 FastAPI 实例，GET /openapi.json 和 /）
4. 测量行覆盖率（coverage 可用时）
5. 返回真实结果，失败信息用于回灌 MVP 修复
"""

import os
import re
import sys
import json
import time
import shutil
import tempfile
import subprocess
import importlib.util
from typing import Dict, Any, List

from agents.base import BaseAgent, AgentResult
from llm.adapter import LLMAdapter


class TestingAgent(BaseAgent):
    """测试Agent：真实执行验证"""

    name = "testing"

    def __init__(self, llm: LLMAdapter, timeout: int = 120):
        super().__init__(llm)
        self.timeout = timeout

    async def execute(self, **kwargs) -> AgentResult:
        code_files = kwargs.get("code_files", [])
        project_info = kwargs.get("project_info", {}) or {}
        test_files = kwargs.get("test_files", []) or project_info.get("test_files", [])

        if not code_files:
            return self._success({
                "test_cases": [], "bugs": [],
                "coverage": {"line": 0, "branch": 0, "function": 0},
                "total_tests": 0, "passed": 0, "failed": 0,
                "all_passed": False, "smoke_test": {"passed": False, "detail": "无代码"},
                "summary": "无代码需要测试", "suggestions": [], "raw_output": "",
            })

        start = time.time()
        try:
            data = await self._run_real_tests(code_files, test_files)
            return self._success(data, time.time() - start)
        except Exception as e:
            return self._error(str(e), time.time() - start)

    async def _run_real_tests(self, code_files: List[Dict], test_files: List[Dict]) -> Dict[str, Any]:
        """把代码写入沙箱并真实执行测试。"""
        sandbox = tempfile.mkdtemp(prefix="magent_test_")
        try:
            self._write_files(sandbox, code_files)
            self._write_files(sandbox, test_files)

            # 1. 真实运行 pytest（coverage 可用时顺带测覆盖率）
            pytest_result, coverage = self._run_pytest_with_coverage(sandbox)

            # 2. 启动应用做冒烟探活
            smoke = self._run_smoke_test(sandbox)

            bugs = self._extract_bugs(pytest_result)

            # 至少要有测试真实跑起来并全部通过才算 all_passed（0 个测试不算通过）
            no_tests = pytest_result["passed"] == 0 and pytest_result["failed"] == 0
            all_passed = (pytest_result["failed"] == 0 and not no_tests
                          and smoke.get("passed", False))

            return {
                "test_cases": [],
                "coverage": coverage,
                "bugs": bugs,
                "total_tests": pytest_result["total"],
                "passed": pytest_result["passed"],
                "failed": pytest_result["failed"],
                "all_passed": all_passed,
                "smoke_test": smoke,
                "summary": pytest_result["summary"],
                "suggestions": self._extract_suggestions(pytest_result, bugs),
                "raw_output": pytest_result["raw"],
            }
        finally:
            shutil.rmtree(sandbox, ignore_errors=True)

    # ------------------------------------------------------------------
    # 文件与执行
    # ------------------------------------------------------------------
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

    def _env(self, sandbox: str) -> Dict[str, str]:
        env = dict(os.environ)
        env["PYTHONPATH"] = sandbox + os.pathsep + env.get("PYTHONPATH", "")
        env["PYTHONIOENCODING"] = "utf-8"
        return env

    def _run_pytest_with_coverage(self, sandbox: str):
        """运行 pytest，coverage 可用时顺带测覆盖率。返回 (pytest_result, coverage)。"""
        env = self._env(sandbox)
        coverage_available = importlib.util.find_spec("coverage") is not None

        base = [sys.executable, "-m", "pytest", "-q", "--tb=short", "-p", "no:cacheprovider"]
        if coverage_available:
            cmd = [sys.executable, "-m", "coverage", "run", "--source=.", "-m", "pytest",
                   "-q", "--tb=short", "-p", "no:cacheprovider"]
        else:
            cmd = base

        try:
            proc = subprocess.run(cmd, cwd=sandbox, env=env,
                                  capture_output=True, text=True, timeout=self.timeout)
        except subprocess.TimeoutExpired:
            return ({"total": 0, "passed": 0, "failed": 0, "summary": "pytest 执行超时", "raw": ""},
                    {"line": -1, "branch": -1, "function": -1, "available": coverage_available})

        output = (proc.stdout or "") + "\n" + (proc.stderr or "")

        passed = failed = 0
        m = re.search(r"(\d+)\s+passed", output)
        if m:
            passed = int(m.group(1))
        m = re.search(r"(\d+)\s+failed", output)
        if m:
            failed = int(m.group(1))
        m = re.search(r"(\d+)\s+error", output)
        if m:
            failed += int(m.group(1))

        summary = f"{passed} passed, {failed} failed"
        if "no tests ran" in output or (passed == 0 and failed == 0 and proc.returncode == 5):
            summary = "未收集到测试用例"

        coverage = self._coverage_report(sandbox, env) if coverage_available else \
            {"line": -1, "branch": -1, "function": -1, "available": False}

        return ({"total": passed + failed, "passed": passed, "failed": failed,
                 "summary": summary, "raw": output, "returncode": proc.returncode},
                coverage)

    def _coverage_report(self, sandbox: str, env: Dict[str, str]) -> Dict[str, Any]:
        try:
            r = subprocess.run([sys.executable, "-m", "coverage", "report", "-m"],
                               cwd=sandbox, env=env, capture_output=True, text=True, timeout=30)
            m = re.search(r"TOTAL\s+\d+\s+\d+\s+(\d+)%", r.stdout or "")
            # 无数据（如没有测试跑起来）视为 0% 覆盖率，而非 -1（-1 会被当作"无法测量"而跳过门槛）
            line = int(m.group(1)) if m else 0
            return {"line": line, "branch": -1, "function": -1, "available": True}
        except Exception as e:
            return {"line": -1, "branch": -1, "function": -1, "available": True, "error": str(e)}

    # ------------------------------------------------------------------
    # 冒烟测试：真实启动应用并探活
    # ------------------------------------------------------------------
    def _run_smoke_test(self, sandbox: str) -> Dict[str, Any]:
        probe = '''
import json, importlib
from fastapi import FastAPI

app = None
for name in ("main", "app", "server"):
    try:
        mod = importlib.import_module(name)
    except Exception:
        continue
    for attr in dir(mod):
        obj = getattr(mod, attr)
        if isinstance(obj, FastAPI):
            app = obj
            break
    if app is not None:
        break

if app is None:
    print(json.dumps({"error": "未找到 FastAPI 实例（main.py 需包含 app = FastAPI(...)）"}))
else:
    from fastapi.testclient import TestClient
    client = TestClient(app)
    out = {}
    for path in ("/openapi.json", "/"):
        try:
            out[path] = client.get(path).status_code
        except Exception as e:
            out[path] = f"error:{e}"
    print(json.dumps(out))
'''
        probe_path = os.path.join(sandbox, "_smoke_probe.py")
        with open(probe_path, "w", encoding="utf-8") as f:
            f.write(probe)

        try:
            proc = subprocess.run([sys.executable, probe_path], cwd=sandbox,
                                  env=self._env(sandbox), capture_output=True, text=True, timeout=30)
        except subprocess.TimeoutExpired:
            return {"passed": False, "detail": "冒烟测试超时"}

        out = (proc.stdout or "").strip()
        stderr = (proc.stderr or "").strip()
        if proc.returncode != 0 or not out:
            return {"passed": False, "detail": (stderr or "应用无法导入/启动")[:500]}

        try:
            result = json.loads(out)
        except json.JSONDecodeError:
            return {"passed": False, "detail": out[:500]}

        if "error" in result:
            return {"passed": False, "detail": result["error"][:500]}

        openapi_status = result.get("/openapi.json")
        passed = openapi_status == 200
        detail = "应用真实启动成功，/openapi.json 返回 200" if passed else f"探活失败: {result}"
        return {"passed": passed, "detail": detail}

    # ------------------------------------------------------------------
    # 从真实输出提取 Bug 和建议
    # ------------------------------------------------------------------
    def _extract_bugs(self, pytest_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        bugs = []
        output = pytest_result.get("raw", "")

        # 没有收集到任何测试 → critical（测试缺失，无法验证功能）
        if pytest_result.get("passed", 0) == 0 and pytest_result.get("failed", 0) == 0:
            bugs.append({
                "id": "BUG-NOTESTS",
                "severity": "critical",
                "description": "未收集到任何测试用例（pytest 未发现 tests/test_api.py，MVP 可能漏生成测试文件）",
                "file_path": "",
                "steps_to_reproduce": "运行 pytest，确认存在 tests/test_api.py",
            })

        # 收集/导入错误 → critical（应用根本跑不起来）
        for m in re.finditer(r"^ERROR (.+)$", output, re.MULTILINE):
            bugs.append({
                "id": f"BUG-{len(bugs) + 1}",
                "severity": "critical",
                "description": f"测试收集/导入错误: {m.group(1).strip()}",
                "file_path": "",
                "steps_to_reproduce": f"运行 pytest，见原始输出",
            })

        # 断言失败 → major
        for m in re.finditer(r"^FAILED (.+?)(?: - (.+))?$", output, re.MULTILINE):
            name = m.group(1).strip()
            detail = (m.group(2) or "").strip()
            bugs.append({
                "id": f"BUG-{len(bugs) + 1}",
                "severity": "major",
                "description": f"测试失败: {name}" + (f" — {detail}" if detail else ""),
                "file_path": name.split("::")[0],
                "steps_to_reproduce": f"运行 pytest {name}",
            })

        # 有失败但没解析到具体条目（如非标准输出）
        if pytest_result.get("failed", 0) > 0 and not bugs:
            bugs.append({
                "id": "BUG-1",
                "severity": "major",
                "description": f"{pytest_result.get('failed', 0)} 个测试失败（见原始输出）",
                "file_path": "",
                "steps_to_reproduce": "运行 pytest",
            })

        return bugs

    def _extract_suggestions(self, pytest_result: Dict[str, Any], bugs: List[Dict]) -> List[str]:
        suggestions = []
        if bugs:
            suggestions.append("修复所有失败的测试，重点看原始输出的 traceback 定位问题")
        if pytest_result.get("returncode") not in (0, None):
            suggestions.append(f"pytest 返回码 {pytest_result.get('returncode')}，请修复后重新验证")
        return suggestions
