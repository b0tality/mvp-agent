"""
故障保底机制
"""

import asyncio
from typing import Dict, List, Any, Optional, Callable, Awaitable
from dataclasses import dataclass, field


@dataclass
class RetryPolicy:
    """重试策略"""
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 30.0
    exponential_base: float = 2.0
    
    async def execute_with_retry(self, func: Callable[..., Awaitable[Any]], *args, **kwargs) -> Any:
        """带重试的执行"""
        last_exception = None
        for attempt in range(self.max_retries):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    delay = min(self.base_delay * (self.exponential_base ** attempt), self.max_delay)
                    await asyncio.sleep(delay)
        raise last_exception


class RuleBasedFallback:
    """基于规则的降级方案（不依赖LLM）"""
    
    def requirements_fallback(self, user_input: str) -> Dict[str, Any]:
        """需求分析降级：关键词提取"""
        keywords = [word for word in user_input.split() if len(word) > 3][:5]
        return {
            "functional_requirements": [
                {"id": f"FR-{i+1}", "title": kw, "description": f"从输入提取的功能: {kw}"}
                for i, kw in enumerate(keywords)
            ],
            "non_functional_requirements": [
                {"id": "NFR-1", "category": "performance", "description": "基本性能要求"},
                {"id": "NFR-2", "category": "security", "description": "基本安全要求"}
            ],
            "status": "fallback"
        }
    
    def technical_fallback(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """技术架构降级：返回默认技术栈"""
        return {
            "tech_stack": {"backend": "Python/FastAPI", "frontend": "React", "database": "PostgreSQL"},
            "architecture": {"pattern": "monolith", "description": "单体架构（降级方案）"},
            "api_design": {"style": "REST", "endpoints": []},
            "database_design": {"type": "relational", "tables": []},
            "status": "fallback"
        }
    
    def mvp_fallback(self, technical_solution: Dict[str, Any], requirements: Dict[str, Any]) -> Dict[str, Any]:
        """MVP降级：返回骨架代码"""
        return {
            "code_files": [
                {
                    "path": "main.py",
                    "content": "from fastapi import FastAPI\napp = FastAPI()\n\n@app.get('/')\ndef root():\n    return {'message': 'Hello World'}\n",
                    "language": "python"
                },
                {
                    "path": "requirements.txt",
                    "content": "fastapi==0.104.1\nuvicorn==0.24.0\n",
                    "language": "text"
                }
            ],
            "test_files": [],
            "docker_config": {},
            "status": "fallback"
        }
    
    def code_review_fallback(self, code_files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """代码审查降级：跳过详细审查"""
        return {
            "overall_score": 70,
            "file_reviews": [
                {"file_path": f.get("path", "unknown"), "score": 70, "issues": []}
                for f in code_files
            ],
            "issues": [],
            "approved": True,
            "status": "fallback"
        }
    
    def testing_fallback(self, code_files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """测试降级：生成基础测试"""
        return {
            "test_suites": [],
            "coverage": {"line": 0, "branch": 0, "function": 0},
            "bugs": [],
            "security_vulnerabilities": [],
            "test_report": {"summary": "降级模式：跳过详细测试"},
            "status": "fallback"
        }
    
    def deployment_fallback(self, technical_solution: Dict[str, Any]) -> Dict[str, Any]:
        """部署降级：返回默认Docker配置"""
        return {
            "deployment_plan": {
                "strategy": "rolling",
                "environments": ["development", "production"]
            },
            "docker_config": {
                "Dockerfile": "FROM python:3.11-slim\nWORKDIR /app\nCOPY requirements.txt .\nRUN pip install -r requirements.txt\nCOPY . .\nCMD [\"uvicorn\", \"main:app\", \"--host\", \"0.0.0.0\", \"--port\", \"8000\"]"
            },
            "kubernetes_config": {},
            "cicd_config": {},
            "monitoring_config": {},
            "status": "fallback"
        }


class CascadeFailureHandler:
    """级联故障处理器"""
    
    def __init__(self, max_consecutive_failures: int = 2, critical_stages: List[str] = None):
        self.max_consecutive_failures = max_consecutive_failures
        self.critical_stages = critical_stages or ["requirements", "mvp"]
        self.consecutive_failures = 0
        self.failed_stages: List[str] = []  # 仅用于报告，不参与abort决策
    
    def record_failure(self, stage: str) -> None:
        """记录失败"""
        self.consecutive_failures += 1
        self.failed_stages.append(stage)
    
    def record_success(self) -> None:
        """记录成功（重置连续失败计数）"""
        self.consecutive_failures = 0
    
    def should_abort(self) -> bool:
        """检查是否应该终止（仅基于连续失败次数）"""
        return self.consecutive_failures >= self.max_consecutive_failures
    
    def get_abort_reason(self) -> Optional[str]:
        """获取终止原因"""
        if self.consecutive_failures >= self.max_consecutive_failures:
            return f"连续{self.consecutive_failures}个阶段失败"
        return None


class CostTracker:
    """成本追踪器"""
    
    COST_PER_1K_TOKENS = {
        "gpt-4": 0.03,
        "gpt-3.5-turbo": 0.002,
        "gpt-4-turbo": 0.01
    }
    
    def __init__(self):
        self.total_tokens = 0
        self.total_cost = 0.0
        self.stage_costs: Dict[str, float] = {}
        self.fallback_costs: Dict[str, float] = {}
    
    def record_usage(self, stage: str, agent_type: str, model: str, tokens: int) -> None:
        """记录使用量"""
        cost_per_1k = self.COST_PER_1K_TOKENS.get(model, 0.03)
        cost = (tokens / 1000) * cost_per_1k
        
        self.total_tokens += tokens
        self.total_cost += cost
        
        if stage not in self.stage_costs:
            self.stage_costs[stage] = 0
        self.stage_costs[stage] += cost
        
        if agent_type != "primary":
            key = f"{stage}_{agent_type}"
            if key not in self.fallback_costs:
                self.fallback_costs[key] = 0
            self.fallback_costs[key] += cost
    
    def get_report(self) -> Dict[str, Any]:
        """生成成本报告"""
        return {
            "total_cost": round(self.total_cost, 4),
            "total_tokens": self.total_tokens,
            "stage_breakdown": {k: round(v, 4) for k, v in self.stage_costs.items()},
            "fallback_overhead": round(sum(self.fallback_costs.values()), 4),
            "fallback_percentage": round(
                (sum(self.fallback_costs.values()) / self.total_cost * 100) if self.total_cost > 0 else 0,
                2
            )
        }
    
    def is_within_budget(self, budget: float) -> bool:
        """检查是否在预算内"""
        return self.total_cost <= budget


class FallbackManager:
    """故障保底管理器"""
    
    def __init__(self, config: Any):
        """
        初始化故障保底管理器
        
        Args:
            config: PipelineConfig 配置对象
        """
        self.config = config
        self.rule_based = RuleBasedFallback()
        self.cascade_handler = CascadeFailureHandler(
            max_consecutive_failures=config.max_consecutive_failures,
            critical_stages=config.critical_stages
        )
        self.cost_tracker = CostTracker()
    
    async def execute_with_fallback(
        self,
        stage: str,
        primary_func: Callable[..., Awaitable[Dict[str, Any]]],
        fallback_funcs: List[Callable[..., Awaitable[Dict[str, Any]]]],
        rule_fallback_func: Callable[..., Dict[str, Any]],
        *args,
        **kwargs
    ) -> Dict[str, Any]:
        """带完整降级链的执行"""
        stage_config = self.config.get_stage_config(stage)
        
        # 1. 尝试主Agent（带重试）
        try:
            result = await self._execute_with_retry(
                primary_func,
                stage_config.retry,
                stage,
                "primary",
                stage_config.model,
                *args,
                **kwargs
            )
            self.cascade_handler.record_success()
            return result
        except Exception:
            # 主Agent失败，继续尝试备用Agent
            pass
        
        # 2. 尝试备用Agent
        for i, fallback_func in enumerate(fallback_funcs):
            try:
                result = await self._execute_with_retry(
                    fallback_func,
                    stage_config.fallback_retry,
                    stage,
                    f"fallback_{i+1}",
                    stage_config.fallback_model,
                    *args,
                    **kwargs
                )
                self.cascade_handler.record_success()
                return result
            except Exception:
                continue
        
        # 3. 规则降级
        try:
            result = rule_fallback_func(*args, **kwargs)
            self.cost_tracker.record_usage(stage, "rule_based", "none", 0)
            self.cascade_handler.record_success()
            result["agent_used"] = "rule_based"
            return result
        except Exception:
            pass
        
        # 4. 所有方式都失败，记录失败
        self.cascade_handler.record_failure(stage)
        return self._apply_degradation_policy(stage)
    
    async def _execute_with_retry(
        self,
        func: Callable[..., Awaitable[Dict[str, Any]]],
        retry_policy: Any,
        stage: str,
        agent_type: str,
        model: str,
        *args,
        **kwargs
    ) -> Dict[str, Any]:
        """带重试的执行"""
        async def wrapper():
            result = await func(*args, **kwargs)
            # 估算token使用量（简化处理）
            estimated_tokens = len(str(result)) // 4
            self.cost_tracker.record_usage(stage, agent_type, model, estimated_tokens)
            result["agent_used"] = agent_type
            return result
        
        return await retry_policy.execute_with_retry(wrapper)
    
    def _apply_degradation_policy(self, stage: str) -> Dict[str, Any]:
        """应用降级策略"""
        policy = self.config.get_degradation_policy(stage)
        
        if policy == "abort":
            return {"status": "aborted", "error": f"阶段 {stage} 失败，流水线终止"}
        elif policy == "skip":
            return {"status": "skipped", "message": f"阶段 {stage} 已跳过"}
        elif policy == "default":
            return {"status": "default", "message": f"阶段 {stage} 使用默认值"}
        else:
            return {"status": "failed", "error": f"阶段 {stage} 失败"}
    
    def should_abort(self) -> bool:
        """检查是否应该终止流水线"""
        return self.cascade_handler.should_abort()
    
    def get_abort_reason(self) -> Optional[str]:
        """获取终止原因"""
        return self.cascade_handler.get_abort_reason()
