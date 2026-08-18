"""
软件部署智能体主类
负责部署方案设计、CI/CD配置、容器化配置、监控配置
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from .state import DeploymentState, DeploymentStateManager
from .prompts import (
    DEPLOYMENT_SYSTEM_PROMPT,
    DEPLOYMENT_PLAN_PROMPT,
    DOCKER_CONFIG_PROMPT,
    KUBERNETES_CONFIG_PROMPT,
    CICD_CONFIG_PROMPT,
    MONITORING_CONFIG_PROMPT,
    DEPLOYMENT_DOCS_PROMPT,
    COST_ESTIMATION_PROMPT
)
from .tools import (
    DeploymentPlannerTool,
    DockerConfiguratorTool,
    KubernetesConfiguratorTool,
    CICDConfiguratorTool,
    MonitoringConfiguratorTool,
    DeploymentDocGeneratorTool
)


class DeploymentAgent:
    """
    软件部署智能体
    
    职责：
    1. 设计部署方案
    2. 生成Docker配置
    3. 生成Kubernetes配置
    4. 生成CI/CD配置
    5. 生成监控配置
    6. 生成部署文档
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化软件部署智能体
        
        Args:
            config: 配置参数
                - model: 模型名称，默认 mimo
                - temperature: 温度参数，默认 0.2
                - max_tokens: 最大token数，默认 4000
                - api_key: API密钥
                - base_url: API基础URL（用于本地LLM）
        """
        self.config = config or {}
        
        # 初始化LLM（支持本地LLM）
        llm_kwargs = {
            "model": self.config.get("model", "mimo"),
            "temperature": self.config.get("temperature", 0.2),
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
        self.state_manager = DeploymentStateManager()
        
        # 创建智能体
        self.agent = self._create_agent()
        
        # 对话历史
        self.conversation_history: List[Dict[str, str]] = []
    
    def _init_tools(self) -> List[Any]:
        """初始化工具集"""
        return [
            DeploymentPlannerTool(llm=self.llm),
            DockerConfiguratorTool(llm=self.llm),
            KubernetesConfiguratorTool(llm=self.llm),
            CICDConfiguratorTool(llm=self.llm),
            MonitoringConfiguratorTool(llm=self.llm),
            DeploymentDocGeneratorTool(llm=self.llm)
        ]
    
    def _create_agent(self):
        """创建智能体"""
        # 使用新的 create_agent API
        agent = create_agent(
            model=self.llm,
            tools=self.tools,
            system_prompt=DEPLOYMENT_SYSTEM_PROMPT
        )
        return agent
    
    async def plan_deployment(
        self,
        code_files: List[Dict[str, Any]],
        technical_solution: Dict[str, Any],
        test_results: Dict[str, Any],
        project_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        规划部署
        
        Args:
            code_files: 代码文件列表
            technical_solution: 技术方案
            test_results: 测试结果
            project_info: 项目信息
            
        Returns:
            部署规划结果
        """
        # 更新状态
        self.state_manager.set_code_files(code_files)
        self.state_manager.set_technical_solution(technical_solution)
        self.state_manager.set_test_results(test_results)
        if project_info:
            self.state_manager.set_project_info(project_info)
        
        self.state_manager.set_status("in_progress")
        
        # 添加到对话历史
        self.conversation_history.append({
            "role": "user",
            "content": f"规划部署: {len(code_files)} 个代码文件",
            "timestamp": datetime.now().isoformat()
        })
        
        try:
            # 步骤1: 设计部署方案
            self.state_manager.update("current_step", "planning_deployment")
            deployment_plan = await self._plan_deployment(
                technical_solution, project_info or {}, test_results
            )
            self.state_manager.set_deployment_plan(deployment_plan)
            self.state_manager.set_environments(deployment_plan.get("environments", {}))
            self.state_manager.set_infrastructure(deployment_plan.get("infrastructure", {}))
            
            # 步骤2: 生成Docker配置
            self.state_manager.update("current_step", "configuring_docker")
            docker_config = await self._configure_docker(
                project_info or {},
                technical_solution.get("tech_stack", {})
            )
            self.state_manager.set_docker_config(docker_config)
            self.state_manager.set_dockerfile(docker_config.get("dockerfile", {}).get("content", ""))
            self.state_manager.set_docker_compose(docker_config.get("docker_compose", {}).get("content", ""))
            
            # 步骤3: 生成Kubernetes配置
            self.state_manager.update("current_step", "configuring_kubernetes")
            kubernetes_config = await self._configure_kubernetes(
                project_info or {},
                docker_config
            )
            self.state_manager.set_kubernetes_config(kubernetes_config)
            
            # 步骤4: 生成CI/CD配置
            self.state_manager.update("current_step", "configuring_cicd")
            cicd_config = await self._configure_cicd(
                project_info or {},
                deployment_plan
            )
            self.state_manager.set_cicd_config(cicd_config)
            
            # 步骤5: 生成监控配置
            self.state_manager.update("current_step", "configuring_monitoring")
            monitoring_config = await self._configure_monitoring(
                project_info or {},
                deployment_plan
            )
            self.state_manager.set_monitoring_config(monitoring_config)
            
            # 步骤6: 生成部署文档
            self.state_manager.update("current_step", "generating_docs")
            deployment_docs = await self._generate_docs(
                deployment_plan,
                {
                    "docker_config": docker_config,
                    "kubernetes_config": kubernetes_config,
                    "cicd_config": cicd_config,
                    "monitoring_config": monitoring_config
                }
            )
            self.state_manager.set_deployment_docs(deployment_docs.get("deployment_guide", {}).get("content", ""))
            self.state_manager.set_runbook(deployment_docs.get("operations_manual", {}).get("content", ""))
            
            # 完成
            self.state_manager.set_deployment_status("planned")
            self.state_manager.set_status("completed")
            
            # 返回完整结果
            return {
                "status": "success",
                "deployment_plan": deployment_plan,
                "docker_config": docker_config,
                "kubernetes_config": kubernetes_config,
                "cicd_config": cicd_config,
                "monitoring_config": monitoring_config,
                "documentation": deployment_docs,
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
    
    async def _plan_deployment(
        self,
        technical_solution: Dict[str, Any],
        project_info: Dict[str, Any],
        test_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """设计部署方案"""
        tool = DeploymentPlannerTool(llm=self.llm)
        return await tool._arun(technical_solution, project_info, test_results)
    
    async def _configure_docker(
        self,
        project_info: Dict[str, Any],
        tech_stack: Dict[str, Any]
    ) -> Dict[str, Any]:
        """配置Docker"""
        tool = DockerConfiguratorTool(llm=self.llm)
        return await tool._arun(project_info, tech_stack)
    
    async def _configure_kubernetes(
        self,
        project_info: Dict[str, Any],
        docker_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """配置Kubernetes"""
        tool = KubernetesConfiguratorTool(llm=self.llm)
        return await tool._arun(project_info, docker_config)
    
    async def _configure_cicd(
        self,
        project_info: Dict[str, Any],
        deployment_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """配置CI/CD"""
        tool = CICDConfiguratorTool(llm=self.llm)
        return await tool._arun(project_info, deployment_config)
    
    async def _configure_monitoring(
        self,
        system_info: Dict[str, Any],
        deployment_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """配置监控"""
        tool = MonitoringConfiguratorTool(llm=self.llm)
        return await tool._arun(system_info, deployment_config)
    
    async def _generate_docs(
        self,
        deployment_config: Dict[str, Any],
        operations_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成部署文档"""
        tool = DeploymentDocGeneratorTool(llm=self.llm)
        return await tool._arun(deployment_config, operations_info)
    
    async def estimate_cost(
        self,
        deployment_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        估算部署成本
        
        Args:
            deployment_config: 部署配置
            
        Returns:
            成本估算结果
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", "你是一位资深的云架构师。请估算部署成本。"),
            ("human", f"""请估算以下部署配置的成本：

部署配置：
{json.dumps(deployment_config, ensure_ascii=False, indent=2)}

请以JSON格式输出成本估算。""")
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
        
        self.state_manager.set_cost_estimation(parsed)
        
        return parsed
    
    def get_state(self) -> DeploymentState:
        """获取当前状态"""
        return self.state_manager.get_all()
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """获取对话历史"""
        return self.conversation_history
    
    def get_deployment_plan(self) -> Dict[str, Any]:
        """获取部署计划"""
        return self.state_manager.get("deployment_plan")
    
    def get_docker_config(self) -> Dict[str, Any]:
        """获取Docker配置"""
        return self.state_manager.get("docker_config")
    
    def get_kubernetes_config(self) -> Dict[str, Any]:
        """获取Kubernetes配置"""
        return self.state_manager.get("kubernetes_config")
    
    def get_cicd_config(self) -> Dict[str, Any]:
        """获取CI/CD配置"""
        return self.state_manager.get("cicd_config")
    
    def get_monitoring_config(self) -> Dict[str, Any]:
        """获取监控配置"""
        return self.state_manager.get("monitoring_config")
    
    def get_deployment_docs(self) -> str:
        """获取部署文档"""
        return self.state_manager.get("deployment_docs")
    
    def reset(self) -> None:
        """重置智能体状态"""
        self.state_manager.reset()
        self.conversation_history = []


class DeploymentAgentFactory:
    """软件部署智能体工厂"""
    
    @staticmethod
    def create(config: Optional[Dict[str, Any]] = None) -> DeploymentAgent:
        """创建智能体实例"""
        return DeploymentAgent(config)


# 导入json模块
import json
