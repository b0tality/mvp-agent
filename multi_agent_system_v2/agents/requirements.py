"""
需求分析Agent
"""

import time
from typing import Dict, Any
from agents.base import BaseAgent, AgentResult
from llm.adapter import LLMAdapter
from tools.requirements_tools import (
    RequirementParserTool,
    UserStoryGeneratorTool,
    AcceptanceCriteriaTool,
    PriorityCalculatorTool,
)


class RequirementsAgent(BaseAgent):
    """
    需求分析Agent
    
    职责：
    1. 解析用户需求
    2. 生成用户故事
    3. 生成验收标准
    4. 优先级排序
    """

    name = "requirements"

    def __init__(self, llm: LLMAdapter):
        super().__init__(llm)
        self.parser = RequirementParserTool(llm)
        self.story_gen = UserStoryGeneratorTool(llm)
        self.criteria_gen = AcceptanceCriteriaTool(llm)
        self.priority_calc = PriorityCalculatorTool(llm)

    async def execute(self, **kwargs) -> AgentResult:
        """
        执行需求分析
        
        kwargs:
            user_input: 用户输入的需求描述
        """
        user_input = kwargs.get("user_input", "")
        if not user_input:
            return self._error("缺少 user_input 参数")

        start = time.time()

        try:
            # 1. 解析需求
            parsed = await self.parser.run(user_input=user_input)

            # 2. 生成用户故事
            stories = await self.story_gen.run(requirements=parsed)

            # 3. 生成验收标准（锚定原始需求，保留可验证细节）
            criteria = await self.criteria_gen.run(
                user_stories=stories.get("user_stories", []),
                requirements=parsed,
                user_input=user_input,
            )

            # 4. 优先级排序
            priority = await self.priority_calc.run(requirements=parsed)

            duration = time.time() - start

            # 合并结果
            data = {
                **parsed,
                "user_stories": stories.get("user_stories", []),
                "acceptance_criteria": criteria.get("acceptance_criteria", []),
                "priority_matrix": priority,
            }

            return self._success(data, duration)

        except Exception as e:
            return self._error(str(e), time.time() - start)
