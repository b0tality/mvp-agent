"""
流水线编排器
"""

import asyncio
import time
from typing import Dict, Any, List, Callable, Awaitable
from agents.base import BaseAgent, AgentResult
from pipeline.state import PipelineState, StageRecord, IterationRecord
from pipeline.fallback import FallbackManager
from schemas import PipelineResult, StageResult


class PipelineOrchestrator:
    """
    流水线编排器
    
    执行流程：
    requirements → technical → mvp → [code_review, testing] → deployment
                                       ↑          ↓
                                       └── 迭代循环 ┘
                                       
    迭代循环：
    - code_review发现问题 → mvp改进代码 → 重新review
    - testing发现bug → mvp修复代码 → 重新test
    - 最多迭代 max_iterations 次
    """

    STAGES = [
        "requirements",
        "technical",
        "mvp",
        "code_review",
        "testing",
        "deployment",
    ]

    DEPENDENCIES = {
        "requirements": [],
        "technical": ["requirements"],
        "mvp": ["requirements", "technical"],
        "code_review": ["mvp"],
        "testing": ["mvp"],
        "deployment": ["mvp", "testing"],
    }

    PARALLEL_GROUPS = [
        ["requirements"],
        ["technical"],
        ["mvp"],
        ["code_review", "testing"],  # 并行
        ["deployment"],
    ]

    def __init__(self, agents: Dict[str, BaseAgent], max_iterations: int = 3):
        self.agents = agents
        self.state = PipelineState()
        self.fallback = FallbackManager(max_consecutive_failures=2)
        self.max_iterations = max_iterations

    async def run(self, user_input: str) -> PipelineResult:
        """运行完整流水线"""
        start = time.time()
        stage_results: Dict[str, StageResult] = {}
        failed_stages: List[str] = []
        degraded_stages: List[str] = []

        for group in self.PARALLEL_GROUPS:
            if self.fallback.should_abort():
                return self._build_result("aborted", stage_results, failed_stages, degraded_stages, start)

            # 过滤可执行阶段
            executable = []
            for stage_name in group:
                if not self._check_dependencies(stage_name, stage_results):
                    stage_results[stage_name] = StageResult(stage=stage_name, status="skipped", error="依赖未满足")
                else:
                    executable.append(stage_name)

            if not executable:
                continue

            # 执行阶段
            if len(executable) == 1:
                name = executable[0]

                # mvp阶段特殊处理：可能需要迭代
                if name == "mvp":
                    result = await self._run_mvp_with_iterations(user_input, stage_results)
                else:
                    result = await self._execute_stage(name, user_input)

                print(f"  [{name}] 完成: {result.status} ({result.duration_seconds:.1f}s)", flush=True)
                self._process_stage_result(name, result, stage_results, failed_stages, degraded_stages)
            else:
                # 并行执行（code_review + testing）
                print(f"  [{', '.join(executable)}] 并行执行...", flush=True)
                results = await asyncio.gather(
                    *[self._execute_stage(name, user_input) for name in executable],
                    return_exceptions=True,
                )

                for stage_name, result in zip(executable, results):
                    if isinstance(result, Exception):
                        result = StageResult(stage=stage_name, status="error", error=str(result))
                    print(f"  [{stage_name}] 完成: {result.status} ({result.duration_seconds:.1f}s)", flush=True)
                    self._process_stage_result(stage_name, result, stage_results, failed_stages, degraded_stages)

                # 检查是否需要迭代
                need_iterate, feedback = self._check_need_iteration(stage_results)
                if need_iterate and self.state.current_iteration < self.max_iterations:
                    await self._run_iteration(feedback, user_input, stage_results, failed_stages, degraded_stages)

        status = "failed" if len(failed_stages) == len(self.STAGES) else ("partial" if failed_stages else "success")
        return self._build_result(status, stage_results, failed_stages, degraded_stages, start)

    async def _run_mvp_with_iterations(
        self,
        user_input: str,
        stage_results: Dict[str, StageResult],
    ) -> StageResult:
        """执行MVP阶段（带编译验证循环）"""
        print(f"  [mvp] 开始执行...", flush=True)
        result = await self._execute_stage("mvp", user_input)

        if result.status != "success":
            return result

        # 编译验证循环
        from tools.mvp_tools import CodeVerifierTool
        verifier = CodeVerifierTool(llm=None)  # 不需要LLM

        for verify_iter in range(self.max_iterations):
            code_files = result.data.get("code_files", [])
            if not code_files:
                break

            print(f"  [mvp] 编译验证 (第{verify_iter + 1}次)...", flush=True)
            verify_result = await verifier.run(code_files=code_files)

            if verify_result.get("passed"):
                print(f"  [mvp] 编译验证通过!", flush=True)
                break

            # 有编译错误，需要修复
            errors = verify_result.get("errors", [])
            print(f"  [mvp] 发现 {len(errors)} 个编译错误，正在修复...", flush=True)

            # 用编译错误作为feedback让MVP修复
            feedback = {
                "compile_errors": errors,
                "issues": [],
                "bugs": [],
                "suggestions": [],
            }

            result = await self._execute_stage(
                "mvp",
                user_input,
                extra_kwargs={
                    "feedback": feedback,
                    "current_code": code_files,
                    "iteration": verify_iter + 1,
                },
            )

            if result.status != "success":
                print(f"  [mvp] 修复失败: {result.error}", flush=True)
                break

        return result

    def _check_need_iteration(self, stage_results: Dict[str, StageResult]) -> tuple:
        """检查是否需要迭代"""
        feedback = {}

        # 检查code_review结果
        review_data = stage_results.get("code_review", StageResult(stage="code_review", status="skipped")).data
        if review_data:
            score = review_data.get("overall_score", 100)
            issues = review_data.get("issues", [])
            # 只有存在实际问题才迭代（issues非空且分数低于70）
            if len(issues) > 0 and score < 70:
                feedback["code_review"] = {
                    "issues": issues,
                    "suggestions": review_data.get("suggestions", []),
                    "score": score,
                }

        # 检查testing结果
        test_data = stage_results.get("testing", StageResult(stage="testing", status="skipped")).data
        if test_data:
            bugs = test_data.get("bugs", [])
            critical_bugs = [b for b in bugs if b.get("severity") == "critical"]
            major_bugs = [b for b in bugs if b.get("severity") == "major"]
            if critical_bugs or major_bugs:
                feedback["testing"] = {
                    "bugs": critical_bugs + major_bugs,
                    "suggestions": test_data.get("suggestions", []),
                }

        need_iterate = len(feedback) > 0
        return need_iterate, feedback

    async def _run_iteration(
        self,
        feedback: Dict[str, Any],
        user_input: str,
        stage_results: Dict[str, StageResult],
        failed_stages: List[str],
        degraded_stages: List[str],
    ) -> None:
        """执行迭代循环"""
        iteration = self.state.increment_iteration()

        # 合并反馈
        merged_feedback = {
            "issues": feedback.get("code_review", {}).get("issues", []),
            "bugs": feedback.get("testing", {}).get("bugs", []),
            "suggestions": (
                feedback.get("code_review", {}).get("suggestions", [])
                + feedback.get("testing", {}).get("suggestions", [])
            ),
        }

        issue_count = len(merged_feedback["issues"])
        bug_count = len(merged_feedback["bugs"])
        print(f"\n  === 迭代 {iteration}/{self.max_iterations}: {issue_count}个问题, {bug_count}个Bug ===", flush=True)

        # 记录迭代
        self.state.add_iteration(IterationRecord(
            iteration=iteration,
            stage="code_review" if "code_review" in feedback else "testing",
            reason=f"发现{issue_count}个问题, {bug_count}个Bug",
            issues_count=issue_count,
            bugs_count=bug_count,
        ))

        # 重新执行MVP（带反馈）
        current_code = self.state.get("mvp").get("code_files", [])
        mvp_result = await self._execute_stage(
            "mvp",
            user_input,
            extra_kwargs={
                "feedback": merged_feedback,
                "current_code": current_code,
                "iteration": iteration,
            },
        )
        self._process_stage_result("mvp", mvp_result, stage_results, failed_stages, degraded_stages)
        print(f"  [mvp] 迭代{iteration}完成: {mvp_result.status} ({mvp_result.duration_seconds:.1f}s)", flush=True)

        if mvp_result.status == "error":
            return

        # 重新并行执行code_review + testing
        print(f"  [code_review, testing] 重新审查...", flush=True)
        results = await asyncio.gather(
            self._execute_stage("code_review", user_input),
            self._execute_stage("testing", user_input),
            return_exceptions=True,
        )

        for stage_name, result in zip(["code_review", "testing"], results):
            if isinstance(result, Exception):
                result = StageResult(stage=stage_name, status="error", error=str(result))
            self._process_stage_result(stage_name, result, stage_results, failed_stages, degraded_stages)
            print(f"  [{stage_name}] 迭代{iteration}完成: {result.status} ({result.duration_seconds:.1f}s)", flush=True)

        # 检查是否还需要继续迭代
        need_more, new_feedback = self._check_need_iteration(stage_results)
        if need_more and self.state.current_iteration < self.max_iterations:
            await self._run_iteration(new_feedback, user_input, stage_results, failed_stages, degraded_stages)

    async def _execute_stage(
        self,
        stage_name: str,
        user_input: str,
        extra_kwargs: Dict[str, Any] = None,
    ) -> StageResult:
        """执行单个阶段"""
        agent = self.agents.get(stage_name)
        if not agent:
            return StageResult(stage=stage_name, status="error", error=f"未找到 {stage_name} Agent")

        kwargs = self._build_stage_kwargs(stage_name, user_input)
        if extra_kwargs:
            kwargs.update(extra_kwargs)

        fallback_func = self._get_fallback_func(stage_name)

        async def primary_wrapper(**kw) -> Dict[str, Any]:
            result = await agent.execute(**kw)
            return result.model_dump()

        result_data = await self.fallback.execute(
            stage_name=stage_name,
            primary_func=primary_wrapper,
            fallback_func=fallback_func,
            **kwargs,
        )

        status = result_data.get("status", "error")
        return StageResult(
            stage=stage_name,
            status=status,
            data=result_data.get("data", result_data),
            error=result_data.get("error"),
            agent_used=result_data.get("agent_used", "primary"),
            duration_seconds=result_data.get("duration_seconds", 0.0),
        )

    def _process_stage_result(
        self,
        stage_name: str,
        result: StageResult,
        stage_results: Dict[str, StageResult],
        failed_stages: List[str],
        degraded_stages: List[str],
    ) -> None:
        stage_results[stage_name] = result
        self.state.update(stage_name, result.data)

        if result.status == "error":
            failed_stages.append(stage_name)
        elif result.agent_used == "fallback":
            degraded_stages.append(stage_name)

        self.state.add_history(StageRecord(
            stage=stage_name,
            status=result.status,
            duration_seconds=result.duration_seconds,
            agent_used=result.agent_used,
            error=result.error,
            iteration=self.state.current_iteration,
        ))

    def _build_result(
        self,
        status: str,
        stage_results: Dict[str, StageResult],
        failed_stages: List[str],
        degraded_stages: List[str],
        start: float,
    ) -> PipelineResult:
        return PipelineResult(
            status=status,
            stages=stage_results,
            failed_stages=failed_stages,
            degraded_stages=degraded_stages,
            total_duration=time.time() - start,
        )

    def _build_stage_kwargs(self, stage_name: str, user_input: str) -> Dict[str, Any]:
        if stage_name == "requirements":
            return {"user_input": user_input}
        elif stage_name == "technical":
            return {"requirements": self.state.get("requirements")}
        elif stage_name == "mvp":
            return {
                "technical_solution": self.state.get("technical"),
                "requirements": self.state.get("requirements"),
            }
        elif stage_name == "code_review":
            mvp_data = self.state.get("mvp")
            return {"code_files": mvp_data.get("code_files", []), "project_info": mvp_data}
        elif stage_name == "testing":
            mvp_data = self.state.get("mvp")
            return {"code_files": mvp_data.get("code_files", []), "project_info": mvp_data}
        elif stage_name == "deployment":
            return {
                "code_files": self.state.get("mvp").get("code_files", []),
                "technical_solution": self.state.get("technical"),
                "test_results": self.state.get("testing"),
            }
        return {}

    def _get_fallback_func(self, stage_name: str) -> Callable[..., Dict[str, Any]]:
        fallbacks = {
            "requirements": self._fallback_requirements,
            "technical": self._fallback_technical,
            "mvp": self._fallback_mvp,
            "code_review": self._fallback_code_review,
            "testing": self._fallback_testing,
            "deployment": self._fallback_deployment,
        }
        return fallbacks.get(stage_name, self._fallback_default)

    def _check_dependencies(self, stage_name: str, results: Dict[str, StageResult]) -> bool:
        deps = self.DEPENDENCIES.get(stage_name, [])
        for dep in deps:
            dep_result = results.get(dep)
            if not dep_result or dep_result.status not in ("success", "fallback"):
                return False
        return True

    def _fallback_requirements(self, **kwargs) -> Dict[str, Any]:
        user_input = kwargs.get("user_input", "")
        keywords = [w for w in user_input.split() if len(w) > 3][:5]
        return {
            "status": "fallback",
            "functional_requirements": [{"id": f"FR-{i+1}", "title": kw, "description": f"从输入提取: {kw}"} for i, kw in enumerate(keywords)],
            "non_functional_requirements": [],
            "user_stories": [],
            "acceptance_criteria": [],
            "priority_matrix": {"must_have": [], "should_have": [], "could_have": [], "wont_have": []},
        }

    def _fallback_technical(self, **kwargs) -> Dict[str, Any]:
        return {
            "status": "fallback",
            "tech_stack": {"backend": "Python/FastAPI", "frontend": "React", "database": "PostgreSQL"},
            "architecture": {"pattern": "monolith"},
        }

    def _fallback_mvp(self, **kwargs) -> Dict[str, Any]:
        return {
            "status": "fallback",
            "code_files": [{"path": "main.py", "content": "from fastapi import FastAPI\napp = FastAPI()", "language": "python"}],
            "test_files": [],
        }

    def _fallback_code_review(self, **kwargs) -> Dict[str, Any]:
        return {"status": "fallback", "overall_score": 70, "approved": True, "issues": []}

    def _fallback_testing(self, **kwargs) -> Dict[str, Any]:
        return {"status": "fallback", "test_cases": [], "bugs": [], "coverage": {"line": 0, "branch": 0, "function": 0}}

    def _fallback_deployment(self, **kwargs) -> Dict[str, Any]:
        return {"status": "fallback", "deployment_plan": {"strategy": "rolling", "environments": ["dev", "prod"]}, "docker_config": {"dockerfile": "FROM python:3.11-slim"}}

    def _fallback_default(self, **kwargs) -> Dict[str, Any]:
        return {"status": "fallback"}
