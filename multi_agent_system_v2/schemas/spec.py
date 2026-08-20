"""
Spec 相关 Schema —— spec-driven 架构的「唯一真相源」

与旧 requirements/technical 的本质区别：
- 旧：需求/设计是散文，靠 LLM 之间传文本、互相理解；
- 新：ProjectSpec 是一份**带类型、机器可校验、人可审阅**的正式契约，
  后续所有测试与契约校验都由它**确定性推导**（零 LLM），不再有翻译环节。
"""

from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field


class EndpointSpec(BaseModel):
    """一个 API 端点的正式契约。"""
    method: str = Field(description="HTTP 方法: GET/POST/PUT/DELETE/PATCH")
    path: str = Field(description="路径，如 /todos 或 /todos/{id}")
    summary: str = Field(default="", description="一句话说明")
    request_body: Optional[Union[Dict[str, Any], List[Any]]] = Field(
        default=None,
        description="能成功触发该端点的合法请求体示例（GET/DELETE 留空）。单个对象用 dict；批量端点（一次传多条）用 list。",
    )
    response_status: int = Field(default=200, description="成功状态码（POST 常为 201）")
    query_params: Optional[Dict[str, str]] = Field(
        default=None, description="查询参数示例（如 {'priority': 'high'}），无则省略。不要写进 path。"
    )

    class Config:
        extra = "allow"


class RuleSpec(BaseModel):
    """一条可执行的行为规则（业务校验 / 错误分支）。"""
    description: str = Field(description="规则说明，如「空标题返回 422」")
    method: str = Field(default="POST", description="HTTP 方法")
    path: str = Field(description="路径（不要用 {id} 参数，资源级 404 由不变式测试覆盖）")
    request_body: Optional[Union[Dict[str, Any], List[Any]]] = Field(
        default=None,
        description="触发该规则的请求体（如缺字段的空 body）；批量规则用 list（如 [{'name': ''}]）。",
    )
    expect_status: int = Field(description="期望状态码，如 422/400/409/404")
    expect_contains: Optional[str] = Field(
        default=None, description="响应体中必须包含的子串（可选，用于核对错误信息）"
    )
    query_params: Optional[Dict[str, str]] = Field(
        default=None, description="触发该规则的查询参数（如 {'priority': 'nonexistent'}），无则省略。"
    )

    class Config:
        extra = "allow"


class ProjectSpec(BaseModel):
    """项目 Spec：端点契约 + 行为规则，spec-driven 流水线的唯一真相源。"""
    project_name: str = Field(description="项目名，小写字母+下划线")
    description: str = Field(default="", description="项目描述")
    endpoints: List[EndpointSpec] = Field(default_factory=list, description="端点契约")
    rules: List[RuleSpec] = Field(default_factory=list, description="行为规则")

    class Config:
        extra = "allow"
