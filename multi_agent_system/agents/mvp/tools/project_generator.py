"""
Generate project structure
"""

from typing import Dict, List, Any, Optional
from langchain.tools import BaseTool
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
import json


class ProjectGeneratorToolOutput(BaseModel):
    """Output schema"""
    directories: List[str] = Field(default_factory=list, description="Directories")
    files: List[str] = Field(default_factory=list, description="Files")


class ProjectGeneratorTool(BaseTool):
    """Generate project structure"""
    
    name: str = "project_generator"
    description: str = "Perform Generate project structure"
    
    llm: Optional[ChatOpenAI] = None
    
    def __init__(self, llm: Optional[ChatOpenAI] = None, **kwargs):
        super().__init__(**kwargs)
        self.llm = llm or ChatOpenAI(model="gpt-4", temperature=0.3)
    
    def _run(self, requirements: Dict[str, Any], tech_stack: Dict[str, Any], run_manager=None) -> Dict[str, Any]:
        """Execute"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert. Analyze and provide structured JSON output."),
            ("human", "Please analyze the input and provide structured output.")
        ])
        
        structured_llm = self.llm.with_structured_output(ProjectGeneratorToolOutput)
        chain = prompt | structured_llm
        
        try:
            result = chain.invoke({"requirements": json.dumps(requirements, ensure_ascii=False), "tech_stack": json.dumps(tech_stack, ensure_ascii=False)})
            return result.model_dump()
        except:
            try:
                raw_chain = prompt | self.llm
                raw_result = raw_chain.invoke({"requirements": json.dumps(requirements, ensure_ascii=False), "tech_stack": json.dumps(tech_stack, ensure_ascii=False)})
                return json.loads(raw_result.content)
            except:
                return {"directories": [], "files": []}
    
    async def _arun(self, requirements: Dict[str, Any], tech_stack: Dict[str, Any], run_manager=None) -> Dict[str, Any]:
        """Async execute"""
        import asyncio
        return await asyncio.to_thread(self._run, requirements, tech_stack)
