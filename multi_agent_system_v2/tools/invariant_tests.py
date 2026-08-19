"""
确定性不变式测试生成器（非 LLM，独立 ground truth）

从应用的 OpenAPI schema（真实执行 `app.openapi()`）机械推导「通用不变式」测试：
- 资源标识唯一性：连续 POST 两次，id 必须不同
- 计数一致性：GET 列表 → POST 一个 → 列表长度 +1
- 删除后 404：POST → DELETE → GET 应返回 404

这些测试**不是 LLM 写的**，而是从 API 契约（OpenAPI）机械推导的独立裁判，
专门对治「作者自测与生成代码同源」的 sham：LLM 既可能写不出 id 自增的代码、
也可能写不出 id 唯一的测试；但这里的测试是确定性的，与生成代码的盲区无关，
因此它们的失败是「真 bug」信号，可以放心当作硬门槛。

所有步骤都降级：只要有一处无法确定（schema 拿不到、找不到 POST、请求体太复杂），
就跳过对应测试——宁可少测，不生成会误报的断言。
"""

import os
import sys
import json
import tempfile
import shutil
import subprocess
from typing import Any, Dict, List, Optional

from tools.deps import ensure_deps


def _write_files(sandbox: str, code_files: List[Dict]) -> None:
    for cf in code_files:
        rel = (cf.get("path") or "").replace("\\", "/").lstrip("./")
        fp = os.path.join(sandbox, rel)
        d = os.path.dirname(fp)
        if d:
            os.makedirs(d, exist_ok=True)
        with open(fp, "w", encoding="utf-8") as f:
            f.write(cf.get("content", ""))


def _discover_openapi(code_files: List[Dict]) -> Optional[Dict]:
    """把代码写进沙箱，真实 import 出 FastAPI app 并返回其 openapi schema + 模块名。"""
    sandbox = tempfile.mkdtemp(prefix="magent_inv_")
    try:
        _write_files(sandbox, code_files)
        deps = ensure_deps(code_files)
        probe = (
            "import json, sys, importlib\n"
            "sys.path.insert(0, '.')\n"
            "app = None\n"
            "mod = None\n"
            "for _mn in ('main', 'app', 'api', 'server'):\n"
            "    try:\n"
            "        _m = importlib.import_module(_mn)\n"
            "    except Exception:\n"
            "        continue\n"
            "    _a = getattr(_m, 'app', None)\n"
            "    if _a is not None and hasattr(_a, 'openapi'):\n"
            "        app, mod = _a, _mn\n"
            "        break\n"
            "    for _n, _o in vars(_m).items():\n"
            "        if hasattr(_o, 'openapi') and hasattr(_o, 'routes'):\n"
            "            app, mod = _o, _mn\n"
            "            break\n"
            "    if app is not None:\n"
            "        break\n"
            "if app is None:\n"
            "    print('{}')\n"
            "else:\n"
            "    print(json.dumps({'module': mod, 'schema': app.openapi()}))\n"
        )
        probe_path = os.path.join(sandbox, "_probe.py")
        with open(probe_path, "w", encoding="utf-8") as f:
            f.write(probe)
        env = dict(os.environ)
        if deps:
            env["PYTHONPATH"] = deps + os.pathsep + env.get("PYTHONPATH", "")
        proc = subprocess.run(
            [sys.executable, probe_path],
            cwd=sandbox, capture_output=True, text=True, timeout=60, env=env,
        )
        try:
            return json.loads((proc.stdout or "").strip())
        except json.JSONDecodeError:
            return None
    except Exception:
        return None
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)


def _resolve(schema: Dict, ref: str) -> Optional[Dict]:
    if not ref.startswith("#/"):
        return None
    cur: Any = schema
    for p in ref.lstrip("#/").split("/"):
        if not isinstance(cur, dict) or p not in cur:
            return None
        cur = cur[p]
    return cur if isinstance(cur, dict) else None


def _find_post(schema: Dict) -> Optional[Dict]:
    """找到第一个「POST 且响应含 id 字段」的资源，返回其 path/id 字段/请求体字段。"""
    for path, methods in schema.get("paths", {}).items():
        if not isinstance(methods, dict):
            continue
        post = methods.get("post")
        if not isinstance(post, dict):
            continue

        id_field = None
        for code in ("201", "200"):
            resp = (post.get("responses") or {}).get(code, {})
            jschema = (resp.get("content") or {}).get("application/json", {}).get("schema", {})
            if "$ref" in jschema:
                jschema = _resolve(schema, jschema["$ref"]) or jschema
            props = jschema.get("properties", {})
            if "id" in props:
                id_field = "id"
            else:
                for k in props:
                    if k.lower().endswith("id"):
                        id_field = k
                        break
            if id_field:
                break
        if not id_field:
            continue

        rb = post.get("requestBody", {})
        rb_schema = (rb.get("content") or {}).get("application/json", {}).get("schema", {})
        if "$ref" in rb_schema:
            rb_schema = _resolve(schema, rb_schema["$ref"]) or rb_schema
        props = rb_schema.get("properties", {})
        required = rb_schema.get("required", [])
        # 只支持「扁平原始类型字段」的请求体，复杂嵌套直接跳过
        if not props or any(not isinstance(v, dict) for v in props.values()):
            request_fields = {}
        else:
            request_fields = {k: props[k] for k in required if k in props}

        return {"path": path, "id_field": id_field, "request_fields": request_fields}
    return None


