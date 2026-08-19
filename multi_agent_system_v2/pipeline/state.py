"""
流水线状态管理
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import json


class StageRecord(BaseModel):
    """阶段执行记录"""
    stage: str
    status: str
    duration_seconds: float = 0.0
    agent_used: str = "primary"
    error: Optional[str] = None
    iteration: int = 0  # 迭代次数


class IterationRecord(BaseModel):
    """迭代记录"""
    iteration: int
    stage: str  # 触发迭代的阶段（code_review/testing/acceptance）
    reason: str  # 迭代原因
    issues_count: int = 0
    bugs_count: int = 0
    acceptance_failures: int = 0


class PipelineState:
    """流水线共享状态"""

    def __init__(self):
        self.data: Dict[str, Any] = {}
        self.history: List[StageRecord] = []
        self.iterations: List[IterationRecord] = []
        self.current_iteration: int = 0

    def update(self, stage: str, data: Dict[str, Any]) -> None:
        """更新阶段数据"""
        self.data[stage] = data

    def get(self, stage: str) -> Dict[str, Any]:
        """获取阶段数据"""
        return self.data.get(stage, {})

    def add_history(self, record: StageRecord) -> None:
        """添加执行记录"""
        self.history.append(record)

    def add_iteration(self, record: IterationRecord) -> None:
        """添加迭代记录"""
        self.iterations.append(record)

    def increment_iteration(self) -> int:
        """增加迭代计数"""
        self.current_iteration += 1
        return self.current_iteration

    def to_dict(self) -> Dict[str, Any]:
        return {
            "data": self.data,
            "history": [r.model_dump() for r in self.history],
            "iterations": [r.model_dump() for r in self.iterations],
            "current_iteration": self.current_iteration,
        }

    def save(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, path: str) -> "PipelineState":
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        state = cls()
        state.data = data.get("data", {})
        state.current_iteration = data.get("current_iteration", 0)
        for h in data.get("history", []):
            state.history.append(StageRecord(**h))
        for i in data.get("iterations", []):
            state.iterations.append(IterationRecord(**i))
        return state
