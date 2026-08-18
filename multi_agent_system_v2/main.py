"""
多智能体应用开发系统 V2 入口
"""

import asyncio
import argparse
from dotenv import load_dotenv

from config.settings import PipelineConfig
from llm import OpenAIAdapter
from agents.requirements import RequirementsAgent
from agents.technical import TechnicalAgent
from agents.mvp import MVPAgent
from agents.code_review import CodeReviewAgent
from agents.testing import TestingAgent
from agents.deployment import DeploymentAgent
from pipeline import PipelineOrchestrator


async def run_requirements(user_input: str) -> None:
    """运行需求分析"""
    config = PipelineConfig.from_env()
    llm = OpenAIAdapter(api_key=config.api_key, base_url=config.base_url, model=config.model)
    agent = RequirementsAgent(llm)

    print("\n" + "=" * 60)
    print("需求分析...")
    print("=" * 60)

    result = await agent.execute(user_input=user_input)

    print(f"\n状态: {result.status}")
    print(f"耗时: {result.duration_seconds:.1f}s")
    print(f"Agent: {result.agent_used}")

    if result.status == "success":
        print(f"\n功能需求: {len(result.data.get('functional_requirements', []))} 条")
        print(f"用户故事: {len(result.data.get('user_stories', []))} 条")
        print(f"验收标准: {len(result.data.get('acceptance_criteria', []))} 条")

        print("\n功能需求:")
        for req in result.data.get("functional_requirements", []):
            rid = req.get("id", "?")
            title = req.get("title", "?")
            desc = req.get("description", "")[:50]
            print(f"  [{rid}] {title}: {desc}...")
    else:
        print(f"\n错误: {result.error}")

    print("=" * 60)


async def run_pipeline(user_input: str) -> None:
    """运行完整流水线"""
    config = PipelineConfig.from_env()
    llm = OpenAIAdapter(api_key=config.api_key, base_url=config.base_url, model=config.model)

    # 创建所有Agent
    agents = {
        "requirements": RequirementsAgent(llm),
        "technical": TechnicalAgent(llm),
        "mvp": MVPAgent(llm),
        "code_review": CodeReviewAgent(llm),
        "testing": TestingAgent(llm),
        "deployment": DeploymentAgent(llm),
    }

    orchestrator = PipelineOrchestrator(agents, max_iterations=3)

    print("\n" + "=" * 60)
    print("运行完整流水线（含迭代优化）...")
    print("=" * 60)

    result = await orchestrator.run(user_input)

    print(f"\n状态: {result.status}")
    print(f"总耗时: {result.total_duration:.1f}s")
    print(f"迭代次数: {orchestrator.state.current_iteration}")
    print(f"失败阶段: {result.failed_stages}")
    print(f"降级阶段: {result.degraded_stages}")

    if result.abort_reason:
        print(f"中止原因: {result.abort_reason}")

    print("\n各阶段结果:")
    for stage, sr in result.stages.items():
        print(f"  {stage}: {sr.status} ({sr.duration_seconds:.1f}s, {sr.agent_used})")

    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="多智能体应用开发系统 V2")
    parser.add_argument("--input", "-i", type=str, help="用户需求输入")
    parser.add_argument("--pipeline", action="store_true", help="运行完整流水线")

    args = parser.parse_args()

    # 加载环境变量
    load_dotenv(r"C:\Users\MECHREV\agent\multi_agent_system\.env", override=True)

    user_input = args.input or "开发一个待办事项应用"

    if args.pipeline:
        asyncio.run(run_pipeline(user_input))
    else:
        asyncio.run(run_requirements(user_input))


if __name__ == "__main__":
    main()
