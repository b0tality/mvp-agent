"""
多智能体应用开发系统 V2 入口
"""

import asyncio
import argparse
import json
import os
import re
import shutil
from dotenv import load_dotenv

from config.settings import PipelineConfig
from config.logging_config import setup_logging
from llm import OpenAIAdapter
from agents.requirements import RequirementsAgent
from agents.technical import TechnicalAgent
from agents.code_review import CodeReviewAgent
from agents.testing import TestingAgent
from agents.acceptance import AcceptanceAgent
from agents.deployment import DeploymentAgent
from agents.builder import BuilderAgent
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

    # 创建所有Agent（mvp 阶段用 BuilderAgent 自主闭环，取代旧的 MVPAgent + 硬编码迭代）
    agents = {
        "requirements": RequirementsAgent(llm),
        "technical": TechnicalAgent(llm),
        "mvp": BuilderAgent(llm),
        "code_review": CodeReviewAgent(llm),
        "testing": TestingAgent(llm),
        "acceptance": AcceptanceAgent(llm),
        "deployment": DeploymentAgent(llm),
    }

    orchestrator = PipelineOrchestrator(agents, max_iterations=4)

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

    # 打印验收盲区告警（UI 标准 vs 无前端）
    accept_stage = result.stages.get("acceptance")
    accept_data = (accept_stage.data if accept_stage else {}) or {}
    for w in accept_data.get("warnings", []):
        print(f"\n  [验收告警] {w.get('message', '')}", flush=True)

    print("=" * 60)

    # 把生成的代码落盘（无论成败都保存，失败时 summary 会记录原因，便于排查）
    save_generated_code(result, orchestrator.state)


OUTPUT_BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")


def _safe_join(base: str, rel_path: str):
    """安全拼接相对路径，返回 None 表示非法（防路径穿越）。"""
    clean = os.path.normpath((rel_path or "").strip().lstrip("/\\"))
    if clean in ("", ".", "..") or clean.startswith("..") or os.path.isabs(clean):
        return None
    return os.path.join(base, clean)


def save_generated_code(result, state=None) -> str | None:
    """把流水线产物（代码 + 部署配置 + 摘要）落盘，返回输出目录绝对路径。"""
    mvp = result.stages.get("mvp")
    if not mvp or not mvp.data:
        print("\n[mvp] 阶段无数据，跳过代码保存")
        return None

    data = mvp.data
    raw_name = str(data.get("project_name") or "mvp_project")
    project_name = re.sub(r"[^0-9a-zA-Z_]+", "_", raw_name).strip("_").lower() or "mvp_project"
    project_dir = os.path.join(OUTPUT_BASE, project_name)
    shutil.rmtree(project_dir, ignore_errors=True)  # 清掉上一次运行的残留文件
    written = 0

    def write_file(rel_path: str, content: str) -> None:
        nonlocal written
        if not content:
            return
        dest = _safe_join(project_dir, rel_path)
        if dest is None:
            print(f"  [跳过] 非法路径: {rel_path!r}")
            return
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "w", encoding="utf-8") as f:
            f.write(content)
        written += 1

    for cf in data.get("code_files", []):
        write_file(cf.get("path", ""), cf.get("content", ""))
    for tf in data.get("test_files", []):
        write_file(tf.get("path", ""), tf.get("content", ""))

    # 兜底：若 LLM 没生成 requirements.txt，写入默认依赖
    has_req = any((cf.get("path") or "").strip().lstrip("/\\") == "requirements.txt"
                  for cf in data.get("code_files", []))
    if not has_req:
        write_file("requirements.txt", "fastapi>=0.104\nuvicorn>=0.24\npytest>=7\nhttpx>=0.24\n")

    # 部署产物
    deploy = result.stages.get("deployment")
    if deploy and deploy.data:
        docker = deploy.data.get("docker_config") or {}
        write_file("Dockerfile", docker.get("dockerfile", ""))
        write_file("docker-compose.yml", docker.get("docker_compose", ""))

    # 流水线摘要
    write_file("summary.json", json.dumps(_build_summary(result, project_name, state), ensure_ascii=False, indent=2))

    # 把运行日志复制进项目目录，便于单次运行复盘（FileHandler 每条记录都会 flush，copy2 能拿到最新内容）
    run_log = os.path.join(OUTPUT_BASE, "run.log")
    if os.path.exists(run_log):
        try:
            shutil.copy2(run_log, os.path.join(project_dir, "run.log"))
        except OSError:
            pass

    rel = os.path.relpath(project_dir, os.path.dirname(os.path.abspath(__file__)))
    print(f"\n已生成 {written} 个文件 → {rel}/")
    return project_dir


