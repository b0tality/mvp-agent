"""
技术架构师智能体测试
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from agents.technical import TechnicalAgent, TechnicalStateManager


class TestTechnicalStateManager:
    """测试技术状态管理器"""
    
    def setup_method(self):
        """测试前准备"""
        self.manager = TechnicalStateManager()
    
    def test_initial_state(self):
        """测试初始状态"""
        state = self.manager.get_all()
        assert state["status"] == "initialized"
        assert state["requirements"] == {}
        assert state["system_architecture"] == {}
        assert state["tech_stack"] == {}
    
    def test_set_requirements(self):
        """测试设置需求"""
        requirements = {"functional_requirements": []}
        self.manager.set_requirements(requirements)
        assert self.manager.get("requirements") == requirements
    
    def test_set_architecture(self):
        """测试设置架构"""
        architecture = {"pattern": "微服务"}
        self.manager.set_architecture(architecture)
        assert self.manager.get("system_architecture") == architecture
    
    def test_set_tech_stack(self):
        """测试设置技术栈"""
        tech_stack = {"frontend": {}, "backend": {}}
        self.manager.set_tech_stack(tech_stack)
        assert self.manager.get("tech_stack") == tech_stack
    
    def test_set_api_design(self):
        """测试设置API设计"""
        api_design = {"endpoints": []}
        self.manager.set_api_design(api_design)
        assert self.manager.get("api_design") == api_design
    
    def test_add_api_endpoint(self):
        """测试添加API端点"""
        endpoint = {"path": "/users", "method": "GET"}
        self.manager.add_api_endpoint(endpoint)
        assert len(self.manager.get("api_endpoints")) == 1
    
    def test_set_database_design(self):
        """测试设置数据库设计"""
        design = {"models": []}
        self.manager.set_database_design(design)
        assert self.manager.get("database_design") == design
    
    def test_set_security_design(self):
        """测试设置安全设计"""
        design = {"authentication": {}}
        self.manager.set_security_design(design)
        assert self.manager.get("security_design") == design
    
    def test_set_cost_estimation(self):
        """测试设置成本估算"""
        estimation = {"total": 10000}
        self.manager.set_cost_estimation(estimation)
        assert self.manager.get("cost_estimation") == estimation
    
    def test_add_adr(self):
        """测试添加架构决策记录"""
        adr = {"id": "ADR-001", "title": "选择数据库"}
        self.manager.add_adr(adr)
        assert len(self.manager.get("architecture_decision_records")) == 1
    
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
    
    def test_history(self):
        """测试历史记录"""
        self.manager.set_requirements({"test": True})
        self.manager.set_architecture({"pattern": "单体"})
        history = self.manager.get_history()
        assert len(history) == 2
    
    def test_reset(self):
        """测试重置"""
        self.manager.set_requirements({"test": True})
        self.manager.set_status("in_progress")
        self.manager.reset()
        
        state = self.manager.get_all()
        assert state["status"] == "initialized"
        assert state["requirements"] == {}


class TestTechnicalAgent:
    """测试技术架构师智能体"""
    
    def setup_method(self):
        """测试前准备"""
        self.config = {
            "model": "gpt-4",
            "temperature": 0.2
        }
    
    @pytest.mark.asyncio
    async def test_agent_initialization(self):
        """测试智能体初始化"""
        agent = TechnicalAgent(self.config)
        assert agent.config == self.config
        assert agent.llm is not None
        assert len(agent.tools) == 6
    
    @pytest.mark.asyncio
    async def test_get_state(self):
        """测试获取状态"""
        agent = TechnicalAgent(self.config)
        state = agent.get_state()
        assert state["status"] == "initialized"
    
    @pytest.mark.asyncio
    async def test_get_conversation_history(self):
        """测试获取对话历史"""
        agent = TechnicalAgent(self.config)
        history = agent.get_conversation_history()
        assert history == []
    
    @pytest.mark.asyncio
    async def test_get_technical_spec(self):
        """测试获取技术规格文档"""
        agent = TechnicalAgent(self.config)
        spec = agent.get_technical_spec()
        assert spec == {}
    
    @pytest.mark.asyncio
    async def test_reset(self):
        """测试重置"""
        agent = TechnicalAgent(self.config)
        agent.conversation_history.append({"role": "user", "content": "test"})
        agent.reset()
        
        assert agent.conversation_history == []
        assert agent.get_state()["status"] == "initialized"


class TestArchitectureDesignerTool:
    """测试架构设计工具"""
    
    @pytest.mark.asyncio
    async def test_tool_initialization(self):
        """测试工具初始化"""
        from agents.technical.tools.architecture_designer import ArchitectureDesignerTool
        tool = ArchitectureDesignerTool()
        assert tool.name == "architecture_designer"


class TestTechStackSelectorTool:
    """测试技术栈选择工具"""
    
    @pytest.mark.asyncio
    async def test_tool_initialization(self):
        """测试工具初始化"""
        from agents.technical.tools.tech_stack_selector import TechStackSelectorTool
        tool = TechStackSelectorTool()
        assert tool.name == "tech_stack_selector"


class TestAPIDesignerTool:
    """测试API设计工具"""
    
    @pytest.mark.asyncio
    async def test_tool_initialization(self):
        """测试工具初始化"""
        from agents.technical.tools.api_designer import APIDesignerTool
        tool = APIDesignerTool()
        assert tool.name == "api_designer"


class TestDatabaseDesignerTool:
    """测试数据库设计工具"""
    
    @pytest.mark.asyncio
    async def test_tool_initialization(self):
        """测试工具初始化"""
        from agents.technical.tools.database_designer import DatabaseDesignerTool
        tool = DatabaseDesignerTool()
        assert tool.name == "database_designer"


class TestSecurityDesignerTool:
    """测试安全设计工具"""
    
    @pytest.mark.asyncio
    async def test_tool_initialization(self):
        """测试工具初始化"""
        from agents.technical.tools.security_designer import SecurityDesignerTool
        tool = SecurityDesignerTool()
        assert tool.name == "security_designer"


class TestCostEstimatorTool:
    """测试成本估算工具"""
    
    @pytest.mark.asyncio
    async def test_tool_initialization(self):
        """测试工具初始化"""
        from agents.technical.tools.cost_estimator import CostEstimatorTool
        tool = CostEstimatorTool()
        assert tool.name == "cost_estimator"


# 运行测试
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
