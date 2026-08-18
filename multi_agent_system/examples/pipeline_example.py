"""
流水线使用示例
"""

import asyncio
import json
from dotenv import load_dotenv

from agents.requirements import RequirementsAgent
from agents.technical import TechnicalAgent
from agents.mvp import MVPDeveloperAgent
from agents.code_review import CodeReviewAgent
from agents.testing import TestingAgent
from agents.deployment import DeploymentAgent
from config.settings import get_default_config
from pipeline import PipelineOrchestrator, PipelineConfig


async def example_full_pipeline():
    """完整流水线示例"""
    print("=" * 60)
    print("示例1: 完整流水线运行")
    print("=" * 60)
    
    # 加载环境变量
    load_dotenv()
    
    # 获取配置
    config = get_default_config()
    
    # 创建所有Agent
    agents = {
        "requirements": RequirementsAgent(config),
        "technical": TechnicalAgent(config),
        "mvp": MVPDeveloperAgent(config),
        "code_review": CodeReviewAgent(config),
        "testing": TestingAgent(config),
        "deployment": DeploymentAgent(config)
    }
    
    # 创建流水线配置
    pipeline_config = PipelineConfig(
        model=config.get("model", "gpt-4"),
        persistence_path="./example_state.json"
    )
    
    # 创建编排器
    orchestrator = PipelineOrchestrator(pipeline_config, agents)
    
    # 运行
    user_input = "开发一个博客系统，支持用户认证、文章发布、评论功能"
    result = await orchestrator.run(user_input)
    
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))


async def example_single_stage():
    """单阶段运行示例"""
    print("\n" + "=" * 60)
    print("示例2: 单阶段运行")
    print("=" * 60)
    
    # 加载环境变量
    load_dotenv()
    
    # 获取配置
    config = get_default_config()
    
    # 创建Agent
    agents = {
        "requirements": RequirementsAgent(config)
    }
    
    # 创建流水线配置
    pipeline_config = PipelineConfig()
    
    # 创建编排器
    orchestrator = PipelineOrchestrator(pipeline_config, agents)
    
    # 只运行需求分析
    result = await orchestrator.run_stage(
        "requirements",
        user_input="开发一个待办事项应用"
    )
    
    print(json.dumps(result, ensure_ascii=False, indent=2))


async def example_with_checkpoint():
    """带检查点的示例"""
    print("\n" + "=" * 60)
    print("示例3: 带检查点保存")
    print("=" * 60)
    
    # 加载环境变量
    load_dotenv()
    
    # 获取配置
    config = get_default_config()
    
    # 创建所有Agent
    agents = {
        "requirements": RequirementsAgent(config),
        "technical": TechnicalAgent(config),
        "mvp": MVPDeveloperAgent(config),
        "code_review": CodeReviewAgent(config),
        "testing": TestingAgent(config),
        "deployment": DeploymentAgent(config)
    }
    
    # 创建流水线配置（带持久化路径）
    pipeline_config = PipelineConfig(
        model=config.get("model", "gpt-4"),
        persistence_path="./checkpoint_example.json"
    )
    
    # 创建编排器
    orchestrator = PipelineOrchestrator(pipeline_config, agents)
    
    # 运行
    user_input = "开发一个任务管理系统，支持任务创建、分配、跟踪"
    result = await orchestrator.run(user_input)
    
    print(f"状态: {result.status}")
    print(f"检查点已保存到: ./checkpoint_example.json")
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))


async def main():
    """主函数"""
    print("多智能体流水线编排器 - 使用示例")
    print("=" * 60)
    
    await example_full_pipeline()
    await example_single_stage()
    await example_with_checkpoint()
    
    print("\n" + "=" * 60)
    print("所有示例执行完成!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
