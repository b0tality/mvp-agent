"""
MVP实现智能体状态定义
"""

from typing import TypedDict, List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum


class CodeLanguage(str, Enum):
    """支持的编程语言"""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    GO = "go"
    RUST = "rust"


class FrameworkType(str, Enum):
    """框架类型"""
    FASTAPI = "fastapi"
    FLASK = "flask"
    DJANGO = "django"
    EXPRESS = "express"
    NESTJS = "nestjs"
    SPRING_BOOT = "spring_boot"


@dataclass
class CodeFile:
    """代码文件定义"""
    path: str
    content: str
    language: str
    description: str
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class TestCase:
    """测试用例定义"""
    id: str
    name: str
    description: str
    file_path: str
    test_code: str
    status: str = "pending"  # pending, passed, failed


@dataclass
class Dependency:
    """依赖定义"""
    name: str
    version: str
    category: str  # main, dev, test
    description: str


class MVPState(TypedDict):
    """MVP实现状态"""
    
    # 输入
    technical_solution: dict            # 技术方案
    requirements: dict                  # 需求
    
    # 项目结构
    project_structure: dict             # 项目结构
    project_name: str                   # 项目名称
    project_path: str                   # 项目路径
    
    # 代码生成
    code_files: list                    # 代码文件列表
    generated_modules: list             # 已生成模块
    current_module: str                 # 当前模块
    
    # 依赖管理
    dependencies: list                  # 依赖列表
    requirements_txt: str               # requirements.txt内容
    package_json: str                   # package.json内容
    
    # 测试
    test_files: list                    # 测试文件列表
    test_results: dict                  # 测试结果
    test_coverage: float                # 测试覆盖率
    
    # 代码质量
    code_quality: dict                  # 代码质量指标
    lint_results: dict                  # 代码检查结果
    type_check_results: dict            # 类型检查结果
    
    # 文档
    readme: str                         # README内容
    api_docs: str                       # API文档
    code_comments: dict                 # 代码注释
    
    # 构建和运行
    build_scripts: dict                 # 构建脚本
    run_scripts: dict                   # 运行脚本
    docker_config: dict                 # Docker配置
    
    # 元数据
    status: str                         # 实现状态
    progress: float                     # 进度百分比
    created_at: str                     # 创建时间
    updated_at: str                     # 更新时间
    errors: list                        # 错误记录
    warnings: list                      # 警告记录


class MVPStateManager:
    """MVP状态管理器"""
    
    def __init__(self):
        self._state: MVPState = {
            "technical_solution": {},
            "requirements": {},
            "project_structure": {},
            "project_name": "",
            "project_path": "",
            "code_files": [],
            "generated_modules": [],
            "current_module": "",
            "dependencies": [],
            "requirements_txt": "",
            "package_json": "",
            "test_files": [],
            "test_results": {},
            "test_coverage": 0.0,
            "code_quality": {},
            "lint_results": {},
            "type_check_results": {},
            "readme": "",
            "api_docs": "",
            "code_comments": {},
            "build_scripts": {},
            "run_scripts": {},
            "docker_config": {},
            "status": "initialized",
            "progress": 0.0,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "errors": [],
            "warnings": []
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
    
    def get_all(self) -> MVPState:
        """获取完整状态"""
        return self._state.copy()
    
    def get_history(self) -> list:
        """获取变更历史"""
        return self._history
    
    def set_technical_solution(self, solution: dict) -> None:
        """设置技术方案"""
        self._state["technical_solution"] = solution
        self._state["updated_at"] = datetime.now().isoformat()
    
    def set_requirements(self, requirements: dict) -> None:
        """设置需求"""
        self._state["requirements"] = requirements
        self._state["updated_at"] = datetime.now().isoformat()
    
    def set_project_info(self, name: str, path: str) -> None:
        """设置项目信息"""
        self._state["project_name"] = name
        self._state["project_path"] = path
        self._state["updated_at"] = datetime.now().isoformat()
    
    def set_project_structure(self, structure: dict) -> None:
        """设置项目结构"""
        self._state["project_structure"] = structure
        self._state["updated_at"] = datetime.now().isoformat()
    
    def add_code_file(self, file: dict) -> None:
        """添加代码文件"""
        self._state["code_files"].append(file)
        self._state["updated_at"] = datetime.now().isoformat()
    
    def update_code_file(self, path: str, content: str) -> None:
        """更新代码文件"""
        for file in self._state["code_files"]:
            if file["path"] == path:
                file["content"] = content
                file["updated_at"] = datetime.now().isoformat()
                break
        self._state["updated_at"] = datetime.now().isoformat()
    
    def add_module(self, module: str) -> None:
        """添加已生成模块"""
        if module not in self._state["generated_modules"]:
            self._state["generated_modules"].append(module)
        self._state["updated_at"] = datetime.now().isoformat()
    
    def set_current_module(self, module: str) -> None:
        """设置当前模块"""
        self._state["current_module"] = module
        self._state["updated_at"] = datetime.now().isoformat()
    
    def add_dependency(self, dep: dict) -> None:
        """添加依赖"""
        self._state["dependencies"].append(dep)
        self._state["updated_at"] = datetime.now().isoformat()
    
    def set_requirements_txt(self, content: str) -> None:
        """设置requirements.txt内容"""
        self._state["requirements_txt"] = content
        self._state["updated_at"] = datetime.now().isoformat()
    
    def add_test_file(self, file: dict) -> None:
        """添加测试文件"""
        self._state["test_files"].append(file)
        self._state["updated_at"] = datetime.now().isoformat()
    
    def set_test_results(self, results: dict) -> None:
        """设置测试结果"""
        self._state["test_results"] = results
        self._state["updated_at"] = datetime.now().isoformat()
    
    def set_test_coverage(self, coverage: float) -> None:
        """设置测试覆盖率"""
        self._state["test_coverage"] = coverage
        self._state["updated_at"] = datetime.now().isoformat()
    
    def set_code_quality(self, quality: dict) -> None:
        """设置代码质量指标"""
        self._state["code_quality"] = quality
        self._state["updated_at"] = datetime.now().isoformat()
    
    def set_readme(self, content: str) -> None:
        """设置README内容"""
        self._state["readme"] = content
        self._state["updated_at"] = datetime.now().isoformat()
    
    def set_api_docs(self, content: str) -> None:
        """设置API文档"""
        self._state["api_docs"] = content
        self._state["updated_at"] = datetime.now().isoformat()
    
    def set_docker_config(self, config: dict) -> None:
        """设置Docker配置"""
        self._state["docker_config"] = config
        self._state["updated_at"] = datetime.now().isoformat()
    
    def set_status(self, status: str) -> None:
        """设置状态"""
        self._state["status"] = status
        self._state["updated_at"] = datetime.now().isoformat()
    
    def set_progress(self, progress: float) -> None:
        """设置进度"""
        self._state["progress"] = min(100.0, max(0.0, progress))
        self._state["updated_at"] = datetime.now().isoformat()
    
    def add_error(self, error: str) -> None:
        """添加错误记录"""
        self._state["errors"].append({
            "timestamp": datetime.now().isoformat(),
            "message": error
        })
        self._state["updated_at"] = datetime.now().isoformat()
    
    def add_warning(self, warning: str) -> None:
        """添加警告记录"""
        self._state["warnings"].append({
            "timestamp": datetime.now().isoformat(),
            "message": warning
        })
        self._state["updated_at"] = datetime.now().isoformat()
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return self._state.copy()
    
    def reset(self) -> None:
        """重置状态"""
        self.__init__()
