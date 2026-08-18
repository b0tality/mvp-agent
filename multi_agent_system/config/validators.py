"""
配置验证模块

提供配置验证功能，确保所有必需的配置都已正确设置。
"""

import os
import sys
from typing import List, Dict, Any, Tuple
from pathlib import Path

from .settings import get_settings, Settings


class ConfigValidator:
    """配置验证器"""
    
    def __init__(self, settings: Settings = None):
        self.settings = settings or get_settings()
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def validate_all(self) -> Tuple[bool, List[str], List[str]]:
        """验证所有配置"""
        self.errors = []
        self.warnings = []
        
        self._validate_required()
        self._validate_openai()
        self._validate_database()
        self._validate_redis()
        self._validate_security()
        self._validate_paths()
        self._validate_production()
        
        return len(self.errors) == 0, self.errors, self.warnings
    
    def _validate_required(self):
        """验证必需的配置"""
        # 检查 OpenAI API Key
        api_key = os.getenv("OPENAI_API_KEY", "")
        if not api_key or api_key == "your-openai-api-key-here":
            self.errors.append("OPENAI_API_KEY is not set or is using default value")
    
    def _validate_openai(self):
        """验证 OpenAI 配置"""
        try:
            openai = self.settings.openai
            
            # 检查模型
            valid_models = ["gpt-4", "gpt-4-turbo", "gpt-4-turbo-preview", "gpt-3.5-turbo"]
            if openai.model not in valid_models:
                self.warnings.append(f"OpenAI model '{openai.model}' is not in recommended list: {valid_models}")
            
            # 检查温度
            if openai.temperature < 0 or openai.temperature > 2:
                self.errors.append(f"OpenAI temperature must be between 0 and 2, got {openai.temperature}")
            
            # 检查 max_tokens
            if openai.max_tokens < 1:
                self.errors.append(f"OpenAI max_tokens must be positive, got {openai.max_tokens}")
            
        except Exception as e:
            self.errors.append(f"OpenAI configuration error: {e}")
    
    def _validate_database(self):
        """验证数据库配置"""
        try:
            db = self.settings.database
            
            # 检查连接 URL
            if not db.database_url:
                self.errors.append("Database URL is not configured")
            
            # 检查连接池配置
            if db.pool_size < 1:
                self.errors.append(f"Database pool_size must be positive, got {db.pool_size}")
            
            if db.max_overflow < 0:
                self.errors.append(f"Database max_overflow must be non-negative, got {db.max_overflow}")
            
        except Exception as e:
            self.errors.append(f"Database configuration error: {e}")
    
    def _validate_redis(self):
        """验证 Redis 配置"""
        try:
            redis = self.settings.redis
            
            # 检查连接 URL
            if not redis.redis_url:
                self.errors.append("Redis URL is not configured")
            
        except Exception as e:
            self.errors.append(f"Redis configuration error: {e}")
    
    def _validate_security(self):
        """验证安全配置"""
        try:
            security = self.settings.security
            
            # 检查 JWT 密钥
            if security.jwt_secret_key == "your-jwt-secret-key-change-in-production":
                if self.settings.app.is_production:
                    self.errors.append("JWT_SECRET_KEY must be changed in production!")
                else:
                    self.warnings.append("JWT_SECRET_KEY is using default value")
            
            # 检查 CORS 配置
            if "*" in security.cors_origins and self.settings.app.is_production:
                self.warnings.append("CORS origins is set to '*' in production environment")
            
        except Exception as e:
            self.errors.append(f"Security configuration error: {e}")
    
    def _validate_paths(self):
        """验证路径配置"""
        try:
            # 检查日志目录
            log_dir = Path(self.settings.log.file).parent
            if not log_dir.exists():
                try:
                    log_dir.mkdir(parents=True, exist_ok=True)
                    self.warnings.append(f"Created log directory: {log_dir}")
                except Exception as e:
                    self.errors.append(f"Cannot create log directory: {e}")
            
            # 检查状态存储目录
            state_dir = self.settings.state.storage_path
            if not state_dir.exists():
                try:
                    state_dir.mkdir(parents=True, exist_ok=True)
                    self.warnings.append(f"Created state storage directory: {state_dir}")
                except Exception as e:
                    self.errors.append(f"Cannot create state storage directory: {e}")
            
        except Exception as e:
            self.errors.append(f"Path validation error: {e}")
    
    def _validate_production(self):
        """验证生产环境特定配置"""
        if not self.settings.app.is_production:
            return
        
        # 检查调试模式
        if self.settings.app.debug:
            self.warnings.append("Debug mode is enabled in production environment")
        
        # 检查工作进程数
        if self.settings.app.workers < 2:
            self.warnings.append("Consider using more workers in production")
        
        # 检查日志级别
        if self.settings.log.level == "DEBUG":
            self.warnings.append("DEBUG log level in production may impact performance")


def validate_config() -> bool:
    """验证配置并打印结果"""
    validator = ConfigValidator()
    is_valid, errors, warnings = validator.validate_all()
    
    if warnings:
        print("\n⚠️  配置警告:")
        for warning in warnings:
            print(f"  - {warning}")
    
    if errors:
        print("\n❌ 配置错误:")
        for error in errors:
            print(f"  - {error}")
        return False
    
    if not warnings:
        print("✅ 配置验证通过!")
    
    return True


def check_env_file() -> bool:
    """检查 .env 文件是否存在"""
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists():
        if env_example.exists():
            print("⚠️  .env 文件不存在，但找到 .env.example")
            print("   请运行: cp .env.example .env")
            print("   然后编辑 .env 文件填入实际值")
        else:
            print("❌ .env 和 .env.example 文件都不存在")
        return False
    
    return True


if __name__ == "__main__":
    print("🔍 检查配置...")
    print("-" * 50)
    
    # 检查 .env 文件
    check_env_file()
    
    # 验证配置
    is_valid = validate_config()
    
    if not is_valid:
        print("\n请修复上述错误后重试")
        sys.exit(1)
    else:
        print("\n配置检查完成!")
