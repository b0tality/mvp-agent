"""
测试Agent —— 真实验证 + 确定性不变式测试

两层职责：
1. 基线：真实运行 Builder 自带的测试（pytest + coverage + 冒烟）。
2. 不变式：从应用的 OpenAPI 契约（真实执行 app.openapi()）机械推导「通用不变式」测试
   （id 唯一性/计数一致/删除后 404），真实运行，失败即真 bug。

关键：不变式测试**不是 LLM 写的**，是确定性的、与生成代码的盲区无关的独立裁判——
直接对治「作者自测与代码同源」的 sham。原来的 LLM 对抗测试（red-team QA）因为贵且会
误报（状态隔离、臆测未定义行为），已被这条确定性路径取代。
"""

import re
import time
from typing import Dict, Any, List

from agents.base import BaseAgent, AgentResult
from llm.adapter import LLMAdapter
from tools.executors import run_tests
from tools.invariant_tests import generate_invariant_tests


_ADVERSARIAL_SYSTEM = """（保留：历史对抗测试提示词，当前流程已改用确定性不变式测试，不再调用。）"""


class TestingAgent(BaseAgent):
    """测试Agent：真实执行验证 + 对抗性找 bug"""

    name = "testing"

    def __init__(self, llm: LLMAdapter, timeout: int = 120):
        super().__init__(llm)
        self.timeout = timeout

    async def execute(self, **kwargs) -> AgentResult:
        code_files = kwargs.get("code_files", [])
        project_info = kwargs.get("project_info", {}) or {}
        test_files = kwargs.get("test_files", []) or project_info.get("test_files", [])

        if not code_files:
            return self._success({
                "test_cases": [], "bugs": [],
                "coverage": {"line": 0, "branch": 0, "function": 0},
                "total_tests": 0, "passed": 0, "failed": 0,
                "all_passed": False, "smoke_test": {"passed": False, "detail": "无代码"},
                "summary": "无代码需要测试", "suggestions": [], "raw_output": "",
            })

        start = time.time()
        try:
            data = await run_tests(code_files, test_files, timeout=self.timeout)

            # 确定性不变式测试：非 LLM，从 OpenAPI 契约机械推导，硬门槛（真 bug）
            try:
                inv_code = generate_invariant_tests(code_files)
            except Exception:
                inv_code = ""

            if (inv_code or "").strip():
                inv_file = {"path": "tests/test_invariants.py", "content": inv_code, "language": "python"}
                combined = await run_tests(code_files, test_files + [inv_file], timeout=self.timeout)
                # 不变式测试文件本身没被正确收集（生成器有 bug）→ 退回基线，不把坏测试当 bug
                if not self._adversarial_invalid(combined, data):
                    combined["invariants_generated"] = True
                    data = combined

            return self._success(data, time.time() - start)
        except Exception as e:
            return self._error(str(e), time.time() - start)

    async def _generate_adversarial_tests(self, code_files: List[Dict], test_files: List[Dict]) -> str:
        user = f"代码文件：\n{code_files}\n\n现有测试：\n{test_files}"
        code = await self.llm.generate(_ADVERSARIAL_SYSTEM, user)
        return self._strip_code_fences(code)

    @staticmethod
    def _strip_code_fences(code: str) -> str:
        code = (code or "").strip()
        m = re.search(r"```(?:python|py)?\s*\n(.*?)```", code, re.DOTALL)
        if m:
            return m.group(1).strip()
        return code

    @staticmethod
    def _adversarial_invalid(combined: Dict[str, Any], base: Dict[str, Any]) -> bool:
        """对抗测试文件本身无效（收集/导入错误）→ 返回 True，而非发现了真实 bug。

        只有「基线没有、合并后新增」的 critical 收集类错误才判定为坏测试；
        普通的断言失败（major）是真实 bug 信号，不在这里过滤。
        """
        def critical_descs(r):
            return {b.get("description", "") for b in (r.get("bugs") or [])
                    if b.get("severity") == "critical"}

        new_critical = critical_descs(combined) - critical_descs(base)
        return any(("收集" in d) or ("导入" in d) or ("未收集到" in d) for d in new_critical)

    @staticmethod
    def _split_adversarial(combined: Dict[str, Any]) -> Dict[str, Any]:
        """把「对抗测试失败」从「作者测试失败」里拆出来。

        对抗测试是 LLM 独立生成的 red-team 信号，可能因状态隔离、臆测未定义行为而误报。
        因此：对抗失败仍保留在 bugs 里喂给 builder 修（能抓住 id 唯一性这类真 bug），
        但 all_passed 只看「作者测试 + 冒烟」——对抗失败不硬性阻塞部署。
        """
        adv_path = "tests/test_adversarial.py"
        adv_bugs = [b for b in combined.get("bugs", []) if (b.get("file_path") or "") == adv_path]
        combined["adversarial_bugs"] = adv_bugs

        # 重算 all_passed：作者测试失败数 = 总失败数 - 对抗失败数（每个 FAILED 行对应一个测试）
        author_failed = max(0, combined.get("failed", 0) - len(adv_bugs))
        no_tests = combined.get("passed", 0) == 0 and author_failed == 0
        combined["all_passed"] = (
            author_failed == 0
            and not no_tests
            and (combined.get("smoke_test") or {}).get("passed", False)
        )
        return combined
