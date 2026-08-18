"""
多智能体应用开发系统
"""

from .agents.requirements import RequirementsAgent
from .agents.technical import TechnicalAgent
from .agents.mvp import MVPDeveloperAgent
from .agents.code_review import CodeReviewAgent
from .agents.testing import TestingAgent
from .agents.deployment import DeploymentAgent
from .config.settings import get_default_config, SystemConfig

__version__ = "1.0.0"
__all__ = [
    "RequirementsAgent",
    "TechnicalAgent",
    "MVPDeveloperAgent",
    "CodeReviewAgent",
    "TestingAgent",
    "DeploymentAgent",
    "get_default_config",
    "SystemConfig"
]
