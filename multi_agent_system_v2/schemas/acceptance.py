"""
验收测试相关Schema
"""

from pydantic import BaseModel, Field
from typing import List


class AcceptanceResult(BaseModel):
    """单个验收标准的结果"""
    criterion_id: str = Field(default="", description="验收标准ID")
    description: str = Field(default="", description="验收标准描述")
    passed: bool = Field(default=False, description="是否通过")
    detail: str = Field(default="", description="通过/失败详情")


class AcceptanceOutput(BaseModel):
    """验收测试完整输出"""
    results: List[AcceptanceResult] = Field(default_factory=list, description="逐条验收结果")
    total: int = Field(default=0, description="验收标准总数")
    passed: int = Field(default=0, description="通过数")
    failed: int = Field(default=0, description="失败数")
    all_passed: bool = Field(default=False, description="是否全部通过")
    raw_output: str = Field(default="", description="pytest 原始输出")
