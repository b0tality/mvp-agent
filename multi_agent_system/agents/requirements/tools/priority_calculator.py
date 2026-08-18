"""
优先级计算工具
"""

from typing import Dict, List, Any, Optional
from langchain.tools import BaseTool
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
import json


# 输出Schema定义
class PriorityCalculatorToolOutput(BaseModel):
    """使用MoSCoW方法对需求进行优先级排序输出Schema"""
    priority_matrix: Dict[str, List[str]] = Field(default_factory=lambda: {"must_have": [], "should_have": [], "could_have": [], "wont_have": []}, description="优先级矩阵")


class PriorityCalculatorTool(BaseTool):
    """使用MoSCoW方法对需求进行优先级排序"""
    
    name: str = "priority_calculator"
    description: str = """
    使用MoSCoW方法对需求进行优先级排序
    """
    
    llm: Optional[ChatOpenAI] = None
    
    def __init__(self, llm: Optional[ChatOpenAI] = None, **kwargs):
        super().__init__(**kwargs)
        self.llm = llm or ChatOpenAI(model="gpt-4", temperature=0.3)
    
    def _run(
        self,
        requirements: Dict[str, Any],
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> Dict[str, Any]:
        """计算优先级"""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一位资深项目经理。请使用MoSCoW方法对需求进行优先级排序。

输出必须是严格的JSON格式，包含以下字段：
- priority_matrix: 优先级矩阵，包含must_have, should_have, could_have, wont_have四个列表"""),
            ("human", """请对以下需求进行优先级排序：\n{requirements}""")
        ])
        
        # 使用structured_output强制格式
        structured_llm = self.llm.with_structured_output(PriorityCalculatorToolOutput)
        chain = prompt | structured_llm
        
        try:
            result = chain.invoke({"requirements": json.dumps(requirements, ensure_ascii=False)})
            # 转换为字典
            parsed = result.model_dump()
        except Exception as e:
            # 降级：尝试手动解析
            try:
                raw_chain = prompt | self.llm
                raw_result = raw_chain.invoke({"requirements": json.dumps(requirements, ensure_ascii=False)})
                parsed = json.loads(raw_result.content)
            except:
                parsed = {"priority_matrix": {"must_have": [], "should_have": [], "could_have": [], "wont_have": []}}
        
        return parsed
    
    async def _arun(
        self,
        requirements: Dict[str, Any],
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> Dict[str, Any]:
        """异步计算优先级"""
        import asyncio
        return await asyncio.to_thread(self._run, requirements)
