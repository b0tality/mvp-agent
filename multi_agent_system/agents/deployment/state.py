"""
软件部署智能体状态定义
"""

from typing import TypedDict, List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum


class Environment(str, Enum):
    """部署环境"""
    DEVELOPMENT = "development"    # 开发环境
    STAGING = "staging"            # 预发布环境
    PRODUCTION = "production"      # 生产环境


class DeploymentStrategy(str, Enum):
    """部署策略"""
    ROLLING = "rolling"            # 滚动部署
    BLUE_GREEN = "blue_green"      # 蓝绿部署
    CANARY = "canary"              # 金丝雀部署
    RECREATE = "recreate"          # 重新部署


class CloudProvider(str, Enum):
    """云服务提供商"""
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"
    ALIYUN = "aliyun"
    TENCENT = "tencent"
    SELF_HOSTED = "self_hosted"


@dataclass
class Infrastructure:
    """基础设施配置"""
    provider: CloudProvider
    region: str
    instance_type: str
    instances: int
    storage: str
    network: Dict[str, Any]


@dataclass
class ContainerConfig:
    """容器配置"""
    base_image: str
    build_args: Dict[str, str]
    ports: List[int]
    volumes: List[str]
    environment: Dict[str, str]
    resources: Dict[str, str]


@dataclass
class CICDPipeline:
    """CI/CD流水线"""
    provider: str  # GitHub Actions, GitLab CI, Jenkins, etc.
    stages: List[Dict[str, Any]]
    triggers: List[str]
    environment_variables: Dict[str, str]


@dataclass
class MonitoringConfig:
    """监控配置"""
    metrics_enabled: bool
    logging_enabled: bool
    tracing_enabled: bool
    alerting_enabled: bool
    tools: List[str]  # Prometheus, Grafana, ELK, etc.


@dataclass
class DeploymentPlan:
    """部署计划"""
    environment: Environment
    strategy: DeploymentStrategy
    infrastructure: Infrastructure
    containers: List[ContainerConfig]
    cicd: CICDPipeline
    monitoring: MonitoringConfig
    rollback_plan: Dict[str, Any]
    estimated_cost: Dict[str, Any]


class DeploymentState(TypedDict):
    """软件部署状态"""
    
    # 输入
    code_files: list                    # 代码文件列表
    project_info: dict                  # 项目信息
    technical_solution: dict            # 技术方案
    test_results: dict                  # 测试结果
    
    # 部署配置
    deployment_plan: dict               # 部署计划
    environments: dict                  # 环境配置
    infrastructure: dict                # 基础设施配置
    
    # 容器化
    docker_config: dict                 # Docker配置
    dockerfile: str                     # Dockerfile内容
    docker_compose: str                 # docker-compose.yml内容
    kubernetes_config: dict             # Kubernetes配置
    
    # CI/CD
    cicd_config: dict                   # CI/CD配置
    pipeline_stages: list               # 流水线阶段
    deployment_scripts: list            # 部署脚本
    
    # 监控
    monitoring_config: dict             # 监控配置
    logging_config: dict                # 日志配置
    alerting_config: dict               # 告警配置
    
    # 安全
    security_config: dict               # 安全配置
    ssl_config: dict                    # SSL配置
    firewall_rules: list                # 防火墙规则
    
    # 成本
    cost_estimation: dict               # 成本估算
    resource_optimization: dict         # 资源优化建议
    
    # 部署状态
    deployment_status: str              # 部署状态
    deployed_environments: list         # 已部署环境
    deployment_history: list            # 部署历史
    
    # 文档
    deployment_docs: str                # 部署文档
    runbook: str                        # 运维手册
    
    # 元数据
    status: str                         # 智能体状态
    created_at: str                     # 创建时间
    updated_at: str                     # 更新时间
    errors: list                        # 错误记录


