"""
健壮性修复离线测试（不联网）

验证评估里列的修复：
1. 防振荡：_problem_signature / _signature_improved / _should_iterate
2. 验收 UI 盲区检测：_detect_ui_gap
"""

import sys

sys.path.insert(0, r'C:\Users\MECHREV\agent\multi_agent_system_v2')

from agents.acceptance import AcceptanceAgent
from pipeline.orchestrator import PipelineOrchestrator
from schemas import StageResult


def _sr(data=None):
    return StageResult(stage="x", status="success", data=data or {})


def test_detect_ui_gap():
    criteria_ui = [{"id": "AC-001", "description": "用户点击保存按钮，界面显示新待办事项"}]
    criteria_api = [{"id": "AC-002", "description": "POST /api/todos 返回 201"}]
    code_api = [{"path": "main.py", "content": "from fastapi import FastAPI\napp = FastAPI()"}]
    code_front = [{"path": "static/index.html", "content": "<html><body></body></html>"}]

    # 1) UI 标准 + 无前端 → 告警
    w = AcceptanceAgent._detect_ui_gap(criteria_ui, code_api)
    assert len(w) == 1 and w[0]["type"] == "ui_api_gap", w

    # 2) UI 标准 + 有前端 → 无告警
    w = AcceptanceAgent._detect_ui_gap(criteria_ui, code_front)
    assert w == [], w

    # 3) 纯 API 标准 → 无告警
    w = AcceptanceAgent._detect_ui_gap(criteria_api, code_api)
    assert w == [], w


def test_problem_signature_and_improve():
    # 构造：2 个 critical/major 审查问题 + 1 个 critical bug + 3 个验收失败
    review = {"issues": [
        {"severity": "critical", "description": "a"},
        {"severity": "major", "description": "b"},
        {"severity": "minor", "description": "c"},
    ]}
    test = {"bugs": [{"severity": "critical", "description": "d"}], "all_passed": False}
    accept = {"failed": 3}
    stages = {"code_review": _sr(review), "testing": _sr(test), "acceptance": _sr(accept)}

    sig = PipelineOrchestrator._problem_signature(stages)
    assert sig == (2, 1, 3), sig

    # 严格改善判定
    assert PipelineOrchestrator._signature_improved((1, 0, 1), (2, 1, 3)) is True
    assert PipelineOrchestrator._signature_improved((2, 1, 3), (2, 1, 3)) is False   # 无变化
    assert PipelineOrchestrator._signature_improved((2, 2, 3), (2, 1, 3)) is False   # 变差


def test_should_iterate_anti_oscillation():
    orch = PipelineOrchestrator({}, max_iterations=3)
    review = {"issues": [{"severity": "critical", "description": "x"},
                         {"severity": "major", "description": "y"}]}
    stages = {
        "code_review": _sr(review),
        "testing": _sr({"all_passed": True, "bugs": []}),
        "acceptance": _sr({"all_passed": True, "failed": 0}),
    }

    # 第一轮：应迭代
    need, _ = orch._should_iterate(stages)
    assert need is True

    # 第二轮：签名未改善 → 防振荡，停止
    need, _ = orch._should_iterate(stages)
    assert need is False

    # 若问题减少 → 允许继续
    improved = {
        "code_review": _sr({"issues": [{"severity": "critical", "description": "x"}]}),
        "testing": _sr({"all_passed": True, "bugs": []}),
        "acceptance": _sr({"all_passed": True, "failed": 0}),
    }
    need, _ = orch._should_iterate(improved)
    assert need is True


def test_signature_net_improvement_tradeoff():
    """加权净改善：允许验收失败大幅下降，即使 code_review 轻微回退。

    对应真实场景：(0,0,6) → (1,0,3) 应判为「净改善」继续迭代，
    而不是旧 Pareto 判据下的「未改善」提前停止。
    """
    # 验收 6→3（-3）换取 code_review 0→1（+1）是净改善
    assert PipelineOrchestrator._signature_improved((1, 0, 3), (0, 0, 6)) is True
    # 反向（验收变差）不是改善
    assert PipelineOrchestrator._signature_improved((0, 0, 6), (0, 0, 3)) is False
    # 用 5 个 code_review 问题换 1 个验收失败，代价太大，不是净改善
    assert PipelineOrchestrator._signature_improved((5, 0, 0), (0, 0, 1)) is False
    # 无变化不视为改善（防止死循环）
    assert PipelineOrchestrator._signature_improved((1, 0, 3), (1, 0, 3)) is False


if __name__ == "__main__":
    test_detect_ui_gap()
    test_problem_signature_and_improve()
    test_should_iterate_anti_oscillation()
    test_signature_net_improvement_tradeoff()
    print("[PASS] robustness: 防振荡 + 验收 UI 盲区检测 + 加权净改善 全部通过")
