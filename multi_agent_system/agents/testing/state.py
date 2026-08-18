"""
软件测试智能体状态定义
"""

from typing import TypedDict, List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum


class TestType(str, Enum):
    """测试类型"""
    UNIT = "unit"                # 单元测试
    INTEGRATION = "integration"  # 集成测试
    E2E = "e2e"                  # 端到端测试
    PERFORMANCE = "performance"  # 性能测试
    SECURITY = "security"        # 安全测试
    STRESS = "stress"            # 压力测试


class TestStatus(str, Enum):
    """测试状态"""
    PENDING = "pending"      # 待执行
    RUNNING = "running"      # 执行中
    PASSED = "passed"        # 通过
    FAILED = "failed"        # 失败
    SKIPPED = "skipped"      # 跳过
    ERROR = "error"          # 错误


class SeverityLevel(str, Enum):
    """缺陷严重程度"""
    CRITICAL = "critical"    # 严重缺陷
    HIGH = "high"            # 高优先级
    MEDIUM = "medium"        # 中等优先级
    LOW = "low"              # 低优先级


@dataclass
class TestCase:
    """测试用例定义"""
    id: str
    name: str
    description: str
    test_type: TestType
    file_path: str
    function_name: str
    status: TestStatus = TestStatus.PENDING
    execution_time: float = 0.0
    error_message: str = ""
    stack_trace: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    executed_at: str = ""


@dataclass
class TestSuite:
    """测试套件定义"""
    id: str
    name: str
    description: str
    test_type: TestType
    test_cases: List[TestCase]
    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    error: int = 0
    execution_time: float = 0.0
    coverage: float = 0.0


@dataclass
class Bug:
    """缺陷定义"""
    id: str
    title: str
    description: str
    severity: SeverityLevel
    test_case_id: str
    file_path: str
    line_number: int
    steps_to_reproduce: List[str]
    expected_behavior: str
    actual_behavior: str
    status: str = "open"  # open, in_progress, fixed, closed
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class PerformanceMetric:
    """性能指标"""
    endpoint: str
    method: str
    response_time_avg: float  # 平均响应时间(ms)
    response_time_p95: float  # P95响应时间(ms)
    response_time_p99: float  # P99响应时间(ms)
    throughput: float         # 吞吐量(req/s)
    error_rate: float         # 错误率(%)
    concurrent_users: int     # 并发用户数


class TestingState(TypedDict):
    """软件测试状态"""
    
    # 输入
    code_files: list                    # 代码文件列表
    project_info: dict                  # 项目信息
    test_config: dict                   # 测试配置
    
    # 测试套件
    test_suites: list                   # 测试套件列表
    unit_test_suite: dict               # 单元测试套件
    integration_test_suite: dict        # 集成测试套件
    e2e_test_suite: dict                # 端到端测试套件
    performance_test_suite: dict        # 性能测试套件
    security_test_suite: dict           # 安全测试套件
    
    # 测试结果
    total_tests: int                    # 总测试数
    passed_tests: int                   # 通过数
    failed_tests: int                   # 失败数
    skipped_tests: int                  # 跳过数
    error_tests: int                    # 错误数
    
    # 覆盖率
    line_coverage: float                # 行覆盖率
    branch_coverage: float              # 分支覆盖率
    function_coverage: float            # 函数覆盖率
    overall_coverage: float             # 总体覆盖率
    
    # 性能指标
    performance_metrics: list           # 性能指标列表
    avg_response_time: float            # 平均响应时间
    p95_response_time: float            # P95响应时间
    p99_response_time: float            # P99响应时间
    throughput: float                   # 吞吐量
    error_rate: float                   # 错误率
    
    # 缺陷
    bugs: list                          # 缺陷列表
    critical_bugs: int                  # 严重缺陷数
    high_bugs: int                      # 高优先级缺陷数
    medium_bugs: int                    # 中等优先级缺陷数
    low_bugs: int                       # 低优先级缺陷数
    
    # 安全测试
    security_vulnerabilities: list      # 安全漏洞
    security_score: float               # 安全评分
    
    # 测试报告
    test_report: dict                   # 测试报告
    summary: str                        # 测试总结
    
    # 元数据
    status: str                         # 测试状态
    progress: float                     # 进度百分比
    started_at: str                     # 开始时间
    completed_at: str                   # 完成时间
    execution_time: float               # 总执行时间
    errors: list                        # 错误记录


