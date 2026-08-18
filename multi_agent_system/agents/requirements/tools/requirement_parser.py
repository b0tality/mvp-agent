"""
需求解析工具
"""

from typing import Dict, List, Any, Optional
from langchain.tools import BaseTool
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
import json


# 输出Schema定义
class RequirementParserToolOutput(BaseModel):
    """解析用户需求，提取功能和非功能需求输出Schema"""
    functional_requirements: List[Dict[str, str]] = Field(default_factory=list, description="功能需求列表")
    non_functional_requirements: List[Dict[str, str]] = Field(default_factory=list, description="非功能需求列表")
    constraints: List[str] = Field(default_factory=list, description="约束条件")
    assumptions: List[str] = Field(default_factory=list, description="假设条件")
    risks: List[str] = Field(default_factory=list, description="风险点")


class RequirementParserTool(BaseTool):
    """解析用户需求，提取功能和非功能需求"""
    
    name: str = "requirement_parser"
    description: str = """
    解析用户自然语言需求，提取功能需求、非功能需求、约束条件等
    """
    
    llm: Optional[ChatOpenAI] = None
    
    def __init__(self, llm: Optional[ChatOpenAI] = None, **kwargs):
        super().__init__(**kwargs)
        self.llm = llm or ChatOpenAI(model="gpt-4", temperature=0.3)
    
    def _run(
        self,
        user_input: str,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> Dict[str, Any]:
        """解析需求"""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一位资深需求分析师。请分析用户需求，提取结构化信息。

输出必须是严格的JSON格式，包含以下字段：
- functional_requirements: 功能需求列表，每个元素包含id, title, description\n- non_functional_requirements: 非功能需求列表，每个元素包含id, category, description\n- constraints: 约束条件列表\n- assumptions: 假设条件列表\n- risks: 风险点列表"""),
            ("human", """请分析以下用户需求：\n{user_input}""")
        ])
        
        # 使用structured_output强制格式
        structured_llm = self.llm.with_structured_output(RequirementParserToolOutput)
        chain = prompt | structured_llm
        
        try:
            result = chain.invoke({"user_input": user_input})
            # 转换为字典
            parsed = result.model_dump()
        except Exception as e:
            # 降级：尝试手动解析
            try:
                raw_chain = prompt | self.llm
                raw_result = raw_chain.invoke({"user_input": user_input})
                parsed = json.loads(raw_result.content)
            except:
                parsed = {"functional_requirements": [], "non_functional_requirements": [], "constraints": [], "assumptions": [], "risks": []}
        
        return parsed
    
    async def _arun(
        self,
        user_input: str,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> Dict[str, Any]:
        """异步解析需求"""
        import asyncio
        return await asyncio.to_thread(self._run, user_input)
