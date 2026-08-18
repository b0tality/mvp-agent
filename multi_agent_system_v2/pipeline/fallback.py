"""
故障处理
解决V1的问题：
1. should_abort()只检查consecutive_failures，不检查failed_stages
2. primary_func和fallback_func统一用**kwargs
"""

from typing import Dict, Any, Callable, Awaitable


class FallbackManager:
    """
    故障处理管理器
    
    简化设计：
    - should_abort() 只检查 consecutive_failures
    - failed_stages 仅用于报告
    - 所有函数统一用 **kwargs
    """

    def __init__(self, max_consecutive_failures: int = 2):
        self.max_consecutive_failures = max_consecutive_failures
        self.consecutive_failures = 0
        self.failed_stages: list = []  # 仅报告用

    async def execute(
        self,
        stage_name: str,
        primary_func: Callable[..., Awaitable[Dict[str, Any]]],
        fallback_func: Callable[..., Dict[str, Any]],
        **kwargs,
    ) -> Dict[str, Any]:
        """
        带降级的执行
        
        primary_func 和 fallback_func 都用 **kwargs 接收参数，
        不存在签名不匹配问题。
        """
        # 1. 尝试主函数
        try:
            result = await primary_func(**kwargs)
            self._record_success()
            result["agent_used"] = "primary"
            return result
        except Exception:
            pass

        # 2. 尝试降级函数
        try:
            result = fallback_func(**kwargs)
            self._record_success()
            result["agent_used"] = "fallback"
            return result
        except Exception:
            pass

        # 3. 全部失败
        self._record_failure(stage_name)
        return {
            "status": "error",
            "error": f"阶段 {stage_name} 全部失败",
            "agent_used": "none",
        }

    def _record_success(self):
        self.consecutive_failures = 0

    def _record_failure(self, stage: str):
        self.consecutive_failures += 1
        self.failed_stages.append(stage)

    def should_abort(self) -> bool:
        """只检查连续失败次数"""
        return self.consecutive_failures >= self.max_consecutive_failures

    def get_abort_reason(self) -> str:
        return f"连续{self.consecutive_failures}个阶段失败"
