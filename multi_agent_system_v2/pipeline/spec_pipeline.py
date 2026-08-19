"""
spec-driven 流水线（新架构）

Spec → 确定性推导 → 代码生成 → 确定性验证 → 部署

与旧 orchestrator 的根本区别：
- LLM 只剩两处：NL → Spec（spec_agent），Spec → 代码（builder）。
- 验证全部由确定性代码从 Spec 推导（spec_derive）+ 代码 OpenAPI 推导（invariant_tests）。
- 没有 code_review、没有软信号机制、没有验收的 LLM 翻译——这些全部被删掉了。
"""

import time
import logging
from typing import Dict, Any, List

from schemas.spec import ProjectSpec
from tools.spec_derive import derive_acceptance_tests, contract_check
from tools.invariant_tests import generate_invariant_tests
from tools.executors import run_tests

logger = logging.getLogger("spec_pipeline")

_MIN_COVERAGE = 80


def _format_gate_feedback(test_result: Dict[str, Any], contract: Dict[str, Any]) -> Dict[str, Any]:
    """把硬门槛失败原因格式化成 builder 能据以定点修复的反馈 dict。"""
    hints = []
    if not contract.get("match"):
        if contract.get("error"):
            # 契约校验拿不到 openapi（app 无法导入 / openapi 生成抛异常）——这是真实的
            # 代码缺陷，但跟「缺端点」不是一回事，要明确告诉 builder 修什么。
            hints.append(f"契约校验失败（openapi 探针异常）: {contract['error'][:800]}")
        if contract.get("missing"):
            hints.append(f"缺少端点（必须补实现）: {', '.join(contract['missing'])}")
        if contract.get("extra"):
            hints.append(f"多余端点（spec 之外，必须删除）: {', '.join(contract['extra'])}")
    return {
        "hints": hints,
        "test_output": (test_result.get("raw_output") or "")[:4000],
    }