def _find_delete_path(schema: Dict, post_path: str) -> Optional[str]:
    """找 DELETE 端点：路径以 post_path + '/{' 开头（如 POST /todo → DELETE /todo/{todo_id}）。"""
    for path, methods in schema.get("paths", {}).items():
        if path.startswith(post_path + "/{") and isinstance(methods, dict) and "delete" in methods:
            return path
    return None


def _find_get_list(schema: Dict, path: str) -> bool:
    """POST 路径上是否有一个返回数组（列表）的 GET——这是「集合资源」的判据。

    只有集合资源（如 /todo）才适用 id 唯一性/计数一致性这类不变式；
    对 register/login 这种「无列表、有唯一键」的端点，强行套不变式会误报
    （重复注册返回 409 而非新 id、GET 注册路径返回 405），所以这里宁可跳过。
    """
    methods = schema.get("paths", {}).get(path, {})
    if not isinstance(methods, dict):
        return False
    get = methods.get("get")
    if not isinstance(get, dict):
        return False
    for code in ("200", "201"):
        resp = (get.get("responses") or {}).get(code, {})
        jschema = (resp.get("content") or {}).get("application/json", {}).get("schema", {})
        if "$ref" in jschema:
            jschema = _resolve(schema, jschema["$ref"]) or jschema
        if isinstance(jschema, dict) and jschema.get("type") == "array":
            return True
    return False


def _sample(prop: Dict) -> Any:
    """从 schema 采样一个能通过校验的请求体值（尊重 minLength/format/enum/minimum）。"""
    t = (prop.get("type") or "").lower()
    if prop.get("enum"):
        return prop["enum"][0]
    if t == "string":
        fmt = (prop.get("format") or "").lower()
        if fmt == "email":
            return "test@example.com"
        if fmt == "uuid":
            return "00000000-0000-0000-0000-000000000000"
        mn = prop.get("minLength") or prop.get("min_length") or 1
        mx = prop.get("maxLength") or prop.get("max_length")
        try:
            mn = int(mn)
        except (TypeError, ValueError):
            mn = 1
        s = "x" * max(1, mn)
        if mx is not None:
            try:
                mx = int(mx)
                if mx >= 1 and len(s) > mx:
                    s = s[:mx]
            except (TypeError, ValueError):
                pass
        return s
    if t == "integer":
        mn = prop.get("minimum")
        return int(mn) if isinstance(mn, (int, float)) else 1
    if t == "number":
        mn = prop.get("minimum")
        return float(mn) if isinstance(mn, (int, float)) else 1.5
    if t == "boolean":
        return False
    if t == "array":
        return []
    return "x"


def generate_invariant_tests(code_files: List[Dict]) -> str:
    """返回确定性不变式 pytest 代码；发现不了 API 契约时返回空串（降级）。"""
    discovered = _discover_openapi(code_files)
    if not discovered or not discovered.get("schema"):
        return ""
    schema = discovered["schema"]
    module = discovered.get("module") or "main"
    res = _find_post(schema)
    if not res:
        return ""

    path = res["path"]
    # 集合资源判据：POST 路径上必须有返回列表的 GET，否则不变式不适用（见 _find_get_list）
    if not _find_get_list(schema, path):
        return ""
    id_field = res["id_field"]
    body = {k: _sample(v) for k, v in res["request_fields"].items()}
    body_literal = json.dumps(body, ensure_ascii=False) if body else "{}"
    delete_path = _find_delete_path(schema, path)

    tests = []

    # 1. id 唯一性
    tests.append(f'''def test_invariant_id_unique():
    r1 = client.post({path!r}, json={body_literal})
    r2 = client.post({path!r}, json={body_literal})
    assert r1.status_code in (200, 201), r1.text
    assert r2.status_code in (200, 201), r2.text
    assert r1.json()[{id_field!r}] != r2.json()[{id_field!r}]''')

    # 2. 计数一致性
    tests.append(f'''def test_invariant_count_consistent():
    before = len(client.get({path!r}).json())
    client.post({path!r}, json={body_literal})
    after = len(client.get({path!r}).json())
    assert after == before + 1''')

    # 3. 删除后 404（仅当存在对应 DELETE 端点，且路径参数名可解析）
    if delete_path:
        m = __import__("re").search(r"/\{([^}/]+)\}", delete_path)
        if m:
            param = m.group(1)
            replace_src = "{" + param + "}"
            tests.append(f'''def test_invariant_delete_then_404():
    r = client.post({path!r}, json={body_literal})
    rid = r.json()[{id_field!r}]
    url = {delete_path!r}.replace({replace_src!r}, str(rid))
    client.delete(url)
    g = client.get(url)
    assert g.status_code == 404''')

    if not tests:
        return ""

    return f'''import pytest
from fastapi.testclient import TestClient
from {module} import app


client = TestClient(app)


''' + "\n\n\n".join(tests) + "\n"
