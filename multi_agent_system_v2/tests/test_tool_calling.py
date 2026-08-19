"""
generate_with_tools 的离线单元测试（mock client，不联网、不耗 token）

验证 agentic 循环：
1. LLM 的 tool_calls 被正确执行并把结果回灌（role=tool 消息）
2. tools 参数原样传给 API
3. 循环在 LLM 不再调用工具时结束，返回最终回答
4. 可选 output_schema 把最终回答解析成 Pydantic 模型
5. 未知工具 / 工具抛异常时降级为错误文本，不中断循环
"""

import sys
import asyncio
import json

sys.path.insert(0, r'C:\Users\MECHREV\agent\multi_agent_system_v2')

from llm import OpenAIAdapter
from pydantic import BaseModel


# ----------------------------------------------------------------------
# 假 OpenAI client：按 script 顺序返回消息，并记录每次 create 的入参
# ----------------------------------------------------------------------
class FakeTCFunction:
    def __init__(self, name, arguments):
        self.name = name
        self.arguments = arguments


class FakeToolCall:
    def __init__(self, call_id, name, arguments):
        self.id = call_id
        self.type = "function"
        self.function = FakeTCFunction(name, arguments)


class FakeMessage:
    def __init__(self, content=None, tool_calls=None):
        self.content = content
        self.tool_calls = tool_calls


class FakeChoice:
    def __init__(self, message):
        self.message = message


class FakeResponse:
    def __init__(self, message):
        self.choices = [FakeChoice(message)]


class FakeCompletions:
    def __init__(self, script):
        self.script = list(script)
        self.calls = []

    async def create(self, **kwargs):
        self.calls.append(kwargs)
        i = len(self.calls) - 1
        if i < len(self.script):
            return FakeResponse(self.script[i])
        return FakeResponse(FakeMessage(content="done"))


class FakeChat:
    def __init__(self, script):
        self.completions = FakeCompletions(script)


class FakeClient:
    def __init__(self, script):
        self.chat = FakeChat(script)


def build_llm(script):
    """构造一个带全新 fake client 的 adapter，返回 (llm, completions)。"""
    llm = OpenAIAdapter(api_key="k", base_url="http://x", model="m")
    llm.client = FakeClient(script)
    return llm, llm.client.chat.completions


async def add(args):
    return {"sum": args["a"] + args["b"]}


async def boom(args):
    raise RuntimeError("内部错误")


TOOLS = [{
    "type": "function",
    "function": {
        "name": "add",
        "description": "两数相加",
        "parameters": {
            "type": "object",
            "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}},
            "required": ["a", "b"],
        },
    },
}]

SCRIPT_TWO_ROUNDS = [
    FakeMessage(tool_calls=[FakeToolCall("call_1", "add", '{"a": 1, "b": 2}')]),
    FakeMessage(content='{"result": 3}'),
]


async def main():
    # 1) 返回最终文本
    llm, compl = build_llm(SCRIPT_TWO_ROUNDS)
    text = await llm.generate_with_tools("sys", "user", TOOLS, {"add": add})
    assert text == '{"result": 3}', f"got: {text!r}"

    # 2) 工具结果被回灌：第2轮 messages 里有 role=tool 消息
    second_call = compl.calls[1]
    tool_msgs = [m for m in second_call["messages"] if m["role"] == "tool"]
    assert len(tool_msgs) == 1, f"expected 1 tool msg, got {tool_msgs}"
    assert json.loads(tool_msgs[0]["content"]) == {"sum": 3}

    # 3) tools 参数原样传给 API
    assert second_call["tools"] == TOOLS

    # 4) output_schema 解析最终回答
    class Out(BaseModel):
        result: int

    llm2, _ = build_llm(SCRIPT_TWO_ROUNDS)
    model = await llm2.generate_with_tools("sys", "user", TOOLS, {"add": add}, output_schema=Out)
    assert isinstance(model, Out) and model.result == 3

    # 5) 未知工具 → 错误文本回灌，不抛异常
    script_unknown = [
        FakeMessage(tool_calls=[FakeToolCall("call_1", "nope", '{}')]),
        FakeMessage(content="ok"),
    ]
    llm3, compl3 = build_llm(script_unknown)
    out = await llm3.generate_with_tools("sys", "user", TOOLS, {"add": add})
    assert out == "ok"
    tool_msg = [m for m in compl3.calls[1]["messages"] if m["role"] == "tool"][0]
    assert "未知工具" in tool_msg["content"]

    # 6) 工具抛异常 → 错误文本回灌，不中断
    script_boom = [
        FakeMessage(tool_calls=[FakeToolCall("call_1", "add", '{"a": 1, "b": 2}')]),
        FakeMessage(content="ok"),
    ]
    llm4, compl4 = build_llm(script_boom)
    out = await llm4.generate_with_tools("sys", "user", TOOLS, {"add": boom})
    assert out == "ok"
    tool_msg = [m for m in compl4.calls[1]["messages"] if m["role"] == "tool"][0]
    assert "执行出错" in tool_msg["content"]

    print("[PASS] generate_with_tools: 工具调用 → 执行 → 回灌 → 最终回答/结构化解析/异常降级 全部通过")


if __name__ == "__main__":
    asyncio.run(main())
