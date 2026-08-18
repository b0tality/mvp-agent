"""
技术架构师智能体主类
负责技术方案设计
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from .state import TechnicalState, TechnicalStateManager
from .prompts import (
    TECHNICAL_SYSTEM_PROMPT,
    ARCHITECTURE_DESIGN_PROMPT,
    TECH_STACK_PROMPT,
    API_DESIGN_PROMPT,
    DATABASE_DESIGN_PROMPT,
    SECURITY_DESIGN_PROMPT,
    COST_ESTIMATION_PROMPT,
    ADR_PROMPT
)
from .tools import (
    ArchitectureDesignerTool,
    TechStackSelectorTool,
    APIDesignerTool,
    DatabaseDesignerTool,
    SecurityDesignerTool,
    CostEstimatorTool
)


class TechnicalAgent:
    """
    技术架构师智能体
    
    职责：
    1. 设计系统架构
    2. 选择技术栈
    3. 设计API
    4. 设计数据库
    5. 设计安全方案
    6. 估算成本
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化技术架构师智能体
        
        Args:
            config: 配置参数
                - model: 模型名称，默认 mimo
                - temperature: 温度参数，默认 0.2
                - max_tokens: 最大token数，默认 6000
                - api_key: API密钥
                - base_url: API基础URL（用于本地LLM）
        """
        self.config = config or {}
        
        # 初始化LLM（支持本地LLM）
        llm_kwargs = {
            "model": self.config.get("model", "mimo"),
            "temperature": self.config.get("temperature", 0.2),
            "max_tokens": self.config.get("max_tokens", 6000),
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
        self.state_manager = TechnicalStateManager()
        
        # 创建智能体
        self.agent = self._create_agent()
        
        # 对话历史
        self.conversation_history: List[Dict[str, str]] = []
    
    def _init_tools(self) -> List[Any]:
        """初始化工具集"""
        return [
            ArchitectureDesignerTool(llm=self.llm),
            TechStackSelectorTool(llm=self.llm),
            APIDesignerTool(llm=self.llm),
            DatabaseDesignerTool(llm=self.llm),
            SecurityDesignerTool(llm=self.llm),
            CostEstimatorTool(llm=self.llm)
        ]
    
    def _create_agent(self):
        """创建智能体"""
        # 使用新的 create_agent API
        agent = create_agent(
            model=self.llm,
            tools=self.tools,
            system_prompt=TECHNICAL_SYSTEM_PROMPT
        )
        return agent
    
    async def design_technical_solution(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """
        设计技术方案
        
        Args:
            requirements: 需求分析结果
            
        Returns:
            技术方案，包含架构、技术栈、API、数据库、安全、成本等
        """
        # 更新状态
        self.state_manager.set_requirements(requirements)
        self.state_manager.set_status("in_progress")
        
        # 添加到对话历史
        self.conversation_history.append({
            "role": "user",
            "content": f"设计技术方案: {json.dumps(requirements, ensure_ascii=False)}",
            "timestamp": datetime.now().isoformat()
        })
        
        try:
            # 步骤1: 设计系统架构
            self.state_manager.update("current_phase", "designing_architecture")
            architecture = await self._design_architecture(requirements)
            self.state_manager.set_architecture(architecture)
            
            # 步骤2: 选择技术栈
            self.state_manager.update("current_phase", "selecting_tech_stack")
            tech_stack = await self._select_tech_stack(architecture, requirements)
            self.state_manager.set_tech_stack(tech_stack)
            
            # 步骤3: 设计API
            self.state_manager.update("current_phase", "designing_api")
            api_design = await self._design_api(requirements, tech_stack)
            self.state_manager.set_api_design(api_design)
            
            # 步骤4: 设计数据库
            self.state_manager.update("current_phase", "designing_database")
            database_design = await self._design_database(requirements, api_design)
            self.state_manager.set_database_design(database_design)
            
            # 步骤5: 设计安全方案
            self.state_manager.update("current_phase", "designing_security")
            security_design = await self._design_security(requirements, architecture)
            self.state_manager.set_security_design(security_design)
            
            # 步骤6: 估算成本
            self.state_manager.update("current_phase", "estimating_cost")
            cost_estimation = await self._estimate_cost(tech_stack, architecture, requirements)
            self.state_manager.set_cost_estimation(cost_estimation)
            
            # 生成技术规格文档
            self.state_manager.update("current_phase", "generating_spec")
            technical_spec = self._generate_technical_spec()
            self.state_manager.update("technical_spec", technical_spec)
            
            self.state_manager.set_status("completed")
            self.state_manager.update("current_phase", "completed")
            
            # 返回完整结果
            return {
                "status": "success",
                "architecture": architecture,
                "tech_stack": tech_stack,
                "api_design": api_design,
                "database_design": database_design,
                "security_design": security_design,
                "cost_estimation": cost_estimation,
                "technical_spec": technical_spec,
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
    
    async def _design_architecture(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """设计系统架构"""
        tool = ArchitectureDesignerTool(llm=self.llm)
        return await tool._arun(requirements)
    
    async def _select_tech_stack(
        self,
        architecture: Dict[str, Any],
        requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """选择技术栈"""
        tool = TechStackSelectorTool(llm=self.llm)
        return await tool._arun(architecture, requirements)
    
    async def _design_api(
        self,
        requirements: Dict[str, Any],
        tech_stack: Dict[str, Any]
    ) -> Dict[str, Any]:
        """设计API"""
        tool = APIDesignerTool(llm=self.llm)
        return await tool._arun(requirements, tech_stack)
    
    async def _design_database(
        self,
        requirements: Dict[str, Any],
        api_design: Dict[str, Any]
    ) -> Dict[str, Any]:
        """设计数据库"""
        tool = DatabaseDesignerTool(llm=self.llm)
        return await tool._arun(requirements, api_design)
    
    async def _design_security(
        self,
        requirements: Dict[str, Any],
        architecture: Dict[str, Any]
    ) -> Dict[str, Any]:
        """设计安全方案"""
        tool = SecurityDesignerTool(llm=self.llm)
        return await tool._arun(requirements, architecture)
    
    async def _estimate_cost(
        self,
        tech_stack: Dict[str, Any],
        architecture: Dict[str, Any],
        requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """估算成本"""
        tool = CostEstimatorTool(llm=self.llm)
        return await tool._arun(tech_stack, architecture, requirements)
    
    def _generate_technical_spec(self) -> Dict[str, Any]:
        """生成技术规格文档"""
        return {
            "document_info": {
                "title": "技术规格文档",
                "version": "1.0",
                "created_at": datetime.now().isoformat(),
                "status": "draft"
            },
            "executive_summary": {
                "project_overview": "基于需求的技术方案概述",
                "key_decisions": [],
                "risks_and_mitigations": []
            },
            "architecture_overview": self.state_manager.get("system_architecture"),
            "tech_stack": self.state_manager.get("tech_stack"),
            "api_specification": self.state_manager.get("api_design"),
            "database_schema": self.state_manager.get("database_design"),
            "security_measures": self.state_manager.get("security_design"),
            "cost_estimation": self.state_manager.get("cost_estimation"),
            "implementation_plan": {
                "phases": [],
                "timeline": {},
                "resources": {}
            },
            "appendices": {
                "architecture_decisions": self.state_manager.get("architecture_decision_records"),
                "glossary": {},
                "references": []
            }
        }
    
    async def create_adr(
        self,
        title: str,
        context: str,
        decision: str,
        consequences: str,
        alternatives: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        创建架构决策记录
        
        Args:
            title: 决策标题
            context: 决策背景
            decision: 决策内容
            consequences: 决策后果
            alternatives: 替代方案
            
        Returns:
            架构决策记录
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", "你是一位资深的技术架构师。请创建架构决策记录（ADR）。"),
            ("human", f"""请创建架构决策记录：

标题：{title}
背景：{context}
决策：{decision}
后果：{consequences}
替代方案：{json.dumps(alternatives, ensure_ascii=False)}

请以JSON格式输出ADR。""")
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
                parsed = {"error": "无法解析输出"}
        
        # 添加到状态
        self.state_manager.add_adr(parsed)
        
        return parsed
    
    def get_state(self) -> TechnicalState:
        """获取当前状态"""
        return self.state_manager.get_all()
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """获取对话历史"""
        return self.conversation_history
    
    def get_technical_spec(self) -> Dict[str, Any]:
        """获取技术规格文档"""
        return self.state_manager.get("technical_spec")
    
    def reset(self) -> None:
        """重置智能体状态"""
        self.state_manager.reset()
        self.conversation_history = []


class TechnicalAgentFactory:
    """技术架构师智能体工厂"""
    
    @staticmethod
    def create(config: Optional[Dict[str, Any]] = None) -> TechnicalAgent:
        """创建智能体实例"""
        return TechnicalAgent(config)


# 导入json模块
import json
