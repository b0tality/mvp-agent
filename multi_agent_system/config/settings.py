"""
多智能体应用开发系统 - 配置管理模块

提供类型安全的配置管理，支持从环境变量和 .env 文件加载配置。
"""

import os
from typing import Optional, List, Dict, Any
from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings
from pydantic.networks import AnyHttpUrl


# ============================================================================
# 应用基础配置
# ============================================================================

class AppSettings(BaseSettings):
    """应用基础配置"""
    
    name: str = Field(default="multi-agent-system", alias="APP_NAME")
    version: str = Field(default="1.0.0", alias="APP_VERSION")
    environment: str = Field(default="development", alias="ENVIRONMENT")
    debug: bool = Field(default=True, alias="DEBUG")
    host: str = Field(default="0.0.0.0", alias="APP_HOST")
    port: int = Field(default=8000, alias="APP_PORT")
    workers: int = Field(default=4, alias="WORKERS")
    
    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        allowed = ["development", "staging", "production"]
        if v not in allowed:
            raise ValueError(f"environment must be one of {allowed}")
        return v
    
    @property
    def is_development(self) -> bool:
        return self.environment == "development"
    
    @property
    def is_staging(self) -> bool:
        return self.environment == "staging"
    
    @property
    def is_production(self) -> bool:
        return self.environment == "production"
    
    class Config:
        env_prefix = "APP_"
        case_sensitive = False


# ============================================================================
# OpenAI 配置
# ============================================================================

class OpenAISettings(BaseSettings):
    """OpenAI 配置"""
    
    api_key: str = Field(..., alias="OPENAI_API_KEY")
    model: str = Field(default="gpt-4", alias="OPENAI_MODEL")
    temperature: float = Field(default=0.3, alias="OPENAI_TEMPERATURE")
    max_tokens: int = Field(default=4000, alias="OPENAI_MAX_TOKENS")
    timeout: int = Field(default=60, alias="OPENAI_TIMEOUT")
    max_retries: int = Field(default=3, alias="OPENAI_MAX_RETRIES")
    org_id: Optional[str] = Field(default=None, alias="OPENAI_ORG_ID")
    
    @field_validator("temperature")
    @classmethod
    def validate_temperature(cls, v: float) -> float:
        if not 0.0 <= v <= 2.0:
            raise ValueError("temperature must be between 0.0 and 2.0")
        return v
    
    @field_validator("max_tokens")
    @classmethod
    def validate_max_tokens(cls, v: int) -> int:
        if v < 1:
            raise ValueError("max_tokens must be positive")
        return v
    
    @field_validator("api_key")
    @classmethod
    def validate_api_key(cls, v: str) -> str:
        if not v or v == "your-openai-api-key-here":
            raise ValueError("OPENAI_API_KEY must be set")
        return v
    
    class Config:
        env_prefix = "OPENAI_"
        case_sensitive = False


# ============================================================================
# 本地LLM配置 (MiMo)
# ============================================================================

class LocalLLMSettings(BaseSettings):
    """本地LLM配置 (MiMo)"""
    
    api_key: str = Field(default="sk-placeholder", alias="LOCAL_LLM_API_KEY")
    base_url: str = Field(default="http://localhost:8000/v1", alias="LOCAL_LLM_BASE_URL")
    model: str = Field(default="mimo", alias="LOCAL_LLM_MODEL")
    temperature: float = Field(default=0.3, alias="LOCAL_LLM_TEMPERATURE")
    max_tokens: int = Field(default=4000, alias="LOCAL_LLM_MAX_TOKENS")
    timeout: int = Field(default=120, alias="LOCAL_LLM_TIMEOUT")
    max_retries: int = Field(default=3, alias="LOCAL_LLM_MAX_RETRIES")
    
    @field_validator("temperature")
    @classmethod
    def validate_temperature(cls, v: float) -> float:
        if not 0.0 <= v <= 2.0:
            raise ValueError("temperature must be between 0.0 and 2.0")
        return v
    
    @field_validator("max_tokens")
    @classmethod
    def validate_max_tokens(cls, v: int) -> int:
        if v < 1:
            raise ValueError("max_tokens must be positive")
        return v
    
    class Config:
        env_prefix = "LOCAL_LLM_"
        case_sensitive = False


