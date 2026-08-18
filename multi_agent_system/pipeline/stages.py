"""
阶段定义和执行
"""

from enum import Enum
from typing import Dict, List, Any, Optional, Callable, Awaitable
from dataclasses import dataclass


class Stage(str, Enum):
    """流水线阶段枚举"""
    REQUIREMENTS = "requirements"
    TECHNICAL = "technical"
    MVP = "mvp"
    CODE_REVIEW = "code_review"
    TESTING = "testing"
    DEPLOYMENT = "deployment"


@dataclass
class StageDependency:
    """阶段依赖关系"""
    dependencies: Dict[str, List[str]] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = {
                Stage.REQUIREMENTS: [],
                Stage.TECHNICAL: [Stage.REQUIREMENTS],
                Stage.MVP: [Stage.REQUIREMENTS, Stage.TECHNICAL],
                Stage.CODE_REVIEW: [Stage.MVP],
                Stage.TESTING: [Stage.MVP],
                Stage.DEPLOYMENT: [Stage.MVP, Stage.TESTING]
            }
    
    def can_proceed(self, stage: str, completed_stages: List[str]) -> bool:
        """检查阶段是否可以继续"""
        deps = self.dependencies.get(stage, [])
        return all(dep in completed_stages for dep in deps)
    
    def get_minimal_deps(self, stage: str) -> List[str]:
        """获取最小依赖（降级时使用）"""
        minimal_deps = {
            Stage.MVP: [Stage.REQUIREMENTS],
            Stage.CODE_REVIEW: [Stage.MVP],
            Stage.TESTING: [Stage.MVP],
            Stage.DEPLOYMENT: [Stage.MVP]
        }
        return minimal_deps.get(stage, self.dependencies.get(stage, []))


class StageExecutor:
    """阶段执行器"""
    
    def __init__(self):
        self._executors: Dict[str, Callable[..., Awaitable[Dict[str, Any]]]] = {}
    
    def register(self, stage: str, executor: Callable[..., Awaitable[Dict[str, Any]]]) -> None:
        """注册阶段执行器"""
        self._executors[stage] = executor
    
    async def execute(self, stage: str, **kwargs) -> Dict[str, Any]:
        """执行阶段"""
        if stage not in self._executors:
            raise ValueError(f"未注册的阶段: {stage}")
        return await self._executors[stage](**kwargs)
    
    def has_executor(self, stage: str) -> bool:
        """检查是否有执行器"""
        return stage in self._executors
