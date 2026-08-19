"""
真执行器：把生成的代码真实跑起来验证（无 LLM，纯确定性）。

这些是 function-calling 工具的 handler 本体，也是 TestingAgent / AcceptanceAgent /
CodeVerifierTool 共享的唯一实现源。签名都接收显式数据（code_files/test_files/...），
不持有状态，便于单独测试与被 LLM 工具调用复用。

三个执行器：
- verify_code(code_files)              编译/语法验证（ast.parse + py_compile）
- run_tests(code_files, test_files)    pytest + coverage + 冒烟探活
- run_acceptance(criteria, code_files, test_code)  运行验收 pytest
"""

import os
import re
import sys
import ast
import json
import shutil
import tempfile
import subprocess
import importlib.util
from typing import Dict, Any, List

from tools.deps import ensure_deps, install_packages

# Python 3.10+ 提供；老版本回退空集（此时 stdlib 误判只会多一次 pip 尝试，无副作用）
_STDLIB_MODULES = set(getattr(sys, "stdlib_module_names", ()))

# 执行环境常带 FORCE_COLOR/COLORTERM，pytest 输出会夹 ANSI 转义码，破坏 `^E`/`^ERROR`
# 这类行首锚定的正则解析。统一剥掉，保证原始输出可被确定性解析。
_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def _strip_ansi(s: str) -> str:
    return _ANSI_RE.sub("", s)


# ----------------------------------------------------------------------
# 共享工具函数
# ----------------------------------------------------------------------
def _write_files(sandbox: str, files: List[Dict]) -> None:
    """把文件列表写入沙箱，跳过空路径/空内容，拦截路径穿越。"""
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


def _env(sandbox: str, extra: str = None) -> Dict[str, str]:
    env = dict(os.environ)
    paths = [sandbox]
    if extra:
        paths.insert(0, extra)
    env["PYTHONPATH"] = os.pathsep.join(paths) + os.pathsep + env.get("PYTHONPATH", "")
    env["PYTHONIOENCODING"] = "utf-8"
    return env


# 生成代码常写异步 FastAPI + 异步测试（async def / AsyncClient / @pytest.mark.asyncio）。
# pytest-asyncio 默认 strict 模式不处理普通 @pytest.fixture 的 async fixture，导致
# 「requested an async fixture ... with no plugin that handled it」→ 全部收集错误。
# 在沙箱里写一个 pytest.ini 打开 auto 模式，兼容同步/异步两种测试写法。
_PYTEST_INI = """\
[pytest]
asyncio_mode = auto
asyncio_default_fixture_loop_scope = function
"""


def _write_pytest_ini(sandbox: str) -> None:
    with open(os.path.join(sandbox, "pytest.ini"), "w", encoding="utf-8") as f:
        f.write(_PYTEST_INI)


# ----------------------------------------------------------------------
# verify_code：编译验证
# ----------------------------------------------------------------------
async def verify_code(code_files: List[Dict]) -> Dict[str, Any]:
    """对代码文件做语法(AST)+编译(py_compile)检查，返回错误列表。"""
    if not code_files:
        return {"passed": True, "errors": [], "file_errors": {}}

    errors = []
    file_errors = {}

    with tempfile.TemporaryDirectory() as tmpdir:
        for cf in code_files:
            path = (cf.get("path") or "").strip().lstrip("/\\")
            content = cf.get("content") or ""
            if not path or not content:
                continue
            clean = os.path.normpath(path)
            if clean.startswith("..") or os.path.isabs(clean):
                continue
            file_path = os.path.join(tmpdir, clean)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

        for cf in code_files:
            path = (cf.get("path") or "").strip().lstrip("/\\")
            content = cf.get("content") or ""
            if not path.endswith(".py") or not content:
                continue
            clean = os.path.normpath(path)
            if clean.startswith("..") or os.path.isabs(clean):
                continue
            file_path = os.path.join(tmpdir, clean)
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
                    capture_output=True, text=True, timeout=10,
                )
                if result.returncode != 0:
                    file_errs.append({"type": "compile", "message": result.stderr.strip()})
            except subprocess.TimeoutExpired:
                file_errs.append({"type": "timeout", "message": "编译超时"})
            except Exception as e:
                file_errs.append({"type": "error", "message": str(e)})

            if file_errs:
                file_errors[path] = file_errs
                for err in file_errs:
                    errors.append({"file": path, **err})

    return {"passed": len(errors) == 0, "errors": errors, "file_errors": file_errors}


