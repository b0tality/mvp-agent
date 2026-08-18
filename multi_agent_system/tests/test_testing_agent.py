"""
软件测试智能体测试
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from agents.testing import TestingAgent, TestingStateManager


class TestTestingStateManager:
    """测试软件测试状态管理器"""
    
    def setup_method(self):
        """测试前准备"""
        self.manager = TestingStateManager()
    
    def test_initial_state(self):
        """测试初始状态"""
        state = self.manager.get_all()
        assert state["status"] == "initialized"
        assert state["total_tests"] == 0
        assert state["passed_tests"] == 0
        assert state["failed_tests"] == 0
        assert state["progress"] == 0.0
    
    def test_set_code_files(self):
        """测试设置代码文件"""
        files = [{"path": "test.py", "content": "print('hello')"}]
        self.manager.set_code_files(files)
        assert self.manager.get("code_files") == files
    
    def test_update_test_counts(self):
        """测试更新测试计数"""
        self.manager.update_test_counts(passed=10, failed=2, skipped=1)
        assert self.manager.get("passed_tests") == 10
        assert self.manager.get("failed_tests") == 2
        assert self.manager.get("skipped_tests") == 1
        assert self.manager.get("total_tests") == 13
    
    def test_set_coverage(self):
        """测试设置覆盖率"""
        self.manager.set_coverage(85.0, 75.0, 90.0)
        assert self.manager.get("line_coverage") == 85.0
        assert self.manager.get("branch_coverage") == 75.0
        assert self.manager.get("function_coverage") == 90.0
        assert self.manager.get("overall_coverage") == 83.33333333333333
    
    def test_add_bug(self):
        """测试添加缺陷"""
        bug = {
            "id": "BUG-001",
            "title": "测试缺陷",
            "severity": "critical"
        }
        self.manager.add_bug(bug)
        assert len(self.manager.get("bugs")) == 1
        assert self.manager.get("critical_bugs") == 1
    
    def test_add_bug_severity(self):
        """测试添加不同严重程度的缺陷"""
        self.manager.add_bug({"severity": "critical"})
        self.manager.add_bug({"severity": "high"})
        self.manager.add_bug({"severity": "medium"})
        self.manager.add_bug({"severity": "low"})
        
        assert self.manager.get("critical_bugs") == 1
        assert self.manager.get("high_bugs") == 1
        assert self.manager.get("medium_bugs") == 1
        assert self.manager.get("low_bugs") == 1
    
    def test_set_performance_summary(self):
        """测试设置性能摘要"""
        self.manager.set_performance_summary(100.0, 200.0, 300.0, 1000.0, 0.01)
        assert self.manager.get("avg_response_time") == 100.0
        assert self.manager.get("p95_response_time") == 200.0
        assert self.manager.get("p99_response_time") == 300.0
        assert self.manager.get("throughput") == 1000.0
        assert self.manager.get("error_rate") == 0.01
    
    def test_set_security_score(self):
        """测试设置安全评分"""
        self.manager.set_security_score(85.0)
        assert self.manager.get("security_score") == 85.0
    
    def test_set_security_score_bounds(self):
        """测试安全评分边界"""
        self.manager.set_security_score(150.0)
        assert self.manager.get("security_score") == 100.0
        
        self.manager.set_security_score(-10.0)
        assert self.manager.get("security_score") == 0.0
    
    def test_set_progress(self):
        """测试设置进度"""
        self.manager.set_progress(75.0)
        assert self.manager.get("progress") == 75.0
    
    def test_set_progress_bounds(self):
        """测试进度边界"""
        self.manager.set_progress(150.0)
        assert self.manager.get("progress") == 100.0
        
        self.manager.set_progress(-10.0)
        assert self.manager.get("progress") == 0.0
    
    def test_reset(self):
        """测试重置"""
        self.manager.set_progress(50.0)
        self.manager.set_status("in_progress")
        self.manager.update_test_counts(passed=10, failed=2)
        self.manager.reset()
        
        state = self.manager.get_all()
        assert state["status"] == "initialized"
        assert state["progress"] == 0.0
        assert state["total_tests"] == 0


class TestTestingAgent:
    """测试软件测试智能体"""
    
    def setup_method(self):
        """测试前准备"""
        self.config = {
            "model": "gpt-4",
            "temperature": 0.2
        }
    
    @pytest.mark.asyncio
    async def test_agent_initialization(self):
        """测试智能体初始化"""
        agent = TestingAgent(self.config)
        assert agent.config == self.config
        assert agent.llm is not None
        assert len(agent.tools) == 6
    
    @pytest.mark.asyncio
    async def test_get_state(self):
        """测试获取状态"""
        agent = TestingAgent(self.config)
        state = agent.get_state()
        assert state["status"] == "initialized"
    
    @pytest.mark.asyncio
    async def test_get_conversation_history(self):
        """测试获取对话历史"""
        agent = TestingAgent(self.config)
        history = agent.get_conversation_history()
        assert history == []
    
    @pytest.mark.asyncio
    async def test_get_bugs(self):
        """测试获取缺陷列表"""
        agent = TestingAgent(self.config)
        bugs = agent.get_bugs()
        assert bugs == []
    
    @pytest.mark.asyncio
    async def test_get_test_report(self):
        """测试获取测试报告"""
        agent = TestingAgent(self.config)
        report = agent.get_test_report()
        assert report == {}
    
    @pytest.mark.asyncio
    async def test_reset(self):
        """测试重置"""
        agent = TestingAgent(self.config)
        agent.state_manager.set_progress(50.0)
        agent.conversation_history.append({"role": "user", "content": "test"})
        agent.reset()
        
        assert agent.conversation_history == []
        assert agent.get_state()["progress"] == 0.0


class TestUnitTestGeneratorTool:
    """测试单元测试生成工具"""
    
    @pytest.mark.asyncio
    async def test_tool_initialization(self):
        """测试工具初始化"""
        from agents.testing.tools.unit_test_generator import UnitTestGeneratorTool
        tool = UnitTestGeneratorTool()
        assert tool.name == "unit_test_generator"


class TestIntegrationTestGeneratorTool:
    """测试集成测试生成工具"""
    
    @pytest.mark.asyncio
    async def test_tool_initialization(self):
        """测试工具初始化"""
        from agents.testing.tools.integration_test_generator import IntegrationTestGeneratorTool
        tool = IntegrationTestGeneratorTool()
        assert tool.name == "integration_test_generator"


class TestPerformanceTestGeneratorTool:
    """测试性能测试生成工具"""
    
    @pytest.mark.asyncio
    async def test_tool_initialization(self):
        """测试工具初始化"""
        from agents.testing.tools.performance_test_generator import PerformanceTestGeneratorTool
        tool = PerformanceTestGeneratorTool()
        assert tool.name == "performance_test_generator"


class TestSecurityTestGeneratorTool:
    """测试安全测试生成工具"""
    
    @pytest.mark.asyncio
    async def test_tool_initialization(self):
        """测试工具初始化"""
        from agents.testing.tools.security_test_generator import SecurityTestGeneratorTool
        tool = SecurityTestGeneratorTool()
        assert tool.name == "security_test_generator"


class TestTestDataGeneratorTool:
    """测试测试数据生成工具"""
    
    @pytest.mark.asyncio
    async def test_tool_initialization(self):
        """测试工具初始化"""
        from agents.testing.tools.test_data_generator import TestDataGeneratorTool
        tool = TestDataGeneratorTool()
        assert tool.name == "test_data_generator"


class TestTestReportGeneratorTool:
    """测试测试报告生成工具"""
    
    @pytest.mark.asyncio
    async def test_tool_initialization(self):
        """测试工具初始化"""
        from agents.testing.tools.test_report_generator import TestReportGeneratorTool
        tool = TestReportGeneratorTool()
        assert tool.name == "test_report_generator"


# 运行测试
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
