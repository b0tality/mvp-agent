"""
部署相关Schema
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any


class DeploymentEnvironment(BaseModel):
    """部署环境"""
    name: str = Field(description="环境名称")
    url: str = Field(default="", description="访问地址")
    config: Dict[str, Any] = Field(default_factory=dict, description="环境配置")


class DeploymentPlan(BaseModel):
    """部署方案"""
    strategy: str = Field(default="rolling", description="部署策略")
    environments: List[DeploymentEnvironment] = Field(default_factory=list, description="环境列表")
    steps: List[str] = Field(default_factory=list, description="部署步骤")


class DockerConfig(BaseModel):
    """Docker配置"""
    dockerfile: str = Field(default="", description="Dockerfile内容")
    docker_compose: str = Field(default="", description="docker-compose.yml内容")


class KubernetesConfig(BaseModel):
    """Kubernetes配置"""
    deployments: List[Dict[str, Any]] = Field(default_factory=list, description="Deployment配置")
    services: List[Dict[str, Any]] = Field(default_factory=list, description="Service配置")


class CICDConfig(BaseModel):
    """CI/CD配置"""
    workflows: List[Dict[str, Any]] = Field(default_factory=list, description="工作流配置")


class MonitoringConfig(BaseModel):
    """监控配置"""
    prometheus: Dict[str, Any] = Field(default_factory=dict, description="Prometheus配置")
    grafana: Dict[str, Any] = Field(default_factory=dict, description="Grafana配置")
    alerts: List[Dict[str, Any]] = Field(default_factory=list, description="告警规则")


class DeploymentOutput(BaseModel):
    """部署输出"""
    deployment_plan: DeploymentPlan = Field(
        default_factory=DeploymentPlan, description="部署方案"
    )
    docker_config: DockerConfig = Field(
        default_factory=DockerConfig, description="Docker配置"
    )
    kubernetes_config: KubernetesConfig = Field(
        default_factory=KubernetesConfig, description="Kubernetes配置"
    )
    cicd_config: CICDConfig = Field(
        default_factory=CICDConfig, description="CI/CD配置"
    )
    monitoring_config: MonitoringConfig = Field(
        default_factory=MonitoringConfig, description="监控配置"
    )