async def run_spec_pipeline(
    user_input: str,
    spec_agent,
    builder,
    deployment_agent=None,
    timeout: int = 120,
    spec_review=None,
    spec_auto_review=None,
    max_review_rounds: int = 3,
    max_build_retries: int = 1,
) -> Dict[str, Any]:
    """运行 spec-driven 流水线，返回结构化结果 dict。

    spec_review：可选的人工审阅回调 `async (spec) -> str`，返回 "approve" / "reject" /
    其它字符串（视为修改意见，据此重新生成）。为 None 时不审阅（非交互/测试环境）。

    spec_auto_review：可选的自动完备性评审回调 `async (user_input, spec) -> str`，返回
    "approve" / 修复意见字符串（据此重新生成）。为 None 时不做自动评审。
    典型来源：SpecReviewAgent.to_callback(...)。

    max_review_rounds：人工审阅 + 自动评审共用的重新生成轮数上限。

    max_build_retries：builder 未通过硬门槛时的外层重试次数（把失败测试输出/契约差异
    回灌 builder 定点修复）。总尝试次数 = 1 + max_build_retries。
    """
    start = time.time()
    out: Dict[str, Any] = {
        "status": "error",
        "project_name": "spec_project",
        "spec": None,
        "code_files": [],
        "test_files": [],
        "test_result": None,
        "contract": None,
        "coverage_line": None,
        "gate_ok": False,
        "build_rounds": 0,
        "deployment": None,
        "duration_seconds": 0.0,
    }

    # 1. NL → Spec（LLM #1，全系统唯一一次理解需求）+ 人工审阅 + 自动完备性评审
    spec = None
    feedback = ""
    approved = (spec_review is None and spec_auto_review is None)  # 无任何评审时视为已通过
    for _ in range(max_review_rounds + 1):
        spec_res = await spec_agent.execute(user_input=user_input, feedback=feedback)
        if spec_res.status != "success":
            out["error"] = f"spec 生成失败: {spec_res.error}"
            out["duration_seconds"] = time.time() - start
            return out
        try:
            spec = ProjectSpec.model_validate(spec_res.data)
        except Exception as e:
            out["error"] = f"spec 解析失败: {e}"
            out["duration_seconds"] = time.time() - start
            return out

        # 人工审阅：approve 通过；reject 硬中止；其它字符串 = 修改意见 → 重新生成
        if spec_review is not None:
            verdict = await spec_review(spec)
            if verdict == "approve":
                approved = True
                break
            if verdict == "reject":
                out["status"] = "rejected"
                out["error"] = "spec 未通过人工审阅，已中止"
                out["spec"] = spec.model_dump()
                out["project_name"] = spec.project_name
                out["duration_seconds"] = time.time() - start
                return out
            feedback = str(verdict) if not feedback else f"{feedback}\n{str(verdict)}"
            continue

        # 自动完备性评审：approve 通过；否则反馈意见 → 重新生成
        if spec_auto_review is not None:
            verdict = await spec_auto_review(user_input, spec)
            if verdict == "approve":
                approved = True
                break
            feedback = str(verdict) if not feedback else f"{feedback}\n{str(verdict)}"
            continue

        # 无评审
        approved = True
        break

    if not approved:
        out["review_note"] = f"审阅 {max_review_rounds} 轮仍未确认，按最后生成的 spec 继续"

    out["project_name"] = spec.project_name
    out["spec"] = spec.model_dump()

    # 2. 确定性推导验收测试（零 LLM）
    acceptance_code = derive_acceptance_tests(spec)
    seed_tests = [{
        "path": "tests/test_acceptance.py",
        "content": acceptance_code,
        "language": "python",
    }]

    # 3+4+5. 代码生成 → 确定性验证 → 硬门槛（外层重试：没过门槛就把失败信息回灌 builder 定点修复）
    code_files: List[Dict] = []
    test_files: List[Dict] = []
    test_result: Dict[str, Any] = {}
    contract: Dict[str, Any] = {}
    coverage_line = -1
    gate_ok = False
    build_feedback = None

    for _round in range(max_build_retries + 1):
        build_res = await builder.execute(
            spec=spec.model_dump(),
            seed_tests=seed_tests,
            project_name=spec.project_name,
            current_code=code_files if _round > 0 else [],
            feedback=build_feedback if _round > 0 else None,
        )
        if build_res.status != "success":
            out["error"] = f"代码生成失败: {build_res.error}"
            out["duration_seconds"] = time.time() - start
            return out
        code_files = build_res.data.get("code_files", []) or []
        if not code_files:
            out["error"] = "builder 未产出任何代码"
            out["duration_seconds"] = time.time() - start
            return out

        # 确定性验证：推导验收测试 + 代码 OpenAPI 推导的不变式测试 + 契约校验 + 覆盖率
        test_files = list(seed_tests)
        try:
            inv_code = generate_invariant_tests(code_files)
        except Exception:
            inv_code = ""
        if (inv_code or "").strip():
            test_files.append({
                "path": "tests/test_invariants.py",
                "content": inv_code,
                "language": "python",
            })

        test_result = await run_tests(code_files, test_files, timeout=timeout)
        contract = contract_check(spec, code_files)
        coverage_line = (test_result.get("coverage") or {}).get("line", -1)

        # 硬门槛：测试全过 + 覆盖率 ≥80 + 契约完全匹配
        gate_ok = (
            test_result.get("all_passed", False)
            and (coverage_line < 0 or coverage_line >= _MIN_COVERAGE)
            and contract.get("match", False)
        )
        if gate_ok:
            break
        build_feedback = _format_gate_feedback(test_result, contract)

    out["code_files"] = code_files
    out["test_result"] = test_result
    out["test_files"] = test_files
    out["contract"] = contract
    out["coverage_line"] = coverage_line
    out["gate_ok"] = gate_ok
    out["build_rounds"] = _round + 1

    # 硬门槛未通过时的原因（诊断用）
    if not gate_ok:
        reasons = []
        if not test_result.get("all_passed", False):
            reasons.append("测试未全部通过")
        if not (coverage_line < 0 or coverage_line >= _MIN_COVERAGE):
            reasons.append(f"覆盖率 {coverage_line}% < {_MIN_COVERAGE}%")
        if not contract.get("match", False):
            reasons.append(
                f"契约不符（缺 {contract.get('missing')}，多 {contract.get('extra')}）"
            )
        out["gate_reasons"] = reasons

    # 6. 部署（仅当门槛通过）
    if gate_ok and deployment_agent is not None:
        try:
            dres = await deployment_agent.execute(
                code_files=code_files,
                technical_solution={"spec": spec.model_dump()},
            )
            out["deployment"] = dres.data if dres.status == "success" else {"error": dres.error}
        except Exception as e:
            out["deployment"] = {"error": str(e)}

    out["status"] = "success" if gate_ok else "failed"
    out["duration_seconds"] = time.time() - start
    return out
