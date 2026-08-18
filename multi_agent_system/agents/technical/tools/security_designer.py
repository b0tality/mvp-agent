"""
Design security solution
"""

from typing import Dict, List, Any, Optional
from langchain.tools import BaseTool
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
import json


class SecurityDesignerToolOutput(BaseModel):
    """Output schema"""
    authentication: Dict[str, Any] = Field(default_factory=dict, description="Authentication")
    authorization: Dict[str, Any] = Field(default_factory=dict, description="Authorization")
    encryption: Dict[str, Any] = Field(default_factory=dict, description="Encryption")


class SecurityDesignerTool(BaseTool):
    """Design security solution"""
    
    name: str = "security_designer"
    description: str = "Perform Design security solution"
    
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
        
        structured_llm = self.llm.with_structured_output(SecurityDesignerToolOutput)
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
                return {"authentication": {}, "authorization": {}, "encryption": {}}
    
    async def _arun(self, requirements: Dict[str, Any], architecture: Dict[str, Any], run_manager=None) -> Dict[str, Any]:
        """Async execute"""
        import asyncio
        return await asyncio.to_thread(self._run, requirements, architecture)
