"""
验收标准生成工具
"""

from typing import Dict, List, Any, Optional
from langchain.tools import BaseTool
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
import json


# 输出Schema定义
class AcceptanceCriteriaToolOutput(BaseModel):
    """为用户故事生成验收标准输出Schema"""
    acceptance_criteria: List[Dict[str, str]] = Field(default_factory=list, description="验收标准列表")


class AcceptanceCriteriaTool(BaseTool):
    """为用户故事生成验收标准"""
    
    name: str = "acceptance_criteria_generator"
    description: str = """
    为用户故事生成详细的验收标准
    """
    
    llm: Optional[ChatOpenAI] = None
    
    def __init__(self, llm: Optional[ChatOpenAI] = None, **kwargs):
        super().__init__(**kwargs)
        self.llm = llm or ChatOpenAI(model="gpt-4", temperature=0.3)
    
    def _run(
        self,
        user_story: Dict[str, Any],
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> Dict[str, Any]:
        """生成验收标准"""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一位资深测试工程师。请为用户故事生成详细的验收标准。

输出必须是严格的JSON格式，包含以下字段：
- acceptance_criteria: 验收标准列表，每个元素包含id, description, given, when, then"""),
            ("human", """请为以下用户故事生成验收标准：\n{user_story}""")
        ])
        
        # 使用structured_output强制格式
        structured_llm = self.llm.with_structured_output(AcceptanceCriteriaToolOutput)
        chain = prompt | structured_llm
        
        try:
            result = chain.invoke({"user_story": json.dumps(user_story, ensure_ascii=False)})
            # 转换为字典
            parsed = result.model_dump()
        except Exception as e:
            # 降级：尝试手动解析
            try:
                raw_chain = prompt | self.llm
                raw_result = raw_chain.invoke({"user_story": json.dumps(user_story, ensure_ascii=False)})
                parsed = json.loads(raw_result.content)
            except:
                parsed = {"acceptance_criteria": []}
        
        return parsed
    
    async def _arun(
        self,
        user_story: Dict[str, Any],
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> Dict[str, Any]:
        """异步生成验收标准"""
        import asyncio
        return await asyncio.to_thread(self._run, user_story)
