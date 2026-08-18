"""
用户故事生成工具
"""

from typing import Dict, List, Any, Optional
from langchain.tools import BaseTool
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
import json


# 输出Schema定义
class UserStoryGeneratorToolOutput(BaseModel):
    """生成标准格式的用户故事输出Schema"""
    user_stories: List[Dict[str, str]] = Field(default_factory=list, description="用户故事列表")


class UserStoryGeneratorTool(BaseTool):
    """生成标准格式的用户故事"""
    
    name: str = "user_story_generator"
    description: str = """
    根据需求生成用户故事
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
        """生成用户故事"""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一位资深需求分析师。请根据需求生成标准的用户故事。

输出必须是严格的JSON格式，包含以下字段：
- user_stories: 用户故事列表，每个元素包含id, role, feature, benefit, priority"""),
            ("human", """请根据以下需求生成用户故事：\n功能需求：{functional_requirements}\n非功能需求：{non_functional_requirements}""")
        ])
        
        # 使用structured_output强制格式
        structured_llm = self.llm.with_structured_output(UserStoryGeneratorToolOutput)
        chain = prompt | structured_llm
        
        try:
            result = chain.invoke({"functional_requirements": json.dumps(requirements.get("functional_requirements", []), ensure_ascii=False), "non_functional_requirements": json.dumps(requirements.get("non_functional_requirements", []), ensure_ascii=False)})
            # 转换为字典
            parsed = result.model_dump()
        except Exception as e:
            # 降级：尝试手动解析
            try:
                raw_chain = prompt | self.llm
                raw_result = raw_chain.invoke({"functional_requirements": json.dumps(requirements.get("functional_requirements", []), ensure_ascii=False), "non_functional_requirements": json.dumps(requirements.get("non_functional_requirements", []), ensure_ascii=False)})
                parsed = json.loads(raw_result.content)
            except:
                parsed = {"user_stories": []}
        
        return parsed
    
    async def _arun(
        self,
        requirements: Dict[str, Any],
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> Dict[str, Any]:
        """异步生成用户故事"""
        import asyncio
        return await asyncio.to_thread(self._run, requirements)
