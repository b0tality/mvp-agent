"""
MVP实现智能体主类
负责最小可行产品开发
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from .state import MVPState, MVPStateManager
from .prompts import (
    MVP_SYSTEM_PROMPT,
    PROJECT_STRUCTURE_PROMPT,
    CODE_GENERATION_PROMPT,
    DATA_MODEL_PROMPT,
    API_ENDPOINT_PROMPT,
    AUTH_GENERATION_PROMPT,
    TEST_GENERATION_PROMPT,
    DOCUMENTATION_PROMPT,
    DOCKER_CONFIG_PROMPT,
    CODE_OPTIMIZATION_PROMPT
)
from .tools import (
    ProjectGeneratorTool,
    CodeGeneratorTool,
    TestGeneratorTool,
    DocGeneratorTool,
    DockerGeneratorTool,
    CodeOptimizerTool
)


class MVPDeveloperAgent:
    """
    MVP实现智能体
    
    职责：
    1. 生成项目结构
    2. 生成代码文件
    3. 生成测试用例
    4. 生成项目文档
    5. 生成Docker配置
    6. 优化代码质量
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化MVP实现智能体
        
        Args:
            config: 配置参数
                - model: 模型名称，默认 mimo
                - temperature: 温度参数，默认 0.4
                - max_tokens: 最大token数，默认 8000
                - api_key: API密钥
                - base_url: API基础URL（用于本地LLM）
        """
        self.config = config or {}
        
        # 初始化LLM（支持本地LLM）
        llm_kwargs = {
            "model": self.config.get("model", "mimo"),
            "temperature": self.config.get("temperature", 0.4),
            "max_tokens": self.config.get("max_tokens", 8000),
        }
        
        # 如果配置了api_key和base_url，使用本地LLM
        if "api_key" in self.config:
            llm_kwargs["api_key"] = self.config["api_key"]
        if "base_url" in self.config:
            llm_kwargs["base_url"] = self.config["base_url"]
        
        self.llm = ChatOpenAI(**llm_kwargs)
        
        # 初始化工具
        self.tools = self._init_tools()
        
        # 初始化状态管理器
        self.state_manager = MVPStateManager()
        
        # 创建智能体
        self.agent = self._create_agent()
        
        # 对话历史
        self.conversation_history: List[Dict[str, str]] = []
    
    def _init_tools(self) -> List[Any]:
        """初始化工具集"""
        return [
            ProjectGeneratorTool(llm=self.llm),
            CodeGeneratorTool(llm=self.llm),
            TestGeneratorTool(llm=self.llm),
            DocGeneratorTool(llm=self.llm),
            DockerGeneratorTool(llm=self.llm),
            CodeOptimizerTool(llm=self.llm)
        ]
    
    def _create_agent(self):
        """创建智能体"""
        # 使用新的 create_agent API
        agent = create_agent(
            model=self.llm,
            tools=self.tools,
            system_prompt=MVP_SYSTEM_PROMPT
        )
        return agent
    
    async def develop_mvp(
        self,
        technical_solution: Dict[str, Any],
        requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        开发MVP
        
        Args:
            technical_solution: 技术方案
            requirements: 需求分析
            
        Returns:
            MVP开发结果
        """
        # 更新状态
        self.state_manager.set_technical_solution(technical_solution)
        self.state_manager.set_requirements(requirements)
        self.state_manager.set_status("in_progress")
        
        # 添加到对话历史
        self.conversation_history.append({
            "role": "user",
            "content": f"开发MVP: {json.dumps(requirements, ensure_ascii=False)}",
            "timestamp": datetime.now().isoformat()
        })
        
        try:
            # 步骤1: 生成项目结构
            self.state_manager.set_current_module("project_structure")
            self.state_manager.set_progress(10.0)
            project_structure = await self._generate_project_structure(technical_solution, requirements)
            self.state_manager.set_project_structure(project_structure)
            self.state_manager.set_project_info(
                project_structure.get("project_name", "mvp_project"),
                f"./projects/{project_structure.get('project_name', 'mvp_project')}"
            )
            
            # 步骤2: 生成数据模型
            self.state_manager.set_current_module("data_models")
            self.state_manager.set_progress(25.0)
            data_models = await self._generate_data_models(technical_solution)
            for model in data_models.get("models", []):
                self.state_manager.add_code_file(model)
            
            # 步骤3: 生成API端点
            self.state_manager.set_current_module("api_endpoints")
            self.state_manager.set_progress(40.0)
            api_endpoints = await self._generate_api_endpoints(
                technical_solution, data_models
            )
            for endpoint in api_endpoints.get("endpoints", []):
                self.state_manager.add_code_file(endpoint)
            
            # 步骤4: 生成认证授权
            self.state_manager.set_current_module("authentication")
            self.state_manager.set_progress(55.0)
            auth_code = await self._generate_auth(technical_solution)
            for key, value in auth_code.items():
                if isinstance(value, dict) and "file_path" in value:
                    self.state_manager.add_code_file(value)
            
            # 步骤5: 生成测试用例
            self.state_manager.set_current_module("tests")
            self.state_manager.set_progress(70.0)
            test_files = await self._generate_tests(
                self.state_manager.get("code_files"),
                "mvp"
            )
            for test in test_files.get("test_files", []):
                self.state_manager.add_test_file(test)
            
            # 步骤6: 生成文档
            self.state_manager.set_current_module("documentation")
            self.state_manager.set_progress(80.0)
            docs = await self._generate_docs(
                technical_solution,
                self.state_manager.get("code_files"),
                technical_solution.get("api_design", {})
            )
            self.state_manager.set_readme(docs.get("readme", {}).get("content", ""))
            self.state_manager.set_api_docs(docs.get("api_docs", {}).get("content", ""))
            
            # 步骤7: 生成Docker配置
            self.state_manager.set_current_module("docker")
            self.state_manager.set_progress(90.0)
            docker_config = await self._generate_docker_config(
                technical_solution,
                technical_solution.get("tech_stack", {})
            )
            self.state_manager.set_docker_config(docker_config)
            
            # 完成
            self.state_manager.set_progress(100.0)
            self.state_manager.set_status("completed")
            self.state_manager.add_module("all")
            
            # 返回完整结果
            return {
                "status": "success",
                "project_name": self.state_manager.get("project_name"),
                "project_path": self.state_manager.get("project_path"),
                "code_files": self.state_manager.get("code_files"),
                "test_files": self.state_manager.get("test_files"),
                "dependencies": self.state_manager.get("dependencies"),
                "documentation": {
                    "readme": self.state_manager.get("readme"),
                    "api_docs": self.state_manager.get("api_docs")
                },
                "docker_config": self.state_manager.get("docker_config"),
                "progress": 100.0,
                "state": self.state_manager.get_all()
            }
            
        except Exception as e:
            self.state_manager.add_error(str(e))
            self.state_manager.set_status("error")
            return {
                "status": "error",
                "error": str(e),
                "progress": self.state_manager.get("progress"),
                "state": self.state_manager.get_all()
            }
    
    async def _generate_project_structure(
        self,
        technical_solution: Dict[str, Any],
        requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成项目结构"""
        tool = ProjectGeneratorTool(llm=self.llm)
        return await tool._arun(technical_solution, requirements)
    
    async def _generate_data_models(
        self,
        technical_solution: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成数据模型"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", "你是一位资深的全栈开发工程师。请生成数据模型代码。"),
            ("human", f"""请根据以下技术方案生成数据模型：

数据库设计：
{json.dumps(technical_solution.get('database_design', {}), ensure_ascii=False, indent=2)}

技术栈：
{json.dumps(technical_solution.get('tech_stack', {}), ensure_ascii=False, indent=2)}

请以JSON格式输出数据模型。""")
        ])
        
        chain = prompt | self.llm
        result = chain.invoke({})
        
        try:
            parsed = json.loads(result.content)
        except json.JSONDecodeError:
            json_match = re.search(r'\{[\s\S]*\}', result.content)
            if json_match:
                parsed = json.loads(json_match.group())
            else:
                parsed = {"models": []}
        
        return parsed
    
    async def _generate_api_endpoints(
        self,
        technical_solution: Dict[str, Any],
        data_models: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成API端点"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", "你是一位资深的全栈开发工程师。请生成API端点代码。"),
            ("human", f"""请根据以下信息生成API端点：

API设计：
{json.dumps(technical_solution.get('api_design', {}), ensure_ascii=False, indent=2)}

数据模型：
{json.dumps(data_models, ensure_ascii=False, indent=2)}

技术栈：
{json.dumps(technical_solution.get('tech_stack', {}), ensure_ascii=False, indent=2)}

请以JSON格式输出API端点。""")
        ])
        
        chain = prompt | self.llm
        result = chain.invoke({})
        
        try:
            parsed = json.loads(result.content)
        except json.JSONDecodeError:
            json_match = re.search(r'\{[\s\S]*\}', result.content)
            if json_match:
                parsed = json.loads(json_match.group())
            else:
                parsed = {"endpoints": []}
        
        return parsed
    
    async def _generate_auth(
        self,
        technical_solution: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成认证授权代码"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", "你是一位资深的全栈开发工程师。请生成认证授权代码。"),
            ("human", f"""请根据以下安全设计生成认证授权代码：

安全设计：
{json.dumps(technical_solution.get('security_design', {}), ensure_ascii=False, indent=2)}

技术栈：
{json.dumps(technical_solution.get('tech_stack', {}), ensure_ascii=False, indent=2)}

请以JSON格式输出认证授权代码。""")
        ])
        
        chain = prompt | self.llm
        result = chain.invoke({})
        
        try:
            parsed = json.loads(result.content)
        except json.JSONDecodeError:
            json_match = re.search(r'\{[\s\S]*\}', result.content)
            if json_match:
                parsed = json.loads(json_match.group())
            else:
                parsed = {}
        
        return parsed
    
    async def _generate_tests(
        self,
        code_files: List[Dict[str, Any]],
        module_name: str
    ) -> Dict[str, Any]:
        """生成测试用例"""
        tool = TestGeneratorTool(llm=self.llm)
        return await tool._arun(code_files, module_name)
    
    async def _generate_docs(
        self,
        project_info: Dict[str, Any],
        code_files: List[Dict[str, Any]],
        api_design: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成文档"""
        tool = DocGeneratorTool(llm=self.llm)
        return await tool._arun(project_info, code_files, api_design)
    
    async def _generate_docker_config(
        self,
        project_info: Dict[str, Any],
        tech_stack: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成Docker配置"""
        tool = DockerGeneratorTool(llm=self.llm)
        return await tool._arun(project_info, tech_stack)
    
    async def optimize_code(
        self,
        optimization_goals: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        优化代码
        
        Args:
            optimization_goals: 优化目标
            
        Returns:
            优化结果
        """
        if optimization_goals is None:
            optimization_goals = ["performance", "readability", "security"]
        
        code_files = self.state_manager.get("code_files")
        if not code_files:
            return {"status": "error", "error": "没有代码文件可优化"}
        
        tool = CodeOptimizerTool(llm=self.llm)
        result = await tool._arun(code_files, optimization_goals)
        
        # 更新代码文件
        for optimized in result.get("optimized_files", []):
            self.state_manager.update_code_file(
                optimized["path"],
                optimized["optimized_content"]
            )
        
        return result
    
    def get_state(self) -> MVPState:
        """获取当前状态"""
        return self.state_manager.get_all()
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """获取对话历史"""
        return self.conversation_history
    
    def get_code_files(self) -> List[Dict[str, Any]]:
        """获取代码文件列表"""
        return self.state_manager.get("code_files")
    
    def get_test_files(self) -> List[Dict[str, Any]]:
        """获取测试文件列表"""
        return self.state_manager.get("test_files")
    
    def get_progress(self) -> float:
        """获取进度"""
        return self.state_manager.get("progress")
    
    def reset(self) -> None:
        """重置智能体状态"""
        self.state_manager.reset()
        self.conversation_history = []


class MVPDeveloperAgentFactory:
    """MVP实现智能体工厂"""
    
    @staticmethod
    def create(config: Optional[Dict[str, Any]] = None) -> MVPDeveloperAgent:
        """创建智能体实例"""
        return MVPDeveloperAgent(config)


# 导入json模块
import json
