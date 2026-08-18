"""
技术方案工具集
"""

from typing import Dict, Any, List
from tools.base import BaseTool
from schemas import TechnicalOutput


class ArchitectureDesignerTool(BaseTool):
    """架构设计工具"""
    name = "architecture_designer"
    description = "设计系统架构"

    async def run(self, **kwargs) -> Dict[str, Any]:
        requirements = kwargs.get("requirements", {})
        result = await self.llm.generate_structured(
            "你是一位资深系统架构师。请根据需求设计系统架构。",
            f"需求：{requirements}",
            TechnicalOutput
        )
        return result.model_dump()


class TechStackSelectorTool(BaseTool):
    """技术栈选择工具"""
    name = "tech_stack_selector"
    description = "选择合适的技术栈"

    async def run(self, **kwargs) -> Dict[str, Any]:
        requirements = kwargs.get("requirements", {})
        from schemas import TechStack
        result = await self.llm.generate_structured(
            "你是一位资深技术顾问。请根据需求选择技术栈。",
            f"需求：{requirements}",
            TechStack
        )
        return result.model_dump()


class APIDesignerTool(BaseTool):
    """API设计工具"""
    name = "api_designer"
    description = "设计RESTful API"

    async def run(self, **kwargs) -> Dict[str, Any]:
        requirements = kwargs.get("requirements", {})
        from schemas import APIDesign
        result = await self.llm.generate_structured(
            "你是一位资深API架构师。请设计RESTful API。",
            f"需求：{requirements}",
            APIDesign
        )
        return result.model_dump()


class DatabaseDesignerTool(BaseTool):
    """数据库设计工具"""
    name = "database_designer"
    description = "设计数据库schema"

    async def run(self, **kwargs) -> Dict[str, Any]:
        requirements = kwargs.get("requirements", {})
        from schemas import DatabaseDesign
        result = await self.llm.generate_structured(
            "你是一位资深数据库架构师。请设计数据库schema。",
            f"需求：{requirements}",
            DatabaseDesign
        )
        return result.model_dump()


class SecurityDesignerTool(BaseTool):
    """安全设计工具"""
    name = "security_designer"
    description = "设计安全方案"

    async def run(self, **kwargs) -> Dict[str, Any]:
        requirements = kwargs.get("requirements", {})
        from schemas import SecurityDesign
        result = await self.llm.generate_structured(
            "你是一位资深安全架构师。请设计安全方案。",
            f"需求：{requirements}",
            SecurityDesign
        )
        return result.model_dump()


class CostEstimatorTool(BaseTool):
    """成本估算工具"""
    name = "cost_estimator"
    description = "估算项目成本"

    async def run(self, **kwargs) -> Dict[str, Any]:
        requirements = kwargs.get("requirements", {})
        from schemas import CostEstimation
        result = await self.llm.generate_structured(
            "你是一位资深项目经理。请估算项目成本。",
            f"需求：{requirements}",
            CostEstimation
        )
        return result.model_dump()