class DeploymentStateManager:
    """软件部署状态管理器"""
    
    def __init__(self):
        self._state: DeploymentState = {
            "code_files": [],
            "project_info": {},
            "technical_solution": {},
            "test_results": {},
            "deployment_plan": {},
            "environments": {},
            "infrastructure": {},
            "docker_config": {},
            "dockerfile": "",
            "docker_compose": "",
            "kubernetes_config": {},
            "cicd_config": {},
            "pipeline_stages": [],
            "deployment_scripts": [],
            "monitoring_config": {},
            "logging_config": {},
            "alerting_config": {},
            "security_config": {},
            "ssl_config": {},
            "firewall_rules": [],
            "cost_estimation": {},
            "resource_optimization": {},
            "deployment_status": "pending",
            "deployed_environments": [],
            "deployment_history": [],
            "deployment_docs": "",
            "runbook": "",
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
    
    def get_all(self) -> DeploymentState:
        """获取完整状态"""
        return self._state.copy()
    
    def get_history(self) -> list:
        """获取变更历史"""
        return self._history
    
    def set_code_files(self, files: list) -> None:
        """设置代码文件"""
        self._state["code_files"] = files
    
    def set_project_info(self, info: dict) -> None:
        """设置项目信息"""
        self._state["project_info"] = info
    
    def set_technical_solution(self, solution: dict) -> None:
        """设置技术方案"""
        self._state["technical_solution"] = solution
    
    def set_test_results(self, results: dict) -> None:
        """设置测试结果"""
        self._state["test_results"] = results
    
    def set_deployment_plan(self, plan: dict) -> None:
        """设置部署计划"""
        self._state["deployment_plan"] = plan
    
    def set_environments(self, envs: dict) -> None:
        """设置环境配置"""
        self._state["environments"] = envs
    
    def set_infrastructure(self, infra: dict) -> None:
        """设置基础设施配置"""
        self._state["infrastructure"] = infra
    
    def set_docker_config(self, config: dict) -> None:
        """设置Docker配置"""
        self._state["docker_config"] = config
    
    def set_dockerfile(self, content: str) -> None:
        """设置Dockerfile"""
        self._state["dockerfile"] = content
    
    def set_docker_compose(self, content: str) -> None:
        """设置docker-compose.yml"""
        self._state["docker_compose"] = content
    
    def set_kubernetes_config(self, config: dict) -> None:
        """设置Kubernetes配置"""
        self._state["kubernetes_config"] = config
    
    def set_cicd_config(self, config: dict) -> None:
        """设置CI/CD配置"""
        self._state["cicd_config"] = config
    
    def add_pipeline_stage(self, stage: dict) -> None:
        """添加流水线阶段"""
        self._state["pipeline_stages"].append(stage)
    
    def add_deployment_script(self, script: dict) -> None:
        """添加部署脚本"""
        self._state["deployment_scripts"].append(script)
    
    def set_monitoring_config(self, config: dict) -> None:
        """设置监控配置"""
        self._state["monitoring_config"] = config
    
    def set_logging_config(self, config: dict) -> None:
        """设置日志配置"""
        self._state["logging_config"] = config
    
    def set_alerting_config(self, config: dict) -> None:
        """设置告警配置"""
        self._state["alerting_config"] = config
    
    def set_security_config(self, config: dict) -> None:
        """设置安全配置"""
        self._state["security_config"] = config
    
    def set_ssl_config(self, config: dict) -> None:
        """设置SSL配置"""
        self._state["ssl_config"] = config
    
    def add_firewall_rule(self, rule: dict) -> None:
        """添加防火墙规则"""
        self._state["firewall_rules"].append(rule)
    
    def set_cost_estimation(self, estimation: dict) -> None:
        """设置成本估算"""
        self._state["cost_estimation"] = estimation
    
    def set_resource_optimization(self, optimization: dict) -> None:
        """设置资源优化建议"""
        self._state["resource_optimization"] = optimization
    
    def set_deployment_status(self, status: str) -> None:
        """设置部署状态"""
        self._state["deployment_status"] = status
    
    def add_deployed_environment(self, env: str) -> None:
        """添加已部署环境"""
        if env not in self._state["deployed_environments"]:
            self._state["deployed_environments"].append(env)
    
    def add_deployment_history(self, record: dict) -> None:
        """添加部署历史"""
        self._state["deployment_history"].append(record)
    
    def set_deployment_docs(self, docs: str) -> None:
        """设置部署文档"""
        self._state["deployment_docs"] = docs
    
    def set_runbook(self, runbook: str) -> None:
        """设置运维手册"""
        self._state["runbook"] = runbook
    
    def set_status(self, status: str) -> None:
        """设置状态"""
        self._state["status"] = status
    
    def add_error(self, error: str) -> None:
        """添加错误记录"""
        self._state["errors"].append({
            "timestamp": datetime.now().isoformat(),
            "message": error
        })
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return self._state.copy()
    
    def reset(self) -> None:
        """重置状态"""
        self.__init__()
