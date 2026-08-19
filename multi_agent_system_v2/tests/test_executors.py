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


async def main():
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
