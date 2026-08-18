"""
流水线编排器
"""

import asyncio
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

from .state import PipelineState, StageRecord, PipelineCheckpoint
from .config import PipelineConfig
from .stages import Stage, StageExecutor, StageDependency
from .fallback import FallbackManager


@dataclass
class PipelineResult:
    """流水线结果"""
    status: str  # success/partial/failed/aborted
    results: Dict[str, Dict[str, Any]]
    failed_stages: List[str]
    degraded_stages: List[str]
    abort_reason: Optional[str] = None
    cost_report: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "status": self.status,
            "results": self.results,
            "summary": {
                "total_stages": 6,
                "success_stages": len([r for r in self.results.values() if r.get("status") in ["success", "fallback"]]),
                "failed_stages": len(self.failed_stages),
                "degraded_stages": len(self.degraded_stages)
            },
            "failed_stages": self.failed_stages,
            "degraded_stages": self.degraded_stages,
            "abort_reason": self.abort_reason,
            "cost_report": self.cost_report
        }


class PipelineOrchestrator:
    """6-Agent流水线编排器"""
    
    def __init__(self, config: PipelineConfig, agents: Dict[str, Any]):
        """
        初始化流水线编排器
        
        Args:
            config: 流水线配置
            agents: Agent字典，key为阶段名，value为Agent实例
        """
        self.config = config
        self.agents = agents
        self.state = PipelineState()
        self.fallback_manager = FallbackManager(config)
        self.stage_executor = StageExecutor()
        self.stage_dependency = StageDependency()
        self._register_stage_executors()
    
    def _register_stage_executors(self) -> None:
        """注册阶段执行器"""
        self.stage_executor.register(Stage.REQUIREMENTS, self._run_requirements)
        self.stage_executor.register(Stage.TECHNICAL, self._run_technical)
        self.stage_executor.register(Stage.MVP, self._run_mvp)
        self.stage_executor.register(Stage.CODE_REVIEW, self._run_code_review)
        self.stage_executor.register(Stage.TESTING, self._run_testing)
        self.stage_executor.register(Stage.DEPLOYMENT, self._run_deployment)
    
    async def run(self, user_input: str) -> PipelineResult:
        """
        完整流水线运行
        
        Args:
            user_input: 用户输入的需求描述
            
        Returns:
            PipelineResult: 流水线运行结果
        """
        self.state.current_stage = "started"
        results = {}
        failed_stages = []
        degraded_stages = []
        
        stages = [
            Stage.REQUIREMENTS,
            Stage.TECHNICAL,
            Stage.MVP,
            Stage.CODE_REVIEW,
            Stage.TESTING,
            Stage.DEPLOYMENT
        ]
        
        for stage in stages:
            # 检查是否跳过
            if self.config.should_skip(stage):
                results[stage] = {"status": "skipped"}
                self.fallback_manager.cascade_handler.record_success()  # 跳过不算失败
                continue
            
            # 检查依赖
            completed = [s for s in results if results[s].get("status") in ["success", "fallback", "default"]]
            if not self.stage_dependency.can_proceed(stage, completed):
                minimal_deps = self.stage_dependency.get_minimal_deps(stage)
                if not all(dep in completed for dep in minimal_deps):
                    results[stage] = {"status": "skipped", "reason": "依赖不满足"}
                    self.fallback_manager.cascade_handler.record_success()  # 跳过不算失败
                    continue
            
            # 检查是否应该终止
            if self.fallback_manager.should_abort():
                abort_reason = self.fallback_manager.get_abort_reason()
                print(f"DEBUG: Aborting at stage {stage}")
                print(f"DEBUG: abort_reason: {abort_reason}")
                print(f"DEBUG: cascade_handler.consecutive_failures: {self.fallback_manager.cascade_handler.consecutive_failures}")
                print(f"DEBUG: cascade_handler.failed_stages: {self.fallback_manager.cascade_handler.failed_stages}")
                return PipelineResult(
                    status="aborted",
                    results=results,
                    failed_stages=failed_stages,
                    degraded_stages=degraded_stages,
                    abort_reason=abort_reason,
                    cost_report=self.fallback_manager.cost_tracker.get_report()
                )
            
            # 执行阶段
            self.state.current_stage = stage
            started_at = datetime.now()
            
            try:
                result = await self.stage_executor.execute(
                    stage,
                    user_input=user_input if stage == Stage.REQUIREMENTS else None,
                    requirements=self.state.requirements if stage != Stage.REQUIREMENTS else None,
                    technical_solution=self.state.technical_solution if stage in [Stage.MVP, Stage.DEPLOYMENT] else None,
                    code_files=self.state.mvp_result.get("code_files", []) if stage in [Stage.CODE_REVIEW, Stage.TESTING, Stage.DEPLOYMENT] else None,
                    project_info=self.state.mvp_result if stage in [Stage.CODE_REVIEW, Stage.TESTING] else None,
                    test_results=self.state.test_results if stage == Stage.DEPLOYMENT else None
                )
                
                print(f"DEBUG: Stage {stage} completed with status: {result.get('status')}")
                print(f"DEBUG: Stage {stage} agent_used: {result.get('agent_used')}")
                
                # 更新状态
                self.state.update(stage, result)
                results[stage] = result
                
                # 检查是否降级（只有明确标记为非primary时才算降级）
                agent_used = result.get("agent_used")
                if agent_used and agent_used != "primary":
                    degraded_stages.append(stage)
                
                # 记录历史
                completed_at = datetime.now()
                duration = (completed_at - started_at).total_seconds()
                self.state.add_history(StageRecord(
                    stage=stage,
                    status=result.get("status", "success"),
                    started_at=started_at.isoformat(),
                    completed_at=completed_at.isoformat(),
                    duration_seconds=duration,
                    agent_used=result.get("agent_used", "primary")
                ))
                
                # 保存检查点
                self._save_checkpoint(stage)
                
            except Exception as e:
                failed_stages.append(stage)
                results[stage] = {"status": "failed", "error": str(e)}
        
        # 确定最终状态
        if failed_stages:
            if len(failed_stages) == len(stages):
                status = "failed"
            else:
                status = "partial"
        else:
            status = "success"
        
        return PipelineResult(
            status=status,
            results=results,
            failed_stages=failed_stages,
            degraded_stages=degraded_stages,
            cost_report=self.fallback_manager.cost_tracker.get_report()
        )
    
    async def run_stage(self, stage: str, **kwargs) -> Dict[str, Any]:
        """
        运行单个阶段
        
        Args:
            stage: 阶段名称
            **kwargs: 阶段参数
            
        Returns:
            Dict: 阶段执行结果
        """
        return await self.stage_executor.execute(stage, **kwargs)
    
    async def resume_from_checkpoint(self, checkpoint_path: str) -> PipelineResult:
        """
        从检查点恢复
        
        Args:
            checkpoint_path: 检查点文件路径
            
        Returns:
            PipelineResult: 流水线运行结果
        """
        self.state = PipelineState.load_from_file(checkpoint_path)
        # 从最后一个检查点继续
        # TODO: 实现完整的恢复逻辑
        pass
    
    def _save_checkpoint(self, stage: str) -> None:
        """保存检查点"""
        checkpoint = PipelineCheckpoint(
            stage=stage,
            timestamp=datetime.now().isoformat(),
            state_snapshot=self.state.to_dict(),
            agent_states={}
        )
        self.state.add_checkpoint(checkpoint)
        
        # 如果配置了持久化路径，保存到文件
        if self.config.persistence_path:
            self.state.save_to_file(self.config.persistence_path)
    
    # 阶段执行方法
    async def _run_requirements(self, user_input: str, **kwargs) -> Dict[str, Any]:
        """阶段1: 需求分析"""
        agent = self.agents.get("requirements")
        if not agent:
            raise ValueError("未找到需求分析Agent")
        
        return await self.fallback_manager.execute_with_fallback(
            Stage.REQUIREMENTS,
            agent.analyze_requirements,
            [],  # 备用函数列表
            self.fallback_manager.rule_based.requirements_fallback,
            user_input
        )
    
    async def _run_technical(self, requirements: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """阶段2: 技术架构"""
        agent = self.agents.get("technical")
        if not agent:
            raise ValueError("未找到技术架构Agent")
        
        return await self.fallback_manager.execute_with_fallback(
            Stage.TECHNICAL,
            agent.design_technical_solution,
            [],
            self.fallback_manager.rule_based.technical_fallback,
            requirements
        )
    
    async def _run_mvp(self, technical_solution: Dict[str, Any], requirements: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """阶段3: MVP实现"""
        agent = self.agents.get("mvp")
        if not agent:
            raise ValueError("未找到MVP实现Agent")
        
        return await self.fallback_manager.execute_with_fallback(
            Stage.MVP,
            agent.develop_mvp,
            [],
            lambda ts, req: self.fallback_manager.rule_based.mvp_fallback(ts, req),
            technical_solution,
            requirements
        )
    
    async def _run_code_review(self, code_files: List[Dict[str, Any]], project_info: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """阶段4: 代码审查"""
        agent = self.agents.get("code_review")
        if not agent:
            raise ValueError("未找到代码审查Agent")
        
        result = await self.fallback_manager.execute_with_fallback(
            Stage.CODE_REVIEW,
            agent.review_code,
            [],
            self.fallback_manager.rule_based.code_review_fallback,
            code_files,
            project_info
        )
        
        # 检查是否需要回退
        if result.get("overall_score", 100) < 80:
            self.state.add_rollback({
                "from_stage": Stage.CODE_REVIEW,
                "to_stage": Stage.MVP,
                "reason": "quality_score_below_threshold",
                "feedback": result.get("issues", [])
            })
        
        return result
    
    async def _run_testing(self, code_files: List[Dict[str, Any]], project_info: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """阶段5: 测试"""
        agent = self.agents.get("testing")
        if not agent:
            raise ValueError("未找到测试Agent")
        
        result = await self.fallback_manager.execute_with_fallback(
            Stage.TESTING,
            agent.run_tests,
            [],
            self.fallback_manager.rule_based.testing_fallback,
            code_files,
            project_info
        )
        
        # 检查是否有严重bug
        bugs = result.get("bugs", [])
        if any(bug.get("severity") == "critical" for bug in bugs):
            self.state.add_rollback({
                "from_stage": Stage.TESTING,
                "to_stage": Stage.MVP,
                "reason": "critical_bugs_found",
                "feedback": bugs
            })
        
        return result
    
    async def _run_deployment(
        self,
        code_files: List[Dict[str, Any]],
        technical_solution: Dict[str, Any],
        test_results: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """阶段6: 部署规划"""
        agent = self.agents.get("deployment")
        if not agent:
            raise ValueError("未找到部署Agent")
        
        return await self.fallback_manager.execute_with_fallback(
            Stage.DEPLOYMENT,
            agent.plan_deployment,
            [],
            self.fallback_manager.rule_based.deployment_fallback,
            code_files,
            technical_solution,
            test_results
        )
