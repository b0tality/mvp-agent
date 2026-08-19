"""
依赖安装器（非 LLM，确定性）

真实执行（pytest / coverage / 冒烟 / 验收 / 不变式测试）都在**当前 Python 环境**里跑，
但生成的代码可能 import 本环境没装的三方库（如 passlib、bcrypt、PyJWT 等），
一旦 import 失败，pytest 在「收集」阶段就报 ImportError，导致：
- 作者测试 0 个收集到、覆盖率骤降
- 验收测试 0/14 全灭
- 不变式测试因 `app.openapi()` 无法导入而整体跳过

这里的修复：执行前把生成代码里声明的 `requirements.txt` 装进**按内容哈希分片的共享缓存**，
把缓存目录塞进 PYTHONPATH，让 import 能命中，且跨运行复用（同一份依赖只装一次）。

关键降级：安装失败不抛异常、不阻塞流程——退回「现状」（import 失败会如实反映在测试结果里）。
"""

import os
import sys
import hashlib
import tempfile
import subprocess
from typing import Dict, List, Optional

_CACHE_ROOT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "output", ".deps_cache",
)


def _requirements_content(code_files: List[Dict]) -> Optional[str]:
    """从 code_files 里找 requirements.txt（或 .txt），返回内容；找不到返回 None。"""
    for cf in code_files:
        path = (cf.get("path") or "").strip().replace("\\", "/").rstrip("/").lower()
        if path == "requirements.txt" or path.endswith("/requirements.txt"):
            content = (cf.get("content") or "").strip()
            if content:
                return content
    return None


def ensure_deps(code_files: List[Dict], timeout: int = 180) -> Optional[str]:
    """确保生成代码的三方依赖可导入，返回可加入 PYTHONPATH 的缓存目录（无依赖则 None）。

    以 requirements.txt 内容哈希为 key 分片缓存：同一份依赖只 `pip install --target` 一次。
    安装失败（无网络/编译失败）时返回 None，不影响流程——后续 import 失败会如实报错。
    """
    req = _requirements_content(code_files)
    if not req:
        return None

    key = hashlib.sha256(req.encode("utf-8")).hexdigest()[:16]
    target = os.path.join(_CACHE_ROOT, key)
    done = os.path.join(target, ".done")

    if not os.path.isfile(done):
        os.makedirs(target, exist_ok=True)
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".txt", prefix="req_", delete=False, encoding="utf-8"
            ) as rf:
                rf.write(req)
                req_path = rf.name
            subprocess.run(
                [sys.executable, "-m", "pip", "install",
                 "--quiet", "--disable-pip-version-check", "--target", target, "-r", req_path],
                capture_output=True, text=True, timeout=timeout, check=True,
            )
        except Exception:
            # 安装失败：退回无缓存目录。若目录里残留了不完整内容，也别当成有效缓存。
            return None
        finally:
            try:
                os.unlink(req_path)
            except Exception:
                pass
        with open(done, "w", encoding="utf-8") as f:
            f.write("ok\n")

    return target if os.path.isdir(target) else None


# import 名 → pip 包名 不一致的常见映射（import jwt → PyJWT 等）
_IMPORT_TO_PIP = {
    "jwt": "PyJWT",
    "cv2": "opencv-python-headless",
    "PIL": "Pillow",
    "sklearn": "scikit-learn",
    "yaml": "PyYAML",
    "bs4": "beautifulsoup4",
    "dotenv": "python-dotenv",
    "attr": "attrs",
}


def install_packages(packages: List[str], timeout: int = 180) -> Optional[str]:
    """安装一组明确的包名到共享缓存（用于环境自愈），返回缓存目录；失败返回 None。

    与 ensure_deps 的区别：这里按「包名列表」直接 pip install，而不是读 requirements.txt。
    供 run_tests/run_acceptance 在检测到 `ModuleNotFoundError` 后补装缺失依赖时调用。
    """
    if not packages:
        return None

    pkgs = sorted({_IMPORT_TO_PIP.get(p, p) for p in packages})
    key = "pkg_" + hashlib.sha256("\n".join(pkgs).encode("utf-8")).hexdigest()[:16]
    target = os.path.join(_CACHE_ROOT, key)
    done = os.path.join(target, ".done")

    if not os.path.isfile(done):
        os.makedirs(target, exist_ok=True)
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install",
                 "--quiet", "--disable-pip-version-check", "--target", target] + pkgs,
                capture_output=True, text=True, timeout=timeout, check=True,
            )
        except Exception:
            return None
        with open(done, "w", encoding="utf-8") as f:
            f.write("ok\n")

    return target if os.path.isdir(target) else None