def _build_summary(result, project_name: str, state=None) -> dict:
    def stage_data(name):
        s = result.stages.get(name)
        return (s.data if s else {}) or {}

    req = stage_data("requirements")
    tech = stage_data("technical")
    review = stage_data("code_review")
    testing = stage_data("testing")
    accept = stage_data("acceptance")
    deploy = stage_data("deployment")

    return {
        "project_name": project_name,
        "status": result.status,
        "total_duration_s": round(result.total_duration, 1),
        "requirements": {
            "functional": [r.get("title") for r in req.get("functional_requirements", [])],
            "non_functional": [r.get("title") for r in req.get("non_functional_requirements", [])],
        },
        "tech_stack": tech.get("tech_stack", {}),
        "architecture_pattern": (tech.get("architecture") or {}).get("pattern"),
        "api_endpoints": [
            f"{e.get('method', 'GET')} {e.get('path', '/')}"
            for e in (tech.get("api_design") or {}).get("endpoints", [])
        ],
        "code_review_score": review.get("overall_score"),
        "code_review_issues": len(review.get("issues", [])),
        "code_review": {
            "score": review.get("overall_score"),
            "issues": review.get("issues", []),
            "summary": review.get("summary", ""),
        },
        "testing_bugs": len(testing.get("bugs", [])),
        "testing": {
            "total_tests": testing.get("total_tests"),
            "passed": testing.get("passed"),
            "failed": testing.get("failed"),
            "all_passed": testing.get("all_passed"),
            "coverage_line": (testing.get("coverage") or {}).get("line"),
            "smoke": testing.get("smoke_test", {}),
            "bugs": testing.get("bugs", []),
            "raw_output": testing.get("raw_output", "")[:6000],
        },
        "acceptance": {
            "total": accept.get("total"),
            "passed": accept.get("passed"),
            "failed": accept.get("failed"),
            "all_passed": accept.get("all_passed"),
            "results": accept.get("results", []),
            "warnings": accept.get("warnings", []),
            "raw_output": accept.get("raw_output", "")[:6000],
        },
        "deployment_strategy": (deploy.get("deployment_plan") or {}).get("strategy"),
        # 迭代历史：复盘「为什么迭代、每轮发现了什么、各阶段每轮耗时」
        "iterations": [
            {
                "iteration": r.iteration,
                "stage": r.stage,
                "reason": r.reason,
                "issues_count": r.issues_count,
                "bugs_count": r.bugs_count,
                "acceptance_failures": r.acceptance_failures,
            }
            for r in (state.iterations if state else [])
        ],
        "stage_history": [
            {
                "stage": r.stage,
                "status": r.status,
                "duration_seconds": r.duration_seconds,
                "agent_used": r.agent_used,
                "iteration": r.iteration,
                "error": r.error,
            }
            for r in (state.history if state else [])
        ],
    }


async def run_builder(user_input: str) -> None:
    """运行 Builder 自主循环（requirements → technical → builder）"""
    config = PipelineConfig.from_env()
    llm = OpenAIAdapter(api_key=config.api_key, base_url=config.base_url, model=config.model)

    print("\n" + "=" * 60)
    print("运行 Builder 自主循环（requirements → technical → builder）...")
    print("=" * 60)

    req = await RequirementsAgent(llm).execute(user_input=user_input)
    if req.status != "success":
        print(f"\n[requirements] 失败: {req.error}")
        return
    print(f"  [requirements] {req.status} ({req.duration_seconds:.1f}s)")

    tech = await TechnicalAgent(llm).execute(requirements=req.data)
    if tech.status != "success":
        print(f"\n[technical] 失败: {tech.error}")
        return
    print(f"  [technical] {tech.status} ({tech.duration_seconds:.1f}s)")

    builder = BuilderAgent(llm)
    result = await builder.execute(
        user_input=user_input,
        requirements=req.data,
        technical_solution=tech.data,
    )

    print(f"\n  [builder] {result.status} ({result.duration_seconds:.1f}s)")
    if result.status == "success":
        tr = result.data.get("test_result") or {}
        print(f"    代码文件: {len(result.data.get('code_files', []))} 个")
        print(f"    测试: {tr.get('passed', 0)} passed / {tr.get('failed', 0)} failed, all_passed={tr.get('all_passed')}")
        cov = (tr.get('coverage') or {}).get('line')
        print(f"    覆盖率: {cov}%")
        smoke = tr.get('smoke_test') or {}
        print(f"    冒烟: {smoke.get('passed')} — {smoke.get('detail', '')}")
    else:
        print(f"    错误: {result.error}")

    print("=" * 60)
    save_builder_output(result)


