"""
真执行器的离线验证（不联网、不耗 token）

验证 ② 抽出来的三个执行器行为正确，且重构后的 TestingAgent 委托正常：
1. verify_code：正确代码通过，语法错误被捕获
2. run_tests：真实跑 pytest + 冒烟，全绿判定 all_passed
3. run_acceptance：真实跑验收 pytest，逐条解析 PASSED
4. TestingAgent.execute 委托到 run_tests，结果一致
"""

import sys
import asyncio

sys.path.insert(0, r'C:\Users\MECHREV\agent\multi_agent_system_v2')

from tools.executors import verify_code, run_tests, run_acceptance
from tools import executors
from agents.testing import TestingAgent


MAIN_PY = {
    "path": "main.py",
    "language": "python",
    "content": '''from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "hello"}

@app.get("/health")
def health():
    return {"status": "ok"}
''',
}

TEST_API_PY = {
    "path": "tests/test_api.py",
    "language": "python",
    "content": '''from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_root():
    assert client.get("/").status_code == 200

def test_health():
    assert client.get("/health").json() == {"status": "ok"}
''',
}

BROKEN_PY = {
    "path": "broken.py",
    "language": "python",
    "content": "def broken(\n",
}


def test_extract_missing_third_party():
    """缺依赖识别：只认 ModuleNotFoundError 的三方包，排除 stdlib / 本地模块 / ImportError。"""
    # 缺三方依赖 → 提出来补装
    out = "E   ModuleNotFoundError: No module named 'passlib'\n"
    assert executors._extract_missing_third_party(out, [{"path": "main.py"}]) == ["passlib"], "应识别 passlib"
    # 本地模块（mymodule.py 是生成代码）→ 不误报为缺依赖
    out = "E   ModuleNotFoundError: No module named 'mymodule'\n"
    assert executors._extract_missing_third_party(out, [{"path": "mymodule.py"}]) == [], "本地模块不应误报"
    # stdlib → 不误报
    out = "E   ModuleNotFoundError: No module named 'os'\n"
    assert executors._extract_missing_third_party(out, []) == [], "stdlib 不应误报"
    # ImportError cannot import name 是代码级导入 bug，不是缺依赖
    out = "E   ImportError: cannot import name 'foo' from 'bar'\n"
    assert executors._extract_missing_third_party(out, []) == [], "ImportError 不是缺依赖"


def test_root_cause_extraction():
    out = "E   ModuleNotFoundError: No module named 'passlib'\n"
    assert executors._root_cause(out) == "ModuleNotFoundError: No module named 'passlib'"
    assert executors._root_cause("1 passed\n") == ""


def test_self_heal_loop_reinstalls():
    """环境自愈：首跑缺依赖 → 补装 → 重跑，installed 记录补装包名，final_deps 指向新缓存。"""
    calls = {"n": 0}

    def fake_run(deps):
        calls["n"] += 1
        return {"raw": "ModuleNotFoundError: No module named 'passlib'"} if calls["n"] == 1 \
            else {"raw": "1 passed"}

    real_install = executors.install_packages
    executors.install_packages = lambda pkgs: "/fake/deps"
    try:
        result, final_deps, installed = executors._self_heal_loop(
            "/sandbox", 120, None, [{"path": "main.py"}], fake_run,
        )
    finally:
        executors.install_packages = real_install

    assert calls["n"] == 2, f"应重跑一次，实际跑 {calls['n']} 次"
    assert installed == ["passlib"], installed
    assert result["raw"] == "1 passed"
    assert final_deps == "/fake/deps", final_deps


async def main():
    test_extract_missing_third_party()
    test_root_cause_extraction()
    test_self_heal_loop_reinstalls()

    # 1) verify_code：正确代码通过
    r = await verify_code([MAIN_PY, TEST_API_PY])
    assert r["passed"] is True, f"valid code should pass, got {r}"

    # 2) verify_code：语法错误被捕获
    r = await verify_code([BROKEN_PY])
    assert r["passed"] is False
    assert any(e["type"] == "syntax" for e in r["errors"]), f"expected syntax error, got {r}"

    # 3) run_tests：真实跑 pytest + 冒烟，2 个测试全绿
    r = await run_tests([MAIN_PY], [TEST_API_PY])
    assert r["total_tests"] == 2, f"expected 2 tests, got {r['total_tests']}"
    assert r["passed"] == 2 and r["failed"] == 0, f"got {r['passed']}p/{r['failed']}f"
    assert r["all_passed"] is True, f"all_passed should be True, got {r}"
    assert r["smoke_test"]["passed"] is True, f"smoke should pass, got {r['smoke_test']}"

    # 4) run_acceptance：真实跑验收 pytest，逐条解析 PASSED
    criteria = [{"id": "AC-001", "description": "GET /health 返回 200 且 status=ok"}]
    test_code = '''from fastapi.testclient import TestClient
from main import app
client = TestClient(app)

def test_ac_AC_001():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}
'''
    r = await run_acceptance(criteria, [MAIN_PY], test_code)
    assert r["total"] == 1 and r["passed"] == 1, f"got {r['passed']}/{r['total']}"
    assert r["all_passed"] is True, f"acceptance all_passed should be True, got {r}"

    # 5) TestingAgent.execute 委托到 run_tests，结果一致
    agent = TestingAgent(llm=None)
    ar = await agent.execute(code_files=[MAIN_PY], test_files=[TEST_API_PY])
    assert ar.status == "success", f"agent status: {ar.status}"
    assert ar.data["all_passed"] is True and ar.data["passed"] == 2, f"agent data: {ar.data}"

    print("[PASS] executors: verify_code / run_tests / run_acceptance / TestingAgent 委托 全部通过")


if __name__ == "__main__":
    asyncio.run(main())
