"""
需求分析智能体测试
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from agents.requirements import RequirementsAgent, RequirementsStateManager


class TestRequirementsStateManager:
    """测试需求状态管理器"""
    
    def setup_method(self):
        """测试前准备"""
        self.manager = RequirementsStateManager()
    
    def test_initial_state(self):
        """测试初始状态"""
        state = self.manager.get_all()
        assert state["status"] == "initialized"
        assert state["current_phase"] == "idle"
        assert state["functional_requirements"] == []
        assert state["non_functional_requirements"] == []
    
    def test_update_state(self):
        """测试更新状态"""
        self.manager.update("user_input", "测试输入")
        assert self.manager.get("user_input") == "测试输入"
    
    def test_set_phase(self):
        """测试设置阶段"""
        self.manager.set_phase("analyzing")
        assert self.manager.get("current_phase") == "analyzing"
    
    def test_set_status(self):
        """测试设置状态"""
        self.manager.set_status("in_progress")
        assert self.manager.get("status") == "in_progress"
    
    def test_add_functional_requirement(self):
        """测试添加功能需求"""
        req = {"id": "FR-001", "title": "测试需求"}
        self.manager.add_functional_requirement(req)
        assert len(self.manager.get("functional_requirements")) == 1
    
    def test_add_error(self):
        """测试添加错误"""
        self.manager.add_error("测试错误")
        errors = self.manager.get("errors")
        assert len(errors) == 1
        assert errors[0]["message"] == "测试错误"
    
    def test_assign_agent(self):
        """测试分配智能体"""
        task = {"id": "TASK-001", "title": "测试任务"}
        self.manager.assign_agent("technical", task)
        agents = self.manager.get("assigned_agents")
        assert "technical" in agents
    
    def test_history(self):
        """测试历史记录"""
        self.manager.update("key1", "value1")
        self.manager.update("key2", "value2")
        history = self.manager.get_history()
        assert len(history) == 2
    
    def test_reset(self):
        """测试重置"""
        self.manager.update("user_input", "测试")
        self.manager.set_status("in_progress")
        self.manager.reset()
        
        state = self.manager.get_all()
        assert state["status"] == "initialized"
        assert state["user_input"] == ""


class TestRequirementsAgent:
    """测试需求分析智能体"""
    
    def setup_method(self):
        """测试前准备"""
        self.config = {
            "model": "gpt-4",
            "temperature": 0.3
        }
    
    @pytest.mark.asyncio
    async def test_agent_initialization(self):
        """测试智能体初始化"""
        agent = RequirementsAgent(self.config)
        assert agent.config == self.config
        assert agent.llm is not None
        assert len(agent.tools) == 5
    
    @pytest.mark.asyncio
    async def test_get_state(self):
        """测试获取状态"""
        agent = RequirementsAgent(self.config)
        state = agent.get_state()
        assert state["status"] == "initialized"
    
    @pytest.mark.asyncio
    async def test_get_conversation_history(self):
        """测试获取对话历史"""
        agent = RequirementsAgent(self.config)
        history = agent.get_conversation_history()
        assert history == []
    
    @pytest.mark.asyncio
    async def test_reset(self):
        """测试重置"""
        agent = RequirementsAgent(self.config)
        agent.conversation_history.append({"role": "user", "content": "test"})
        agent.reset()
        
        assert agent.conversation_history == []
        assert agent.get_state()["status"] == "initialized"


class TestRequirementParserTool:
    """测试需求解析工具"""
    
    @pytest.mark.asyncio
    async def test_parser_initialization(self):
        """测试解析器初始化"""
        from agents.requirements.tools.requirement_parser import RequirementParserTool
        tool = RequirementParserTool()
        assert tool.name == "requirement_parser"


class TestUserStoryGeneratorTool:
    """测试用户故事生成工具"""
    
    @pytest.mark.asyncio
    async def test_generator_initialization(self):
        """测试生成器初始化"""
        from agents.requirements.tools.user_story_generator import UserStoryGeneratorTool
        tool = UserStoryGeneratorTool()
        assert tool.name == "user_story_generator"


class TestAcceptanceCriteriaTool:
    """测试验收标准工具"""
    
    @pytest.mark.asyncio
    async def test_criteria_initialization(self):
        """测试验收标准工具初始化"""
        from agents.requirements.tools.acceptance_criteria import AcceptanceCriteriaTool
        tool = AcceptanceCriteriaTool()
        assert tool.name == "acceptance_criteria_generator"


class TestPriorityCalculatorTool:
    """测试优先级计算工具"""
    
    @pytest.mark.asyncio
    async def test_calculator_initialization(self):
        """测试计算器初始化"""
        from agents.requirements.tools.priority_calculator import PriorityCalculatorTool
        tool = PriorityCalculatorTool()
        assert tool.name == "priority_calculator"


class TestCoordinatorTool:
    """测试协调器工具"""
    
    def setup_method(self):
        """测试前准备"""
        from agents.requirements.tools.coordinator import CoordinatorTool
        self.coordinator = CoordinatorTool()
    
    def test_coordinator_initialization(self):
        """测试协调器初始化"""
        assert self.coordinator.name == "coordinator"
        assert self.coordinator.agents == {}
        assert self.coordinator.tasks == {}
    
    def test_register_agent(self):
        """测试注册智能体"""
        mock_agent = MagicMock()
        self.coordinator.register_agent("technical", mock_agent)
        assert "technical" in self.coordinator.agents
    
    def test_check_progress_empty(self):
        """测试检查空进度"""
        result = self.coordinator._run("check_progress", {})
        assert result["total_tasks"] == 0
        assert result["progress_percentage"] == 0
    
    def test_handle_error_unknown_task(self):
        """测试处理未知任务错误"""
        result = self.coordinator._run("handle_error", {
            "task_id": "UNKNOWN",
            "error_message": "测试错误"
        })
        assert "error" in result


# 运行测试
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
