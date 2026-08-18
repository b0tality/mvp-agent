"""
流水线配置
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


@dataclass
class RetryConfig:
    """重试配置"""
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 30.0
    exponential_base: float = 2.0


@dataclass
class StageConfig:
    """阶段配置"""
    model: str = "mimo"
    temperature: float = 0.3
    max_tokens: int = 4000
    timeout: int = 180
    retry: RetryConfig = field(default_factory=RetryConfig)
    fallback_model: str = "mimo"
    fallback_timeout: int = 120
    fallback_retry: RetryConfig = field(default_factory=lambda: RetryConfig(max_retries=2))


@dataclass
class PipelineConfig:
    """流水线配置"""
    model: str = "mimo"
    max_retries: int = 3
    skip_stages: List[str] = field(default_factory=list)
    persistence_path: Optional[str] = None
    cost_limit: float = 1.0
    
    stage_configs: Dict[str, StageConfig] = field(default_factory=lambda: {
        "requirements": StageConfig(model="mimo", temperature=0.3, timeout=120),
        "technical": StageConfig(model="mimo", temperature=0.2, timeout=180),
        "mvp": StageConfig(model="mimo", temperature=0.4, timeout=300, max_tokens=8000),
        "code_review": StageConfig(model="mimo", temperature=0.1, timeout=180),
        "testing": StageConfig(model="mimo", temperature=0.2, timeout=240),
        "deployment": StageConfig(model="mimo", temperature=0.2, timeout=180),
    })
    
    critical_stages: List[str] = field(default_factory=lambda: ["requirements", "mvp"])
    skippable_stages: List[str] = field(default_factory=lambda: ["code_review", "deployment"])
    max_consecutive_failures: int = 2
    
    degradation_policies: Dict[str, str] = field(default_factory=lambda: {
        "requirements": "abort",
        "technical": "default",
        "mvp": "abort",
        "code_review": "skip",
        "testing": "skip",
        "deployment": "default"
    })
    
    def get_stage_config(self, stage: str) -> StageConfig:
        """获取阶段配置"""
        return self.stage_configs.get(stage, StageConfig())
    
    def should_skip(self, stage: str) -> bool:
        """检查是否跳过该阶段"""
        return stage in self.skip_stages
    
    def is_critical(self, stage: str) -> bool:
        """检查是否是关键阶段"""
        return stage in self.critical_stages
    
    def get_degradation_policy(self, stage: str) -> str:
        """获取降级策略"""
        return self.degradation_policies.get(stage, "abort")
