"""
OpenAI兼容API适配器
支持OpenAI API以及兼容接口（如小米MiMo）
"""

import json
from typing import Type, TypeVar
from pydantic import BaseModel, ValidationError
from openai import AsyncOpenAI

from .adapter import LLMAdapter

T = TypeVar("T", bound=BaseModel)


class OpenAIAdapter(LLMAdapter):
    """
    OpenAI兼容API适配器
    
    支持:
    - OpenAI官方API
    - 任何兼容OpenAI格式的API（如小米MiMo）
    """

    def __init__(self, api_key: str, base_url: str, model: str):
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        """生成文本响应"""
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return response.choices[0].message.content

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

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content
            try:
                return output_schema.model_validate_json(content)
            except ValidationError as e:
                last_error = e

        raise last_error

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
