"""
多智能体应用开发系统入口
"""

import asyncio
import argparse
import json
from dotenv import load_dotenv

from agents.requirements import RequirementsAgent
from agents.technical import TechnicalAgent
from agents.mvp import MVPDeveloperAgent
from agents.code_review import CodeReviewAgent
from agents.testing import TestingAgent
from agents.deployment import DeploymentAgent
from config.settings import get_default_config, get_requirements_agent_config
from pipeline import PipelineOrchestrator, PipelineConfig


async def run_requirements_analysis(user_input: str) -> None:
    """运行需求分析"""
    
    # 加载环境变量（强制覆盖）
    load_dotenv(override=True)
    
    # 获取配置
    config = get_requirements_agent_config()
    
    # 创建智能体
    agent = RequirementsAgent(config)
    
    # 分析需求
    print("\n" + "=" * 60)
    print("开始需求分析...")
    print("=" * 60)
    
    result = await agent.analyze_requirements(user_input)
    
    # 输出结果
    print("\n" + "=" * 60)
    print("需求分析结果:")
    print("=" * 60)
    
    if result.get("status") == "success":
        print("\n✓ 分析成功!")
        
        # 显示功能需求
        print("\n功能需求:")
        for req in result.get("requirements", {}).get("functional_requirements", []):
            print(f"  - [{req.get('id')}] {req.get('title')}: {req.get('description')}")
        
        # 显示非功能需求
        print("\n非功能需求:")
        for req in result.get("requirements", {}).get("non_functional_requirements", []):
            print(f"  - [{req.get('id')}] {req.get('category')}: {req.get('description')}")
        
        # 显示用户故事
        print("\n用户故事:")
        for story in result.get("user_stories", {}).get("user_stories", []):
            print(f"  - [{story.get('id')}] 作为{story.get('role')}，我想要{story.get('feature')}，以便{story.get('benefit')}")
        
        # 显示优先级
        print("\n优先级矩阵:")
        priority_matrix = result.get("priority_matrix", {}).get("priority_matrix", {})
        for priority, items in priority_matrix.items():
            print(f"  {priority}:")
            for item in items:
                if isinstance(item, dict):
                    print(f"    - {item.get('id')}: {item.get('title')}")
                else:
                    print(f"    - {item}")
    else:
        print(f"\n✗ 分析失败: {result.get('error')}")
    
    print("\n" + "=" * 60)


async def run_pipeline(user_input: str, persistence_path: str = None) -> None:
    """运行完整流水线"""
    
    # 加载环境变量（强制覆盖）
    load_dotenv(override=True)
    
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
        persistence_path=persistence_path
    )
    
    # 创建编排器
    orchestrator = PipelineOrchestrator(pipeline_config, agents)
    
    # 运行流水线
    print("\n" + "=" * 60)
    print("开始运行完整流水线...")
    print("=" * 60)
    
    result = await orchestrator.run(user_input)
    
    # 输出结果
    print("\n" + "=" * 60)
    print("流水线运行结果:")
    print("=" * 60)
    print(f"状态: {result.status}")
    print(f"成功阶段: {[s for s, r in result.results.items() if r.get('status') in ['success', 'fallback']]}")
    print(f"失败阶段: {result.failed_stages}")
    print(f"降级阶段: {result.degraded_stages}")
    
    # 显示成本报告
    cost = result.cost_report
    print(f"\n成本报告:")
    print(f"  总成本: ${cost.get('total_cost', 0)}")
    print(f"  总Token: {cost.get('total_tokens', 0)}")
    print(f"  降级开销: ${cost.get('fallback_overhead', 0)}")
    
    # 保存结果
    if persistence_path:
        result_path = persistence_path.replace(".json", "_result.json")
        with open(result_path, "w", encoding="utf-8") as f:
            json.dump(result.to_dict(), f, ensure_ascii=False, indent=2)
        print(f"\n结果已保存到: {result_path}")
    
    print("\n" + "=" * 60)


def main():
    """主函数"""
    
    parser = argparse.ArgumentParser(description="多智能体应用开发系统")
    parser.add_argument(
        "--input", "-i",
        type=str,
        help="用户需求输入"
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="交互模式"
    )
    parser.add_argument(
        "--pipeline",
        action="store_true",
        help="运行完整流水线"
    )
    parser.add_argument(
        "--save",
        type=str,
        help="保存状态到文件（仅pipeline模式）"
    )
    
    args = parser.parse_args()
    
    if args.pipeline:
        # 流水线模式
        if args.input:
            asyncio.run(run_pipeline(args.input, args.save))
        else:
            example_input = "我想开发一个在线商城系统，主要功能包括用户注册、商品浏览、购物车、在线支付、订单管理"
            asyncio.run(run_pipeline(example_input, args.save))
    
    elif args.interactive:
        # 交互模式
        print("多智能体应用开发系统 - 交互模式")
        print("输入 'quit' 或 'exit' 退出")
        print("=" * 60)
        
        while True:
            user_input = input("\n请输入您的需求: ").strip()
            
            if user_input.lower() in ["quit", "exit"]:
                print("再见!")
                break
            
            if user_input:
                asyncio.run(run_requirements_analysis(user_input))
    
    elif args.input:
        # 命令行模式（仅需求分析）
        asyncio.run(run_requirements_analysis(args.input))
    
    else:
        # 默认示例
        example_input = """
        我想开发一个在线商城系统，主要功能包括：
        1. 用户注册和登录
        2. 商品浏览和搜索
        3. 购物车功能
        4. 在线支付
        5. 订单管理
        """
        
        asyncio.run(run_requirements_analysis(example_input))


if __name__ == "__main__":
    main()
