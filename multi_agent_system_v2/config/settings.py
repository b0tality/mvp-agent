"""
配置管理
"""

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PipelineConfig:
    """流水线配置"""
    model: str = "mimo-v2.5"
    api_key: str = ""
    base_url: str = "https://api.xiaomimimo.com/v1"
    max_consecutive_failures: int = 2
    persistence_path: Optional[str] = None

    @classmethod
    def from_env(cls) -> "PipelineConfig":
        """从环境变量加载配置"""
        return cls(
            model=os.getenv("LOCAL_LLM_MODEL", "mimo-v2.5"),
            api_key=os.getenv("LOCAL_LLM_API_KEY", ""),
            base_url=os.getenv("LOCAL_LLM_BASE_URL", "https://api.xiaomimimo.com/v1"),
        )
