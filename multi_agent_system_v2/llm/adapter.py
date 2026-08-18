"""
LLM适配器抽象基类
解决V1的外部依赖耦合问题：Agent不直接依赖langchain/openai，只依赖此接口
"""

from abc import ABC, abstractmethod
from typing import Type, TypeVar, Optional
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLMAdapter(ABC):
    """
    LLM适配器抽象基类
    
    所有LLM交互通过此接口，Agent层不直接依赖任何LLM库。
    换LLM provider只需实现新的Adapter，不改Agent代码。
    """

    @abstractmethod
    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        """
        生成文本响应
        
        Args:
            system_prompt: 系统提示词
            user_prompt: 用户提示词
            
        Returns:
            LLM生成的文本
        """
        pass

    @abstractmethod
    async def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        output_schema: Type[T],
    ) -> T:
        """
        生成结构化响应（强制Schema输出）
        
        使用API的response_format约束输出格式，保证返回值符合Schema。
        不靠Prompt约束，靠API层强制。
        
        Args:
            system_prompt: 系统提示词
            user_prompt: 用户提示词
            output_schema: Pydantic模型类，定义输出格式
            
        Returns:
            符合Schema的Pydantic模型实例
        """
        pass
