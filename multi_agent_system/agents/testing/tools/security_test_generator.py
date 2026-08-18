"""
Generate security tests
"""

from typing import Dict, List, Any, Optional
from langchain.tools import BaseTool
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
import json


class SecurityTestGeneratorToolOutput(BaseModel):
    """Output schema"""
    test_cases: List[Dict[str, str]] = Field(default_factory=list, description="Test cases")
    attack_vectors: List[str] = Field(default_factory=list, description="Attack vectors")


class SecurityTestGeneratorTool(BaseTool):
    """Generate security tests"""
    
    name: str = "security_test_generator"
    description: str = "Perform Generate security tests"
    
    llm: Optional[ChatOpenAI] = None
    
    def __init__(self, llm: Optional[ChatOpenAI] = None, **kwargs):
        super().__init__(**kwargs)
        self.llm = llm or ChatOpenAI(model="gpt-4", temperature=0.3)
    
    def _run(self, api_design: Dict[str, Any], security_design: Dict[str, Any] = None, run_manager=None) -> Dict[str, Any]:
        """Execute"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert. Analyze and provide structured JSON output."),
            ("human", "Please analyze the input and provide structured output.")
        ])
        
        structured_llm = self.llm.with_structured_output(SecurityTestGeneratorToolOutput)
        chain = prompt | structured_llm
        
        try:
            result = chain.invoke({"api_design": json.dumps(api_design, ensure_ascii=False), "security_design": json.dumps(security_design or {}, ensure_ascii=False)})
            return result.model_dump()
        except:
            try:
                raw_chain = prompt | self.llm
                raw_result = raw_chain.invoke({"api_design": json.dumps(api_design, ensure_ascii=False), "security_design": json.dumps(security_design or {}, ensure_ascii=False)})
                return json.loads(raw_result.content)
            except:
                return {"test_cases": [], "attack_vectors": []}
    
    async def _arun(self, api_design: Dict[str, Any], security_design: Dict[str, Any] = None, run_manager=None) -> Dict[str, Any]:
        """Async execute"""
        import asyncio
        return await asyncio.to_thread(self._run, api_design, security_design)
