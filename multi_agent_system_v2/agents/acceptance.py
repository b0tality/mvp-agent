"""
验收测试Agent —— 把验收标准（考卷）转成可执行 pytest 并真实运行

具体执行逻辑委托给 tools.executors.run_acceptance（与 function-calling 工具共享同一实现）。
核心作用：需求阶段产出的 acceptance_criteria 是「考卷」，本 agent 在代码生成后，
把考卷逐条转成真实可跑的测试，核对「需求说返回 400，代码到底是不是 400」。

与 MVP 自带的测试不同：
- MVP 测试由生成代码的同一个 LLM 所写，可能与错误实现互相印证（自洽但错）；
- 验收测试由验收标准驱动，严格按需求断言，代码错了就必须让它失败。
"""

import re
import time
from typing import Dict, Any, List

from agents.base import BaseAgent, AgentResult
from llm.adapter import LLMAdapter
from tools.executors import run_acceptance


class AcceptanceAgent(BaseAgent):
    """验收测试Agent：真实执行验收标准"""

    name = "acceptance"

    def __init__(self, llm: LLMAdapter, timeout: int = 120):
        super().__init__(llm)
        self.timeout = timeout

    async def execute(self, **kwargs) -> AgentResult:
        criteria = kwargs.get("acceptance_criteria", []) or []
        code_files = kwargs.get("code_files", []) or []
        api_design = kwargs.get("api_design", {}) or {}

        if not criteria:
            return self._success({
                "results": [], "total": 0, "passed": 0, "failed": 0,
                "all_passed": True, "raw_output": "",
            })

        if not code_files:
            results = [{
                "criterion_id": c.get("id", ""),
                "description": c.get("description", ""),
                "passed": False, "detail": "无代码",
            } for c in criteria]
            return self._success({
                "results": results, "total": len(criteria), "passed": 0,
                "failed": len(criteria), "all_passed": False, "raw_output": "",
            })

        start = time.time()
        try:
            test_code = await self._generate_acceptance_tests(criteria, code_files, api_design)
            data = await run_acceptance(criteria, code_files, test_code, timeout=self.timeout)
            # UI 验收盲区检测：验收标准描述 UI 行为，但代码没实现前端 → 显式告警
            warnings = self._detect_ui_gap(criteria, code_files)
            if warnings:
                data["warnings"] = warnings
            return self._success(data, time.time() - start)
        except Exception as e:
            return self._error(str(e), time.time() - start)

    # ------------------------------------------------------------------
    # 生成验收测试（这部分需要 LLM）
    # ------------------------------------------------------------------
    async def _generate_acceptance_tests(self, criteria, code_files, api_design) -> str:
        system = """你是一位严格的验收测试工程师。请把「验收标准」逐条转成可执行的 pytest 测试。

要求：
1. 每个验收标准生成一个测试函数，函数名必须是 test_ac_<criterion_id>，其中 criterion_id 里的非字母数字字符替换为下划线（如 AC-001 → test_ac_AC_001）。
2. 测试用**同步**写法，文件顶部固定：
   from fastapi.testclient import TestClient
   from main import app
   client = TestClient(app)
   然后每个测试直接 `resp = client.post(path, json={...})` / `client.get(path)` 同步调用断言。
   **禁止 async def、禁止 AsyncClient/ASGITransport、禁止 async with**——同步 TestClient 对异步 FastAPI 同样可用，且不会出现「client 已关闭」的生命周期问题。
3. 严格按验收标准里写明的期望来断言（状态码、返回内容），不要迁就代码的实际行为——代码错了就必须让它测失败。
4. 根据 api_design 和代码确定正确的 method、path、请求体字段名。
5. 只测验收标准明确要求的行为，不额外发挥。
6. 只输出纯 pytest 代码，不要输出 markdown 代码块标记，不要任何解释文字。"""
        user = f"""验收标准：
{criteria}

API设计：
{api_design}

代码文件（参考导入方式和接口签名）：
{code_files}"""
        code = await self.llm.generate(system, user)
        return self._strip_code_fences(code)

    @staticmethod
    def _strip_code_fences(code: str) -> str:
        code = (code or "").strip()
        m = re.search(r"```(?:python|py)?\s*\n(.*?)```", code, re.DOTALL)
        if m:
            return m.group(1).strip()
        return code

    # ------------------------------------------------------------------
    # UI 验收盲区检测
    # ------------------------------------------------------------------
    _UI_KEYWORDS = [
        "界面", "按钮", "点击", "复选框", "页面", "视觉", "前端", "输入框",
        "浏览器", "表单", "下拉", "弹窗", "视图", "显示在", "导航",
    ]

    @classmethod
    def _is_ui_criterion(cls, description: str) -> bool:
        d = (description or "").lower()
        return any(k in d for k in cls._UI_KEYWORDS)

    @staticmethod
    def _has_frontend(code_files: List[Dict]) -> bool:
        for cf in code_files:
            path = (cf.get("path") or "").lower()
            content = (cf.get("content") or "") or ""
            if path.endswith((".html", ".js", ".css", ".vue", ".jsx", ".tsx")):
                return True
            low = content.lower()
            if "staticfiles" in low or "htmlresponse" in low or "<html" in low or "<script" in low:
                return True
        return False

    @classmethod
    def _detect_ui_gap(cls, criteria: List[Dict], code_files: List[Dict]) -> List[Dict]:
        """若验收标准描述 UI 行为但代码无前端，返回告警（否则验收会形同虚设：UI 标准被映射成 API 测试）。"""
        ui_criteria = [c for c in criteria if cls._is_ui_criterion(c.get("description", ""))]
        if not ui_criteria or cls._has_frontend(code_files):
            return []
        return [{
            "type": "ui_api_gap",
            "message": (
                f"验收标准 {len(ui_criteria)} 条描述 UI 行为（界面/按钮/点击等），"
                "但代码未实现前端（无 html/js/StaticFiles），验收测试被映射为 API 测试，"
                "UI 需求实际未得到验证"
            ),
            "criterion_ids": [c.get("id", "") for c in ui_criteria],
        }]
