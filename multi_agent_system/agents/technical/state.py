"""
技术架构师状态定义
"""

from typing import TypedDict, List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field


class TechnicalState(TypedDict):
    """技术架构状态"""
    
    # 输入
    requirements: dict                  # 需求分析结果
    
    # 架构设计
    system_architecture: dict           # 系统架构
    component_design: dict              # 组件设计
    deployment_architecture: dict       # 部署架构
    
    # 技术选型
    tech_stack: dict                    # 技术栈
    framework_choices: dict             # 框架选择
    database_design: dict               # 数据库设计
    
    # API设计
    api_design: dict                    # API设计
    api_endpoints: list                 # API端点列表
    data_models: dict                   # 数据模型
    
    # 安全设计
    security_design: dict               # 安全设计
    authentication: dict                # 认证方案
    authorization: dict                 # 授权方案
    data_protection: dict               # 数据保护
    
    # 成本估算
    cost_estimation: dict               # 成本估算
    resource_requirements: dict         # 资源需求
    scaling_strategy: dict              # 扩展策略
    
    # 文档
    technical_spec: dict                # 技术规格文档
    architecture_decision_records: list # 架构决策记录
    
    # 元数据
    status: str                         # 设计状态
    created_at: str                     # 创建时间
    updated_at: str                     # 更新时间
    errors: list                        # 错误记录


@dataclass
class ArchitectureDecision:
    """架构决策记录"""
    id: str
    title: str
    context: str
    decision: str
    consequences: str
    alternatives: list = field(default_factory=list)
    status: str = "proposed"  # proposed, accepted, deprecated, superseded
    date: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class TechStackComponent:
    """技术栈组件"""
    name: str
    category: str  # frontend, backend, database, infrastructure, etc.
    version: str
    description: str
    alternatives: list = field(default_factory=list)
    pros: list = field(default_factory=list)
    cons: list = field(default_factory=list)
    cost: str = "free"  # free, paid, freemium


@dataclass
class APIEndpoint:
    """API端点定义"""
    path: str
    method: str  # GET, POST, PUT, DELETE
    description: str
    request_body: Optional[dict] = None
    response_body: Optional[dict] = None
    authentication: bool = True
    rate_limit: Optional[int] = None


class TechnicalStateManager:
    """技术状态管理器"""
    
    def __init__(self):
        self._state: TechnicalState = {
            "requirements": {},
            "system_architecture": {},
            "component_design": {},
            "deployment_architecture": {},
            "tech_stack": {},
            "framework_choices": {},
            "database_design": {},
            "api_design": {},
            "api_endpoints": [],
            "data_models": {},
            "security_design": {},
            "authentication": {},
            "authorization": {},
            "data_protection": {},
            "cost_estimation": {},
            "resource_requirements": {},
            "scaling_strategy": {},
            "technical_spec": {},
            "architecture_decision_records": [],
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
    
    def get_all(self) -> TechnicalState:
        """获取完整状态"""
        return self._state.copy()
    
    def get_history(self) -> list:
        """获取变更历史"""
        return self._history
    
    def set_requirements(self, requirements: dict) -> None:
        """设置需求"""
        self._state["requirements"] = requirements
        self._state["updated_at"] = datetime.now().isoformat()
    
    def set_architecture(self, architecture: dict) -> None:
        """设置系统架构"""
        self._state["system_architecture"] = architecture
        self._state["updated_at"] = datetime.now().isoformat()
    
    def set_tech_stack(self, tech_stack: dict) -> None:
        """设置技术栈"""
        self._state["tech_stack"] = tech_stack
        self._state["updated_at"] = datetime.now().isoformat()
    
    def set_api_design(self, api_design: dict) -> None:
        """设置API设计"""
        self._state["api_design"] = api_design
        self._state["updated_at"] = datetime.now().isoformat()
    
    def add_api_endpoint(self, endpoint: dict) -> None:
        """添加API端点"""
        self._state["api_endpoints"].append(endpoint)
        self._state["updated_at"] = datetime.now().isoformat()
    
    def set_database_design(self, design: dict) -> None:
        """设置数据库设计"""
        self._state["database_design"] = design
        self._state["updated_at"] = datetime.now().isoformat()
    
    def set_security_design(self, design: dict) -> None:
        """设置安全设计"""
        self._state["security_design"] = design
        self._state["updated_at"] = datetime.now().isoformat()
    
    def set_cost_estimation(self, estimation: dict) -> None:
        """设置成本估算"""
        self._state["cost_estimation"] = estimation
        self._state["updated_at"] = datetime.now().isoformat()
    
    def add_adr(self, adr: dict) -> None:
        """添加架构决策记录"""
        self._state["architecture_decision_records"].append(adr)
        self._state["updated_at"] = datetime.now().isoformat()
    
    def set_status(self, status: str) -> None:
        """设置状态"""
        self._state["status"] = status
        self._state["updated_at"] = datetime.now().isoformat()
    
    def add_error(self, error: str) -> None:
        """添加错误记录"""
        self._state["errors"].append({
            "timestamp": datetime.now().isoformat(),
            "message": error
        })
        self._state["updated_at"] = datetime.now().isoformat()
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return self._state.copy()
    
    def reset(self) -> None:
        """重置状态"""
        self.__init__()
