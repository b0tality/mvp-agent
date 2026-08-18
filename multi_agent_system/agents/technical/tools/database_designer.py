"""
设计数据库schema
"""

from typing import Dict, List, Any, Optional
from langchain.tools import BaseTool
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
import json


# 输出Schema定义
class DatabaseDesignerToolOutput(BaseModel):
    """设计数据库schema输出Schema"""
    tables: List[Dict[str, Any]] = Field(default_factory=list, description="数据库表列表")


class DatabaseDesignerTool(BaseTool):
    """设计数据库schema"""
    
    name: str = "database_designer"
    description: str = """
    设计数据库schema
    """
    
    llm: Optional[ChatOpenAI] = None
    
    def __init__(self, llm: Optional[ChatOpenAI] = None, **kwargs):
        super().__init__(**kwargs)
        self.llm = llm or ChatOpenAI(model="gpt-4", temperature=0.3)
    
    def _run(
        self,
        requirements: Dict[str, Any], api_design: Dict[str, Any],
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> Dict[str, Any]:
        """设计数据库"""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一位资深数据库架构师。请根据需求和API设计数据库schema。

输出必须是严格的JSON格式，包含以下字段：
- tables: 数据库表列表，每个元素包含name, columns, relationships"""),
            ("human", """请根据以下信息设计数据库：\n需求：{requirements}\nAPI设计：{api_design}""")
        ])
        
        # 使用structured_output强制格式
        structured_llm = self.llm.with_structured_output(DatabaseDesignerToolOutput)
        chain = prompt | structured_llm
        
        try:
            result = chain.invoke({"requirements": json.dumps(requirements, ensure_ascii=False), "api_design": json.dumps(api_design, ensure_ascii=False)})
            # 转换为字典
            parsed = result.model_dump()
        except Exception as e:
            # 降级：尝试手动解析
            try:
                raw_chain = prompt | self.llm
                raw_result = raw_chain.invoke({"requirements": json.dumps(requirements, ensure_ascii=False), "api_design": json.dumps(api_design, ensure_ascii=False)})
                parsed = json.loads(raw_result.content)
            except:
                parsed = {"tables": []}
        
        return parsed
    
    async def _arun(
        self,
        requirements: Dict[str, Any], api_design: Dict[str, Any],
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> Dict[str, Any]:
        """异步设计数据库"""
        import asyncio
        return await asyncio.to_thread(self._run, requirements, api_design)
