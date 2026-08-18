"""
生成测试数据
"""

from typing import Dict, List, Any, Optional
from langchain.tools import BaseTool
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
import json


# 输出Schema定义
class TestDataGeneratorToolOutput(BaseModel):
    """生成测试数据输出Schema"""
    test_data: List[Dict[str, Any]] = Field(default_factory=list, description="测试数据列表")


class TestDataGeneratorTool(BaseTool):
    """生成测试数据"""
    
    name: str = "test_data_generator"
    description: str = """
    生成测试数据
    """
    
    llm: Optional[ChatOpenAI] = None
    
    def __init__(self, llm: Optional[ChatOpenAI] = None, **kwargs):
        super().__init__(**kwargs)
        self.llm = llm or ChatOpenAI(model="gpt-4", temperature=0.3)
    
    def _run(
        self,
        data_models: Dict[str, Any], count: int = 10,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> Dict[str, Any]:
        """生成测试数据"""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一位资深测试工程师。请根据数据模型生成测试数据。

输出必须是严格的JSON格式，包含以下字段：
- test_data: 测试数据列表"""),
            ("human", """请根据以下信息生成测试数据：\n数据模型：{data_models}\n数量：{count}""")
        ])
        
        # 使用structured_output强制格式
        structured_llm = self.llm.with_structured_output(TestDataGeneratorToolOutput)
        chain = prompt | structured_llm
        
        try:
            result = chain.invoke({"data_models": json.dumps(data_models, ensure_ascii=False), "count": count})
            parsed = result.model_dump()
        except Exception as e:
            try:
                raw_chain = prompt | self.llm
                raw_result = raw_chain.invoke({"data_models": json.dumps(data_models, ensure_ascii=False), "count": count})
                parsed = json.loads(raw_result.content)
            except:
                parsed = {"test_data": []}
        
        return parsed
    
    async def _arun(
        self,
        data_models: Dict[str, Any], count: int = 10,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> Dict[str, Any]:
        """异步生成测试数据"""
        import asyncio
        return await asyncio.to_thread(self._run, data_models, count)