# ============================================================================
# 数据库配置
# ============================================================================

class DatabaseSettings(BaseSettings):
    """数据库配置"""
    
    host: str = Field(default="localhost", alias="POSTGRES_HOST")
    port: int = Field(default=5432, alias="POSTGRES_PORT")
    user: str = Field(default="postgres", alias="POSTGRES_USER")
    password: str = Field(default="postgres", alias="POSTGRES_PASSWORD")
    database: str = Field(default="multi_agent_dev", alias="POSTGRES_DB")
    url: Optional[str] = Field(default=None, alias="DATABASE_URL")
    
    # 连接池配置
    pool_size: int = Field(default=20, alias="DB_POOL_SIZE")
    max_overflow: int = Field(default=10, alias="DB_MAX_OVERFLOW")
    pool_timeout: int = Field(default=30, alias="DB_POOL_TIMEOUT")
    pool_recycle: int = Field(default=1800, alias="DB_POOL_RECYCLE")
    
    @property
    def database_url(self) -> str:
        """获取数据库连接 URL"""
        if self.url:
            return self.url
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
    
    @property
    def async_database_url(self) -> str:
        """获取异步数据库连接 URL"""
        url = self.database_url
        return url.replace("postgresql://", "postgresql+asyncpg://")
    
    class Config:
        env_prefix = ""
        case_sensitive = False


# ============================================================================
# Redis 配置
# ============================================================================

class RedisSettings(BaseSettings):
    """Redis 配置"""
    
    host: str = Field(default="localhost", alias="REDIS_HOST")
    port: int = Field(default=6379, alias="REDIS_PORT")
    password: Optional[str] = Field(default=None, alias="REDIS_PASSWORD")
    db: int = Field(default=0, alias="REDIS_DB")
    url: Optional[str] = Field(default=None, alias="REDIS_URL")
    max_connections: int = Field(default=50, alias="REDIS_MAX_CONNECTIONS")
    
    @property
    def redis_url(self) -> str:
        """获取 Redis 连接 URL"""
        if self.url:
            return self.url
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"
    
    class Config:
        env_prefix = "REDIS_"
        case_sensitive = False


# ============================================================================
# Celery 配置
# ============================================================================

class CelerySettings(BaseSettings):
    """Celery 配置"""
    
    broker_url: str = Field(default="redis://localhost:6379/1", alias="CELERY_BROKER_URL")
    result_backend: str = Field(default="redis://localhost:6379/2", alias="CELERY_RESULT_BACKEND")
    task_serializer: str = Field(default="json", alias="CELERY_TASK_SERIALIZER")
    result_serializer: str = Field(default="json", alias="CELERY_RESULT_SERIALIZER")
    task_expires: int = Field(default=3600, alias="CELERY_TASK_EXPIRES")
    concurrency: int = Field(default=4, alias="CELERY_CONCURRENCY")
    
    class Config:
        env_prefix = "CELERY_"
        case_sensitive = False


# ============================================================================
# 日志配置
# ============================================================================

class LogSettings(BaseSettings):
    """日志配置"""
    
    level: str = Field(default="INFO", alias="LOG_LEVEL")
    file: str = Field(default="./logs/system.log", alias="LOG_FILE")
    format: str = Field(default="%(asctime)s - %(name)s - %(levelname)s - %(message)s", alias="LOG_FORMAT")
    rotation_size: int = Field(default=10, alias="LOG_ROTATION_SIZE")
    retention_days: int = Field(default=30, alias="LOG_RETENTION_DAYS")
    json_format: bool = Field(default=False, alias="LOG_JSON_FORMAT")
    
    @field_validator("level")
    @classmethod
    def validate_level(cls, v: str) -> str:
        allowed = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed:
            raise ValueError(f"log level must be one of {allowed}")
        return v.upper()
    
    class Config:
        env_prefix = "LOG_"
        case_sensitive = False


