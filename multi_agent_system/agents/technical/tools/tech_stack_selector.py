"""
Select tech stack
"""

from typing import Dict, List, Any, Optional
from langchain.tools import BaseTool
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
import json


class TechStackSelectorToolOutput(BaseModel):
    """Output schema"""
    backend: str = Field(default="", description="Backend tech")
    frontend: str = Field(default="", description="Frontend tech")
    database: str = Field(default="", description="Database")
    tools: List[str] = Field(default_factory=list, description="Tools list")


class TechStackSelectorTool(BaseTool):
    """Select tech stack"""
    
    name: str = "tech_stack_selector"
    description: str = "Perform Select tech stack"
    
    llm: Optional[ChatOpenAI] = None
    
    def __init__(self, llm: Optional[ChatOpenAI] = None, **kwargs):
        super().__init__(**kwargs)
        self.llm = llm or ChatOpenAI(model="gpt-4", temperature=0.3)
    
    def _run(self, requirements: Dict[str, Any], architecture: Dict[str, Any], run_manager=None) -> Dict[str, Any]:
        """Execute"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert. Analyze and provide structured JSON output."),
            ("human", "Please analyze the input and provide structured output.")
        ])
        
        structured_llm = self.llm.with_structured_output(TechStackSelectorToolOutput)
        chain = prompt | structured_llm
        
        try:
            result = chain.invoke({"requirements": json.dumps(requirements, ensure_ascii=False), "architecture": json.dumps(architecture, ensure_ascii=False)})
            return result.model_dump()
        except:
            try:
                raw_chain = prompt | self.llm
                raw_result = raw_chain.invoke({"requirements": json.dumps(requirements, ensure_ascii=False), "architecture": json.dumps(architecture, ensure_ascii=False)})
                return json.loads(raw_result.content)
            except:
                return {"backend": "", "frontend": "", "database": "", "tools": []}
    
    async def _arun(self, requirements: Dict[str, Any], architecture: Dict[str, Any], run_manager=None) -> Dict[str, Any]:
        """Async execute"""
        import asyncio
        return await asyncio.to_thread(self._run, requirements, architecture)
