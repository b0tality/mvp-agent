"""
Spec 确定性推导器（非 LLM，纯代码）

这是 spec-driven 架构的核心：从一份 ProjectSpec 机械推导出：
1. 验收测试（pytest）—— 每个端点/每条规则一个断言测试；
2. API 契约校验 —— 真实 import 生成的 app，比对 spec 端点 vs app.openapi() 路径。

与 LLM 翻译的根本区别：推导是**确定的、可复现的**，同一份 Spec 永远生成同一份测试，
不会"放水"、不会漂移。不变式测试仍由 tools/invariant_tests.py 从代码的 OpenAPI 推导，
这里只负责「spec → 验收测试」和「spec → 契约校验」。
"""

import os
import re
import sys
import json
import shutil
import tempfile
import subprocess
from typing import Dict, Any, List, Optional

from tools.deps import ensure_deps

_HTTP_METHODS = {"get", "post", "put", "delete", "patch"}


def _sanitize(s: str) -> str:
    s = re.sub(r"[^0-9a-zA-Z_]", "_", s or "")
    return s or "x"


def _path_slug(path: str, method: str) -> str:
    return _sanitize((method or "").lower() + (path or "").replace("/", "_"))


def _has_path_param(path: str) -> bool:
    return "{" in (path or "")


def derive_acceptance_tests(spec) -> str:
    """从 Spec 确定性生成验收 pytest（零 LLM）。

    只对「无路径参数」的端点生成简单成功测试；资源级 GET/DELETE/{id} 的往返与
    删除 404 由不变式测试覆盖。每条 rule 生成一条断言测试。
    """
    lines = [
        "import pytest",
        "from fastapi.testclient import TestClient",
        "from main import app",
        "",
        "",
        "client = TestClient(app)",
        "",
    ]

    # 1. 端点成功测试（无路径参数）
    for i, ep in enumerate(spec.endpoints):
        method = (ep.method or "get").lower()
        path = ep.path or "/"
        if _has_path_param(path):
            continue
        status = ep.response_status or 200
        fn = f"test_endpoint_{i}_{_path_slug(path, method)}"
        if ep.request_body is not None:
            call = f"client.{method}({path!r}, json={ep.request_body!r})"
        else:
            call = f"client.{method}({path!r})"
        lines.append(f"def {fn}():\n    r = {call}\n    assert r.status_code == {status}, r.text\n")

    # 2. 规则测试
    for i, rule in enumerate(spec.rules):
        method = (rule.method or "get").lower()
        path = rule.path or "/"
        fn = f"test_rule_{i}"
        if rule.request_body is not None:
            call = f"client.{method}({path!r}, json={rule.request_body!r})"
        else:
            call = f"client.{method}({path!r})"
        assert_line = f"assert r.status_code == {rule.expect_status}, r.text"
        if rule.expect_contains:
            assert_line += f"\n    assert {rule.expect_contains!r} in r.text"
        lines.append(f"def {fn}():\n    r = {call}\n    {assert_line}\n")

    return "\n".join(lines) + "\n"


def _normalize_path(path: str) -> str:
    """把路径参数名归一化为 {p}，使 /todos/{id} 与 /todos/{todo_id} 视为同一端点。"""
    return re.sub(r"/\{[^}]*\}", "/{p}", path or "")


def _openapi_paths(code_files: List[Dict], timeout: int = 60) -> Optional[Dict]:
    """把代码写进沙箱，真实 import 出 FastAPI app，返回其 openapi paths（拿不到返回 None）。"""
    sandbox = tempfile.mkdtemp(prefix="magent_spec_")
    try:
        for cf in code_files:
            rel = (cf.get("path") or "").replace("\\", "/").lstrip("./")
            if not rel or not cf.get("content"):
                continue
            fp = os.path.join(sandbox, rel)
            d = os.path.dirname(fp)
            if d:
                os.makedirs(d, exist_ok=True)
            with open(fp, "w", encoding="utf-8") as f:
                f.write(cf.get("content", ""))

        deps = ensure_deps(code_files)
        probe = (
            "import json, importlib, sys\n"
            "sys.path.insert(0, '.')\n"
            "app = None\n"
            "for mn in ('main', 'app', 'api', 'server'):\n"
            "    try:\n"
            "        m = importlib.import_module(mn)\n"
            "    except Exception:\n"
            "        continue\n"
            "    a = getattr(m, 'app', None)\n"
            "    if a is not None and hasattr(a, 'openapi'):\n"
            "        app = a\n"
            "        break\n"
            "    for n, o in vars(m).items():\n"
            "        if hasattr(o, 'openapi') and hasattr(o, 'routes'):\n"
            "            app = o\n"
            "            break\n"
            "    if app is not None:\n"
            "        break\n"
            "if app is None:\n"
            "    print('{}')\n"
            "else:\n"
            "    print(json.dumps(app.openapi().get('paths', {})))\n"
        )
        probe_path = os.path.join(sandbox, "_probe.py")
        with open(probe_path, "w", encoding="utf-8") as f:
            f.write(probe)
        env = dict(os.environ)
        if deps:
            env["PYTHONPATH"] = deps + os.pathsep + env.get("PYTHONPATH", "")
        proc = subprocess.run(
            [sys.executable, probe_path], cwd=sandbox,
            capture_output=True, text=True, timeout=timeout, env=env,
        )
        try:
            return json.loads((proc.stdout or "").strip())
        except json.JSONDecodeError:
            return None
    except Exception:
        return None
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)


def contract_check(spec, code_files: List[Dict], timeout: int = 60) -> Dict[str, Any]:
    """API 契约校验：spec 端点集合 vs 生成代码 app.openapi() 的实际路径集合。

    返回 {match, missing, extra, expected, actual}。路径参数名归一化，忽略 FastAPI
    自动加的 /docs 等路径。这是「builder 是否忠于 spec 设计」的硬校验。
    """
    expected = {(ep.method.lower(), _normalize_path(ep.path)) for ep in spec.endpoints}

    paths = _openapi_paths(code_files, timeout)
    if paths is None:
        return {
            "match": False,
            "missing": sorted(f"{m.upper()} {p}" for m, p in expected),
            "extra": [],
            "error": "无法获取 app.openapi()（代码可能无法导入）",
            "expected": len(expected),
            "actual": 0,
        }

    actual_set = set()
    for path, methods in (paths or {}).items():
        if path in ("/openapi.json", "/docs", "/redoc", "/docs/oauth2-redirect"):
            continue
        p = _normalize_path(path)
        for m in methods:
            m = (m or "").lower()
            if m in _HTTP_METHODS:
                actual_set.add((m, p))

    missing = expected - actual_set
    extra = actual_set - expected
    return {
        "match": not missing and not extra,
        "missing": sorted(f"{m.upper()} {p}" for m, p in missing),
        "extra": sorted(f"{m.upper()} {p}" for m, p in extra),
        "expected": len(expected),
        "actual": len(actual_set),
    }
