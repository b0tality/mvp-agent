"""
生成测试用例
"""

from typing import Dict, List, Any, Optional
from langchain.tools import BaseTool
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
import json


# 输出Schema定义
class TestGeneratorToolOutput(BaseModel):
    """生成测试用例输出Schema"""
    test_cases: List[Dict[str, str]] = Field(default_factory=list, description="测试用例列表")


class TestGeneratorTool(BaseTool):
    """生成测试用例"""
    
    name: str = "test_generator"
    description: str = """
    生成测试用例
    """
    
    llm: Optional[ChatOpenAI] = None
    
    def __init__(self, llm: Optional[ChatOpenAI] = None, **kwargs):
        super().__init__(**kwargs)
        self.llm = llm or ChatOpenAI(model="gpt-4", temperature=0.3)
    
    def _run(
        self,
        code_files: List[Dict[str, Any]], test_type: str = "unit",
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> Dict[str, Any]:
        """生成测试"""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一位资深测试工程师。请根据代码生成测试用例。

输出必须是严格的JSON格式，包含以下字段：
- test_cases: 测试用例列表，每个元素包含name, code, type"""),
            ("human", """请根据以下代码生成测试：\n代码文件：{code_files}\n测试类型：{test_type}""")
        ])
        
        # 使用structured_output强制格式
        structured_llm = self.llm.with_structured_output(TestGeneratorToolOutput)
        chain = prompt | structured_llm
        
        try:
            result = chain.invoke({"code_files": json.dumps(code_files, ensure_ascii=False), "test_type": test_type})
            # 转换为字典
            parsed = result.model_dump()
        except Exception as e:
            # 降级：尝试手动解析
            try:
                raw_chain = prompt | self.llm
                raw_result = raw_chain.invoke({"code_files": json.dumps(code_files, ensure_ascii=False), "test_type": test_type})
                parsed = json.loads(raw_result.content)
            except:
                parsed = {"test_cases": []}
        
        return parsed
    
    async def _arun(
        self,
        code_files: List[Dict[str, Any]], test_type: str = "unit",
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> Dict[str, Any]:
        """异步生成测试"""
        import asyncio
        return await asyncio.to_thread(self._run, code_files, test_type)
