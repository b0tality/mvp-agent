"""
LLM抽象层：适配器模式隔离LLM依赖
"""

from .adapter import LLMAdapter
from .openai_adapter import OpenAIAdapter

__all__ = ["LLMAdapter", "OpenAIAdapter"]
