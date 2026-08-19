"""
技术架构Agent
"""

import time
from typing import Dict, Any
from agents.base import BaseAgent, AgentResult
from llm.adapter import LLMAdapter
from schemas import TechnicalOutput


class TechnicalAgent(BaseAgent):
    """技术架构Agent"""

    name = "technical"

    def __init__(self, llm: LLMAdapter):
        super().__init__(llm)

    async def execute(self, **kwargs) -> AgentResult:
        requirements = kwargs.get("requirements", {})
        if not requirements:
            return self._error("缺少 requirements 参数")

        start = time.time()
        try:
            # 一次调用生成完整技术方案
            result = await self.llm.generate_structured(
                """你是一位资深技术架构师。请根据需求设计完整的技术方案。

硬性约束：
- 后端必须用 Python + FastAPI（我们只对 Python 做真实执行验证），主入口为 main.py 含 `app = FastAPI(...)`。
- 前端可用极简静态页面（HTML/JS），或纯 API（无前端）。
- 数据库如非必需，用内存/文件存储即可，避免引入外部依赖。
- 密码哈希/认证必须用 Python 标准库（hashlib.pbkdf2_hmac 或 hmac+hashlib+盐），
  **禁止选用 passlib/bcrypt**（passlib 与新版 bcrypt 不兼容）。JWT 可用 PyJWT 或手写 HMAC。
  尽量少引入第三方依赖，能 stdlib 就 stdlib。

要求：
1. 设计系统架构（选择合适的架构模式）
2. 选择技术栈（后端固定 Python/FastAPI）
3. 设计RESTful API（方法 + 路径 + 描述）
4. 设计数据库schema
5. 设计安全方案
6. 估算开发成本""",
                f"需求：{requirements}",
                TechnicalOutput
            )

            data = result.model_dump()
            return self._success(data, time.time() - start)
        except Exception as e:
            return self._error(str(e), time.time() - start)
