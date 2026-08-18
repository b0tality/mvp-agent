"""
需求分析智能体主类
兼任主管节点角色
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from .state import RequirementsState, RequirementsStateManager
from .prompts import (
    REQUIREMENTS_SYSTEM_PROMPT,
    REQUIREMENT_PARSING_PROMPT,
    USER_STORY_PROMPT,
    ACCEPTANCE_CRITERIA_PROMPT,
    PRIORITIZATION_PROMPT,
    TASK_DECOMPOSITION_PROMPT,
    CLARIFICATION_PROMPT
)
from .tools import (
    RequirementParserTool,
    UserStoryGeneratorTool,
    AcceptanceCriteriaTool,
    PriorityCalculatorTool,
    CoordinatorTool
)


class RequirementsAgent:
    """
    需求分析智能体（兼任主管节点）
    
    职责：
    1. 解析用户需求，生成结构化文档
    2. 协调其他智能体，监控项目进度
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化需求分析智能体
        
        Args:
            config: 配置参数
                - model: 模型名称，默认 mimo
                - temperature: 温度参数，默认 0.3
                - max_tokens: 最大token数，默认 4000
                - api_key: API密钥
                - base_url: API基础URL（用于本地LLM）
        """
        self.config = config or {}
        
        # 初始化LLM（支持本地LLM）
        llm_kwargs = {
            "model": self.config.get("model", "mimo"),
            "temperature": self.config.get("temperature", 0.3),
            "max_tokens": self.config.get("max_tokens", 4000),
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
        self.state_manager = RequirementsStateManager()
        
        # 初始化协调器
        self.coordinator = CoordinatorTool(llm=self.llm)
        
        # 创建智能体
        self.agent = self._create_agent()
        
        # 对话历史
        self.conversation_history: List[Dict[str, str]] = []
    
    def _init_tools(self) -> List[Any]:
        """初始化工具集"""
        return [
            RequirementParserTool(llm=self.llm),
            UserStoryGeneratorTool(llm=self.llm),
            AcceptanceCriteriaTool(llm=self.llm),
            PriorityCalculatorTool(llm=self.llm),
            CoordinatorTool(llm=self.llm)
        ]
    
    def _create_agent(self):
        """创建智能体"""
        # 使用新的 create_agent API
        agent = create_agent(
            model=self.llm,
            tools=self.tools,
            system_prompt=REQUIREMENTS_SYSTEM_PROMPT
        )
        return agent
    
    async def analyze_requirements(self, user_input: str) -> Dict[str, Any]:
        """
        分析用户需求
        
        Args:
            user_input: 用户输入的需求描述
            
        Returns:
            分析结果，包含功能需求、非功能需求等
        """
        # 更新状态
        self.state_manager.set_phase("analyzing")
        self.state_manager.set_status("in_progress")
        self.state_manager.update("user_input", user_input)
        
        # 添加到对话历史
        self.conversation_history.append({
            "role": "user",
            "content": user_input,
            "timestamp": datetime.now().isoformat()
        })
        
        try:
            # 直接使用工具调用，而不是agent
            parsed_requirements = await self._parse_requirements(user_input)
            
            # 生成用户故事
            user_stories = await self._generate_user_stories(parsed_requirements)
            
            # 生成验收标准
            acceptance_criteria = await self._generate_acceptance_criteria(user_stories)
            
            # 优先级排序
            priority_matrix = await self._prioritize_requirements(parsed_requirements)
            
            # 更新状态
            self.state_manager.update("functional_requirements", 
                                     parsed_requirements.get("functional_requirements", []))
            self.state_manager.update("non_functional_requirements", 
                                     parsed_requirements.get("non_functional_requirements", []))
            self.state_manager.update("user_stories", 
                                     user_stories.get("user_stories", []))
            self.state_manager.update("acceptance_criteria", 
                                     acceptance_criteria.get("acceptance_criteria", []))
            self.state_manager.update("priority_matrix", 
                                     priority_matrix.get("priority_matrix", {}))
            
            self.state_manager.set_phase("completed")
            self.state_manager.set_status("completed")
            
            # 返回完整结果
            return {
                "status": "success",
                "requirements": parsed_requirements,
                "user_stories": user_stories,
                "acceptance_criteria": acceptance_criteria,
                "priority_matrix": priority_matrix,
                "state": self.state_manager.get_all()
            }
            
        except Exception as e:
            self.state_manager.add_error(str(e))
            self.state_manager.set_status("error")
            return {
                "status": "error",
                "error": str(e),
                "state": self.state_manager.get_all()
            }
    
    async def _parse_requirements(self, user_input: str) -> Dict[str, Any]:
        """解析需求"""
        tool = RequirementParserTool(llm=self.llm)
        return await tool._arun(user_input)
    
    async def _generate_user_stories(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """生成用户故事"""
        tool = UserStoryGeneratorTool(llm=self.llm)
        return await tool._arun(requirements)
    
    async def _generate_acceptance_criteria(self, user_stories: Dict[str, Any]) -> Dict[str, Any]:
        """生成验收标准"""
        tool = AcceptanceCriteriaTool(llm=self.llm)
        all_criteria = []
        
        for story in user_stories.get("user_stories", []):
            criteria = await tool._arun(story)
            all_criteria.extend(criteria.get("acceptance_criteria", []))
        
        return {"acceptance_criteria": all_criteria}
    
    async def _prioritize_requirements(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """优先级排序"""
        tool = PriorityCalculatorTool(llm=self.llm)
        return await tool._arun(requirements)
    
    async def decompose_tasks(self) -> Dict[str, Any]:
        """
        分解任务
        
        Returns:
            任务分解结果
        """
        self.state_manager.set_phase("decomposing_tasks")
        
        requirements = {
            "functional_requirements": self.state_manager.get("functional_requirements"),
            "non_functional_requirements": self.state_manager.get("non_functional_requirements"),
            "user_stories": self.state_manager.get("user_stories"),
            "priority_matrix": self.state_manager.get("priority_matrix")
        }
        
        result = self.coordinator._run("decompose_tasks", {"requirements": requirements})
        
        self.state_manager.update("tasks", result.get("tasks", []))
        
        return result
    
    async def coordinate_agents(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        协调其他智能体
        
        Args:
            tasks: 任务列表
            
        Returns:
            协调结果
        """
        self.state_manager.set_phase("coordinating")
        
        assignments = {}
        
        for task in tasks:
            task_id = task.get("id")
            assigned_to = task.get("assigned_to")
            
            # 分配任务
            result = self.coordinator._run("assign_task", {
                "task_id": task_id,
                "agent_name": assigned_to
            })
            
            assignments[task_id] = result
            
            # 更新状态
            self.state_manager.assign_agent(assigned_to, task)
        
        # 检查进度
        progress = self.coordinator._run("check_progress", {})
        
        return {
            "assignments": assignments,
            "progress": progress
        }
    
    async def get_progress(self) -> Dict[str, Any]:
        """获取项目进度"""
        return self.coordinator._run("check_progress", {})
    
    async def handle_clarification(self, questions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        处理需求澄清
        
        Args:
            questions: 需要澄清的问题列表
            
        Returns:
            澄清请求
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", "你是一位友好的需求分析师。请生成友好的澄清问题。"),
            ("human", f"""需要澄清的问题：
{questions}

请生成友好的澄清请求。""")
        ])
        
        chain = prompt | self.llm
        result = chain.invoke({})
        
        return {
            "clarification_needed": True,
            "questions": questions,
            "message": result.content
        }
    
    def get_state(self) -> RequirementsState:
        """获取当前状态"""
        return self.state_manager.get_all()
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """获取对话历史"""
        return self.conversation_history
    
    def reset(self) -> None:
        """重置智能体状态"""
        self.state_manager.reset()
        self.conversation_history = []
        self.coordinator = CoordinatorTool(llm=self.llm)


class RequirementsAgentFactory:
    """需求分析智能体工厂"""
    
    @staticmethod
    def create(config: Optional[Dict[str, Any]] = None) -> RequirementsAgent:
        """创建智能体实例"""
        return RequirementsAgent(config)
    
    @staticmethod
    def create_with_agents(
        agents: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None
    ) -> RequirementsAgent:
        """创建并注册其他智能体"""
        agent = RequirementsAgent(config)
        for name, instance in agents.items():
            agent.coordinator.register_agent(name, instance)
        return agent
