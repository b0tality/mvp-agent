"""
工具抽象基类
解决V1的参数不匹配问题：所有工具统一用**kwargs
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
from llm.adapter import LLMAdapter


class BaseTool(ABC):
    """
    工具抽象基类
    
    所有工具实现此接口，统一用 **kwargs 接收参数。
    解决V1中 execute_with_fallback 用 *args 传参与函数签名不匹配的问题。
    """

    name: str = "base_tool"
    description: str = ""

    def __init__(self, llm: LLMAdapter):
        self.llm = llm

    @abstractmethod
    async def run(self, **kwargs) -> Dict[str, Any]:
        """
        执行工具
        
        Args:
            **kwargs: 工具参数（各工具自定义）
            
        Returns:
            工具执行结果字典
        """
        pass
