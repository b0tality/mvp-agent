"""
MVP实现智能体测试
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from agents.mvp import MVPDeveloperAgent, MVPStateManager


class TestMVPStateManager:
    """测试MVP状态管理器"""
    
    def setup_method(self):
        """测试前准备"""
        self.manager = MVPStateManager()
    
    def test_initial_state(self):
        """测试初始状态"""
        state = self.manager.get_all()
        assert state["status"] == "initialized"
        assert state["progress"] == 0.0
        assert state["code_files"] == []
        assert state["test_files"] == []
    
    def test_set_technical_solution(self):
        """测试设置技术方案"""
        solution = {"tech_stack": {}}
        self.manager.set_technical_solution(solution)
        assert self.manager.get("technical_solution") == solution
    
    def test_set_requirements(self):
        """测试设置需求"""
        requirements = {"functional_requirements": []}
        self.manager.set_requirements(requirements)
        assert self.manager.get("requirements") == requirements
    
    def test_set_project_info(self):
        """测试设置项目信息"""
        self.manager.set_project_info("test_project", "./projects/test")
        assert self.manager.get("project_name") == "test_project"
        assert self.manager.get("project_path") == "./projects/test"
    
    def test_add_code_file(self):
        """测试添加代码文件"""
        file = {"path": "src/main.py", "content": "print('hello')"}
        self.manager.add_code_file(file)
        assert len(self.manager.get("code_files")) == 1
    
    def test_update_code_file(self):
        """测试更新代码文件"""
        file = {"path": "src/main.py", "content": "print('hello')"}
        self.manager.add_code_file(file)
        self.manager.update_code_file("src/main.py", "print('world')")
        
        code_files = self.manager.get("code_files")
        assert code_files[0]["content"] == "print('world')"
    
    def test_add_test_file(self):
        """测试添加测试文件"""
        file = {"path": "tests/test_main.py", "content": "def test_main():"}
        self.manager.add_test_file(file)
        assert len(self.manager.get("test_files")) == 1
    
    def test_set_test_coverage(self):
        """测试设置测试覆盖率"""
        self.manager.set_test_coverage(85.5)
        assert self.manager.get("test_coverage") == 85.5
    
    def test_set_readme(self):
        """测试设置README"""
        self.manager.set_readme("# Test Project")
        assert self.manager.get("readme") == "# Test Project"
    
    def test_set_api_docs(self):
        """测试设置API文档"""
        self.manager.set_api_docs("# API Docs")
        assert self.manager.get("api_docs") == "# API Docs"
    
    def test_set_docker_config(self):
        """测试设置Docker配置"""
        config = {"dockerfile": "FROM python:3.11"}
        self.manager.set_docker_config(config)
        assert self.manager.get("docker_config") == config
    
    def test_set_progress(self):
        """测试设置进度"""
        self.manager.set_progress(75.0)
        assert self.manager.get("progress") == 75.0
    
    def test_progress_bounds(self):
        """测试进度边界"""
        self.manager.set_progress(150.0)
        assert self.manager.get("progress") == 100.0
        
        self.manager.set_progress(-10.0)
        assert self.manager.get("progress") == 0.0
    
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
    
    def test_add_warning(self):
        """测试添加警告"""
        self.manager.add_warning("测试警告")
        warnings = self.manager.get("warnings")
        assert len(warnings) == 1
        assert warnings[0]["message"] == "测试警告"
    
    def test_history(self):
        """测试历史记录"""
        self.manager.set_progress(50.0)
        self.manager.set_progress(75.0)
        history = self.manager.get_history()
        assert len(history) == 2
    
    def test_reset(self):
        """测试重置"""
        self.manager.set_progress(50.0)
        self.manager.set_status("in_progress")
        self.manager.reset()
        
        state = self.manager.get_all()
        assert state["status"] == "initialized"
        assert state["progress"] == 0.0


class TestMVPDeveloperAgent:
    """测试MVP实现智能体"""
    
    def setup_method(self):
        """测试前准备"""
        self.config = {
            "model": "gpt-4",
            "temperature": 0.4
        }
    
    @pytest.mark.asyncio
    async def test_agent_initialization(self):
        """测试智能体初始化"""
        agent = MVPDeveloperAgent(self.config)
        assert agent.config == self.config
        assert agent.llm is not None
        assert len(agent.tools) == 6
    
    @pytest.mark.asyncio
    async def test_get_state(self):
        """测试获取状态"""
        agent = MVPDeveloperAgent(self.config)
        state = agent.get_state()
        assert state["status"] == "initialized"
    
    @pytest.mark.asyncio
    async def test_get_conversation_history(self):
        """测试获取对话历史"""
        agent = MVPDeveloperAgent(self.config)
        history = agent.get_conversation_history()
        assert history == []
    
    @pytest.mark.asyncio
    async def test_get_code_files(self):
        """测试获取代码文件"""
        agent = MVPDeveloperAgent(self.config)
        files = agent.get_code_files()
        assert files == []
    
    @pytest.mark.asyncio
    async def test_get_test_files(self):
        """测试获取测试文件"""
        agent = MVPDeveloperAgent(self.config)
        files = agent.get_test_files()
        assert files == []
    
    @pytest.mark.asyncio
    async def test_get_progress(self):
        """测试获取进度"""
        agent = MVPDeveloperAgent(self.config)
        progress = agent.get_progress()
        assert progress == 0.0
    
    @pytest.mark.asyncio
    async def test_reset(self):
        """测试重置"""
        agent = MVPDeveloperAgent(self.config)
        agent.state_manager.set_progress(50.0)
        agent.conversation_history.append({"role": "user", "content": "test"})
        agent.reset()
        
        assert agent.conversation_history == []
        assert agent.get_progress() == 0.0


class TestProjectGeneratorTool:
    """测试项目结构生成工具"""
    
    @pytest.mark.asyncio
    async def test_tool_initialization(self):
        """测试工具初始化"""
        from agents.mvp.tools.project_generator import ProjectGeneratorTool
        tool = ProjectGeneratorTool()
        assert tool.name == "project_generator"


class TestCodeGeneratorTool:
    """测试代码生成工具"""
    
    @pytest.mark.asyncio
    async def test_tool_initialization(self):
        """测试工具初始化"""
        from agents.mvp.tools.code_generator import CodeGeneratorTool
        tool = CodeGeneratorTool()
        assert tool.name == "code_generator"


class TestTestGeneratorTool:
    """测试测试生成工具"""
    
    @pytest.mark.asyncio
    async def test_tool_initialization(self):
        """测试工具初始化"""
        from agents.mvp.tools.test_generator import TestGeneratorTool
        tool = TestGeneratorTool()
        assert tool.name == "test_generator"


class TestDocGeneratorTool:
    """测试文档生成工具"""
    
    @pytest.mark.asyncio
    async def test_tool_initialization(self):
        """测试工具初始化"""
        from agents.mvp.tools.doc_generator import DocGeneratorTool
        tool = DocGeneratorTool()
        assert tool.name == "doc_generator"


class TestDockerGeneratorTool:
    """测试Docker配置生成工具"""
    
    @pytest.mark.asyncio
    async def test_tool_initialization(self):
        """测试工具初始化"""
        from agents.mvp.tools.docker_generator import DockerGeneratorTool
        tool = DockerGeneratorTool()
        assert tool.name == "docker_generator"


class TestCodeOptimizerTool:
    """测试代码优化工具"""
    
    @pytest.mark.asyncio
    async def test_tool_initialization(self):
        """测试工具初始化"""
        from agents.mvp.tools.code_optimizer import CodeOptimizerTool
        tool = CodeOptimizerTool()
        assert tool.name == "code_optimizer"


# 运行测试
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
