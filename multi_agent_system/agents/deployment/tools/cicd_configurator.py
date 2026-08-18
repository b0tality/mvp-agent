"""
生成CI/CD配置
"""

from typing import Dict, List, Any, Optional
from langchain.tools import BaseTool
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
import json


# 输出Schema定义
class CICDConfiguratorToolOutput(BaseModel):
    """生成CI/CD配置输出Schema"""
    workflows: List[Dict[str, Any]] = Field(default_factory=list, description="工作流配置列表")


class CICDConfiguratorTool(BaseTool):
    """生成CI/CD配置"""
    
    name: str = "cicd_configurator"
    description: str = """
    生成CI/CD配置
    """
    
    llm: Optional[ChatOpenAI] = None
    
    def __init__(self, llm: Optional[ChatOpenAI] = None, **kwargs):
        super().__init__(**kwargs)
        self.llm = llm or ChatOpenAI(model="gpt-4", temperature=0.3)
    
    def _run(
        self,
        project_info: Dict[str, Any], tech_stack: Dict[str, Any],
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> Dict[str, Any]:
        """生成CI/CD配置"""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一位资深DevOps工程师。请根据项目信息生成CI/CD配置。

输出必须是严格的JSON格式，包含以下字段：
- workflows: 工作流配置列表"""),
            ("human", """请根据以下信息生成CI/CD配置：\n项目信息：{project_info}\n技术栈：{tech_stack}""")
        ])
        
        # 使用structured_output强制格式
        structured_llm = self.llm.with_structured_output(CICDConfiguratorToolOutput)
        chain = prompt | structured_llm
        
        try:
            result = chain.invoke({"project_info": json.dumps(project_info, ensure_ascii=False), "tech_stack": json.dumps(tech_stack, ensure_ascii=False)})
            parsed = result.model_dump()
        except Exception as e:
            try:
                raw_chain = prompt | self.llm
                raw_result = raw_chain.invoke({"project_info": json.dumps(project_info, ensure_ascii=False), "tech_stack": json.dumps(tech_stack, ensure_ascii=False)})
                parsed = json.loads(raw_result.content)
            except:
                parsed = {"workflows": []}
        
        return parsed
    
    async def _arun(
        self,
        project_info: Dict[str, Any], tech_stack: Dict[str, Any],
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> Dict[str, Any]:
        """异步生成CI/CD配置"""
        import asyncio
        return await asyncio.to_thread(self._run, project_info, tech_stack)
