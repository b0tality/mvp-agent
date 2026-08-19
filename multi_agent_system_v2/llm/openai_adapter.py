"""
OpenAI兼容API适配器
支持OpenAI API以及兼容接口（如小米MiMo）
"""

import json
import time
import inspect
import logging
from typing import Type, TypeVar, Optional, List, Dict, Any, Callable
from pydantic import BaseModel, ValidationError
from openai import AsyncOpenAI

from .adapter import LLMAdapter

T = TypeVar("T", bound=BaseModel)
logger = logging.getLogger("llm")


class OpenAIAdapter(LLMAdapter):
    """
    OpenAI兼容API适配器
    
    支持:
    - OpenAI官方API
    - 任何兼容OpenAI格式的API（如小米MiMo）
    """

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        timeout: float = 120.0,
        max_retries: int = 1,
    ):
        # 显式设 timeout/max_retries：默认 600s 超时 + 2 次重试，一次挂起的请求能拖 15-30 分钟，
        # 把整条流水线卡死在单次 LLM 调用上（实测 code_review 曾卡 913s）。
        self.client = AsyncOpenAI(
            api_key=api_key, base_url=base_url, timeout=timeout, max_retries=max_retries
        )
        self.model = model

    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        """生成文本响应"""
        t0 = time.time()
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            logger.info("generate ok model=%s took=%.1fs", self.model, time.time() - t0)
            return response.choices[0].message.content
        except Exception as e:
            logger.error("generate failed model=%s took=%.1fs err=%s", self.model, time.time() - t0, e)
            raise

    async def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        output_schema: Type[T],
        max_retries: int = 2,
    ) -> T:
        """
        生成结构化响应

        策略：用json_object模式 + 在prompt中描述期望的JSON结构。
        这比json_schema模式更可靠（MiMo对json_schema支持不完整）。

        JSON校验失败时自动重试，把校验错误反馈给LLM让其修正，
        避免单次格式错误导致整个流水线阶段失败。
        """
        # 构建schema描述，告诉LLM期望的JSON结构
        schema_desc = self._build_schema_description(output_schema)

        base_system_prompt = f"""{system_prompt}

你必须以严格的JSON格式输出，结构如下：
{schema_desc}

只输出JSON，不要输出任何其他文字。"""

        last_error = None
        for attempt in range(max_retries + 1):
            prompt = base_system_prompt
            if last_error is not None:
                prompt += f"\n\n上次输出校验失败，错误如下，请务必修正JSON结构后重新输出：\n{last_error}"

            t0 = time.time()
            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    response_format={"type": "json_object"},
                )
            except Exception as e:
                logger.error("generate_structured failed model=%s attempt=%d took=%.1fs err=%s",
                             self.model, attempt, time.time() - t0, e)
                raise
            logger.info("generate_structured model=%s attempt=%d took=%.1fs",
                        self.model, attempt, time.time() - t0)
            content = response.choices[0].message.content
            try:
                return output_schema.model_validate_json(content)
            except ValidationError as e:
                last_error = e
                logger.warning("generate_structured 校验失败 attempt=%d err=%s", attempt, e)

        raise last_error

    async def generate_with_tools(
        self,
        system_prompt: str,
        user_prompt: str,
        tools: List[Dict[str, Any]],
        tool_handlers: Dict[str, Callable[..., Any]],
        output_schema: Optional[Type[BaseModel]] = None,
        max_rounds: int = 6,
    ) -> Any:
        """
        带 function-calling 的 agentic 循环。

        LLM 自主决定调用哪个工具；适配器执行工具并把结果以 role=tool 消息回灌，
        循环直到 LLM 不再调用工具（给出最终回答）或达到 max_rounds。

        tool_handlers 里的可调用对象接受一个 args dict（LLM 传来的 JSON 参数），
        返回任意可 JSON 序列化的结果；同步/异步均支持。
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        final_text = ""

        for round_i in range(max_rounds):
            t0 = time.time()
            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=tools,
                    tool_choice="auto",
                )
            except Exception as e:
                logger.error("generate_with_tools failed model=%s round=%d took=%.1fs err=%s",
                             self.model, round_i, time.time() - t0, e)
                raise
            msg = response.choices[0].message
            tool_calls = getattr(msg, "tool_calls", None) or []

            if not tool_calls:
                final_text = msg.content or ""
                logger.info("generate_with_tools final model=%s round=%d took=%.1fs",
                            self.model, round_i, time.time() - t0)
                break

            logger.info("generate_with_tools round=%d model=%s tools=%s took=%.1fs",
                        round_i, self.model, [tc.function.name for tc in tool_calls], time.time() - t0)

            # 记录 assistant 消息（含 tool_calls）
            messages.append({
                "role": "assistant",
                "content": msg.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in tool_calls
                ],
            })
            final_text = msg.content or ""

            # 逐个执行工具，把结果作为 role=tool 消息回灌
            for tc in tool_calls:
                name = tc.function.name
                try:
                    args = json.loads(tc.function.arguments or "{}")
                except json.JSONDecodeError:
                    args = {}

                handler = tool_handlers.get(name)
                if handler is None:
                    result = f"错误：未知工具 {name}"
                else:
                    try:
                        r = handler(args)
                        if inspect.isawaitable(r):
                            r = await r
                        result = json.dumps(r, ensure_ascii=False, default=str)
                    except Exception as e:
                        result = f"工具 {name} 执行出错: {e}"

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result,
                })

        if output_schema is not None and final_text:
            return output_schema.model_validate_json(final_text)
        return final_text

    def _build_schema_description(self, schema_class: Type[BaseModel]) -> str:
        """从Pydantic模型生成JSON结构描述。

        递归展开嵌套模型（$ref），确保LLM知道每个字段应为对象而非字符串。
        否则嵌套模型字段会被误标为 any 类型，导致LLM返回字符串而非对象。
        """
        schema = schema_class.model_json_schema()
        defs = schema.get("$defs", {})
        properties = schema.get("properties", {})
        required = set(schema.get("required", []))

        lines = ["{"]
        names = list(properties.keys())
        for i, (name, prop) in enumerate(properties.items()):
            type_str = self._describe_property(prop, defs)
            req_str = " (required)" if name in required else " (optional)"
            comma = "," if i < len(names) - 1 else ""
            description = prop.get("description", "")
            lines.append(f'  "{name}": {type_str}{req_str}  // {description}{comma}')

        lines.append("}")
        return "\n".join(lines)

    def _describe_property(self, prop: dict, defs: dict) -> str:
        """描述单个属性的JSON类型，递归展开$ref嵌套模型。"""
        # $ref 引用嵌套模型 → 展开为内联对象描述
        if "$ref" in prop:
            ref_name = prop["$ref"].split("/")[-1]
            target = defs.get(ref_name, {})
            target_props = target.get("properties")
            if target_props:
                inner = [
                    f'"{k}": {self._describe_property(v, defs)}'
                    for k, v in target_props.items()
                ]
                return "{" + ", ".join(inner) + "}"
            return ref_name

        prop_type = prop.get("type")
        if prop_type == "array":
            items = prop.get("items", {})
            if "$ref" in items:
                ref_name = items["$ref"].split("/")[-1]
                target = defs.get(ref_name, {})
                target_props = target.get("properties")
                if target_props:
                    inner = [
                        f'"{k}": {self._describe_property(v, defs)}'
                        for k, v in target_props.items()
                    ]
                    return "Array<{" + ", ".join(inner) + "}>"
                return f"Array<{ref_name}>"
            return f"Array<{items.get('type', 'object')}>"
        if prop_type == "object":
            return "Object"
        if prop_type is None:
            return "any"
        return prop_type
