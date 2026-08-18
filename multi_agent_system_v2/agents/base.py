"""
Agent抽象基类
解决V1的返回格式不一致问题：所有Agent统一返回AgentResult
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from llm.adapter import LLMAdapter


class AgentResult(BaseModel):
    """
    Agent统一返回格式
    
    解决V1中各Agent返回格式不一致的问题。
    Orchestrator只依赖此格式，不关心Agent内部实现。
    """
    status: str = Field(description="状态: success/error/fallback")
    data: Dict[str, Any] = Field(default_factory=dict, description="输出数据")
    error: Optional[str] = Field(default=None, description="错误信息")
    agent_used: str = Field(default="primary", description="使用的Agent类型: primary/fallback")
    duration_seconds: float = Field(default=0.0, description="执行耗时")


class BaseAgent(ABC):
    """
    Agent抽象基类
    
    所有Agent实现此接口，统一返回AgentResult。
    换Agent实现不影响Orchestrator。
    """

    name: str = "base_agent"

    def __init__(self, llm: LLMAdapter):
        self.llm = llm

    @abstractmethod
    async def execute(self, **kwargs) -> AgentResult:
        """
        执行Agent任务
        
        Args:
            **kwargs: Agent参数（各Agent自定义）
            
        Returns:
            AgentResult: 统一格式的执行结果
        """
        pass

    def _success(self, data: Dict[str, Any], duration: float = 0.0) -> AgentResult:
        """构建成功结果"""
        return AgentResult(
            status="success",
            data=data,
            agent_used="primary",
            duration_seconds=duration,
        )

    def _error(self, error: str, duration: float = 0.0) -> AgentResult:
        """构建错误结果"""
        return AgentResult(
            status="error",
            error=error,
            duration_seconds=duration,
        )

    def _fallback(self, data: Dict[str, Any], duration: float = 0.0) -> AgentResult:
        """构建降级结果"""
        return AgentResult(
            status="fallback",
            data=data,
            agent_used="fallback",
            duration_seconds=duration,
        )
