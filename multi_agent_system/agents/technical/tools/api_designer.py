"""
设计RESTful API接口
"""

from typing import Dict, List, Any, Optional
from langchain.tools import BaseTool
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
import json


# 输出Schema定义
class APIDesignerToolOutput(BaseModel):
    """设计RESTful API接口输出Schema"""
    endpoints: List[Dict[str, Any]] = Field(default_factory=list, description="API端点列表")


class APIDesignerTool(BaseTool):
    """设计RESTful API接口"""
    
    name: str = "api_designer"
    description: str = """
    设计RESTful API接口
    """
    
    llm: Optional[ChatOpenAI] = None
    
    def __init__(self, llm: Optional[ChatOpenAI] = None, **kwargs):
        super().__init__(**kwargs)
        self.llm = llm or ChatOpenAI(model="gpt-4", temperature=0.3)
    
    def _run(
        self,
        requirements: Dict[str, Any], tech_stack: Dict[str, Any],
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> Dict[str, Any]:
        """设计API"""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一位资深API架构师。请根据需求和技术栈设计RESTful API。

输出必须是严格的JSON格式，包含以下字段：
- endpoints: API端点列表，每个元素包含method, path, description, request, response"""),
            ("human", """请根据以下信息设计API：\n需求：{requirements}\n技术栈：{tech_stack}""")
        ])
        
        # 使用structured_output强制格式
        structured_llm = self.llm.with_structured_output(APIDesignerToolOutput)
        chain = prompt | structured_llm
        
        try:
            result = chain.invoke({"requirements": json.dumps(requirements, ensure_ascii=False), "tech_stack": json.dumps(tech_stack, ensure_ascii=False)})
            # 转换为字典
            parsed = result.model_dump()
        except Exception as e:
            # 降级：尝试手动解析
            try:
                raw_chain = prompt | self.llm
                raw_result = raw_chain.invoke({"requirements": json.dumps(requirements, ensure_ascii=False), "tech_stack": json.dumps(tech_stack, ensure_ascii=False)})
                parsed = json.loads(raw_result.content)
            except:
                parsed = {"endpoints": []}
        
        return parsed
    
    async def _arun(
        self,
        requirements: Dict[str, Any], tech_stack: Dict[str, Any],
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> Dict[str, Any]:
        """异步设计API"""
        import asyncio
        return await asyncio.to_thread(self._run, requirements, tech_stack)
