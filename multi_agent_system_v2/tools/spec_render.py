"""
Spec 可读化渲染（非 LLM，纯代码）

把 ProjectSpec 渲染成中文可读清单，供人工审阅节点展示。
人只看「意图是否对」，不看裸 JSON；machine 仍只认原始 Spec。
"""

import json
from typing import Any


def _g(obj: Any, key: str, default: Any = "") -> Any:
    """同时兼容 pydantic 模型与 dict 的取值。"""
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _body(ep: Any) -> str | None:
    rb = _g(ep, "request_body", None)
    if rb is None:
        return None
    return json.dumps(rb, ensure_ascii=False)


def render_spec(spec) -> str:
    """把 Spec 渲染成可读清单（端点 + 规则）。"""
    bar = "=" * 56
    lines = [bar]

    lines.append(f"项目: {_g(spec, 'project_name', '')}")
    desc = str(_g(spec, "description", "")).strip()
    if desc:
        lines.append(f"描述: {desc}")

    endpoints = _g(spec, "endpoints", []) or []
    rules = _g(spec, "rules", []) or []

    lines.append("")
    lines.append(f"【API 端点】({len(endpoints)})")
    for i, ep in enumerate(endpoints, 1):
        method = str(_g(ep, "method", "")).upper()
        path = _g(ep, "path", "")
        status = _g(ep, "response_status", 200)
        lines.append(f"  {i}. {method} {path}  →  {status}")
        summary = str(_g(ep, "summary", "")).strip()
        if summary:
            lines.append(f"     {summary}")
        body = _body(ep)
        if body is not None:
            lines.append(f"     示例请求: {body}")

    lines.append("")
    lines.append(f"【校验规则】({len(rules)})")
    if not rules:
        lines.append("  （无）")
    for i, rule in enumerate(rules, 1):
        method = str(_g(rule, "method", "")).upper()
        path = _g(rule, "path", "")
        status = _g(rule, "expect_status", 0)
        desc = str(_g(rule, "description", "")).strip()
        lines.append(f"  {i}. {method} {path}  期望 {status}")
        if desc:
            lines.append(f"     {desc}")
        body = _body(rule)
        if body is not None:
            lines.append(f"     请求: {body}")
        ec = _g(rule, "expect_contains", None)
        if ec:
            lines.append(f"     响应需包含: {ec!r}")

    lines.append(bar)
    return "\n".join(lines)
