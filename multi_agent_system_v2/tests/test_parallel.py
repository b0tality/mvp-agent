"""
测试并行执行：验证 code_review 和 testing 是否并行运行
"""

import sys
import asyncio
import time

sys.path.insert(0, r'C:\Users\MECHREV\agent\multi_agent_system_v2')

from dotenv import load_dotenv
load_dotenv(r'C:\Users\MECHREV\agent\multi_agent_system\.env', override=True)

import os
from llm import OpenAIAdapter
from agents.base import BaseAgent, AgentResult
from pipeline import PipelineOrchestrator


class MockAgent(BaseAgent):
    """模拟Agent，用于测试并行性"""

    def __init__(self, name: str, delay: float = 2.0):
        self.name = name
        self.delay = delay
        self.llm = None  # 不需要LLM

    async def execute(self, **kwargs) -> AgentResult:
        start = time.time()
        print(f"  [{self.name}] 开始执行...", flush=True)
        await asyncio.sleep(self.delay)
        print(f"  [{self.name}] 执行完成 ({time.time() - start:.1f}s)", flush=True)
        return self._success({"result": f"{self.name}_done"}, time.time() - start)


async def test_parallel():
    print("=" * 60)
    print("测试并行执行")
    print("=" * 60)

    # 创建模拟Agent，每个延迟2秒
    agents = {
        "requirements": MockAgent("requirements", 2.0),
        "technical": MockAgent("technical", 2.0),
        "mvp": MockAgent("mvp", 2.0),
        "code_review": MockAgent("code_review", 2.0),
        "testing": MockAgent("testing", 2.0),
        "deployment": MockAgent("deployment", 2.0),
    }

    orchestrator = PipelineOrchestrator(agents)

    print("\n串行执行预计: 6 * 2s = 12s")
    print("并行执行预计: ~8s (code_review和testing并行)\n")

    start = time.time()
    result = await orchestrator.run("测试输入")
    total = time.time() - start

    print(f"\n总耗时: {total:.1f}s")
    print(f"状态: {result.status}")

    print("\n各阶段结果:")
    for stage, sr in result.stages.items():
        print(f"  {stage}: {sr.status} ({sr.duration_seconds:.1f}s)")
        if sr.error:
            print(f"    错误: {sr.error}")

    # 验证并行性
    if total < 11:
        print("\n✓ code_review 和 testing 已并行执行!")
    else:
        print("\n✗ 仍然是串行执行")

    print("=" * 60)


asyncio.run(test_parallel())
