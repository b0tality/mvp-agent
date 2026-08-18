"""
代码审查智能体状态定义
"""

from typing import TypedDict, List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum


class SeverityLevel(str, Enum):
    """严重程度级别"""
    CRITICAL = "critical"    # 严重问题，必须修复
    HIGH = "high"            # 高优先级问题
    MEDIUM = "medium"        # 中等优先级问题
    LOW = "low"              # 低优先级问题
    INFO = "info"            # 信息性提示


class IssueType(str, Enum):
    """问题类型"""
    STYLE = "style"              # 代码风格
    QUALITY = "quality"          # 代码质量
    SECURITY = "security"        # 安全问题
    PERFORMANCE = "performance"  # 性能问题
    COMPLEXITY = "complexity"    # 复杂度问题
    DUPLICATION = "duplication"  # 代码重复
    DOCUMENTATION = "documentation"  # 文档问题
    TEST = "test"                # 测试问题


@dataclass
class CodeIssue:
    """代码问题定义"""
    id: str
    file_path: str
    line_number: int
    column: int
    severity: SeverityLevel
    issue_type: IssueType
    title: str
    description: str
    suggestion: str
    code_snippet: str = ""
    rule_id: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ReviewMetrics:
    """审查指标"""
    total_lines: int = 0
    code_lines: int = 0
    comment_lines: int = 0
    blank_lines: int = 0
    cyclomatic_complexity: float = 0.0
    cognitive_complexity: float = 0.0
    maintainability_index: float = 0.0
    test_coverage: float = 0.0
    duplication_percentage: float = 0.0


@dataclass
class FileReview:
    """文件审查结果"""
    file_path: str
    language: str
    metrics: ReviewMetrics
    issues: List[CodeIssue]
    score: float  # 0-100
    approved: bool
    review_notes: str = ""


class CodeReviewState(TypedDict):
    """代码审查状态"""
    
    # 输入
    code_files: list                    # 代码文件列表
    project_info: dict                  # 项目信息
    review_config: dict                 # 审查配置
    
    # 审查结果
    file_reviews: list                  # 文件审查结果
    total_issues: int                   # 总问题数
    critical_issues: int                # 严重问题数
    high_issues: int                    # 高优先级问题数
    medium_issues: int                  # 中等优先级问题数
    low_issues: int                     # 低优先级问题数
    
    # 代码质量
    overall_score: float                # 总体评分 (0-100)
    code_quality_score: float           # 代码质量评分
    security_score: float               # 安全评分
    performance_score: float            # 性能评分
    maintainability_score: float        # 可维护性评分
    
    # 分类统计
    style_issues: list                  # 风格问题
    quality_issues: list                # 质量问题
    security_issues: list               # 安全问题
    performance_issues: list            # 性能问题
    complexity_issues: list             # 复杂度问题
    
    # 重构建议
    refactoring_suggestions: list       # 重构建议
    best_practices: list                # 最佳实践建议
    
    # 审查决策
    approved: bool                      # 是否通过审查
    review_status: str                  # 审查状态
    review_notes: str                   # 审查备注
    
    # 元数据
    status: str                         # 智能体状态
    created_at: str                     # 创建时间
    updated_at: str                     # 更新时间
    errors: list                        # 错误记录