def save_builder_output(result) -> str | None:
    """把 Builder 产物（代码+测试+摘要）落盘，返回输出目录绝对路径。"""
    if not result or result.status != "success":
        print("\n[builder] 无成功产物，跳过保存")
        return None

    data = result.data
    code_files = data.get("code_files", [])
    if not code_files:
        print("\n[builder] 无代码，跳过保存")
        return None

    raw_name = str(data.get("project_name") or "builder_project")
    project_name = re.sub(r"[^0-9a-zA-Z_]+", "_", raw_name).strip("_").lower() or "builder_project"
    project_dir = os.path.join(OUTPUT_BASE, project_name)
    shutil.rmtree(project_dir, ignore_errors=True)
    written = 0

    def write_file(rel_path: str, content: str) -> None:
        nonlocal written
        if not content:
            return
        dest = _safe_join(project_dir, rel_path)
        if dest is None:
            print(f"  [跳过] 非法路径: {rel_path!r}")
            return
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "w", encoding="utf-8") as f:
            f.write(content)
        written += 1

    for cf in code_files:
        write_file(cf.get("path", ""), cf.get("content", ""))
    for tf in data.get("test_files", []):
        write_file(tf.get("path", ""), tf.get("content", ""))

    tr = data.get("test_result") or {}
    summary = {
        "project_name": project_name,
        "status": result.status,
        "duration_s": round(result.duration_seconds, 1),
        "verify": data.get("verify_result", {}),
        "testing": {
            "total_tests": tr.get("total_tests"),
            "passed": tr.get("passed"),
            "failed": tr.get("failed"),
            "all_passed": tr.get("all_passed"),
            "coverage_line": (tr.get("coverage") or {}).get("line"),
            "smoke": tr.get("smoke_test", {}),
            "raw_output": tr.get("raw_output", "")[:6000],
        },
        "final_text": data.get("final_text", ""),
    }
    write_file("summary.json", json.dumps(summary, ensure_ascii=False, indent=2))

    # 复制运行日志进项目目录
    run_log = os.path.join(OUTPUT_BASE, "run.log")
    if os.path.exists(run_log):
        try:
            shutil.copy2(run_log, os.path.join(project_dir, "run.log"))
        except OSError:
            pass

    rel = os.path.relpath(project_dir, os.path.dirname(os.path.abspath(__file__)))
    print(f"\n已生成 {written} 个文件 → {rel}/")
    return project_dir


def main():
    parser = argparse.ArgumentParser(description="多智能体应用开发系统 V2")
    parser.add_argument("--input", "-i", type=str, help="用户需求输入")
    parser.add_argument("--pipeline", action="store_true", help="运行完整流水线")
    parser.add_argument("--builder", action="store_true", help="运行 Builder 自主循环（requirements→technical→builder）")

    args = parser.parse_args()

    # 加载环境变量
    load_dotenv(r"C:\Users\MECHREV\agent\multi_agent_system\.env", override=True)

    # 初始化日志（控制台 INFO + 文件 DEBUG），任何 LLM 调用/阶段耗时都能在 run.log 里追踪
    setup_logging(OUTPUT_BASE)

    user_input = args.input or "开发一个待办事项应用"

    if args.builder:
        asyncio.run(run_builder(user_input))
    elif args.pipeline:
        asyncio.run(run_pipeline(user_input))
    else:
        asyncio.run(run_requirements(user_input))


if __name__ == "__main__":
    main()
