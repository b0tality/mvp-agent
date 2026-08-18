"""
测试相关Schema
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any


class TestCase(BaseModel):
    """测试用例"""
    id: str = Field(description="测试用例ID")
    name: str = Field(description="测试名称")
    type: str = Field(description="测试类型: unit/integration/performance/security")
    code: str = Field(default="", description="测试代码")
    status: str = Field(default="pending", description="状态: pending/passed/failed")


class TestCoverage(BaseModel):
    """测试覆盖率"""
    line: float = Field(default=0.0, description="行覆盖率")
    branch: float = Field(default=0.0, description="分支覆盖率")
    function: float = Field(default=0.0, description="函数覆盖率")


class Bug(BaseModel):
    """Bug"""
    id: str = Field(description="Bug ID")
    severity: str = Field(description="严重程度: critical/major/minor")
    description: str = Field(description="描述")
    file_path: str = Field(default="", description="文件路径")
    steps_to_reproduce: str = Field(default="", description="复现步骤")


class TestingOutput(BaseModel):
    """测试输出"""
    test_cases: List[TestCase] = Field(default_factory=list, description="测试用例列表")
    coverage: TestCoverage = Field(default_factory=TestCoverage, description="覆盖率")
    bugs: List[Bug] = Field(default_factory=list, description="Bug列表")
    total_tests: int = Field(default=0, description="测试总数")
    passed: int = Field(default=0, description="通过数")
    failed: int = Field(default=0, description="失败数")
    summary: str = Field(default="", description="测试总结")
    suggestions: List[str] = Field(default_factory=list, description="改进建议列表")
    all_passed: bool = Field(default=False, description="全部测试是否通过（真实执行结果）")
    smoke_test: Dict[str, Any] = Field(default_factory=dict, description="应用启动冒烟测试结果")
    raw_output: str = Field(default="", description="测试原始输出")