class CodeReviewStateManager:
    """代码审查状态管理器"""
    
    def __init__(self):
        self._state: CodeReviewState = {
            "code_files": [],
            "project_info": {},
            "review_config": {},
            "file_reviews": [],
            "total_issues": 0,
            "critical_issues": 0,
            "high_issues": 0,
            "medium_issues": 0,
            "low_issues": 0,
            "overall_score": 0.0,
            "code_quality_score": 0.0,
            "security_score": 0.0,
            "performance_score": 0.0,
            "maintainability_score": 0.0,
            "style_issues": [],
            "quality_issues": [],
            "security_issues": [],
            "performance_issues": [],
            "complexity_issues": [],
            "refactoring_suggestions": [],
            "best_practices": [],
            "approved": False,
            "review_status": "pending",
            "review_notes": "",
            "status": "initialized",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "errors": []
        }
        self._history: list = []
    
    def update(self, key: str, value: Any) -> None:
        """更新状态"""
        old_value = self._state.get(key)
        self._history.append({
            "timestamp": datetime.now().isoformat(),
            "key": key,
            "old_value": old_value,
            "new_value": value
        })
        self._state[key] = value
        self._state["updated_at"] = datetime.now().isoformat()
    
    def get(self, key: str) -> Any:
        """获取状态值"""
        return self._state.get(key)
    
    def get_all(self) -> CodeReviewState:
        """获取完整状态"""
        return self._state.copy()
    
    def get_history(self) -> list:
        """获取变更历史"""
        return self._history
    
    def set_code_files(self, files: list) -> None:
        """设置代码文件"""
        self._state["code_files"] = files
        self._state["updated_at"] = datetime.now().isoformat()
    
    def set_project_info(self, info: dict) -> None:
        """设置项目信息"""
        self._state["project_info"] = info
        self._state["updated_at"] = datetime.now().isoformat()
    
    def add_file_review(self, review: dict) -> None:
        """添加文件审查结果"""
        self._state["file_reviews"].append(review)
        self._state["updated_at"] = datetime.now().isoformat()
    
    def add_issue(self, issue: dict) -> None:
        """添加问题"""
        issue_type = issue.get("issue_type", "quality")
        severity = issue.get("severity", "medium")
        
        # 按类型分类
        if issue_type == "style":
            self._state["style_issues"].append(issue)
        elif issue_type == "quality":
            self._state["quality_issues"].append(issue)
        elif issue_type == "security":
            self._state["security_issues"].append(issue)
        elif issue_type == "performance":
            self._state["performance_issues"].append(issue)
        elif issue_type == "complexity":
            self._state["complexity_issues"].append(issue)
        
        # 按严重程度统计
        self._state["total_issues"] += 1
        if severity == "critical":
            self._state["critical_issues"] += 1
        elif severity == "high":
            self._state["high_issues"] += 1
        elif severity == "medium":
            self._state["medium_issues"] += 1
        elif severity == "low":
            self._state["low_issues"] += 1
        
        self._state["updated_at"] = datetime.now().isoformat()
    
    def add_refactoring_suggestion(self, suggestion: dict) -> None:
        """添加重构建议"""
        self._state["refactoring_suggestions"].append(suggestion)
        self._state["updated_at"] = datetime.now().isoformat()
    
    def add_best_practice(self, practice: dict) -> None:
        """添加最佳实践建议"""
        self._state["best_practices"].append(practice)
        self._state["updated_at"] = datetime.now().isoformat()
    
    def set_overall_score(self, score: float) -> None:
        """设置总体评分"""
        self._state["overall_score"] = min(100.0, max(0.0, score))
        self._state["updated_at"] = datetime.now().isoformat()
    
    def set_code_quality_score(self, score: float) -> None:
        """设置代码质量评分"""
        self._state["code_quality_score"] = min(100.0, max(0.0, score))
        self._state["updated_at"] = datetime.now().isoformat()
    
    def set_security_score(self, score: float) -> None:
        """设置安全评分"""
        self._state["security_score"] = min(100.0, max(0.0, score))
        self._state["updated_at"] = datetime.now().isoformat()
    
    def set_performance_score(self, score: float) -> None:
        """设置性能评分"""
        self._state["performance_score"] = min(100.0, max(0.0, score))
        self._state["updated_at"] = datetime.now().isoformat()
    
    def set_maintainability_score(self, score: float) -> None:
        """设置可维护性评分"""
        self._state["maintainability_score"] = min(100.0, max(0.0, score))
        self._state["updated_at"] = datetime.now().isoformat()
    
    def set_approved(self, approved: bool) -> None:
        """设置审查结果"""
        self._state["approved"] = approved
        self._state["review_status"] = "approved" if approved else "rejected"
        self._state["updated_at"] = datetime.now().isoformat()
    
    def set_review_notes(self, notes: str) -> None:
        """设置审查备注"""
        self._state["review_notes"] = notes
        self._state["updated_at"] = datetime.now().isoformat()
    
    def set_status(self, status: str) -> None:
        """设置状态"""
        self._state["status"] = status
        self._state["updated_at"] = datetime.now().isoformat()
    
    def add_error(self, error: str) -> None:
        """添加错误记录"""
        self._state["errors"].append({
            "timestamp": datetime.now().isoformat(),
            "message": error
        })
        self._state["updated_at"] = datetime.now().isoformat()
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return self._state.copy()
    
    def reset(self) -> None:
        """重置状态"""
        self.__init__()
