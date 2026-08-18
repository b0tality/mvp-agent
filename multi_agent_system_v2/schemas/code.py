"""
代码相关Schema
"""

from pydantic import BaseModel, Field, model_validator
from typing import List, Dict, Any, Optional


class CodeFile(BaseModel):
    """
    代码文件
    
    LLM可能返回不同的字段名（path/file_name/filename/name），
    通过validator统一归一化为path。
    """
    path: str = Field(default="", description="文件路径")
    content: str = Field(default="", description="文件内容")
    language: str = Field(default="python", description="编程语言")
    
    # 允许额外字段（LLM可能返回name、file_name等）
    class Config:
        extra = "allow"
    
    @model_validator(mode="before")
    @classmethod
    def normalize_fields(cls, values):
        """归一化字段名"""
        # path: 尝试从多个可能的字段名获取
        if not values.get("path"):
            for key in ["file_name", "filename", "name", "file"]:
                if values.get(key):
                    values["path"] = values[key]
                    break
        
        # content: 尝试从多个可能的字段名获取
        if not values.get("content"):
            for key in ["code", "source", "file_content", "body"]:
                if values.get(key):
                    values["content"] = values[key]
                    break
        
        # language: 根据文件扩展名推断
        if not values.get("language") and values.get("path"):
            path = values["path"]
            if path.endswith(".py"):
                values["language"] = "python"
            elif path.endswith(".js") or path.endswith(".ts"):
                values["language"] = "javascript"
            elif path.endswith(".json"):
                values["language"] = "json"
            elif path.endswith(".txt"):
                values["language"] = "text"
            elif path.endswith(".yml") or path.endswith(".yaml"):
                values["language"] = "yaml"
            elif path.endswith(".html"):
                values["language"] = "html"
            elif path.endswith(".css"):
                values["language"] = "css"
            elif path.endswith(".sql"):
                values["language"] = "sql"
            elif path.endswith(".md"):
                values["language"] = "markdown"
            elif path.endswith("Dockerfile"):
                values["language"] = "dockerfile"
            elif path.endswith(".toml"):
                values["language"] = "toml"
        
        return values


class MVPCodeOutput(BaseModel):
    """MVP代码生成输出"""
    code_files: List[CodeFile] = Field(default_factory=list, description="代码文件列表")
    test_files: List[CodeFile] = Field(default_factory=list, description="测试文件列表")
    docker_config: Dict[str, Any] = Field(default_factory=dict, description="Docker配置")
    project_name: str = Field(default="mvp_project", description="项目名称")
    
    class Config:
        extra = "allow"


class CodeReviewIssue(BaseModel):
    """代码审查问题"""
    severity: str = Field(default="minor", description="严重程度: critical/major/minor")
    file_path: str = Field(default="", description="文件路径")
    line: int = Field(default=0, description="行号")
    description: str = Field(default="", description="问题描述")
    suggestion: str = Field(default="", description="修复建议")
    
    class Config:
        extra = "allow"


class CodeReviewOutput(BaseModel):
    """代码审查输出"""
    overall_score: int = Field(default=70, description="总体评分(0-100)")
    issues: List[CodeReviewIssue] = Field(default_factory=list, description="问题列表")
    approved: bool = Field(default=True, description="是否通过")
    summary: str = Field(default="", description="审查总结")
    suggestions: List[str] = Field(default_factory=list, description="改进建议列表")
    
    class Config:
        extra = "allow"
