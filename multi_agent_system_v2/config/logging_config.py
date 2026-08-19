"""
日志配置：控制台 + 文件双输出。

运行中实时写 run.log（含时间戳），跑挂了也能定位「何时、哪个组件、哪次 LLM 调用」。
"""

import logging
import os


def setup_logging(log_dir: str, level: int = logging.INFO) -> str:
    """初始化根 logger（控制台 INFO + 文件 DEBUG），返回日志文件绝对路径。"""
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "run.log")

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    # 清掉旧 handler，避免重复 setup 时日志重复打印
    for h in list(root.handlers):
        root.removeHandler(h)

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )

    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(fmt)
    root.addHandler(console)

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(fmt)
    root.addHandler(file_handler)

    # 静默第三方库的 DEBUG/INFO 噪音：openai/httpcore 会完整 dump 请求响应体，
    # httpx 会为每次请求打一条 INFO。它们与我们自己的 llm/pipeline 日志重复，只保留 WARNING 及以上。
    for noisy in ("openai", "httpcore", "httpx"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    logging.getLogger("logging_config").info("日志已初始化 → %s", log_path)
    return log_path
