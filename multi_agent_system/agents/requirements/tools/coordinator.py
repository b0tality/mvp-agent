"""
协调器工具
"""

from typing import Dict, List, Any, Optional
from langchain.tools import BaseTool
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
import json


# 输出Schema定义
class CoordinatorToolOutput(BaseModel):
    """协调其他智能体，分配任务，监控进度输出Schema"""
    status: str = Field(default="success", description="操作状态")
    message: str = Field(default="", description="结果消息")
    tasks: List[Dict[str, Any]] = Field(default_factory=list, description="任务列表")


class CoordinatorTool(BaseTool):
    """协调其他智能体，分配任务，监控进度"""
    
    name: str = "coordinator"
    description: str = """
    协调其他智能体，分配任务，监控进度
    """
    
    llm: Optional[ChatOpenAI] = None
    
    def __init__(self, llm: Optional[ChatOpenAI] = None, **kwargs):
        super().__init__(**kwargs)
        self.llm = llm or ChatOpenAI(model="gpt-4", temperature=0.3)
    
    def _run(
        self,
        action: str, data: Dict[str, Any] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> Dict[str, Any]:
        """执行协调操作"""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一位项目经理。请协调智能体团队，分配任务并监控进度。

输出必须是严格的JSON格式，包含以下字段：
- status: 操作状态\n- message: 结果消息\n- tasks: 任务列表（可选）"""),
            ("human", """请执行以下协调操作：\n操作：{action}\n数据：{data}""")
        ])
        
        # 使用structured_output强制格式
        structured_llm = self.llm.with_structured_output(CoordinatorToolOutput)
        chain = prompt | structured_llm
        
        try:
            result = chain.invoke({"action": action, "data": json.dumps(data or {}, ensure_ascii=False)})
            # 转换为字典
            parsed = result.model_dump()
        except Exception as e:
            # 降级：尝试手动解析
            try:
                raw_chain = prompt | self.llm
                raw_result = raw_chain.invoke({"action": action, "data": json.dumps(data or {}, ensure_ascii=False)})
                parsed = json.loads(raw_result.content)
            except:
                parsed = {"status": "error", "message": "无法解析输出"}
        
        return parsed
    
    async def _arun(
        self,
        action: str, data: Dict[str, Any] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> Dict[str, Any]:
        """异步执行协调操作"""
        import asyncio
        return await asyncio.to_thread(self._run, action, data)
