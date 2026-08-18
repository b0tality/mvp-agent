"""
技术方案相关Schema
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class TechStack(BaseModel):
    """技术栈"""
    backend: Any = Field(default="", description="后端技术（字符串或详细配置对象）")
    frontend: Any = Field(default="", description="前端技术")
    database: Any = Field(default="", description="数据库")
    tools: List[Any] = Field(default_factory=list, description="工具列表")
    
    class Config:
        extra = "allow"


class APIEndpoint(BaseModel):
    """API端点"""
    method: str = Field(default="GET", description="HTTP方法")
    path: str = Field(default="/", description="路径")
    description: str = Field(default="", description="描述")
    
    class Config:
        extra = "allow"


class APIDesign(BaseModel):
    """API设计"""
    endpoints: List[APIEndpoint] = Field(default_factory=list, description="端点列表")
    
    class Config:
        extra = "allow"


class DatabaseTable(BaseModel):
    """数据库表"""
    name: str = Field(default="", description="表名")
    columns: List[Dict[str, Any]] = Field(default_factory=list, description="列定义")
    
    class Config:
        extra = "allow"


class DatabaseDesign(BaseModel):
    """数据库设计"""
    tables: List[DatabaseTable] = Field(default_factory=list, description="表列表")
    
    class Config:
        extra = "allow"


class SecurityDesign(BaseModel):
    """安全设计"""
    authentication: Any = Field(default_factory=dict, description="认证方案")
    authorization: Any = Field(default_factory=dict, description="授权方案")
    encryption: Any = Field(default_factory=dict, description="加密方案")
    
    class Config:
        extra = "allow"


class ArchitectureDesign(BaseModel):
    """架构设计"""
    pattern: Any = Field(default="monolith", description="架构模式")
    components: List[Dict[str, Any]] = Field(default_factory=list, description="组件列表")
    connections: List[Dict[str, Any]] = Field(default_factory=list, description="连接关系")
    
    class Config:
        extra = "allow"


class CostEstimation(BaseModel):
    """成本估算"""
    estimated_hours: Any = Field(default=0, description="预估工时")
    team_size: Any = Field(default=0, description="建议团队规模")
    timeline: Any = Field(default="unknown", description="时间线")
    
    class Config:
        extra = "allow"


class TechnicalOutput(BaseModel):
    """技术方案完整输出"""
    architecture: ArchitectureDesign = Field(
        default_factory=ArchitectureDesign, description="架构设计"
    )
    tech_stack: TechStack = Field(
        default_factory=TechStack, description="技术栈"
    )
    api_design: APIDesign = Field(
        default_factory=APIDesign, description="API设计"
    )
    database_design: DatabaseDesign = Field(
        default_factory=DatabaseDesign, description="数据库设计"
    )
    security_design: SecurityDesign = Field(
        default_factory=SecurityDesign, description="安全设计"
    )
    cost_estimation: CostEstimation = Field(
        default_factory=CostEstimation, description="成本估算"
    )
    
    class Config:
        extra = "allow"
