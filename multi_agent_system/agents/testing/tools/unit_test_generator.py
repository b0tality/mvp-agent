"""
Generate unit tests
"""

from typing import Dict, List, Any, Optional
from langchain.tools import BaseTool
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
import json


class UnitTestGeneratorToolOutput(BaseModel):
    """Output schema"""
    test_cases: List[Dict[str, str]] = Field(default_factory=list, description="Test cases")
    coverage_target: int = Field(default=80, description="Coverage target")


class UnitTestGeneratorTool(BaseTool):
    """Generate unit tests"""
    
    name: str = "unit_test_generator"
    description: str = "Perform Generate unit tests"
    
    llm: Optional[ChatOpenAI] = None
    
    def __init__(self, llm: Optional[ChatOpenAI] = None, **kwargs):
        super().__init__(**kwargs)
        self.llm = llm or ChatOpenAI(model="gpt-4", temperature=0.3)
    
    def _run(self, code_file: Dict[str, Any], test_framework: str = "pytest", run_manager=None) -> Dict[str, Any]:
        """Execute"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert. Analyze and provide structured JSON output."),
            ("human", "Please analyze the input and provide structured output.")
        ])
        
        structured_llm = self.llm.with_structured_output(UnitTestGeneratorToolOutput)
        chain = prompt | structured_llm
        
        try:
            result = chain.invoke({"code_file": json.dumps(code_file, ensure_ascii=False), "test_framework": test_framework})
            return result.model_dump()
        except:
            try:
                raw_chain = prompt | self.llm
                raw_result = raw_chain.invoke({"code_file": json.dumps(code_file, ensure_ascii=False), "test_framework": test_framework})
                return json.loads(raw_result.content)
            except:
                return {"test_cases": [], "coverage_target": 80}
    
    async def _arun(self, code_file: Dict[str, Any], test_framework: str = "pytest", run_manager=None) -> Dict[str, Any]:
        """Async execute"""
        import asyncio
        return await asyncio.to_thread(self._run, code_file, test_framework)
