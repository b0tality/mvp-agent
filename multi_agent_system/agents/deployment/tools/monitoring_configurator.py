"""
Configure monitoring
"""

from typing import Dict, List, Any, Optional
from langchain.tools import BaseTool
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
import json


class MonitoringConfiguratorToolOutput(BaseModel):
    """Output schema"""
    prometheus: Dict[str, Any] = Field(default_factory=dict, description="Prometheus config")
    grafana: Dict[str, Any] = Field(default_factory=dict, description="Grafana config")
    alerts: List[Dict[str, Any]] = Field(default_factory=list, description="Alert rules")


class MonitoringConfiguratorTool(BaseTool):
    """Configure monitoring"""
    
    name: str = "monitoring_configurator"
    description: str = "Perform Configure monitoring"
    
    llm: Optional[ChatOpenAI] = None
    
    def __init__(self, llm: Optional[ChatOpenAI] = None, **kwargs):
        super().__init__(**kwargs)
        self.llm = llm or ChatOpenAI(model="gpt-4", temperature=0.3)
    
    def _run(self, deployment_plan: Dict[str, Any], infrastructure: Dict[str, Any], run_manager=None) -> Dict[str, Any]:
        """Execute"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert. Analyze and provide structured JSON output."),
            ("human", "Please analyze the input and provide structured output.")
        ])
        
        structured_llm = self.llm.with_structured_output(MonitoringConfiguratorToolOutput)
        chain = prompt | structured_llm
        
        try:
            result = chain.invoke({"deployment_plan": json.dumps(deployment_plan, ensure_ascii=False), "infrastructure": json.dumps(infrastructure, ensure_ascii=False)})
            return result.model_dump()
        except:
            try:
                raw_chain = prompt | self.llm
                raw_result = raw_chain.invoke({"deployment_plan": json.dumps(deployment_plan, ensure_ascii=False), "infrastructure": json.dumps(infrastructure, ensure_ascii=False)})
                return json.loads(raw_result.content)
            except:
                return {"prometheus": {}, "grafana": {}, "alerts": []}
    
    async def _arun(self, deployment_plan: Dict[str, Any], infrastructure: Dict[str, Any], run_manager=None) -> Dict[str, Any]:
        """Async execute"""
        import asyncio
        return await asyncio.to_thread(self._run, deployment_plan, infrastructure)