# ----------------------------------------------------------------------
# run_tests：真实跑 pytest + coverage + 冒烟
# ----------------------------------------------------------------------
async def run_tests(
    code_files: List[Dict],
    test_files: List[Dict],
    timeout: int = 120,
) -> Dict[str, Any]:
    """把代码+测试写入沙箱，真实运行 pytest、测覆盖率、启动应用冒烟探活。"""
    sandbox = tempfile.mkdtemp(prefix="magent_test_")
    try:
        _write_files(sandbox, code_files)
        _write_files(sandbox, test_files)
        _write_pytest_ini(sandbox)

        deps = ensure_deps(code_files)
        pytest_result, coverage, final_deps, auto_installed = _run_pytest_with_self_heal(
            sandbox, timeout, deps, code_files
        )
        smoke = _run_smoke_test(sandbox, final_deps)
        bugs = _extract_bugs(pytest_result)

        # 至少要有测试真实跑起来并全部通过才算 all_passed（0 个测试不算通过）
        no_tests = pytest_result["passed"] == 0 and pytest_result["failed"] == 0
        all_passed = (pytest_result["failed"] == 0 and not no_tests
                      and smoke.get("passed", False))

        return {
            "test_cases": [],
            "coverage": coverage,
            "auto_installed": auto_installed,
            "bugs": bugs,
            "total_tests": pytest_result["total"],
            "passed": pytest_result["passed"],
            "failed": pytest_result["failed"],
            "all_passed": all_passed,
            "smoke_test": smoke,
            "summary": pytest_result["summary"],
            "suggestions": _extract_suggestions(pytest_result, bugs),
            "raw_output": pytest_result["raw"],
        }
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)


def _local_module_stems(code_files: List[Dict]) -> set:
    """生成代码里本地 .py 文件的模块名（用于区分「缺依赖」和「本地模块缺失」）。"""
    stems = set()
    for cf in code_files:
        p = (cf.get("path") or "").replace("\\", "/").rstrip("/")
        if p.endswith(".py"):
            stems.add(os.path.splitext(os.path.basename(p))[0])
    return stems


def _extract_missing_third_party(output: str, code_files: List[Dict]) -> List[str]:
    """从 pytest 输出提取「缺失的三方依赖」顶层模块名（排除 stdlib 和本地代码模块）。

    只认 ModuleNotFoundError（缺包）；ImportError「cannot import name」是代码级导入 bug，
    不在这里处理——那需要改代码，不是装包能解决的。
    """
    found = set()
    for m in re.finditer(r"ModuleNotFoundError: No module named '([^']+)'", output or ""):
        found.add(m.group(1).split(".")[0])
    local = _local_module_stems(code_files)
    return sorted({
        mod for mod in found
        if mod and mod != "__main__" and mod not in _STDLIB_MODULES and mod not in local
    })


def _self_heal_loop(
    sandbox: str, timeout: int, deps: str, code_files: List[Dict],
    run_once, max_heal: int = 3,
):
    """环境自愈主循环：run_once(deps) → 检测缺失三方依赖 → 补装 → 重跑。

    run_once 是「用给定 PYTHONPATH 前缀跑一次测试并返回含 'raw' 字段的 dict」的可调用。
    返回 (result, final_deps, installed)。final_deps 是合并了自愈补装目录后的 PYTHONPATH
    前缀（冒烟/验收都要用它，否则会因缺依赖再次失败）；installed 是这次补装的包名。
    """
    result = run_once(deps)
    current_deps = deps
    installed: List[str] = []
    for _ in range(max_heal):
        missing = _extract_missing_third_party(result.get("raw", ""), code_files)
        if not missing:
            break
        extra = install_packages(missing)
        if not extra:
            break  # 装不上（无网络/包名错），退回现状，别再空转
        installed.extend(missing)
        current_deps = os.pathsep.join([p for p in (extra, current_deps) if p])
        result = run_once(current_deps)
    return result, current_deps, installed


