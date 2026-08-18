"""
配置管理模块使用示例
"""

import asyncio
from config import (
    get_settings,
    get_openai_config,
    get_agent_config,
    get_database_url,
    get_redis_url,
    is_development,
    is_production,
    validate_config,
    ConfigExporter,
    EnvironmentDetector,
)


def example_basic_usage():
    """基本使用示例"""
    print("=" * 60)
    print("示例1: 基本配置使用")
    print("=" * 60)
    
    # 获取配置单例
    settings = get_settings()
    
    # 访问应用配置
    print(f"\n应用名称: {settings.app.name}")
    print(f"应用版本: {settings.app.version}")
    print(f"运行环境: {settings.app.environment}")
    print(f"调试模式: {settings.app.debug}")
    
    # 访问 OpenAI 配置
    print(f"\nOpenAI 模型: {settings.openai.model}")
    print(f"温度参数: {settings.openai.temperature}")
    print(f"最大 Token: {settings.openai.max_tokens}")
    
    # 访问数据库配置
    print(f"\n数据库主机: {settings.database.host}")
    print(f"数据库端口: {settings.database.port}")
    print(f"数据库名称: {settings.database.database}")
    print(f"数据库 URL: {settings.database.database_url}")
    
    # 访问智能体配置
    print(f"\n需求分析师模型: {settings.agents.requirements.model}")
    print(f"技术架构师模型: {settings.agents.technical.model}")
    print(f"MVP开发者模型: {settings.agents.mvp.model}")


def example_convenience_functions():
    """便捷函数示例"""
    print("\n" + "=" * 60)
    print("示例2: 便捷函数使用")
    print("=" * 60)
    
    # 获取 OpenAI 配置
    openai_config = get_openai_config()
    print(f"\nOpenAI 配置: {openai_config}")
    
    # 获取指定智能体配置
    requirements_config = get_agent_config("requirements")
    print(f"需求分析师配置: {requirements_config}")
    
    technical_config = get_agent_config("technical")
    print(f"技术架构师配置: {technical_config}")
    
    # 获取数据库和 Redis URL
    print(f"\n数据库 URL: {get_database_url()}")
    print(f"Redis URL: {get_redis_url()}")
    
    # 环境判断
    print(f"\n是否为开发环境: {is_development()}")
    print(f"是否为生产环境: {is_production()}")


def example_config_validation():
    """配置验证示例"""
    print("\n" + "=" * 60)
    print("示例3: 配置验证")
    print("=" * 60)
    
    # 验证配置
    is_valid = validate_config()
    print(f"\n配置是否有效: {is_valid}")


def example_config_export():
    """配置导出示例"""
    print("\n" + "=" * 60)
    print("示例4: 配置导出")
    print("=" * 60)
    
    exporter = ConfigExporter()
    
    # 导出为 JSON (不含敏感信息)
    json_config = exporter.to_json()
    print(f"\nJSON 配置 (不含敏感信息):")
    print(json_config[:500] + "..." if len(json_config) > 500 else json_config)
    
    # 导出为 YAML
    yaml_config = exporter.to_yaml()
    print(f"\nYAML 配置:")
    print(yaml_config[:500] + "..." if len(yaml_config) > 500 else yaml_config)


def example_environment_detection():
    """环境检测示例"""
    print("\n" + "=" * 60)
    print("示例5: 环境检测")
    print("=" * 60)
    
    detector = EnvironmentDetector()
    
    # 检测环境
    env = detector.detect_environment()
    print(f"\n检测到的环境: {env}")
    
    # 检测运行环境
    print(f"是否在 Docker 中: {detector.is_docker()}")
    print(f"是否在 Kubernetes 中: {detector.is_kubernetes()}")
    print(f"是否在 CI 中: {detector.is_ci()}")
    
    # 获取系统信息
    system_info = detector.get_system_info()
    print(f"\n系统信息:")
    for key, value in system_info.items():
        print(f"  {key}: {value}")


def example_agent_configuration():
    """智能体配置示例"""
    print("\n" + "=" * 60)
    print("示例6: 智能体配置")
    print("=" * 60)
    
    settings = get_settings()
    
    # 获取所有智能体配置
    agents = [
        "requirements",
        "technical",
        "mvp",
        "code_review",
        "testing",
        "deployment",
    ]
    
    print("\n智能体配置:")
    for agent_name in agents:
        agent_config = settings.agents.get_agent_config(agent_name)
        print(f"  {agent_name}:")
        print(f"    模型: {agent_config.model}")
        print(f"    温度: {agent_config.temperature}")
        print(f"    最大Token: {agent_config.max_tokens}")


async def main():
    """主函数"""
    print("多智能体应用开发系统 - 配置管理示例")
    print("=" * 60)
    
    # 运行示例
    example_basic_usage()
    example_convenience_functions()
    example_config_validation()
    example_config_export()
    example_environment_detection()
    example_agent_configuration()
    
    print("\n" + "=" * 60)
    print("所有示例执行完成!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