# ============================================================================
# 安全配置
# ============================================================================

class SecuritySettings(BaseSettings):
    """安全配置"""
    
    jwt_secret_key: str = Field(default="your-jwt-secret-key-change-in-production", alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(default=30, alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")
    jwt_refresh_token_expire_days: int = Field(default=7, alias="JWT_REFRESH_TOKEN_EXPIRE_DAYS")
    
    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:8000",
        alias="CORS_ORIGINS"
    )
    cors_methods: str = Field(
        default="GET,POST,PUT,DELETE,OPTIONS",
        alias="CORS_METHODS"
    )
    cors_headers: str = Field(default="*", alias="CORS_HEADERS")
    
    sandbox_enabled: bool = Field(default=True, alias="SANDBOX_ENABLED")
    max_execution_time: int = Field(default=300, alias="MAX_EXECUTION_TIME")
    allowed_file_extensions: str = Field(
        default=".py,.js,.ts,.json,.yaml,.yml,.md,.txt",
        alias="ALLOWED_FILE_EXTENSIONS"
    )
    max_file_size: int = Field(default=10, alias="MAX_FILE_SIZE")  # MB
    
    @property
    def cors_origins_list(self) -> List[str]:
        """获取CORS origins列表"""
        return [i.strip() for i in self.cors_origins.split(",") if i.strip()]
    
    @property
    def cors_methods_list(self) -> List[str]:
        """获取CORS methods列表"""
        return [i.strip() for i in self.cors_methods.split(",") if i.strip()]
    
    @property
    def allowed_file_extensions_list(self) -> List[str]:
        """获取允许的文件扩展名列表"""
        return [i.strip() for i in self.allowed_file_extensions.split(",") if i.strip()]
    
    @field_validator("jwt_secret_key")
    @classmethod
    def validate_jwt_secret(cls, v: str) -> str:
        if v == "your-jwt-secret-key-change-in-production":
            import warnings
            warnings.warn("JWT_SECRET_KEY is using default value. Change it in production!")
        return v
    
    class Config:
        env_prefix = ""
        case_sensitive = False


# ============================================================================
# 状态管理配置
# ============================================================================

class StateSettings(BaseSettings):
    """状态管理配置"""
    
    persistence: bool = Field(default=True, alias="STATE_PERSISTENCE")
    storage: str = Field(default="./data/states", alias="STATE_STORAGE")
    expiry_days: int = Field(default=30, alias="STATE_EXPIRY_DAYS")
    
    @property
    def storage_path(self) -> Path:
        """获取存储路径"""
        return Path(self.storage)
    
    class Config:
        env_prefix = "STATE_"
        case_sensitive = False


# ============================================================================
# 成本控制配置
# ============================================================================

class CostControlSettings(BaseSettings):
    """成本控制配置"""
    
    max_tokens_per_request: int = Field(default=8000, alias="MAX_TOKENS_PER_REQUEST")
    max_requests_per_minute: int = Field(default=60, alias="MAX_REQUESTS_PER_MINUTE")
    max_requests_per_day: int = Field(default=1000, alias="MAX_REQUESTS_PER_DAY")
    monthly_budget: float = Field(default=1000.0, alias="MONTHLY_BUDGET")
    budget_warning_threshold: int = Field(default=80, alias="BUDGET_WARNING_THRESHOLD")
    budget_exceed_action: str = Field(default="warn", alias="BUDGET_EXCEED_ACTION")
    
    @field_validator("budget_exceed_action")
    @classmethod
    def validate_exceed_action(cls, v: str) -> str:
        allowed = ["warn", "block"]
        if v not in allowed:
            raise ValueError(f"budget_exceed_action must be one of {allowed}")
        return v
    
    class Config:
        env_prefix = ""
        case_sensitive = False


# ============================================================================
# 智能体配置
# ============================================================================

class AgentModelConfig(BaseSettings):
    """单个智能体模型配置"""
    
    model: str = Field(default="gpt-4")
    temperature: float = Field(default=0.3)
    max_tokens: int = Field(default=4000)
    
    class Config:
        case_sensitive = False


class AgentSettings(BaseSettings):
    """智能体配置"""
    
    # 各智能体配置
    requirements: AgentModelConfig = Field(default_factory=lambda: AgentModelConfig(
        model="gpt-4", temperature=0.3, max_tokens=4000
    ))
    technical: AgentModelConfig = Field(default_factory=lambda: AgentModelConfig(
        model="gpt-4", temperature=0.2, max_tokens=6000
    ))
    mvp: AgentModelConfig = Field(default_factory=lambda: AgentModelConfig(
        model="gpt-4", temperature=0.4, max_tokens=8000
    ))
    code_review: AgentModelConfig = Field(default_factory=lambda: AgentModelConfig(
        model="gpt-4", temperature=0.1, max_tokens=4000
    ))
    testing: AgentModelConfig = Field(default_factory=lambda: AgentModelConfig(
        model="gpt-4", temperature=0.1, max_tokens=4000
    ))
    deployment: AgentModelConfig = Field(default_factory=lambda: AgentModelConfig(
        model="gpt-4", temperature=0.2, max_tokens=4000
    ))
    
    # 通用配置
    max_iterations: int = Field(default=10, alias="AGENT_MAX_ITERATIONS")
    verbose: bool = Field(default=True, alias="AGENT_VERBOSE")
    
    def get_agent_config(self, agent_name: str) -> AgentModelConfig:
        """获取指定智能体的配置"""
        return getattr(self, agent_name, self.requirements)
    
    class Config:
        env_prefix = ""
        case_sensitive = False


# ============================================================================
# 监控配置
# ============================================================================

class MonitoringSettings(BaseSettings):
    """监控配置"""
    
    prometheus_port: int = Field(default=9090, alias="PROMETHEUS_PORT")
    metrics_enabled: bool = Field(default=True, alias="METRICS_ENABLED")
    metrics_path: str = Field(default="/metrics", alias="METRICS_PATH")
    
    grafana_port: int = Field(default=3000, alias="GRAFANA_PORT")
    grafana_user: str = Field(default="admin", alias="GRAFANA_USER")
    grafana_password: str = Field(default="admin", alias="GRAFANA_PASSWORD")
    
    flower_port: int = Field(default=5555, alias="FLOWER_PORT")
    flower_user: str = Field(default="admin", alias="FLOWER_USER")
    flower_password: str = Field(default="admin", alias="FLOWER_PASSWORD")
    
    class Config:
        env_prefix = ""
        case_sensitive = False


# ============================================================================
# 通知配置
# ============================================================================

class NotificationSettings(BaseSettings):
    """通知配置"""
    
    slack_webhook_url: Optional[str] = Field(default=None, alias="SLACK_WEBHOOK_URL")
    discord_webhook_url: Optional[str] = Field(default=None, alias="DISCORD_WEBHOOK_URL")
    sentry_dsn: Optional[str] = Field(default=None, alias="SENTRY_DSN")
    
    # 邮件配置
    smtp_host: str = Field(default="smtp.gmail.com", alias="SMTP_HOST")
    smtp_port: int = Field(default=587, alias="SMTP_PORT")
    smtp_user: Optional[str] = Field(default=None, alias="SMTP_USER")
    smtp_password: Optional[str] = Field(default=None, alias="SMTP_PASSWORD")
    email_from_name: str = Field(default="Multi-Agent System", alias="EMAIL_FROM_NAME")
    email_from_address: Optional[str] = Field(default=None, alias="EMAIL_FROM_ADDRESS")
    
    class Config:
        env_prefix = ""
        case_sensitive = False


# ============================================================================
# 云服务配置
# ============================================================================

class AWSSettings(BaseSettings):
    """AWS 配置"""
    
    access_key_id: Optional[str] = Field(default=None, alias="AWS_ACCESS_KEY_ID")
    secret_access_key: Optional[str] = Field(default=None, alias="AWS_SECRET_ACCESS_KEY")
    region: str = Field(default="us-east-1", alias="AWS_REGION")
    s3_bucket: Optional[str] = Field(default=None, alias="AWS_S3_BUCKET")
    
    class Config:
        env_prefix = "AWS_"
        case_sensitive = False


class AzureSettings(BaseSettings):
    """Azure 配置"""
    
    subscription_id: Optional[str] = Field(default=None, alias="AZURE_SUBSCRIPTION_ID")
    resource_group: Optional[str] = Field(default=None, alias="AZURE_RESOURCE_GROUP")
    location: str = Field(default="eastus", alias="AZURE_LOCATION")
    
    class Config:
        env_prefix = "AZURE_"
        case_sensitive = False


class GCPSettings(BaseSettings):
    """GCP 配置"""
    
    project_id: Optional[str] = Field(default=None, alias="GCP_PROJECT_ID")
    region: str = Field(default="us-central1", alias="GCP_REGION")
    
    class Config:
        env_prefix = "GCP_"
        case_sensitive = False


class CloudSettings(BaseSettings):
    """云服务配置"""
    
    aws: AWSSettings = Field(default_factory=AWSSettings)
    azure: AzureSettings = Field(default_factory=AzureSettings)
    gcp: GCPSettings = Field(default_factory=GCPSettings)
    
    class Config:
        case_sensitive = False


# ============================================================================
# 开发工具配置
# ============================================================================

class DevToolsSettings(BaseSettings):
    """开发工具配置"""
    
    hot_reload: bool = Field(default=True, alias="HOT_RELOAD")
    debugger_enabled: bool = Field(default=True, alias="DEBUGGER_ENABLED")
    debugger_port: int = Field(default=5678, alias="DEBUGGER_PORT")
    docs_enabled: bool = Field(default=True, alias="DOCS_ENABLED")
    docs_url: str = Field(default="/docs", alias="DOCS_URL")
    redoc_url: str = Field(default="/redoc", alias="REDOC_URL")
    
    class Config:
        env_prefix = ""
        case_sensitive = False


# ============================================================================
# LangSmith 配置
# ============================================================================

class LangSmithSettings(BaseSettings):
    """LangSmith 配置"""
    
    tracing_v2: bool = Field(default=False, alias="LANGCHAIN_TRACING_V2")
    api_key: Optional[str] = Field(default=None, alias="LANGCHAIN_API_KEY")
    project: str = Field(default="multi-agent-system", alias="LANGCHAIN_PROJECT")
    
    class Config:
        env_prefix = "LANGCHAIN_"
        case_sensitive = False


# ============================================================================
# 主配置类
# ============================================================================

class Settings(BaseSettings):
    """主配置类"""
    
    # 应用配置
    app: AppSettings = Field(default_factory=AppSettings)
    
    # OpenAI 配置 (注释掉，使用本地LLM)
    # openai: OpenAISettings = Field(default_factory=lambda: OpenAISettings(api_key="sk-placeholder"))
    
    # 本地LLM配置 (MiMo)
    local_llm: LocalLLMSettings = Field(default_factory=LocalLLMSettings)
    
    # 数据库配置
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    
    # Redis 配置
    redis: RedisSettings = Field(default_factory=RedisSettings)
    
    # Celery 配置
    celery: CelerySettings = Field(default_factory=CelerySettings)
    
    # 日志配置
    log: LogSettings = Field(default_factory=LogSettings)
    
    # 安全配置
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    
    # 状态管理配置
    state: StateSettings = Field(default_factory=StateSettings)
    
    # 成本控制配置
    cost: CostControlSettings = Field(default_factory=CostControlSettings)
    
    # 智能体配置
    agents: AgentSettings = Field(default_factory=AgentSettings)
    
    # 监控配置
    monitoring: MonitoringSettings = Field(default_factory=MonitoringSettings)
    
    # 通知配置
    notification: NotificationSettings = Field(default_factory=NotificationSettings)
    
    # 云服务配置
    cloud: CloudSettings = Field(default_factory=CloudSettings)
    
    # 开发工具配置
    dev_tools: DevToolsSettings = Field(default_factory=DevToolsSettings)
    
    # LangSmith 配置
    langsmith: LangSmithSettings = Field(default_factory=LangSmithSettings)
    
    @model_validator(mode="after")
    def validate_settings(self) -> "Settings":
        """验证配置"""
        # 生产环境特定验证
        if self.app.is_production:
            if self.app.debug:
                import warnings
                warnings.warn("Debug mode is enabled in production environment!")
            if self.security.jwt_secret_key == "your-jwt-secret-key-change-in-production":
                raise ValueError("JWT_SECRET_KEY must be changed in production!")
        
        return self
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


# ============================================================================
# 配置缓存
# ============================================================================

@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()


def reload_settings() -> Settings:
    """重新加载配置"""
    get_settings.cache_clear()
    return get_settings()


# ============================================================================
# 便捷函数
# ============================================================================

def get_openai_config() -> Dict[str, Any]:
    """获取 OpenAI 配置字典"""
    settings = get_settings()
    return {
        "model": settings.openai.model,
        "temperature": settings.openai.temperature,
        "max_tokens": settings.openai.max_tokens,
        "api_key": settings.openai.api_key,
    }


def get_local_llm_config() -> Dict[str, Any]:
    """获取本地LLM配置字典"""
    settings = get_settings()
    return {
        "model": settings.local_llm.model,
        "temperature": settings.local_llm.temperature,
        "max_tokens": settings.local_llm.max_tokens,
        "api_key": settings.local_llm.api_key,
        "base_url": settings.local_llm.base_url,
    }


def get_agent_config(agent_name: str) -> Dict[str, Any]:
    """获取指定智能体的配置字典"""
    settings = get_settings()
    agent_config = settings.agents.get_agent_config(agent_name)
    # 使用本地LLM配置
    local_llm_config = get_local_llm_config()
    return {
        "model": local_llm_config["model"],
        "temperature": agent_config.temperature,
        "max_tokens": agent_config.max_tokens,
        "api_key": local_llm_config["api_key"],
        "base_url": local_llm_config["base_url"],
    }


def get_database_url() -> str:
    """获取数据库连接 URL"""
    settings = get_settings()
    return settings.database.database_url


def get_redis_url() -> str:
    """获取 Redis 连接 URL"""
    settings = get_settings()
    return settings.redis.redis_url


def is_development() -> bool:
    """是否为开发环境"""
    return get_settings().app.is_development


def is_production() -> bool:
    """是否为生产环境"""
    return get_settings().app.is_production


def get_default_config() -> Dict[str, Any]:
    """获取默认配置（用于流水线）"""
    settings = get_settings()
    local_llm_config = get_local_llm_config()
    return {
        "model": local_llm_config["model"],
        "temperature": local_llm_config["temperature"],
        "max_tokens": local_llm_config["max_tokens"],
        "api_key": local_llm_config["api_key"],
        "base_url": local_llm_config["base_url"],
    }


def get_requirements_agent_config() -> Dict[str, Any]:
    """获取需求分析智能体配置"""
    settings = reload_settings()  # 重新加载配置
    local_llm_config = get_local_llm_config()
    agent_config = settings.agents.requirements
    return {
        "model": local_llm_config["model"],
        "temperature": agent_config.temperature,
        "max_tokens": agent_config.max_tokens,
        "api_key": local_llm_config["api_key"],
        "base_url": local_llm_config["base_url"],
    }
