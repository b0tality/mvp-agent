"""
代码审查智能体测试
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from agents.code_review import CodeReviewAgent, CodeReviewStateManager


class TestCodeReviewStateManager:
    """测试代码审查状态管理器"""
    
    def setup_method(self):
        """测试前准备"""
        self.manager = CodeReviewStateManager()
    
    def test_initial_state(self):
        """测试初始状态"""
        state = self.manager.get_all()
        assert state["status"] == "initialized"
        assert state["total_issues"] == 0
        assert state["critical_issues"] == 0
        assert state["overall_score"] == 0.0
        assert state["approved"] == False
    
    def test_set_code_files(self):
        """测试设置代码文件"""
        files = [{"path": "test.py", "content": "print('hello')"}]
        self.manager.set_code_files(files)
        assert self.manager.get("code_files") == files
    
    def test_add_file_review(self):
        """测试添加文件审查结果"""
        review = {"file_path": "test.py", "score": 85}
        self.manager.add_file_review(review)
        assert len(self.manager.get("file_reviews")) == 1
    
    def test_add_issue_critical(self):
        """测试添加严重问题"""
        issue = {"severity": "critical", "issue_type": "security"}
        self.manager.add_issue(issue)
        assert self.manager.get("total_issues") == 1
        assert self.manager.get("critical_issues") == 1
    
    def test_add_issue_high(self):
        """测试添加高优先级问题"""
        issue = {"severity": "high", "issue_type": "quality"}
        self.manager.add_issue(issue)
        assert self.manager.get("total_issues") == 1
        assert self.manager.get("high_issues") == 1
    
    def test_add_issue_medium(self):
        """测试添加中等优先级问题"""
        issue = {"severity": "medium", "issue_type": "style"}
        self.manager.add_issue(issue)
        assert self.manager.get("total_issues") == 1
        assert self.manager.get("medium_issues") == 1
    
    def test_add_issue_low(self):
        """测试添加低优先级问题"""
        issue = {"severity": "low", "issue_type": "performance"}
        self.manager.add_issue(issue)
        assert self.manager.get("total_issues") == 1
        assert self.manager.get("low_issues") == 1
    
    def test_add_issue_by_type(self):
        """测试按类型添加问题"""
        self.manager.add_issue({"issue_type": "style", "severity": "low"})
        self.manager.add_issue({"issue_type": "quality", "severity": "medium"})
        self.manager.add_issue({"issue_type": "security", "severity": "high"})
        self.manager.add_issue({"issue_type": "performance", "severity": "low"})
        self.manager.add_issue({"issue_type": "complexity", "severity": "medium"})
        
        assert len(self.manager.get("style_issues")) == 1
        assert len(self.manager.get("quality_issues")) == 1
        assert len(self.manager.get("security_issues")) == 1
        assert len(self.manager.get("performance_issues")) == 1
        assert len(self.manager.get("complexity_issues")) == 1
    
    def test_add_refactoring_suggestion(self):
        """测试添加重构建议"""
        suggestion = {"id": "REF-001", "title": "提取方法"}
        self.manager.add_refactoring_suggestion(suggestion)
        assert len(self.manager.get("refactoring_suggestions")) == 1
    
    def test_add_best_practice(self):
        """测试添加最佳实践"""
        practice = {"category": "设计模式", "practice": "使用策略模式"}
        self.manager.add_best_practice(practice)
        assert len(self.manager.get("best_practices")) == 1
    
    def test_set_overall_score(self):
        """测试设置总体评分"""
        self.manager.set_overall_score(85.5)
        assert self.manager.get("overall_score") == 85.5
    
    def test_set_score_bounds(self):
        """测试评分边界"""
        self.manager.set_overall_score(150.0)
        assert self.manager.get("overall_score") == 100.0
        
        self.manager.set_overall_score(-10.0)
        assert self.manager.get("overall_score") == 0.0
    
    def test_set_approved(self):
        """测试设置审查结果"""
        self.manager.set_approved(True)
        assert self.manager.get("approved") == True
        assert self.manager.get("review_status") == "approved"
        
        self.manager.set_approved(False)
        assert self.manager.get("approved") == False
        assert self.manager.get("review_status") == "rejected"
    
    def test_set_review_notes(self):
        """测试设置审查备注"""
        self.manager.set_review_notes("代码质量良好")
        assert self.manager.get("review_notes") == "代码质量良好"
    
    def test_reset(self):
        """测试重置"""
        self.manager.set_overall_score(85.0)
        self.manager.set_approved(True)
        self.manager.add_issue({"severity": "high"})
        self.manager.reset()
        
        state = self.manager.get_all()
        assert state["status"] == "initialized"
        assert state["overall_score"] == 0.0
        assert state["approved"] == False
        assert state["total_issues"] == 0


class TestCodeReviewAgent:
    """测试代码审查智能体"""
    
    def setup_method(self):
        """测试前准备"""
        self.config = {
            "model": "gpt-4",
            "temperature": 0.1
        }
    
    @pytest.mark.asyncio
    async def test_agent_initialization(self):
        """测试智能体初始化"""
        agent = CodeReviewAgent(self.config)
        assert agent.config == self.config
        assert agent.llm is not None
        assert len(agent.tools) == 6
    
    @pytest.mark.asyncio
    async def test_get_state(self):
        """测试获取状态"""
        agent = CodeReviewAgent(self.config)
        state = agent.get_state()
        assert state["status"] == "initialized"
    
    @pytest.mark.asyncio
    async def test_get_conversation_history(self):
        """测试获取对话历史"""
        agent = CodeReviewAgent(self.config)
        history = agent.get_conversation_history()
        assert history == []
    
    @pytest.mark.asyncio
    async def test_get_issues(self):
        """测试获取问题列表"""
        agent = CodeReviewAgent(self.config)
        issues = agent.get_issues()
        assert issues["style"] == []
        assert issues["quality"] == []
        assert issues["security"] == []
        assert issues["performance"] == []
        assert issues["complexity"] == []
    
    @pytest.mark.asyncio
    async def test_get_refactoring_suggestions(self):
        """测试获取重构建议"""
        agent = CodeReviewAgent(self.config)
        suggestions = agent.get_refactoring_suggestions()
        assert suggestions == []
    
    @pytest.mark.asyncio
    async def test_reset(self):
        """测试重置"""
        agent = CodeReviewAgent(self.config)
        agent.state_manager.set_overall_score(85.0)
        agent.conversation_history.append({"role": "user", "content": "test"})
        agent.reset()
        
        assert agent.conversation_history == []
        assert agent.get_state()["overall_score"] == 0.0


class TestStyleCheckerTool:
    """测试代码风格检查工具"""
    
    @pytest.mark.asyncio
    async def test_tool_initialization(self):
        """测试工具初始化"""
        from agents.code_review.tools.style_checker import StyleCheckerTool
        tool = StyleCheckerTool()
        assert tool.name == "style_checker"


class TestQualityAssessorTool:
    """测试代码质量评估工具"""
    
    @pytest.mark.asyncio
    async def test_tool_initialization(self):
        """测试工具初始化"""
        from agents.code_review.tools.quality_assessor import QualityAssessorTool
        tool = QualityAssessorTool()
        assert tool.name == "quality_assessor"


class TestSecurityScannerTool:
    """测试安全扫描工具"""
    
    @pytest.mark.asyncio
    async def test_tool_initialization(self):
        """测试工具初始化"""
        from agents.code_review.tools.security_scanner import SecurityScannerTool
        tool = SecurityScannerTool()
        assert tool.name == "security_scanner"


class TestPerformanceAnalyzerTool:
    """测试性能分析工具"""
    
    @pytest.mark.asyncio
    async def test_tool_initialization(self):
        """测试工具初始化"""
        from agents.code_review.tools.performance_analyzer import PerformanceAnalyzerTool
        tool = PerformanceAnalyzerTool()
        assert tool.name == "performance_analyzer"


class TestComplexityAnalyzerTool:
    """测试复杂度分析工具"""
    
    @pytest.mark.asyncio
    async def test_tool_initialization(self):
        """测试工具初始化"""
        from agents.code_review.tools.complexity_analyzer import ComplexityAnalyzerTool
        tool = ComplexityAnalyzerTool()
        assert tool.name == "complexity_analyzer"


class TestRefactoringAdvisorTool:
    """测试重构建议工具"""
    
    @pytest.mark.asyncio
    async def test_tool_initialization(self):
        """测试工具初始化"""
        from agents.code_review.tools.refactoring_advisor import RefactoringAdvisorTool
        tool = RefactoringAdvisorTool()
        assert tool.name == "refactoring_advisor"


# 运行测试
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
