"""
智能体3：MVP实现
负责最小可行产品开发，包括代码生成、优化、测试和文档
"""

from .agent import MVPDeveloperAgent
from .state import MVPState, MVPStateManager

__all__ = ["MVPDeveloperAgent", "MVPState", "MVPStateManager"]
