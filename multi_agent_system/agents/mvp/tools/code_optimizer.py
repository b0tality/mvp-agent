"""
Optimize code quality
"""

from typing import Dict, List, Any, Optional
from langchain.tools import BaseTool
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
import json


class CodeOptimizerToolOutput(BaseModel):
    """Output schema"""
    optimized_files: List[Dict[str, str]] = Field(default_factory=list, description="Optimized files")
    suggestions: List[str] = Field(default_factory=list, description="Suggestions")


class CodeOptimizerTool(BaseTool):
    """Optimize code quality"""
    
    name: str = "code_optimizer"
    description: str = "Perform Optimize code quality"
    
    llm: Optional[ChatOpenAI] = None
    
    def __init__(self, llm: Optional[ChatOpenAI] = None, **kwargs):
        super().__init__(**kwargs)
        self.llm = llm or ChatOpenAI(model="gpt-4", temperature=0.3)
    
    def _run(self, code_files: List[Dict[str, Any]], goals: List[str] = None, run_manager=None) -> Dict[str, Any]:
        """Execute"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert. Analyze and provide structured JSON output."),
            ("human", "Please analyze the input and provide structured output.")
        ])
        
        structured_llm = self.llm.with_structured_output(CodeOptimizerToolOutput)
        chain = prompt | structured_llm
        
        try:
            result = chain.invoke({"code_files": json.dumps(code_files, ensure_ascii=False), "goals": json.dumps(goals or ["performance", "readability"])})
            return result.model_dump()
        except:
            try:
                raw_chain = prompt | self.llm
                raw_result = raw_chain.invoke({"code_files": json.dumps(code_files, ensure_ascii=False), "goals": json.dumps(goals or ["performance", "readability"])})
                return json.loads(raw_result.content)
            except:
                return {"optimized_files": [], "suggestions": []}
    
    async def _arun(self, code_files: List[Dict[str, Any]], goals: List[str] = None, run_manager=None) -> Dict[str, Any]:
        """Async execute"""
        import asyncio
        return await asyncio.to_thread(self._run, code_files, goals)
