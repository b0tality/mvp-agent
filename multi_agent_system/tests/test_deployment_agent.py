"""
软件部署智能体测试
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from agents.deployment import DeploymentAgent, DeploymentStateManager


class TestDeploymentStateManager:
    """测试软件部署状态管理器"""
    
    def setup_method(self):
        """测试前准备"""
        self.manager = DeploymentStateManager()
    
    def test_initial_state(self):
        """测试初始状态"""
        state = self.manager.get_all()
        assert state["status"] == "initialized"
        assert state["deployment_status"] == "pending"
        assert state["code_files"] == []
        assert state["docker_config"] == {}
        assert state["kubernetes_config"] == {}
    
    def test_set_code_files(self):
        """测试设置代码文件"""
        files = [{"path": "main.py", "content": "print('hello')"}]
        self.manager.set_code_files(files)
        assert self.manager.get("code_files") == files
    
    def test_set_technical_solution(self):
        """测试设置技术方案"""
        solution = {"tech_stack": {}}
        self.manager.set_technical_solution(solution)
        assert self.manager.get("technical_solution") == solution
    
    def test_set_deployment_plan(self):
        """测试设置部署计划"""
        plan = {"deployment_strategy": {"type": "rolling"}}
        self.manager.set_deployment_plan(plan)
        assert self.manager.get("deployment_plan") == plan
    
    def test_set_docker_config(self):
        """测试设置Docker配置"""
        config = {"dockerfile": {"content": "FROM python:3.11"}}
        self.manager.set_docker_config(config)
        assert self.manager.get("docker_config") == config
    
    def test_set_dockerfile(self):
        """测试设置Dockerfile"""
        content = "FROM python:3.11-slim\nWORKDIR /app"
        self.manager.set_dockerfile(content)
        assert self.manager.get("dockerfile") == content
    
    def test_set_docker_compose(self):
        """测试设置docker-compose.yml"""
        content = "version: '3.8'\nservices:\n  app:"
        self.manager.set_docker_compose(content)
        assert self.manager.get("docker_compose") == content
    
    def test_set_kubernetes_config(self):
        """测试设置Kubernetes配置"""
        config = {"deployment": {"content": "apiVersion: apps/v1"}}
        self.manager.set_kubernetes_config(config)
        assert self.manager.get("kubernetes_config") == config
    
    def test_set_cicd_config(self):
        """测试设置CI/CD配置"""
        config = {"ci_config": {"provider": "github_actions"}}
        self.manager.set_cicd_config(config)
        assert self.manager.get("cicd_config") == config
    
    def test_set_monitoring_config(self):
        """测试设置监控配置"""
        config = {"metrics": {"tool": "prometheus"}}
        self.manager.set_monitoring_config(config)
        assert self.manager.get("monitoring_config") == config
    
    def test_set_deployment_docs(self):
        """测试设置部署文档"""
        docs = "# 部署指南\n\n## 环境准备"
        self.manager.set_deployment_docs(docs)
        assert self.manager.get("deployment_docs") == docs
    
    def test_set_runbook(self):
        """测试设置运维手册"""
        runbook = "# 运维手册\n\n## 日常运维"
        self.manager.set_runbook(runbook)
        assert self.manager.get("runbook") == runbook
    
    def test_set_deployment_status(self):
        """测试设置部署状态"""
        self.manager.set_deployment_status("deployed")
        assert self.manager.get("deployment_status") == "deployed"
    
    def test_add_deployed_environment(self):
        """测试添加已部署环境"""
        self.manager.add_deployed_environment("development")
        self.manager.add_deployed_environment("staging")
        assert self.manager.get("deployed_environments") == ["development", "staging"]
    
    def test_add_deployed_environment_duplicate(self):
        """测试添加重复环境"""
        self.manager.add_deployed_environment("development")
        self.manager.add_deployed_environment("development")
        assert self.manager.get("deployed_environments") == ["development"]
    
    def test_set_status(self):
        """测试设置状态"""
        self.manager.set_status("in_progress")
        assert self.manager.get("status") == "in_progress"
    
    def test_add_error(self):
        """测试添加错误"""
        self.manager.add_error("测试错误")
        errors = self.manager.get("errors")
        assert len(errors) == 1
        assert errors[0]["message"] == "测试错误"
    
    def test_reset(self):
        """测试重置"""
        self.manager.set_deployment_status("deployed")
        self.manager.set_status("in_progress")
        self.manager.reset()
        
        state = self.manager.get_all()
        assert state["status"] == "initialized"
        assert state["deployment_status"] == "pending"


class TestDeploymentAgent:
    """测试软件部署智能体"""
    
    def setup_method(self):
        """测试前准备"""
        self.config = {
            "model": "gpt-4",
            "temperature": 0.2
        }
    
    @pytest.mark.asyncio
    async def test_agent_initialization(self):
        """测试智能体初始化"""
        agent = DeploymentAgent(self.config)
        assert agent.config == self.config
        assert agent.llm is not None
        assert len(agent.tools) == 6
    
    @pytest.mark.asyncio
    async def test_get_state(self):
        """测试获取状态"""
        agent = DeploymentAgent(self.config)
        state = agent.get_state()
        assert state["status"] == "initialized"
    
    @pytest.mark.asyncio
    async def test_get_conversation_history(self):
        """测试获取对话历史"""
        agent = DeploymentAgent(self.config)
        history = agent.get_conversation_history()
        assert history == []
    
    @pytest.mark.asyncio
    async def test_get_deployment_plan(self):
        """测试获取部署计划"""
        agent = DeploymentAgent(self.config)
        plan = agent.get_deployment_plan()
        assert plan == {}
    
    @pytest.mark.asyncio
    async def test_get_docker_config(self):
        """测试获取Docker配置"""
        agent = DeploymentAgent(self.config)
        config = agent.get_docker_config()
        assert config == {}
    
    @pytest.mark.asyncio
    async def test_get_kubernetes_config(self):
        """测试获取Kubernetes配置"""
        agent = DeploymentAgent(self.config)
        config = agent.get_kubernetes_config()
        assert config == {}
    
    @pytest.mark.asyncio
    async def test_reset(self):
        """测试重置"""
        agent = DeploymentAgent(self.config)
        agent.state_manager.set_deployment_status("deployed")
        agent.conversation_history.append({"role": "user", "content": "test"})
        agent.reset()
        
        assert agent.conversation_history == []
        assert agent.get_state()["deployment_status"] == "pending"


class TestDeploymentPlannerTool:
    """测试部署方案设计工具"""
    
    @pytest.mark.asyncio
    async def test_tool_initialization(self):
        """测试工具初始化"""
        from agents.deployment.tools.deployment_planner import DeploymentPlannerTool
        tool = DeploymentPlannerTool()
        assert tool.name == "deployment_planner"


class TestDockerConfiguratorTool:
    """测试Docker配置工具"""
    
    @pytest.mark.asyncio
    async def test_tool_initialization(self):
        """测试工具初始化"""
        from agents.deployment.tools.docker_configurator import DockerConfiguratorTool
        tool = DockerConfiguratorTool()
        assert tool.name == "docker_configurator"


class TestKubernetesConfiguratorTool:
    """测试Kubernetes配置工具"""
    
    @pytest.mark.asyncio
    async def test_tool_initialization(self):
        """测试工具初始化"""
        from agents.deployment.tools.kubernetes_configurator import KubernetesConfiguratorTool
        tool = KubernetesConfiguratorTool()
        assert tool.name == "kubernetes_configurator"


class TestCICDConfiguratorTool:
    """测试CI/CD配置工具"""
    
    @pytest.mark.asyncio
    async def test_tool_initialization(self):
        """测试工具初始化"""
        from agents.deployment.tools.cicd_configurator import CICDConfiguratorTool
        tool = CICDConfiguratorTool()
        assert tool.name == "cicd_configurator"


class TestMonitoringConfiguratorTool:
    """测试监控配置工具"""
    
    @pytest.mark.asyncio
    async def test_tool_initialization(self):
        """测试工具初始化"""
        from agents.deployment.tools.monitoring_configurator import MonitoringConfiguratorTool
        tool = MonitoringConfiguratorTool()
        assert tool.name == "monitoring_configurator"


class TestDeploymentDocGeneratorTool:
    """测试部署文档生成工具"""
    
    @pytest.mark.asyncio
    async def test_tool_initialization(self):
        """测试工具初始化"""
        from agents.deployment.tools.deployment_doc_generator import DeploymentDocGeneratorTool
        tool = DeploymentDocGeneratorTool()
        assert tool.name == "deployment_doc_generator"


# 运行测试
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
