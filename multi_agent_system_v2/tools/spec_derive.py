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


def _strip_query(path: str) -> str:
    """把 path 里的查询串（?k=v...）剥掉——查询参数应走 query_params 字段，不该在 path 里。

    SpecAgent 偶发仍会把筛选条件拼进 path（如 /tasks?priority=x），这里防御性剥掉，
    保证下游推导/契约匹配只认「资源路径」。
    """
    return (path or "").split("?", 1)[0]


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
        path = _strip_query(ep.path or "/")
        if _has_path_param(path):
            continue
        status = ep.response_status or 200
        fn = f"test_endpoint_{i}_{_path_slug(path, method)}"
        call = f"client.{method}({path!r}"
        if ep.request_body is not None:
            call += f", json={ep.request_body!r}"
        qp = getattr(ep, "query_params", None) or None
        if qp:
            call += f", params={qp!r}"
        call += ")"
        lines.append(f"def {fn}():\n    r = {call}\n    assert r.status_code == {status}, r.text\n")

    # 2. 规则测试
    for i, rule in enumerate(spec.rules):
        method = (rule.method or "get").lower()
        path = _strip_query(rule.path or "/")
        fn = f"test_rule_{i}"
        call = f"client.{method}({path!r}"
        if rule.request_body is not None:
            call += f", json={rule.request_body!r}"
        qp = getattr(rule, "query_params", None) or None
        if qp:
            call += f", params={qp!r}"
        call += ")"
        assert_line = f"assert r.status_code == {rule.expect_status}, r.text"
        if rule.expect_contains:
            assert_line += f"\n    assert {rule.expect_contains!r} in r.text"

        # 409 冲突（重复创建/唯一键）不能用单次无状态请求判定：第一次创建必然成功。
        # 必须先种一个资源、再发一次触发冲突。种子请求结果忽略（可能已被别的测试建过），
        # 不依赖执行顺序，也不改请求值，对 email/uuid 等格式字段同样安全。
        if rule.expect_status == 409 and rule.request_body is not None and method in ("post", "put"):
            lines.append(
                f"def {fn}():\n"
                f"    client.{method}({path!r}, json={rule.request_body!r})  # 先种资源（结果忽略，可能已存在）\n"
                f"    r = {call}\n"
                f"    {assert_line}\n"
            )
        else:
            lines.append(f"def {fn}():\n    r = {call}\n    {assert_line}\n")

    return "\n".join(lines) + "\n"


def _normalize_path(path: str) -> str:
    """把路径参数名归一化为 {p}，并剥掉查询串，使 /todos/{id} 与 /todos/{todo_id}、
    /tasks?priority=x 与 /tasks 视为同一端点。"""
    return re.sub(r"/\{[^}]*\}", "/{p}", _strip_query(path or ""))


def _openapi_paths(code_files: List[Dict], timeout: int = 60):
    """把代码写进沙箱，真实 import 出 FastAPI app，返回 (paths, error)。

    - 成功：返回 (paths_dict, None)；
    - 拿不到 app / openapi 生成失败：返回 (None, error_str)，error 指明真实原因，
      而不是把「探针失败」误报成「端点全缺」。
    """
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
            "import json, importlib, sys, traceback\n"
            "sys.path.insert(0, '.')\n"
            "app = None\n"
            "import_err = []\n"
            "for mn in ('main', 'app', 'api', 'server'):\n"
            "    try:\n"
            "        m = importlib.import_module(mn)\n"
            "    except Exception as e:\n"
            "        import_err.append('%s: %s' % (mn, e))\n"
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
            "    print(json.dumps({'ok': False, 'error': '未找到 FastAPI app' + (('; ' + '; '.join(import_err)) if import_err else '')}))\n"
            "else:\n"
            "    try:\n"
            "        print(json.dumps({'ok': True, 'paths': app.openapi().get('paths', {})}))\n"
            "    except Exception as e:\n"
            "        print(json.dumps({'ok': False, 'error': 'openapi 生成失败: %s\\n%s' % (e, traceback.format_exc())}))\n"
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
            data = json.loads((proc.stdout or "").strip())
        except json.JSONDecodeError:
            return None, (proc.stderr or proc.stdout or "openapi 探针无输出").strip()[:2000]
        if data.get("ok"):
            return data.get("paths", {}), None
        return None, data.get("error", "openapi 生成失败")
    except Exception as e:
        return None, f"openapi 探针执行异常: {e}"
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)


def contract_check(spec, code_files: List[Dict], timeout: int = 60) -> Dict[str, Any]:
    """API 契约校验：spec 端点集合 vs 生成代码 app.openapi() 的实际路径集合。

    返回 {match, missing, extra, expected, actual}。路径参数名归一化，忽略 FastAPI
    自动加的 /docs 等路径。这是「builder 是否忠于 spec 设计」的硬校验。
    """
    expected = {(ep.method.lower(), _normalize_path(ep.path)) for ep in spec.endpoints}

    paths, oa_error = _openapi_paths(code_files, timeout)
    if paths is None:
        # 探针失败（app 无法导入 / openapi 生成抛异常）≠「端点全缺」。
        # 这里不把 missing 填成所有 expected，否则会给 builder 错误的「补端点」反馈。
        return {
            "match": False,
            "missing": [],
            "extra": [],
            "error": oa_error or "无法获取 app.openapi()（代码可能无法导入）",
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