class TestingStateManager:
    """软件测试状态管理器"""
    
    def __init__(self):
        self._state: TestingState = {
            "code_files": [],
            "project_info": {},
            "test_config": {},
            "test_suites": [],
            "unit_test_suite": {},
            "integration_test_suite": {},
            "e2e_test_suite": {},
            "performance_test_suite": {},
            "security_test_suite": {},
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "skipped_tests": 0,
            "error_tests": 0,
            "line_coverage": 0.0,
            "branch_coverage": 0.0,
            "function_coverage": 0.0,
            "overall_coverage": 0.0,
            "performance_metrics": [],
            "avg_response_time": 0.0,
            "p95_response_time": 0.0,
            "p99_response_time": 0.0,
            "throughput": 0.0,
            "error_rate": 0.0,
            "bugs": [],
            "critical_bugs": 0,
            "high_bugs": 0,
            "medium_bugs": 0,
            "low_bugs": 0,
            "security_vulnerabilities": [],
            "security_score": 100.0,
            "test_report": {},
            "summary": "",
            "status": "initialized",
            "progress": 0.0,
            "started_at": "",
            "completed_at": "",
            "execution_time": 0.0,
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
    
    def get(self, key: str) -> Any:
        """获取状态值"""
        return self._state.get(key)
    
    def get_all(self) -> TestingState:
        """获取完整状态"""
        return self._state.copy()
    
    def get_history(self) -> list:
        """获取变更历史"""
        return self._history
    
    def set_code_files(self, files: list) -> None:
        """设置代码文件"""
        self._state["code_files"] = files
    
    def set_project_info(self, info: dict) -> None:
        """设置项目信息"""
        self._state["project_info"] = info
    
    def set_test_config(self, config: dict) -> None:
        """设置测试配置"""
        self._state["test_config"] = config
    
    def add_test_suite(self, suite: dict) -> None:
        """添加测试套件"""
        self._state["test_suites"].append(suite)
    
    def set_unit_test_suite(self, suite: dict) -> None:
        """设置单元测试套件"""
        self._state["unit_test_suite"] = suite
    
    def set_integration_test_suite(self, suite: dict) -> None:
        """设置集成测试套件"""
        self._state["integration_test_suite"] = suite
    
    def set_e2e_test_suite(self, suite: dict) -> None:
        """设置端到端测试套件"""
        self._state["e2e_test_suite"] = suite
    
    def set_performance_test_suite(self, suite: dict) -> None:
        """设置性能测试套件"""
        self._state["performance_test_suite"] = suite
    
    def set_security_test_suite(self, suite: dict) -> None:
        """设置安全测试套件"""
        self._state["security_test_suite"] = suite
    
    def update_test_counts(self, passed: int = 0, failed: int = 0, skipped: int = 0, error: int = 0) -> None:
        """更新测试计数"""
        self._state["passed_tests"] += passed
        self._state["failed_tests"] += failed
        self._state["skipped_tests"] += skipped
        self._state["error_tests"] += error
        self._state["total_tests"] = (
            self._state["passed_tests"] +
            self._state["failed_tests"] +
            self._state["skipped_tests"] +
            self._state["error_tests"]
        )
    
    def set_coverage(self, line: float, branch: float, function: float) -> None:
        """设置覆盖率"""
        self._state["line_coverage"] = line
        self._state["branch_coverage"] = branch
        self._state["function_coverage"] = function
        self._state["overall_coverage"] = (line + branch + function) / 3
    
    def add_performance_metric(self, metric: dict) -> None:
        """添加性能指标"""
        self._state["performance_metrics"].append(metric)
    
    def set_performance_summary(self, avg: float, p95: float, p99: float, throughput: float, error_rate: float) -> None:
        """设置性能摘要"""
        self._state["avg_response_time"] = avg
        self._state["p95_response_time"] = p95
        self._state["p99_response_time"] = p99
        self._state["throughput"] = throughput
        self._state["error_rate"] = error_rate
    
    def add_bug(self, bug: dict) -> None:
        """添加缺陷"""
        self._state["bugs"].append(bug)
        severity = bug.get("severity", "medium")
        if severity == "critical":
            self._state["critical_bugs"] += 1
        elif severity == "high":
            self._state["high_bugs"] += 1
        elif severity == "medium":
            self._state["medium_bugs"] += 1
        elif severity == "low":
            self._state["low_bugs"] += 1
    
    def add_security_vulnerability(self, vuln: dict) -> None:
        """添加安全漏洞"""
        self._state["security_vulnerabilities"].append(vuln)
    
    def set_security_score(self, score: float) -> None:
        """设置安全评分"""
        self._state["security_score"] = min(100.0, max(0.0, score))
    
    def set_test_report(self, report: dict) -> None:
        """设置测试报告"""
        self._state["test_report"] = report
    
    def set_summary(self, summary: str) -> None:
        """设置测试总结"""
        self._state["summary"] = summary
    
    def set_status(self, status: str) -> None:
        """设置状态"""
        self._state["status"] = status
    
    def set_progress(self, progress: float) -> None:
        """设置进度"""
        self._state["progress"] = min(100.0, max(0.0, progress))
    
    def set_started_at(self, time: str) -> None:
        """设置开始时间"""
        self._state["started_at"] = time
    
    def set_completed_at(self, time: str) -> None:
        """设置完成时间"""
        self._state["completed_at"] = time
    
    def set_execution_time(self, time: float) -> None:
        """设置执行时间"""
        self._state["execution_time"] = time
    
    def add_error(self, error: str) -> None:
        """添加错误记录"""
        self._state["errors"].append({
            "timestamp": datetime.now().isoformat(),
            "message": error
        })
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return self._state.copy()
    
    def reset(self) -> None:
        """重置状态"""
        self.__init__()
