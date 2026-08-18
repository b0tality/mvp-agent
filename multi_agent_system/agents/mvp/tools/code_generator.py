"""
生成代码文件
"""

from typing import Dict, List, Any, Optional
from langchain.tools import BaseTool
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
import json


# 输出Schema定义
class CodeGeneratorToolOutput(BaseModel):
    """生成代码文件输出Schema"""
    files: List[Dict[str, str]] = Field(default_factory=list, description="代码文件列表")


class CodeGeneratorTool(BaseTool):
    """生成代码文件"""
    
    name: str = "code_generator"
    description: str = """
    根据设计生成代码文件
    """
    
    llm: Optional[ChatOpenAI] = None
    
    def __init__(self, llm: Optional[ChatOpenAI] = None, **kwargs):
        super().__init__(**kwargs)
        self.llm = llm or ChatOpenAI(model="gpt-4", temperature=0.3)
    
    def _run(
        self,
        spec: Dict[str, Any], language: str = "python",
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> Dict[str, Any]:
        """生成代码"""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一位资深全栈开发工程师。请根据规格说明生成代码。

输出必须是严格的JSON格式，包含以下字段：
- files: 代码文件列表，每个元素包含path, content, language"""),
            ("human", """请根据以下规格生成代码：\n规格：{spec}\n语言：{language}""")
        ])
        
        # 使用structured_output强制格式
        structured_llm = self.llm.with_structured_output(CodeGeneratorToolOutput)
        chain = prompt | structured_llm
        
        try:
            result = chain.invoke({"spec": json.dumps(spec, ensure_ascii=False), "language": language})
            # 转换为字典
            parsed = result.model_dump()
        except Exception as e:
            # 降级：尝试手动解析
            try:
                raw_chain = prompt | self.llm
                raw_result = raw_chain.invoke({"spec": json.dumps(spec, ensure_ascii=False), "language": language})
                parsed = json.loads(raw_result.content)
            except:
                parsed = {"files": []}
        
        return parsed
    
    async def _arun(
        self,
        spec: Dict[str, Any], language: str = "python",
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> Dict[str, Any]:
        """异步生成代码"""
        import asyncio
        return await asyncio.to_thread(self._run, spec, language)