def _run_pytest_with_self_heal(
    sandbox: str, timeout: int, deps: str, code_files: List[Dict], max_heal: int = 3,
):
    """跑 pytest + coverage，检测到缺失三方依赖就自动补装并重跑（环境自愈）。

    返回 (pytest_result, coverage, final_deps, installed)。final_deps 是合并了自愈补装
    目录后的 PYTHONPATH 前缀（冒烟探活也要用它，否则冒烟会因缺依赖再次失败）。
    """
    result, final_deps, installed = _self_heal_loop(
        sandbox, timeout, deps, code_files,
        lambda d: _run_pytest_with_coverage(sandbox, timeout, d)[0],
        max_heal=max_heal,
    )
    # coverage 由最后一次 coverage run 写入 .coverage，这里补读最终报告
    coverage = _coverage_report(sandbox, _env(sandbox, final_deps)) \
        if importlib.util.find_spec("coverage") is not None else \
        {"line": -1, "branch": -1, "function": -1, "available": False}
    return result, coverage, final_deps, installed


def _run_pytest_with_coverage(sandbox: str, timeout: int, deps: str = None):
    env = _env(sandbox, deps)
    coverage_available = importlib.util.find_spec("coverage") is not None

    if coverage_available:
        cmd = [sys.executable, "-m", "coverage", "run", "--source=.", "-m", "pytest",
               "-q", "--tb=short", "--color=no", "-p", "no:cacheprovider"]
    else:
        cmd = [sys.executable, "-m", "pytest", "-q", "--tb=short", "--color=no",
               "-p", "no:cacheprovider"]

    try:
        proc = subprocess.run(cmd, cwd=sandbox, env=env,
                              capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return ({"total": 0, "passed": 0, "failed": 0, "summary": "pytest 执行超时", "raw": ""},
                {"line": -1, "branch": -1, "function": -1, "available": coverage_available})

    output = _strip_ansi((proc.stdout or "") + "\n" + (proc.stderr or ""))

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

    coverage = _coverage_report(sandbox, env) if coverage_available else \
        {"line": -1, "branch": -1, "function": -1, "available": False}

    return ({"total": passed + failed, "passed": passed, "failed": failed,
             "summary": summary, "raw": output, "returncode": proc.returncode},
            coverage)


def _coverage_report(sandbox: str, env: Dict[str, str]) -> Dict[str, Any]:
    try:
        r = subprocess.run([sys.executable, "-m", "coverage", "report", "-m"],
                           cwd=sandbox, env=env, capture_output=True, text=True, timeout=30)
        m = re.search(r"TOTAL\s+\d+\s+\d+\s+(\d+)%", _strip_ansi(r.stdout or ""))
        line = int(m.group(1)) if m else 0
        return {"line": line, "branch": -1, "function": -1, "available": True}
    except Exception as e:
        return {"line": -1, "branch": -1, "function": -1, "available": True, "error": str(e)}


def _run_smoke_test(sandbox: str, deps: str = None) -> Dict[str, Any]:
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
                              env=_env(sandbox, deps), capture_output=True, text=True, timeout=30)
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


def _root_cause(output: str) -> str:
    """从 pytest 短 traceback 里抓最可能的一行根因（`E   <异常>: <消息>`）。

    这行通常直接点出「缺依赖」还是「代码 import 错」——正是喂给 builder 判定
    「该补 requirements 还是改代码」的关键信号。
    """
    for m in re.finditer(r"^E\s+(\S[^:]*):\s*(.+)$", output, re.MULTILINE):
        return f"{m.group(1)}: {m.group(2).strip()}"
    return ""


