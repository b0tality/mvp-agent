"""
需求分析智能体状态定义
"""

from typing import TypedDict, List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field


class RequirementsState(TypedDict):
    """需求分析状态"""
    
    # 输入
    user_input: str                    # 用户原始输入
    conversation_history: list         # 对话历史
    
    # 解析结果
    functional_requirements: list      # 功能需求列表
    non_functional_requirements: list  # 非功能需求列表
    constraints: list                  # 约束条件
    assumptions: list                  # 假设条件
    risks: list                        # 风险点
    
    # 结构化输出
    user_stories: list                 # 用户故事
    acceptance_criteria: list          # 验收标准
    priority_matrix: dict              # 优先级矩阵
    
    # 协调状态
    current_phase: str                 # 当前阶段
    assigned_agents: dict              # 已分配的智能体
    progress: dict                     # 进度跟踪
    decisions: list                    # 决策记录
    
    # 元数据
    status: str                        # 分析状态
    created_at: str                    # 创建时间
    updated_at: str                    # 更新时间
    errors: list                       # 错误记录


@dataclass
class Requirement:
    """单个需求定义"""
    id: str
    title: str
    description: str
    type: str  # functional, non_functional, constraint
    priority: str  # must_have, should_have, could_have, wont_have
    status: str = "draft"
    dependencies: list = field(default_factory=list)
    acceptance_criteria: list = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class UserStory:
    """用户故事定义"""
    id: str
    role: str
    feature: str
    benefit: str
    acceptance_criteria: list = field(default_factory=list)
    priority: str = "should_have"
    story_points: int = 0


class RequirementsStateManager:
    """需求状态管理器"""
    
    def __init__(self):
        self._state: RequirementsState = {
            "user_input": "",
            "conversation_history": [],
            "functional_requirements": [],
            "non_functional_requirements": [],
            "constraints": [],
            "assumptions": [],
            "risks": [],
            "user_stories": [],
            "acceptance_criteria": [],
            "priority_matrix": {},
            "current_phase": "idle",
            "assigned_agents": {},
            "progress": {},
            "decisions": [],
            "status": "initialized",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "errors": []
        }
        self._history: list = []
    
    def update(self, key: str, value: Any) -> None:
        """更新状态"""
        old_value = self._state.get(key)
        self._history.append({
            "timestamp": datetime.now().isoformat(),
            "key": key,
            "old_value": old_value,
            "new_value": value
        })
        self._state[key] = value
        self._state["updated_at"] = datetime.now().isoformat()
    
    def get(self, key: str) -> Any:
        """获取状态值"""
        return self._state.get(key)
    
    def get_all(self) -> RequirementsState:
        """获取完整状态"""
        return self._state.copy()
    
    def get_history(self) -> list:
        """获取变更历史"""
        return self._history
    
    def add_functional_requirement(self, req: dict) -> None:
        """添加功能需求"""
        self._state["functional_requirements"].append(req)
        self._state["updated_at"] = datetime.now().isoformat()
    
    def add_non_functional_requirement(self, req: dict) -> None:
        """添加非功能需求"""
        self._state["non_functional_requirements"].append(req)
        self._state["updated_at"] = datetime.now().isoformat()
    
    def add_user_story(self, story: dict) -> None:
        """添加用户故事"""
        self._state["user_stories"].append(story)
        self._state["updated_at"] = datetime.now().isoformat()
    
    def add_error(self, error: str) -> None:
        """添加错误记录"""
        self._state["errors"].append({
            "timestamp": datetime.now().isoformat(),
            "message": error
        })
        self._state["updated_at"] = datetime.now().isoformat()
    
    def set_phase(self, phase: str) -> None:
        """设置当前阶段"""
        self._state["current_phase"] = phase
        self._state["updated_at"] = datetime.now().isoformat()
    
    def set_status(self, status: str) -> None:
        """设置状态"""
        self._state["status"] = status
        self._state["updated_at"] = datetime.now().isoformat()
    
    def assign_agent(self, agent_name: str, task: dict) -> None:
        """分配智能体任务"""
        self._state["assigned_agents"][agent_name] = {
            "task": task,
            "status": "assigned",
            "assigned_at": datetime.now().isoformat()
        }
        self._state["updated_at"] = datetime.now().isoformat()
    
    def update_agent_progress(self, agent_name: str, status: str, result: Any = None) -> None:
        """更新智能体进度"""
        if agent_name in self._state["assigned_agents"]:
            self._state["assigned_agents"][agent_name]["status"] = status
            if result:
                self._state["assigned_agents"][agent_name]["result"] = result
            self._state["updated_at"] = datetime.now().isoformat()
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return self._state.copy()
    
    def reset(self) -> None:
        """重置状态"""
        self.__init__()
