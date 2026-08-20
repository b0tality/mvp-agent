"""
spec-driven 基准运行器（端到端，需要 MiMo API）

对 benchmarks/cases.py 里的每条需求跑一次 spec-driven 流水线（不做人工审阅），
汇总成功率、覆盖率、契约匹配、耗时、重试轮数，输出表格 + 落盘 results.json。

用法：
    python benchmarks/run_benchmark.py                 # 跑全部用例
    python benchmarks/run_benchmark.py todo_crud auth_register_login   # 跑子集
"""

import sys
import os
import json
import asyncio
import argparse
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv(r"C:\Users\MECHREV\agent\multi_agent_system\.env", override=True)

# 控制台 UTF-8（同 main.py，避免 emoji/中文在 GBK 控制台抛 UnicodeEncodeError）
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from config.settings import PipelineConfig
from llm import OpenAIAdapter
from agents.spec_agent import SpecAgent
from agents.builder import BuilderAgent
from agents.deployment import DeploymentAgent
from agents.spec_review_agent import SpecReviewAgent
from pipeline.spec_pipeline import run_spec_pipeline
from benchmarks.cases import get_cases

def _result_file(suite: str) -> str:
    """v1 结果沿用 results.json（已提交的基线），其它 suite 落到 results_<suite>.json 以免覆盖。"""
    name = "results.json" if suite == "v1" else f"results_{suite}.json"
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), name)


async def run_one(name: str, requirement: str, llm, spec_auto_review=None) -> dict:
    r = await run_spec_pipeline(
        requirement,
        SpecAgent(llm), BuilderAgent(llm), DeploymentAgent(llm),
        timeout=180,
        spec_auto_review=spec_auto_review,
    )
    tr = r.get("test_result") or {}
    contract = r.get("contract") or {}
    return {
        "name": name,
        "gate_ok": r.get("gate_ok"),
        "status": r.get("status"),
        "coverage": r.get("coverage_line"),
        "contract_match": contract.get("match"),
        "contract_missing": contract.get("missing", []),
        "contract_extra": contract.get("extra", []),
        "tests_passed": tr.get("passed"),
        "tests_failed": tr.get("failed"),
        "build_rounds": r.get("build_rounds"),
        "duration_s": round(r.get("duration_seconds", 0), 1),
        "error": r.get("error"),
        "gate_reasons": r.get("gate_reasons"),
    }


def _fmt_row(res: dict) -> str:
    status = "✅" if res["gate_ok"] else "❌"
    return (
        f"{status} {res['name']:<26} cov={str(res['coverage']):>4} "
        f"contract={res['contract_match']} rounds={res['build_rounds']} "
        f"tests={res['tests_passed']}/{res['tests_failed']} "
        f"{res['duration_s']}s"
    )


async def main(names, suite="v2", auto_review=True) -> None:
    cfg = PipelineConfig.from_env()
    llm = OpenAIAdapter(api_key=cfg.api_key, base_url=cfg.base_url, model=cfg.model)

    spec_auto_review = SpecReviewAgent(llm).to_callback() if auto_review else None
    cases = get_cases(names, suite=suite)
    review_label = "on" if auto_review else "off"
    print(f"跑 {len(cases)} 个用例（model={cfg.model} suite={suite} auto_review={review_label}）...\n")
    results = []
    for case in cases:
        t0 = time.time()
        res = await run_one(case["name"], case["requirement"], llm, spec_auto_review)
        results.append(res)
        print(_fmt_row(res))
        if res["gate_reasons"]:
            for g in res["gate_reasons"]:
                print(f"         ↳ {g}")
        if res["error"]:
            print(f"         ↳ error: {res['error']}")

    # 汇总
    ok = [r for r in results if r["gate_ok"]]
    print("\n" + "=" * 70)
    print(f"成功率: {len(ok)}/{len(results)} = {100*len(ok)/max(1,len(results)):.0f}%")
    if results:
        covs = [r["coverage"] for r in results if isinstance(r["coverage"], (int, float)) and r["coverage"] >= 0]
        durs = [r["duration_s"] for r in results]
        retries = [r["build_rounds"] for r in results if r["build_rounds"]]
        print(f"平均覆盖率: {sum(covs)/len(covs):.0f}%" if covs else "平均覆盖率: n/a")
        print(f"平均耗时: {sum(durs)/len(durs):.1f}s")
        print(f"平均重试轮数: {sum(retries)/len(retries):.1f}" if retries else "平均重试轮数: n/a")
    print("=" * 70)

    result_file = _result_file(suite)
    with open(result_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n结果已落盘 → {os.path.relpath(result_file, os.getcwd())}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="spec-driven 基准运行器")
    parser.add_argument("cases", nargs="*", help="只跑指定用例名（默认全部）")
    parser.add_argument("--suite", choices=["v1", "v2"], default="v2",
                        help="用例集：v1 首轮基线 / v2 新一轮多样形态（默认 v2）")
    parser.add_argument("--no-auto-review", action="store_true",
                        help="关闭 Spec 自动完备性评审（默认开启）")
    args = parser.parse_args()
    asyncio.run(main(args.cases, args.suite, auto_review=not args.no_auto_review))
