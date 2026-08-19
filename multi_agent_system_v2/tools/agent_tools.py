"""
function-calling 工具：把真执行器暴露给 LLM 自主调用。

TOOL_HANDLERS 是「工具名 -> 可调用对象」映射，直接喂给 LLMAdapter.generate_with_tools；
TOOL_SCHEMAS 是对应的 OpenAI function-calling schema 列表。

注意：这里的 schema 是「纯执行器」的低层签名（显式传 code_files 等完整数据）。
builder agent（下一步）会用带状态的最小参数包装器，避免让 LLM 在工具参数里搬运整份代码。
"""

from .executors import verify_code, run_tests, run_acceptance

TOOL_HANDLERS = {
    "verify_code": verify_code,
    "run_tests": run_tests,
    "run_acceptance": run_acceptance,
}

_FILE_SCHEMA = {
    "type": "object",
    "properties": {
        "path": {"type": "string", "description": "文件路径，如 main.py"},
        "content": {"type": "string", "description": "文件内容"},
        "language": {"type": "string", "description": "语言，如 python"},
    },
    "required": ["path", "content"],
}

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "verify_code",
            "description": "对代码文件做语法(AST)+编译(py_compile)检查，返回编译错误列表。passed=true 表示无错误。",
            "parameters": {
                "type": "object",
                "properties": {
                    "code_files": {"type": "array", "items": _FILE_SCHEMA},
                },
                "required": ["code_files"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_tests",
            "description": "把代码和测试写入沙箱，真实运行 pytest + 测覆盖率 + 冒烟探活，返回通过/失败数和 bug。",
            "parameters": {
                "type": "object",
                "properties": {
                    "code_files": {"type": "array", "items": _FILE_SCHEMA},
                    "test_files": {"type": "array", "items": _FILE_SCHEMA},
                },
                "required": ["code_files"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_acceptance",
            "description": "把验收 pytest 代码写入沙箱并真实运行，逐条核对验收标准是否通过。",
            "parameters": {
                "type": "object",
                "properties": {
                    "criteria": {"type": "array", "items": {"type": "object"}},
                    "code_files": {"type": "array", "items": _FILE_SCHEMA},
                    "test_code": {"type": "string", "description": "验收 pytest 测试代码"},
                },
                "required": ["criteria", "code_files", "test_code"],
            },
        },
    },
]
