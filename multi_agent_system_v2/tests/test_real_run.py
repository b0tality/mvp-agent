"""
实际运行测试：生成代码 → 保存 → 运行验证
"""

import sys
import os
import asyncio
import subprocess
import tempfile
import shutil

sys.path.insert(0, r'C:\Users\MECHREV\agent\multi_agent_system_v2')

from dotenv import load_dotenv
load_dotenv(r'C:\Users\MECHREV\agent\multi_agent_system\.env', override=True)

from llm import OpenAIAdapter
from agents.requirements import RequirementsAgent
from agents.technical import TechnicalAgent
from agents.mvp import MVPAgent

OUTPUT_DIR = r'C:\Users\MECHREV\agent\multi_agent_system_v2\generated_project'


async def generate_project():
    """生成项目代码"""
    from config.settings import PipelineConfig
    config = PipelineConfig.from_env()
    llm = OpenAIAdapter(api_key=config.api_key, base_url=config.base_url, model=config.model)

    user_input = "开发一个简单的待办事项API，支持增删改查"

    # 1. Requirements
    print("[1/3] 需求分析...")
    req = RequirementsAgent(llm)
    req_result = await req.execute(user_input=user_input)
    print(f"  状态: {req_result.status}, 耗时: {req_result.duration_seconds:.1f}s")

    # 2. Technical
    print("[2/3] 技术方案...")
    tech = TechnicalAgent(llm)
    tech_result = await tech.execute(requirements=req_result.data)
    print(f"  状态: {tech_result.status}, 耗时: {tech_result.duration_seconds:.1f}s")

    # 3. MVP
    print("[3/3] 生成代码...")
    mvp = MVPAgent(llm)
    mvp_result = await mvp.execute(
        technical_solution=tech_result.data,
        requirements=req_result.data
    )
    print(f"  状态: {mvp_result.status}, 耗时: {mvp_result.duration_seconds:.1f}s")
    print(f"  代码文件: {len(mvp_result.data.get('code_files', []))}")

    return mvp_result.data


def save_code_files(project_data, output_dir):
    """保存代码文件到目录"""
    code_files = project_data.get("code_files", [])

    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir)

    print(f"\n保存代码到: {output_dir}")
    for cf in code_files:
        path = cf.get("path", "unknown.py")
        content = cf.get("content", "")
        if not content:
            continue

        file_path = os.path.join(output_dir, path)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  - {path} ({len(content)} bytes)")

    return len(code_files)


def verify_syntax(output_dir):
    """验证语法"""
    print("\n语法验证:")
    errors = []
    for root, dirs, files in os.walk(output_dir):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, output_dir)
                result = subprocess.run(
                    [sys.executable, "-m", "py_compile", file_path],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.returncode == 0:
                    print(f"  OK: {rel_path}")
                else:
                    print(f"  FAIL: {rel_path}")
                    print(f"    {result.stderr.strip()}")
                    errors.append(rel_path)

    return errors


def try_import(output_dir):
    """尝试导入main模块"""
    print("\n导入测试:")
    sys.path.insert(0, output_dir)
    try:
        import importlib
        spec = importlib.util.spec_from_file_location("main", os.path.join(output_dir, "main.py"))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        print("  OK: main.py 导入成功")

        # 检查是否有FastAPI app
        if hasattr(module, "app"):
            print(f"  OK: 找到 FastAPI app: {type(module.app).__name__}")
        elif hasattr(module, "app"):
            print(f"  OK: 找到 Flask app: {type(module.app).__name__}")

        return True
    except Exception as e:
        print(f"  FAIL: {e}")
        return False


def try_run_server(output_dir):
    """尝试启动服务器"""
    print("\n启动测试:")
    main_path = os.path.join(output_dir, "main.py")
    if not os.path.exists(main_path):
        print("  SKIP: main.py 不存在")
        return

    # 检查是否安装了依赖
    req_path = os.path.join(output_dir, "requirements.txt")
    if os.path.exists(req_path):
        print("  安装依赖...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", req_path, "-q"],
            capture_output=True,
            timeout=60,
        )

    # 尝试启动服务器（后台运行，几秒后停止）
    print("  启动服务器...")
    try:
        proc = subprocess.Popen(
            [sys.executable, main_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=output_dir,
        )

        # 等待几秒
        import time
        time.sleep(3)

        # 检查是否还在运行
        if proc.poll() is None:
            print("  OK: 服务器启动成功 (PID: {})".format(proc.pid))
            proc.terminate()
            proc.wait(timeout=5)
            return True
        else:
            stdout = proc.stdout.read().decode() if proc.stdout else ""
            stderr = proc.stderr.read().decode() if proc.stderr else ""
            print(f"  FAIL: 服务器退出，返回码: {proc.returncode}")
            if stderr:
                print(f"  STDERR: {stderr[:500]}")
            return False
    except subprocess.TimeoutExpired:
        proc.terminate()
        print("  OK: 服务器启动成功（超时强制停止）")
        return True
    except Exception as e:
        print(f"  FAIL: {e}")
        return False


async def main():
    print("=" * 60)
    print("实际运行测试")
    print("=" * 60)

    # 1. 生成代码
    project_data = await generate_project()

    # 2. 保存代码
    file_count = save_code_files(project_data, OUTPUT_DIR)
    if file_count == 0:
        print("\n没有代码文件，退出")
        return

    # 3. 语法验证
    syntax_errors = verify_syntax(OUTPUT_DIR)
    if syntax_errors:
        print(f"\n语法错误: {syntax_errors}")

    # 4. 导入测试
    import_ok = try_import(OUTPUT_DIR)

    # 5. 启动测试
    if import_ok:
        run_ok = try_run_server(OUTPUT_DIR)
    else:
        print("\n跳过启动测试（导入失败）")

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


asyncio.run(main())
