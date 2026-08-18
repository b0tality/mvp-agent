"""
流水线相关Schema
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class StageResult(BaseModel):
    """阶段执行结果"""
    stage: str = Field(description="阶段名称")
    status: str = Field(description="状态: success/error/fallback/skipped")
    data: Dict[str, Any] = Field(default_factory=dict, description="输出数据")
    error: Optional[str] = Field(default=None, description="错误信息")
    agent_used: str = Field(default="primary", description="使用的Agent类型")
    duration_seconds: float = Field(default=0.0, description="执行耗时")


class PipelineResult(BaseModel):
    """流水线完整结果"""
    status: str = Field(description="状态: success/partial/aborted/failed")
    stages: Dict[str, StageResult] = Field(default_factory=dict, description="各阶段结果")
    failed_stages: List[str] = Field(default_factory=list, description="失败阶段列表")
    degraded_stages: List[str] = Field(default_factory=list, description="降级阶段列表")
    abort_reason: Optional[str] = Field(default=None, description="中止原因")
    total_duration: float = Field(default=0.0, description="总耗时")
    cost_report: Dict[str, Any] = Field(default_factory=dict, description="成本报告")