def _extract_bugs(pytest_result: Dict[str, Any]) -> List[Dict[str, Any]]:
    bugs = []
    output = pytest_result.get("raw", "")
    root = _root_cause(output)

    if pytest_result.get("passed", 0) == 0 and pytest_result.get("failed", 0) == 0:
        desc = "未收集到任何测试用例（pytest 未发现 tests/test_api.py，MVP 可能漏生成测试文件）"
        if root:
            desc += f"（根因: {root}）"
        bugs.append({
            "id": "BUG-NOTESTS",
            "severity": "critical",
            "description": desc,
            "file_path": "",
            "steps_to_reproduce": "运行 pytest，确认存在 tests/test_api.py",
        })

    for m in re.finditer(r"^ERROR (.+)$", output, re.MULTILINE):
        desc = f"测试收集/导入错误: {m.group(1).strip()}"
        if root:
            desc += f"（根因: {root}）"
        bugs.append({
            "id": f"BUG-{len(bugs) + 1}",
            "severity": "critical",
            "description": desc,
            "file_path": "",
            "steps_to_reproduce": "运行 pytest，见原始输出",
        })

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

    if pytest_result.get("failed", 0) > 0 and not bugs:
        bugs.append({
            "id": "BUG-1",
            "severity": "major",
            "description": f"{pytest_result.get('failed', 0)} 个测试失败（见原始输出）",
            "file_path": "",
            "steps_to_reproduce": "运行 pytest",
        })

    return bugs


def _extract_suggestions(pytest_result: Dict[str, Any], bugs: List[Dict]) -> List[str]:
    suggestions = []
    if bugs:
        suggestions.append("修复所有失败的测试，重点看原始输出的 traceback 定位问题")
    if pytest_result.get("returncode") not in (0, None):
        suggestions.append(f"pytest 返回码 {pytest_result.get('returncode')}，请修复后重新验证")
    return suggestions


# ----------------------------------------------------------------------
# run_acceptance：运行验收 pytest
# ----------------------------------------------------------------------
def _run_acceptance_pytest(sandbox: str, timeout: int, deps: str) -> Dict[str, Any]:
    """跑验收 pytest（-v --tb=line，逐条核对），返回 {'raw', 'returncode'} 或超时标记。"""
    env = _env(sandbox, deps)
    cmd = [sys.executable, "-m", "pytest", "-v", "--tb=line", "--color=no",
           "-p", "no:cacheprovider"]
    try:
        proc = subprocess.run(cmd, cwd=sandbox, env=env,
                              capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"raw": "", "timed_out": True}
    output = _strip_ansi((proc.stdout or "") + "\n" + (proc.stderr or ""))
    return {"raw": output, "returncode": proc.returncode}


async def run_acceptance(
    criteria: List[Dict],
    code_files: List[Dict],
    test_code: str,
    timeout: int = 120,
) -> Dict[str, Any]:
    """把验收 pytest 代码写入沙箱并真实运行，逐条核对验收标准。

    与 run_tests 一样走环境自愈：验收测试也会 import main.py，缺三方依赖时先补装再重跑。
    """
    sandbox = tempfile.mkdtemp(prefix="magent_accept_")
    try:
        _write_files(sandbox, code_files)
        _write_pytest_ini(sandbox)
        test_path = os.path.join(sandbox, "test_acceptance.py")
        with open(test_path, "w", encoding="utf-8") as f:
            f.write(test_code)

        deps = ensure_deps(code_files)
        result, _final_deps, auto_installed = _self_heal_loop(
            sandbox, timeout, deps, code_files,
            lambda d: _run_acceptance_pytest(sandbox, timeout, d),
        )
        if result.get("timed_out"):
            return _build_failed(criteria, "验收测试执行超时", "")

        parsed = _parse_results(criteria, result["raw"])
        parsed["auto_installed"] = auto_installed
        return parsed
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)


def _parse_results(criteria: List[Dict], output: str) -> Dict[str, Any]:
    results = []
    for i, c in enumerate(criteria):
        cid = str(c.get("id") or "")
        sanitized = re.sub(r"[^0-9a-zA-Z_]", "_", cid) or f"criterion_{i + 1}"
        test_name = f"test_ac_{sanitized}"

        # 用 `::` 锚定 + 要求函数名后紧跟空白，避免前缀误匹配（AC-001 vs AC-001_ERROR_...）
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


def _build_failed(criteria: List[Dict], detail: str, output: str) -> Dict[str, Any]:
    results = [{
        "criterion_id": c.get("id", ""),
        "description": c.get("description", ""),
        "passed": False, "detail": detail,
    } for c in criteria]
    return {
        "results": results, "total": len(criteria), "passed": 0,
        "failed": len(criteria), "all_passed": False, "raw_output": output,
    }
