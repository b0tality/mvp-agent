"""
需求分析相关Schema
"""

from pydantic import BaseModel, Field, model_validator
from typing import List, Any, Dict


class RequirementItem(BaseModel):
    """单个需求项"""
    id: str = Field(default="", description="需求ID，如FR-001")
    title: str = Field(default="", description="需求标题")
    description: str = Field(default="", description="需求描述")
    
    class Config:
        extra = "allow"
    
    @model_validator(mode="before")
    @classmethod
    def normalize_fields(cls, values):
        """归一化字段名"""
        if not values.get("id"):
            for key in ["ID", "Id", "requirement_id"]:
                if values.get(key):
                    values["id"] = values[key]
                    break
        if not values.get("title"):
            for key in ["name", "summary", "requirement"]:
                if values.get(key):
                    values["title"] = values[key]
                    break
        if not values.get("description"):
            for key in ["desc", "detail", "requirement_description"]:
                if values.get(key):
                    values["description"] = values[key]
                    break
        return values


class UserStory(BaseModel):
    """用户故事"""
    id: str = Field(default="", description="用户故事ID")
    role: str = Field(default="", description="用户角色")
    feature: str = Field(default="", description="功能描述")
    benefit: str = Field(default="", description="业务价值")
    
    class Config:
        extra = "allow"
    
    @model_validator(mode="before")
    @classmethod
    def normalize_fields(cls, values):
        """归一化字段名"""
        if not values.get("id"):
            for key in ["ID", "Id", "story_id"]:
                if values.get(key):
                    values["id"] = values[key]
                    break
        if not values.get("role"):
            for key in ["user_role", "actor", "user"]:
                if values.get(key):
                    values["role"] = values[key]
                    break
        if not values.get("feature"):
            for key in ["title", "name", "action", "story"]:
                if values.get(key):
                    values["feature"] = values[key]
                    break
        if not values.get("benefit"):
            for key in ["value", "goal", "purpose", "reason"]:
                if values.get(key):
                    values["benefit"] = values[key]
                    break
        return values


class AcceptanceCriterion(BaseModel):
    """验收标准"""
    id: str = Field(default="", description="验收标准ID")
    story_id: str = Field(default="", description="关联的用户故事ID")
    description: str = Field(default="", description="验收标准描述")
    
    class Config:
        extra = "allow"
    
    @model_validator(mode="before")
    @classmethod
    def normalize_fields(cls, values):
        """归一化字段名"""
        if not values.get("id"):
            for key in ["ID", "Id", "criteria_id", "ac_id"]:
                if values.get(key):
                    values["id"] = values[key]
                    break
        if not values.get("story_id"):
            for key in ["user_story_id", "story", "related_story"]:
                if values.get(key):
                    values["story_id"] = values[key]
                    break
        if not values.get("description"):
            for key in ["title", "name", "criteria", "criterion", "condition"]:
                if values.get(key):
                    values["description"] = values[key]
                    break
        return values


class PriorityMatrix(BaseModel):
    """优先级矩阵"""
    must_have: List[Any] = Field(default_factory=list, description="必须有")
    should_have: List[Any] = Field(default_factory=list, description="应该有")
    could_have: List[Any] = Field(default_factory=list, description="可以有")
    wont_have: List[Any] = Field(default_factory=list, description="不会有")
    
    class Config:
        extra = "allow"


class RequirementsOutput(BaseModel):
    """需求分析完整输出"""
    functional_requirements: List[RequirementItem] = Field(
        default_factory=list, description="功能需求列表"
    )
    non_functional_requirements: List[RequirementItem] = Field(
        default_factory=list, description="非功能需求列表"
    )
    user_stories: List[UserStory] = Field(
        default_factory=list, description="用户故事列表"
    )
    acceptance_criteria: List[AcceptanceCriterion] = Field(
        default_factory=list, description="验收标准列表"
    )
    priority_matrix: PriorityMatrix = Field(
        default_factory=PriorityMatrix, description="优先级矩阵"
    )
    constraints: List[Any] = Field(default_factory=list, description="约束条件")
    assumptions: List[Any] = Field(default_factory=list, description="假设条件")
    risks: List[Any] = Field(default_factory=list, description="风险点")
    
    class Config:
        extra = "allow"
