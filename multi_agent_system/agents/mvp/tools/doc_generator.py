"""
Generate documentation
"""

from typing import Dict, List, Any, Optional
from langchain.tools import BaseTool
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
import json


class DocGeneratorToolOutput(BaseModel):
    """Output schema"""
    readme: str = Field(default="", description="README content")
    api_docs: str = Field(default="", description="API docs content")


class DocGeneratorTool(BaseTool):
    """Generate documentation"""
    
    name: str = "doc_generator"
    description: str = "Perform Generate documentation"
    
    llm: Optional[ChatOpenAI] = None
    
    def __init__(self, llm: Optional[ChatOpenAI] = None, **kwargs):
        super().__init__(**kwargs)
        self.llm = llm or ChatOpenAI(model="gpt-4", temperature=0.3)
    
    def _run(self, project_info: Dict[str, Any], code_files: List[Dict[str, Any]], api_design: Dict[str, Any], run_manager=None) -> Dict[str, Any]:
        """Execute"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert. Analyze and provide structured JSON output."),
            ("human", "Please analyze the input and provide structured output.")
        ])
        
        structured_llm = self.llm.with_structured_output(DocGeneratorToolOutput)
        chain = prompt | structured_llm
        
        try:
            result = chain.invoke({"project_info": json.dumps(project_info, ensure_ascii=False), "code_files": json.dumps(code_files, ensure_ascii=False), "api_design": json.dumps(api_design, ensure_ascii=False)})
            return result.model_dump()
        except:
            try:
                raw_chain = prompt | self.llm
                raw_result = raw_chain.invoke({"project_info": json.dumps(project_info, ensure_ascii=False), "code_files": json.dumps(code_files, ensure_ascii=False), "api_design": json.dumps(api_design, ensure_ascii=False)})
                return json.loads(raw_result.content)
            except:
                return {"readme": "", "api_docs": ""}
    
    async def _arun(self, project_info: Dict[str, Any], code_files: List[Dict[str, Any]], api_design: Dict[str, Any], run_manager=None) -> Dict[str, Any]:
        """Async execute"""
        import asyncio
        return await asyncio.to_thread(self._run, project_info, code_files, api_design)
