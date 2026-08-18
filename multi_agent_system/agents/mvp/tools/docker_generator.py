"""
Generate Docker config
"""

from typing import Dict, List, Any, Optional
from langchain.tools import BaseTool
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
import json


class DockerGeneratorToolOutput(BaseModel):
    """Output schema"""
    dockerfile: str = Field(default="", description="Dockerfile content")
    docker_compose: str = Field(default="", description="docker-compose content")


class DockerGeneratorTool(BaseTool):
    """Generate Docker config"""
    
    name: str = "docker_generator"
    description: str = "Perform Generate Docker config"
    
    llm: Optional[ChatOpenAI] = None
    
    def __init__(self, llm: Optional[ChatOpenAI] = None, **kwargs):
        super().__init__(**kwargs)
        self.llm = llm or ChatOpenAI(model="gpt-4", temperature=0.3)
    
    def _run(self, project_info: Dict[str, Any], tech_stack: Dict[str, Any], run_manager=None) -> Dict[str, Any]:
        """Execute"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert. Analyze and provide structured JSON output."),
            ("human", "Please analyze the input and provide structured output.")
        ])
        
        structured_llm = self.llm.with_structured_output(DockerGeneratorToolOutput)
        chain = prompt | structured_llm
        
        try:
            result = chain.invoke({"project_info": json.dumps(project_info, ensure_ascii=False), "tech_stack": json.dumps(tech_stack, ensure_ascii=False)})
            return result.model_dump()
        except:
            try:
                raw_chain = prompt | self.llm
                raw_result = raw_chain.invoke({"project_info": json.dumps(project_info, ensure_ascii=False), "tech_stack": json.dumps(tech_stack, ensure_ascii=False)})
                return json.loads(raw_result.content)
            except:
                return {"dockerfile": "", "docker_compose": ""}
    
    async def _arun(self, project_info: Dict[str, Any], tech_stack: Dict[str, Any], run_manager=None) -> Dict[str, Any]:
        """Async execute"""
        import asyncio
        return await asyncio.to_thread(self._run, project_info, tech_stack)
