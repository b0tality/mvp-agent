"""
流水线状态管理
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json


@dataclass
class StageRecord:
    """阶段执行记录"""
    stage: str
    status: str  # success/failed/skipped/degraded
    started_at: str
    completed_at: str
    duration_seconds: float
    agent_used: str  # primary/fallback_1/fallback_2/rule_based
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineCheckpoint:
    """流水线检查点"""
    stage: str
    timestamp: str
    state_snapshot: Dict[str, Any]
    agent_states: Dict[str, Dict[str, Any]]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage": self.stage,
            "timestamp": self.timestamp,
            "state_snapshot": self.state_snapshot,
            "agent_states": self.agent_states
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PipelineCheckpoint":
        return cls(**data)


class PipelineState:
    """流水线共享状态"""
    
    def __init__(self):
        self.requirements: Dict[str, Any] = {}
        self.technical_solution: Dict[str, Any] = {}
        self.mvp_result: Dict[str, Any] = {}
        self.code_review: Dict[str, Any] = {}
        self.test_results: Dict[str, Any] = {}
        self.deployment: Dict[str, Any] = {}
        self.current_stage: str = "pending"
        self.history: List[StageRecord] = []
        self.checkpoints: List[PipelineCheckpoint] = []
        self.rollback_stack: List[Dict[str, Any]] = []
    
    def update(self, stage: str, data: Dict[str, Any]) -> None:
        """更新阶段数据"""
        setattr(self, stage, data)
    
    def get(self, stage: str) -> Dict[str, Any]:
        """获取阶段数据"""
        return getattr(self, stage, {})
    
    def add_history(self, record: StageRecord) -> None:
        """添加执行记录"""
        self.history.append(record)
    
    def add_checkpoint(self, checkpoint: PipelineCheckpoint) -> None:
        """添加检查点"""
        self.checkpoints.append(checkpoint)
    
    def add_rollback(self, rollback_info: Dict[str, Any]) -> None:
        """添加回退信息"""
        self.rollback_stack.append(rollback_info)
    
    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典"""
        return {
            "requirements": self.requirements,
            "technical_solution": self.technical_solution,
            "mvp_result": self.mvp_result,
            "code_review": self.code_review,
            "test_results": self.test_results,
            "deployment": self.deployment,
            "current_stage": self.current_stage,
            "history": [
                {
                    "stage": r.stage,
                    "status": r.status,
                    "started_at": r.started_at,
                    "completed_at": r.completed_at,
                    "duration_seconds": r.duration_seconds,
                    "agent_used": r.agent_used,
                    "error": r.error,
                    "metadata": r.metadata
                }
                for r in self.history
            ],
            "checkpoints": [c.to_dict() for c in self.checkpoints],
            "rollback_stack": self.rollback_stack
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PipelineState":
        """从字典反序列化"""
        state = cls()
        state.requirements = data.get("requirements", {})
        state.technical_solution = data.get("technical_solution", {})
        state.mvp_result = data.get("mvp_result", {})
        state.code_review = data.get("code_review", {})
        state.test_results = data.get("test_results", {})
        state.deployment = data.get("deployment", {})
        state.current_stage = data.get("current_stage", "pending")
        state.rollback_stack = data.get("rollback_stack", [])
        
        for r_data in data.get("history", []):
            state.history.append(StageRecord(**r_data))
        
        for c_data in data.get("checkpoints", []):
            state.checkpoints.append(PipelineCheckpoint.from_dict(c_data))
        
        return state
    
    def save_to_file(self, filepath: str) -> None:
        """保存到文件"""
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
    
    @classmethod
    def load_from_file(cls, filepath: str) -> "PipelineState":
        """从文件加载"""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)
