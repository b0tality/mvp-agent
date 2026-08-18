"""
Generate test report
"""

from typing import Dict, List, Any, Optional
from langchain.tools import BaseTool
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
import json


class TestReportGeneratorToolOutput(BaseModel):
    """Output schema"""
    summary: str = Field(default="", description="Summary")
    details: Dict[str, Any] = Field(default_factory=dict, description="Details")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations")


class TestReportGeneratorTool(BaseTool):
    """Generate test report"""
    
    name: str = "test_report_generator"
    description: str = "Perform Generate test report"
    
    llm: Optional[ChatOpenAI] = None
    
    def __init__(self, llm: Optional[ChatOpenAI] = None, **kwargs):
        super().__init__(**kwargs)
        self.llm = llm or ChatOpenAI(model="gpt-4", temperature=0.3)
    
    def _run(self, test_results: Dict[str, Any], coverage: Dict[str, Any] = None, run_manager=None) -> Dict[str, Any]:
        """Execute"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert. Analyze and provide structured JSON output."),
            ("human", "Please analyze the input and provide structured output.")
        ])
        
        structured_llm = self.llm.with_structured_output(TestReportGeneratorToolOutput)
        chain = prompt | structured_llm
        
        try:
            result = chain.invoke({"test_results": json.dumps(test_results, ensure_ascii=False), "coverage": json.dumps(coverage or {}, ensure_ascii=False)})
            return result.model_dump()
        except:
            try:
                raw_chain = prompt | self.llm
                raw_result = raw_chain.invoke({"test_results": json.dumps(test_results, ensure_ascii=False), "coverage": json.dumps(coverage or {}, ensure_ascii=False)})
                return json.loads(raw_result.content)
            except:
                return {"summary": "", "details": {}, "recommendations": []}
    
    async def _arun(self, test_results: Dict[str, Any], coverage: Dict[str, Any] = None, run_manager=None) -> Dict[str, Any]:
        """Async execute"""
        import asyncio
        return await asyncio.to_thread(self._run, test_results, coverage)
