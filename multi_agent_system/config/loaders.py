"""
配置加载工具模块

提供配置加载、环境检测、配置导出等功能。
"""

import os
import json
import yaml
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from .settings import get_settings, Settings


class ConfigLoader:
    """配置加载器"""
    
    @staticmethod
    def load_from_json(file_path: str) -> Dict[str, Any]:
        """从 JSON 文件加载配置"""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {file_path}")
        
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    @staticmethod
    def load_from_yaml(file_path: str) -> Dict[str, Any]:
        """从 YAML 文件加载配置"""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {file_path}")
        
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    
    @staticmethod
    def load_from_env_file(file_path: str) -> Dict[str, str]:
        """从 .env 文件加载配置"""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Env file not found: {file_path}")
        
        config = {}
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                # 跳过注释和空行
                if not line or line.startswith("#"):
                    continue
                
                # 解析键值对
                if "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # 移除引号
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    
                    config[key] = value
        
        return config


class ConfigExporter:
    """配置导出器"""
    
    def __init__(self, settings: Settings = None):
        self.settings = settings or get_settings()
    
    def to_dict(self, include_secrets: bool = False) -> Dict[str, Any]:
        """导出配置为字典"""
        config = {
            "app": {
                "name": self.settings.app.name,
                "version": self.settings.app.version,
                "environment": self.settings.app.environment,
                "debug": self.settings.app.debug,
            },
            "openai": {
                "model": self.settings.openai.model,
                "temperature": self.settings.openai.temperature,
                "max_tokens": self.settings.openai.max_tokens,
            },
            "database": {
                "host": self.settings.database.host,
                "port": self.settings.database.port,
                "database": self.settings.database.database,
            },
            "redis": {
                "host": self.settings.redis.host,
                "port": self.settings.redis.port,
            },
            "log": {
                "level": self.settings.log.level,
                "file": self.settings.log.file,
            },
            "agents": {
                "requirements": {
                    "model": self.settings.agents.requirements.model,
                    "temperature": self.settings.agents.requirements.temperature,
                },
                "technical": {
                    "model": self.settings.agents.technical.model,
                    "temperature": self.settings.agents.technical.temperature,
                },
                "mvp": {
                    "model": self.settings.agents.mvp.model,
                    "temperature": self.settings.agents.mvp.temperature,
                },
                "code_review": {
                    "model": self.settings.agents.code_review.model,
                    "temperature": self.settings.agents.code_review.temperature,
                },
                "testing": {
                    "model": self.settings.agents.testing.model,
                    "temperature": self.settings.agents.testing.temperature,
                },
                "deployment": {
                    "model": self.settings.agents.deployment.model,
                    "temperature": self.settings.agents.deployment.temperature,
                },
            },
        }
        
        # 包含敏感信息（仅在明确要求时）
        if include_secrets:
            config["openai"]["api_key"] = self.settings.openai.api_key
            config["database"]["password"] = self.settings.database.password
            config["redis"]["password"] = self.settings.redis.password
        
        return config
    
    def to_json(self, file_path: Optional[str] = None, include_secrets: bool = False) -> str:
        """导出配置为 JSON"""
        config = self.to_dict(include_secrets=include_secrets)
        json_str = json.dumps(config, indent=2, ensure_ascii=False)
        
        if file_path:
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(json_str)
        
        return json_str
    
    def to_yaml(self, file_path: Optional[str] = None, include_secrets: bool = False) -> str:
        """导出配置为 YAML"""
        config = self.to_dict(include_secrets=include_secrets)
        yaml_str = yaml.dump(config, default_flow_style=False, allow_unicode=True)
        
        if file_path:
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(yaml_str)
        
        return yaml_str


class EnvironmentDetector:
    """环境检测器"""
    
    @staticmethod
    def detect_environment() -> str:
        """检测当前环境"""
        # 从环境变量检测
        env = os.getenv("ENVIRONMENT", "").lower()
        if env in ["production", "staging", "development"]:
            return env
        
        # 从其他变量推断
        if os.getenv("CI"):
            return "ci"
        
        if os.getenv("DEBUG", "").lower() in ["true", "1"]:
            return "development"
        
        # 默认为开发环境
        return "development"
    
    @staticmethod
    def is_docker() -> bool:
        """检测是否在 Docker 中运行"""
        return Path("/.dockerenv").exists() or os.getenv("DOCKER") == "true"
    
    @staticmethod
    def is_kubernetes() -> bool:
        """检测是否在 Kubernetes 中运行"""
        return os.getenv("KUBERNETES_SERVICE_HOST") is not None
    
    @staticmethod
    def is_ci() -> bool:
        """检测是否在 CI 环境中"""
        return os.getenv("CI") is not None
    
    @staticmethod
    def get_system_info() -> Dict[str, Any]:
        """获取系统信息"""
        import platform
        
        return {
            "platform": platform.system(),
            "platform_release": platform.release(),
            "platform_version": platform.version(),
            "architecture": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "is_docker": EnvironmentDetector.is_docker(),
            "is_kubernetes": EnvironmentDetector.is_kubernetes(),
            "is_ci": EnvironmentDetector.is_ci(),
        }


def generate_env_template(
    output_file: str = ".env.template",
    include_comments: bool = True
) -> None:
    """生成环境变量模板文件"""
    settings = get_settings()
    exporter = ConfigExporter(settings)
    config = exporter.to_dict(include_secrets=False)
    
    lines = []
    
    if include_comments:
        lines.append("# 环境变量模板")
        lines.append(f"# 生成时间: {datetime.now().isoformat()}")
        lines.append("# 请根据实际情况修改以下配置")
        lines.append("")
    
    # 应用配置
    lines.append("# 应用配置")
    lines.append(f"APP_NAME={config['app']['name']}")
    lines.append(f"APP_VERSION={config['app']['version']}")
    lines.append(f"ENVIRONMENT={config['app']['environment']}")
    lines.append(f"DEBUG={config['app']['debug']}")
    lines.append("")
    
    # OpenAI 配置
    lines.append("# OpenAI 配置")
    lines.append("OPENAI_API_KEY=your-api-key-here")
    lines.append(f"OPENAI_MODEL={config['openai']['model']}")
    lines.append(f"OPENAI_TEMPERATURE={config['openai']['temperature']}")
    lines.append(f"OPENAI_MAX_TOKENS={config['openai']['max_tokens']}")
    lines.append("")
    
    # 数据库配置
    lines.append("# 数据库配置")
    lines.append(f"POSTGRES_HOST={config['database']['host']}")
    lines.append(f"POSTGRES_PORT={config['database']['port']}")
    lines.append("POSTGRES_USER=postgres")
    lines.append("POSTGRES_PASSWORD=postgres")
    lines.append(f"POSTGRES_DB={config['database']['database']}")
    lines.append("")
    
    # Redis 配置
    lines.append("# Redis 配置")
    lines.append(f"REDIS_HOST={config['redis']['host']}")
    lines.append(f"REDIS_PORT={config['redis']['port']}")
    lines.append("REDIS_PASSWORD=redis")
    lines.append("")
    
    # 写入文件
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    
    print(f"✅ 环境变量模板已生成: {output_file}")


if __name__ == "__main__":
    # 显示环境信息
    print("🔍 环境信息:")
    print("-" * 50)
    
    info = EnvironmentDetector.get_system_info()
    for key, value in info.items():
        print(f"  {key}: {value}")
    
    print()
    
    # 显示当前配置
    print("📋 当前配置:")
    print("-" * 50)
    
    exporter = ConfigExporter()
    print(exporter.to_json())
