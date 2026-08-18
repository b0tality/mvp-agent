"""
需求分析工具集
"""

from typing import Dict, Any, List
from tools.base import BaseTool
from schemas import RequirementsOutput


class RequirementParserTool(BaseTool):
    """需求解析工具"""

    name = "requirement_parser"
    description = "解析用户自然语言需求，提取结构化信息"

    async def run(self, **kwargs) -> Dict[str, Any]:
        user_input = kwargs.get("user_input", "")
        system_prompt = """你是一位资深需求分析师。请分析用户需求，提取结构化信息。

输出必须包含：
- functional_requirements: 功能需求列表，每个元素包含id, title, description
- non_functional_requirements: 非功能需求列表，每个元素包含id, title, description
- constraints: 约束条件列表
- assumptions: 假设条件列表
- risks: 风险点列表"""
        
        result = await self.llm.generate_structured(
            system_prompt, f"请分析以下用户需求：\n{user_input}", RequirementsOutput
        )
        return result.model_dump()


class UserStoryGeneratorTool(BaseTool):
    """用户故事生成工具"""

    name = "user_story_generator"
    description = "根据需求生成用户故事"

    async def run(self, **kwargs) -> Dict[str, Any]:
        requirements = kwargs.get("requirements", {})
        system_prompt = """你是一位资深需求分析师。请根据需求生成用户故事。

每个用户故事包含：id, role, feature, benefit"""
        
        from schemas import UserStory
        from pydantic import BaseModel
        
        class UserStoryList(BaseModel):
            user_stories: List[UserStory]
        
        result = await self.llm.generate_structured(
            system_prompt,
            f"请根据以下需求生成用户故事：\n{requirements}",
            UserStoryList
        )
        return result.model_dump()


class AcceptanceCriteriaTool(BaseTool):
    """验收标准生成工具"""

    name = "acceptance_criteria_generator"
    description = "根据原始需求生成可执行、可验证的验收标准"

    async def run(self, **kwargs) -> Dict[str, Any]:
        user_stories = kwargs.get("user_stories", [])
        requirements = kwargs.get("requirements", {})
        user_input = kwargs.get("user_input", "")
        system_prompt = """你是一位资深测试工程师。请根据原始需求生成可执行、可验证的验收标准。

硬性要求：
1. 每个验收标准包含：id, story_id, description
2. 必须保留原始需求里的具体可验证细节：状态码（如 400/404）、字段名、边界值、精确行为。禁止把「非数字输入返回 400」泛化成「返回错误提示」这类模糊描述。
3. 每条验收标准要能被一段代码或一个 HTTP 请求客观判断通过/不通过。
4. 覆盖所有功能需求，尤其是错误处理和边界条件。"""

        from schemas import AcceptanceCriterion
        from pydantic import BaseModel

        class CriteriaList(BaseModel):
            acceptance_criteria: List[AcceptanceCriterion]

        result = await self.llm.generate_structured(
            system_prompt,
            f"原始需求：{user_input}\n\n结构化需求：{requirements}\n\n用户故事：{user_stories}",
            CriteriaList
        )
        return result.model_dump()


class PriorityCalculatorTool(BaseTool):
    """优先级计算工具"""

    name = "priority_calculator"
    description = "使用MoSCoW方法对需求进行优先级排序"

    async def run(self, **kwargs) -> Dict[str, Any]:
        requirements = kwargs.get("requirements", {})
        system_prompt = """你是一位资深项目经理。请使用MoSCoW方法对需求进行优先级排序。

输出包含：must_have, should_have, could_have, wont_have 四个列表，每个元素是需求ID。"""
        
        from schemas import PriorityMatrix
        
        result = await self.llm.generate_structured(
            system_prompt,
            f"请对以下需求进行优先级排序：\n{requirements}",
            PriorityMatrix
        )
        return result.model_dump()
