# 多智能体应用开发系统 (Multi-Agent Application Development System)

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![LangChain](https://img.shields.io/badge/LangChain-0.1+-green.svg)](https://langchain.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.0.20+-orange.svg)](https://langchain.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

基于 LangGraph 的多智能体协作开发系统，实现从需求分析到部署的全自动化软件开发流程。

---

## 📖 目录

- [项目概述](#项目概述)
- [系统架构](#系统架构)
- [智能体角色](#智能体角色)
- [核心特性](#核心特性)
- [快速开始](#快速开始)
- [详细使用](#详细使用)
- [项目结构](#项目结构)
- [API参考](#api参考)
- [配置说明](#配置说明)
- [开发指南](#开发指南)
- [测试](#测试)
- [部署](#部署)
- [常见问题](#常见问题)
- [更新日志](#更新日志)
- [贡献指南](#贡献指南)
- [许可证](#许可证)

---

## 项目概述

### 什么是多智能体应用开发系统？

多智能体应用开发系统是一个基于大语言模型（LLM）的自动化软件开发平台。它将软件开发生命周期分解为6个专业化的智能体角色，通过状态同步机制实现智能体间的协作，从而实现从需求分析到软件部署的全流程自动化。

### 为什么需要这个系统？

- **提高开发效率**：自动化重复性工作，缩短开发周期
- **保证代码质量**：多维度代码审查和测试
- **降低人力成本**：减少人工干预，降低开发成本
- **标准化流程**：统一的开发规范和最佳实践
- **快速迭代**：支持快速原型开发和迭代

### 适用场景

- 企业内部应用快速开发
- MVP（最小可行产品）快速验证
- 个人项目快速实现
- 教学和学习软件开发流程
- 自动化代码生成和测试

---

## 系统架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          多智能体应用开发系统                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   用户需求                                                                    │
│      │                                                                       │
│      ▼                                                                       │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                      智能体1：需求分析师（主管节点）                    │   │
│   │              需求解析 → 用户故事 → 优先级排序 → 任务协调               │   │
│   └──────────────────────────────────┬──────────────────────────────────┘   │
│                                      │                                       │
│      ┌───────────────────────────────┼───────────────────────────────┐      │
│      │                               │                               │      │
│      ▼                               ▼                               ▼      │
│   ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐     │
│   │   智能体2：       │    │   智能体3：       │    │   智能体4：       │     │
│   │   技术架构师      │───►│   MVP开发者       │───►│   代码审查员      │     │
│   │   架构设计        │    │   代码生成        │    │   质量审查        │     │
│   │   技术选型        │    │   测试生成        │    │   安全扫描        │     │
│   └──────────────────┘    └──────────────────┘    └──────────────────┘     │
│                                      │                               │      │
│                                      │                               │      │
│                                      ▼                               ▼      │
│                           ┌──────────────────┐    ┌──────────────────┐     │
│                           │   智能体5：       │    │   智能体6：       │     │
│                           │   测试工程师      │───►│   部署工程师      │     │
│                           │   单元测试        │    │   Docker配置      │     │
│                           │   集成测试        │    │   K8s编排         │     │
│                           │   性能测试        │    │   CI/CD配置       │     │
│                           └──────────────────┘    └──────────────────┘     │
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                         共享状态层 (LangGraph State)                  │   │
│   │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │   │
│   │  │ 需求状态 │ │ 技术状态 │ │ MVP状态  │ │ 审查状态 │ │ 测试状态 │  │   │
│   │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘  │   │
│   │  ┌──────────┐ ┌──────────────────────────────────────────────────┐  │   │
│   │  │ 部署状态 │ │                 配置和元数据                       │  │   │
│   │  └──────────┘ └──────────────────────────────────────────────────┘  │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 技术栈

| 层次 | 技术 | 用途 |
|------|------|------|
| **LLM** | OpenAI GPT-4 | 智能体推理和生成 |
| **框架** | LangChain | 智能体编排和工具管理 |
| **状态管理** | LangGraph State | 智能体间状态同步 |
| **容器化** | Docker | 应用容器化 |
| **编排** | Kubernetes | 容器编排 |
| **CI/CD** | GitHub Actions | 持续集成/部署 |
| **监控** | Prometheus + Grafana | 指标监控 |
| **日志** | ELK Stack | 日志收集和分析 |

### 通信机制

智能体间通过 **LangGraph State** 进行同步通信：

```python
class GlobalState(TypedDict):
    # 各智能体的状态
    requirements: dict          # 需求状态
    technical_solution: dict    # 技术状态
    mvp_code: dict              # MVP状态
    code_review: dict           # 审查状态
    test_results: dict          # 测试状态
    deployment_config: dict     # 部署状态
    
    # 协调状态
    current_phase: str          # 当前阶段
    agent_messages: list        # 消息队列
    errors: list                # 错误记录
    status: str                 # 系统状态
```

---

## 智能体角色

### 概览

| 智能体 | 角色 | 核心职责 | 工具数量 |
|--------|------|----------|----------|
| 智能体1 | 需求分析师（主管） | 需求解析、任务协调 | 5 |
| 智能体2 | 技术架构师 | 架构设计、技术选型 | 6 |
| 智能体3 | MVP开发者 | 代码生成、文档生成 | 6 |
| 智能体4 | 代码审查员 | 质量审查、安全扫描 | 6 |
| 智能体5 | 测试工程师 | 测试生成、测试执行 | 6 |
| 智能体6 | 部署工程师 | 容器化、CI/CD配置 | 6 |

### 智能体1：需求分析师（主管节点）

**角色定位**：需求分析与项目协调

**核心功能**：
- 自然语言需求解析
- 用户故事生成（As a... I want... So that...）
- 验收标准定义
- 优先级排序（MoSCoW方法）
- 任务分解与协调

**工具集**：
| 工具 | 功能 |
|------|------|
| `RequirementParserTool` | 解析用户需求 |
| `UserStoryGeneratorTool` | 生成用户故事 |
| `AcceptanceCriteriaTool` | 生成验收标准 |
| `PriorityCalculatorTool` | 计算优先级 |
| `CoordinatorTool` | 协调其他智能体 |

**使用示例**：
```python
from agents.requirements import RequirementsAgent

agent = RequirementsAgent({"model": "gpt-4"})
result = await agent.analyze_requirements("开发一个在线商城系统...")
```

---

### 智能体2：技术架构师

**角色定位**：技术方案设计

**核心功能**：
- 系统架构设计（微服务/单体/无服务器）
- 技术栈选择
- API设计（RESTful）
- 数据库设计
- 安全设计
- 成本估算

**工具集**：
| 工具 | 功能 |
|------|------|
| `ArchitectureDesignerTool` | 设计系统架构 |
| `TechStackSelectorTool` | 选择技术栈 |
| `APIDesignerTool` | 设计API |
| `DatabaseDesignerTool` | 设计数据库 |
| `SecurityDesignerTool` | 设计安全方案 |
| `CostEstimatorTool` | 估算成本 |

**使用示例**：
```python
from agents.technical import TechnicalAgent

agent = TechnicalAgent({"model": "gpt-4"})
result = await agent.design_technical_solution(requirements)
```

---

### 智能体3：MVP开发者

**角色定位**：最小可行产品开发

**核心功能**：
- 项目结构生成
- 数据模型生成（ORM）
- API端点实现
- 认证授权实现
- 测试用例生成
- 文档生成
- Docker配置生成

**工具集**：
| 工具 | 功能 |
|------|------|
| `ProjectGeneratorTool` | 生成项目结构 |
| `CodeGeneratorTool` | 生成代码 |
| `TestGeneratorTool` | 生成测试 |
| `DocGeneratorTool` | 生成文档 |
| `DockerGeneratorTool` | 生成Docker配置 |
| `CodeOptimizerTool` | 优化代码 |

**使用示例**：
```python
from agents.mvp import MVPDeveloperAgent

agent = MVPDeveloperAgent({"model": "gpt-4"})
result = await agent.develop_mvp(technical_solution, requirements)
```

---

### 智能体4：代码审查员

**角色定位**：代码质量审查

**核心功能**：
- 代码风格检查（命名、格式、注释）
- 代码质量评估（可读性、可维护性）
- 安全漏洞扫描（SQL注入、XSS等）
- 性能分析
- 复杂度分析
- 重构建议

**工具集**：
| 工具 | 功能 |
|------|------|
| `StyleCheckerTool` | 检查代码风格 |
| `QualityAssessorTool` | 评估代码质量 |
| `SecurityScannerTool` | 扫描安全漏洞 |
| `PerformanceAnalyzerTool` | 分析性能 |
| `ComplexityAnalyzerTool` | 分析复杂度 |
| `RefactoringAdvisorTool` | 提供重构建议 |

**审查标准**：
| 决策 | 条件 |
|------|------|
| ✅ 通过 | 无严重和高优先级问题，评分 ≥ 80 |
| ⚠️ 需修改 | 存在高优先级问题或评分 < 80 |
| ❌ 不通过 | 存在严重问题或评分 < 60 |

**使用示例**：
```python
from agents.code_review import CodeReviewAgent

agent = CodeReviewAgent({"model": "gpt-4"})
result = await agent.review_code(code_files)
```

---

### 智能体5：测试工程师

**角色定位**：软件测试

**核心功能**：
- 单元测试生成
- 集成测试生成
- 性能测试方案生成
- 安全测试方案生成
- 测试数据生成
- 测试报告生成

**工具集**：
| 工具 | 功能 |
|------|------|
| `UnitTestGeneratorTool` | 生成单元测试 |
| `IntegrationTestGeneratorTool` | 生成集成测试 |
| `PerformanceTestGeneratorTool` | 生成性能测试 |
| `SecurityTestGeneratorTool` | 生成安全测试 |
| `TestDataGeneratorTool` | 生成测试数据 |
| `TestReportGeneratorTool` | 生成测试报告 |

**测试类型**：
- **单元测试**：测试单个函数/方法
- **集成测试**：测试模块间交互
- **性能测试**：负载、压力、并发测试
- **安全测试**：漏洞扫描、渗透测试

**使用示例**：
```python
from agents.testing import TestingAgent

agent = TestingAgent({"model": "gpt-4"})
result = await agent.run_tests(code_files, project_info)
```

---

### 智能体6：部署工程师

**角色定位**：软件部署

**核心功能**：
- 部署方案设计
- Docker配置生成
- Kubernetes配置生成
- CI/CD配置生成
- 监控配置生成
- 部署文档生成

**工具集**：
| 工具 | 功能 |
|------|------|
| `DeploymentPlannerTool` | 设计部署方案 |
| `DockerConfiguratorTool` | 配置Docker |
| `KubernetesConfiguratorTool` | 配置Kubernetes |
| `CICDConfiguratorTool` | 配置CI/CD |
| `MonitoringConfiguratorTool` | 配置监控 |
| `DeploymentDocGeneratorTool` | 生成部署文档 |

**部署策略**：
| 策略 | 停机时间 | 风险 | 回滚速度 |
|------|----------|------|----------|
| 滚动部署 | 无 | 低 | 快 |
| 蓝绿部署 | 无 | 低 | 极快 |
| 金丝雀部署 | 无 | 极低 | 快 |
| 重新部署 | 有 | 中 | 慢 |

**使用示例**：
```python
from agents.deployment import DeploymentAgent

agent = DeploymentAgent({"model": "gpt-4"})
result = await agent.plan_deployment(code_files, technical_solution, test_results)
```

---

## 核心特性

### 1. 状态同步

使用 LangGraph State 实现智能体间的实时状态同步，确保各智能体能够访问最新的项目状态。

```python
# 状态更新会自动同步到所有智能体
state_manager.update("requirements", requirements)
state_manager.update("technical_solution", solution)
```

### 2. 错误恢复

支持自动重试和人工介入的错误处理机制：

```python
# 自动重试
if retry_count < max_retries:
    await retry_task(task)
else:
    await escalate_to_human(task)
```

### 3. 进度监控

实时监控各智能体的工作进度：

```python
progress = agent.get_progress()
# 输出: {"requirements": 100%, "technical": 80%, "mvp": 60%}
```

### 4. 成本控制

内置 token 使用监控和成本控制：

```python
# 成本监控
cost_monitor = CostMonitor(budget=1000)
cost_monitor.track_usage(agent, tokens, cost)
```

### 5. 并行执行

支持智能体间的并行执行，提高开发效率：

```python
# 并行执行多个任务
results = await asyncio.gather(
    agent1.analyze_requirements(input1),
    agent2.design_architecture(input2),
    agent3.generate_code(input3)
)
```

### 6. 可扩展性

模块化设计，易于添加新的智能体或工具：

```python
# 添加新工具
class CustomTool(BaseTool):
    name = "custom_tool"
    description = "自定义工具"
    
    def _run(self, input: str) -> str:
        return result
```

---

## 快速开始

### 环境要求

- Python 3.11+
- OpenAI API Key
- Docker（可选，用于容器化部署）
- Kubernetes（可选，用于容器编排）

### 安装步骤

#### 1. 克隆项目

```bash
git clone https://github.com/your-org/multi-agent-system.git
cd multi-agent-system
```

#### 2. 创建虚拟环境

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows
```

#### 3. 安装依赖

```bash
pip install -r requirements.txt
```

#### 4. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，填入你的 OpenAI API Key
```

`.env` 文件内容：
```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4
OPENAI_TEMPERATURE=0.3
LOG_LEVEL=INFO
```

#### 5. 验证安装

```bash
python -c "from agents.requirements import RequirementsAgent; print('安装成功!')"
```

### 快速体验

```python
import asyncio
from agents.requirements import RequirementsAgent

async def main():
    # 创建需求分析智能体
    agent = RequirementsAgent({
        "model": "gpt-4",
        "temperature": 0.3
    })
    
    # 分析需求
    result = await agent.analyze_requirements("""
        我想开发一个在线商城系统，主要功能包括：
        1. 用户注册和登录
        2. 商品浏览和搜索
        3. 购物车功能
        4. 在线支付
        5. 订单管理
    """)
    
    print(f"分析状态: {result['status']}")
    print(f"功能需求数: {len(result['requirements']['functional_requirements'])}")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 详细使用

### 完整开发流程

```python
import asyncio
from agents.requirements import RequirementsAgent
from agents.technical import TechnicalAgent
from agents.mvp import MVPDeveloperAgent
from agents.code_review import CodeReviewAgent
from agents.testing import TestingAgent
from agents.deployment import DeploymentAgent

async def full_development_pipeline(user_input: str):
    """完整的开发流水线"""
    
    # 1. 需求分析
    print("📋 步骤1: 需求分析...")
    req_agent = RequirementsAgent({"model": "gpt-4"})
    req_result = await req_agent.analyze_requirements(user_input)
    
    if req_result["status"] != "success":
        print(f"❌ 需求分析失败: {req_result.get('error')}")
        return None
    
    # 2. 技术设计
    print("🏗️ 步骤2: 技术设计...")
    tech_agent = TechnicalAgent({"model": "gpt-4"})
    tech_result = await tech_agent.design_technical_solution(req_result["requirements"])
    
    if tech_result["status"] != "success":
        print(f"❌ 技术设计失败: {tech_result.get('error')}")
        return None
    
    # 3. MVP开发
    print("💻 步骤3: MVP开发...")
    mvp_agent = MVPDeveloperAgent({"model": "gpt-4"})
    mvp_result = await mvp_agent.develop_mvp(tech_result, req_result["requirements"])
    
    if mvp_result["status"] != "success":
        print(f"❌ MVP开发失败: {mvp_result.get('error')}")
        return None
    
    # 4. 代码审查
    print("🔍 步骤4: 代码审查...")
    review_agent = CodeReviewAgent({"model": "gpt-4"})
    review_result = await review_agent.review_code(mvp_result["code_files"])
    
    if review_result["status"] != "success":
        print(f"❌ 代码审查失败: {review_result.get('error')}")
        return None
    
    # 5. 软件测试
    print("🧪 步骤5: 软件测试...")
    testing_agent = TestingAgent({"model": "gpt-4"})
    test_result = await testing_agent.run_tests(mvp_result["code_files"], tech_result)
    
    if test_result["status"] != "success":
        print(f"❌ 软件测试失败: {test_result.get('error')}")
        return None
    
    # 6. 部署规划
    print("🚀 步骤6: 部署规划...")
    deploy_agent = DeploymentAgent({"model": "gpt-4"})
    deploy_result = await deploy_agent.plan_deployment(
        mvp_result["code_files"],
        tech_result,
        test_result
    )
    
    if deploy_result["status"] != "success":
        print(f"❌ 部署规划失败: {deploy_result.get('error')}")
        return None
    
    # 输出结果
    print("\n" + "=" * 60)
    print("✅ 开发流水线完成!")
    print("=" * 60)
    print(f"📋 需求: {len(req_result['requirements']['functional_requirements'])} 个功能需求")
    print(f"🏗️ 架构: {tech_result['architecture']['system_architecture']['pattern']}")
    print(f"💻 代码: {len(mvp_result['code_files'])} 个文件")
    print(f"🔍 审查评分: {review_result['overall_score']:.1f}/100")
    print(f"🧪 测试通过率: {test_result['results']['overall']['pass_rate']:.1f}%")
    print(f"🚀 部署策略: {deploy_result['deployment_plan']['deployment_strategy']['type']}")
    
    return {
        "requirements": req_result,
        "technical": tech_result,
        "mvp": mvp_result,
        "review": review_result,
        "testing": test_result,
        "deployment": deploy_result
    }

# 运行完整流水线
if __name__ == "__main__":
    result = asyncio.run(full_development_pipeline("""
        开发一个博客系统，功能包括：
        1. 用户注册和登录
        2. 文章发布和编辑
        3. 评论系统
        4. 标签分类
        5. 搜索功能
    """))
```

### 单独使用智能体

#### 需求分析

```python
from agents.requirements import RequirementsAgent

async def analyze_requirements():
    agent = RequirementsAgent({"model": "gpt-4"})
    
    result = await agent.analyze_requirements("开发一个待办事项应用")
    
    # 获取用户故事
    user_stories = result["user_stories"]["user_stories"]
    for story in user_stories:
        print(f"作为{story['role']}，我想要{story['feature']}，以便{story['benefit']}")
    
    # 获取优先级
    priority_matrix = result["priority_matrix"]["priority_matrix"]
    print(f"必须有: {len(priority_matrix['must_have'])} 个")
    print(f"应该有: {len(priority_matrix['should_have'])} 个")
    
    return result
```

#### 技术设计

```python
from agents.technical import TechnicalAgent

async def design_technical_solution(requirements):
    agent = TechnicalAgent({"model": "gpt-4"})
    
    result = await agent.design_technical_solution(requirements)
    
    # 获取架构设计
    architecture = result["architecture"]["system_architecture"]
    print(f"架构模式: {architecture['pattern']}")
    
    # 获取技术栈
    tech_stack = result["tech_stack"]
    print(f"后端语言: {tech_stack['backend']['language']['name']}")
    print(f"Web框架: {tech_stack['backend']['web_framework']['name']}")
    
    return result
```

#### MVP开发

```python
from agents.mvp import MVPDeveloperAgent

async def develop_mvp(technical_solution, requirements):
    agent = MVPDeveloperAgent({"model": "gpt-4"})
    
    result = await agent.develop_mvp(technical_solution, requirements)
    
    # 获取代码文件
    code_files = result["code_files"]
    for file in code_files:
        print(f"文件: {file['path']}")
        print(f"描述: {file['description']}")
    
    return result
```

#### 代码审查

```python
from agents.code_review import CodeReviewAgent

async def review_code(code_files):
    agent = CodeReviewAgent({"model": "gpt-4"})
    
    result = await agent.review_code(code_files)
    
    # 获取审查结果
    print(f"是否通过: {result['approved']}")
    print(f"总体评分: {result['overall_score']}")
    print(f"问题数量: {result['issues_summary']['total']}")
    
    # 获取重构建议
    suggestions = result["refactoring_suggestions"]
    for suggestion in suggestions[:3]:
        print(f"建议: {suggestion['title']}")
    
    return result
```

#### 软件测试

```python
from agents.testing import TestingAgent

async def run_tests(code_files, project_info):
    agent = TestingAgent({"model": "gpt-4"})
    
    result = await agent.run_tests(code_files, project_info)
    
    # 获取测试结果
    print(f"单元测试通过率: {result['results']['unit_tests']['pass_rate']:.1f}%")
    print(f"总体覆盖率: {result['coverage']['overall']:.1f}%")
    
    # 获取缺陷
    bugs = result["bugs"]
    print(f"缺陷数量: {len(bugs)}")
    
    return result
```

#### 部署规划

```python
from agents.deployment import DeploymentAgent

async def plan_deployment(code_files, technical_solution, test_results):
    agent = DeploymentAgent({"model": "gpt-4"})
    
    result = await agent.plan_deployment(
        code_files,
        technical_solution,
        test_results
    )
    
    # 获取部署配置
    print(f"部署策略: {result['deployment_plan']['deployment_strategy']['type']}")
    print(f"环境数量: {len(result['deployment_plan']['environments'])}")
    
    # 获取Docker配置
    docker_config = result["docker_config"]
    print(f"Dockerfile: {'已生成' if docker_config.get('dockerfile', {}).get('content') else '未生成'}")
    
    return result
```

---

## 项目结构

```
multi_agent_system/
├── 📄 __init__.py                    # 包初始化
├── 📄 main.py                        # 主入口
├── 📄 README.md                      # 项目说明
├── 📄 requirements.txt               # 依赖列表
├── 📄 .env.example                   # 环境变量示例
├── 📄 .gitignore                     # Git忽略文件
│
├── 📁 config/                        # 配置目录
│   ├── 📄 __init__.py
│   └── 📄 settings.py                # 系统配置
│
├── 📁 utils/                         # 工具目录
│   ├── 📄 __init__.py
│   ├── 📄 state_manager.py           # 状态管理器
│   └── 📄 logger.py                  # 日志工具
│
├── 📁 agents/                        # 智能体目录
│   ├── 📄 __init__.py
│   │
│   ├── 📁 requirements/              # 智能体1：需求分析师
│   │   ├── 📄 __init__.py
│   │   ├── 📄 agent.py               # 主智能体类
│   │   ├── 📄 state.py               # 状态定义
│   │   ├── 📄 prompts.py             # 提示词模板
│   │   ├── 📄 README.md              # 智能体文档
│   │   └── 📁 tools/                 # 工具集
│   │       ├── 📄 requirement_parser.py
│   │       ├── 📄 user_story_generator.py
│   │       ├── 📄 acceptance_criteria.py
│   │       ├── 📄 priority_calculator.py
│   │       └── 📄 coordinator.py
│   │
│   ├── 📁 technical/                 # 智能体2：技术架构师
│   │   ├── 📄 __init__.py
│   │   ├── 📄 agent.py
│   │   ├── 📄 state.py
│   │   ├── 📄 prompts.py
│   │   ├── 📄 README.md
│   │   └── 📁 tools/
│   │       ├── 📄 architecture_designer.py
│   │       ├── 📄 tech_stack_selector.py
│   │       ├── 📄 api_designer.py
│   │       ├── 📄 database_designer.py
│   │       ├── 📄 security_designer.py
│   │       └── 📄 cost_estimator.py
│   │
│   ├── 📁 mvp/                       # 智能体3：MVP开发者
│   │   ├── 📄 __init__.py
│   │   ├── 📄 agent.py
│   │   ├── 📄 state.py
│   │   ├── 📄 prompts.py
│   │   ├── 📄 README.md
│   │   └── 📁 tools/
│   │       ├── 📄 project_generator.py
│   │       ├── 📄 code_generator.py
│   │       ├── 📄 test_generator.py
│   │       ├── 📄 doc_generator.py
│   │       ├── 📄 docker_generator.py
│   │       └── 📄 code_optimizer.py
│   │
│   ├── 📁 code_review/               # 智能体4：代码审查员
│   │   ├── 📄 __init__.py
│   │   ├── 📄 agent.py
│   │   ├── 📄 state.py
│   │   ├── 📄 prompts.py
│   │   ├── 📄 README.md
│   │   └── 📁 tools/
│   │       ├── 📄 style_checker.py
│   │       ├── 📄 quality_assessor.py
│   │       ├── 📄 security_scanner.py
│   │       ├── 📄 performance_analyzer.py
│   │       ├── 📄 complexity_analyzer.py
│   │       └── 📄 refactoring_advisor.py
│   │
│   ├── 📁 testing/                   # 智能体5：测试工程师
│   │   ├── 📄 __init__.py
│   │   ├── 📄 agent.py
│   │   ├── 📄 state.py
│   │   ├── 📄 prompts.py
│   │   ├── 📄 README.md
│   │   └── 📁 tools/
│   │       ├── 📄 unit_test_generator.py
│   │       ├── 📄 integration_test_generator.py
│   │       ├── 📄 performance_test_generator.py
│   │       ├── 📄 security_test_generator.py
│   │       ├── 📄 test_data_generator.py
│   │       └── 📄 test_report_generator.py
│   │
│   └── 📁 deployment/                # 智能体6：部署工程师
│       ├── 📄 __init__.py
│       ├── 📄 agent.py
│       ├── 📄 state.py
│       ├── 📄 prompts.py
│       ├── 📄 README.md
│       └── 📁 tools/
│           ├── 📄 deployment_planner.py
│           ├── 📄 docker_configurator.py
│           ├── 📄 kubernetes_configurator.py
│           ├── 📄 cicd_configurator.py
│           ├── 📄 monitoring_configurator.py
│           └── 📄 deployment_doc_generator.py
│
├── 📁 tests/                         # 测试目录
│   ├── 📄 __init__.py
│   ├── 📄 test_requirements_agent.py
│   ├── 📄 test_technical_agent.py
│   ├── 📄 test_mvp_agent.py
│   ├── 📄 test_code_review_agent.py
│   ├── 📄 test_testing_agent.py
│   └── 📄 test_deployment_agent.py
│
├── 📁 examples/                      # 示例目录
│   ├── 📄 __init__.py
│   ├── 📄 requirements_example.py
│   ├── 📄 technical_example.py
│   ├── 📄 mvp_example.py
│   ├── 📄 code_review_example.py
│   ├── 📄 testing_example.py
│   └── 📄 deployment_example.py
│
├── 📁 data/                          # 数据目录
│   └── 📁 states/                    # 状态持久化
│
└── 📁 logs/                          # 日志目录
```

---

## API参考

### RequirementsAgent

```python
class RequirementsAgent:
    def __init__(self, config: Dict[str, Any] = None)
    async def analyze_requirements(self, user_input: str) -> Dict[str, Any]
    async def decompose_tasks(self) -> Dict[str, Any]
    async def coordinate_agents(self, tasks: List[Dict]) -> Dict[str, Any]
    def get_state(self) -> RequirementsState
    def reset(self) -> None
```

### TechnicalAgent

```python
class TechnicalAgent:
    def __init__(self, config: Dict[str, Any] = None)
    async def design_technical_solution(self, requirements: Dict) -> Dict[str, Any]
    async def create_adr(self, title: str, context: str, decision: str, ...) -> Dict[str, Any]
    def get_state(self) -> TechnicalState
    def get_technical_spec(self) -> Dict[str, Any]
    def reset(self) -> None
```

### MVPDeveloperAgent

```python
class MVPDeveloperAgent:
    def __init__(self, config: Dict[str, Any] = None)
    async def develop_mvp(self, technical_solution: Dict, requirements: Dict) -> Dict[str, Any]
    async def optimize_code(self, optimization_goals: List[str] = None) -> Dict[str, Any]
    def get_code_files(self) -> List[Dict[str, Any]]
    def get_test_files(self) -> List[Dict[str, Any]]
    def get_progress(self) -> float
    def reset(self) -> None
```

### CodeReviewAgent

```python
class CodeReviewAgent:
    def __init__(self, config: Dict[str, Any] = None)
    async def review_code(self, code_files: List[Dict], project_info: Dict = None) -> Dict[str, Any]
    def get_issues(self) -> Dict[str, List[Dict]]
    def get_refactoring_suggestions(self) -> List[Dict[str, Any]]
    def reset(self) -> None
```

### TestingAgent

```python
class TestingAgent:
    def __init__(self, config: Dict[str, Any] = None)
    async def run_tests(self, code_files: List[Dict], project_info: Dict = None, test_config: Dict = None) -> Dict[str, Any]
    def get_bugs(self) -> List[Dict[str, Any]]
    def get_test_report(self) -> Dict[str, Any]
    def reset(self) -> None
```

### DeploymentAgent

```python
class DeploymentAgent:
    def __init__(self, config: Dict[str, Any] = None)
    async def plan_deployment(self, code_files: List[Dict], technical_solution: Dict, test_results: Dict, project_info: Dict = None) -> Dict[str, Any]
    async def estimate_cost(self, deployment_config: Dict) -> Dict[str, Any]
    def get_deployment_plan(self) -> Dict[str, Any]
    def get_docker_config(self) -> Dict[str, Any]
    def get_kubernetes_config(self) -> Dict[str, Any]
    def reset(self) -> None
```

---

## 配置说明

### 系统配置

```python
# config/settings.py

@dataclass
class SystemConfig:
    # 项目信息
    project_name: str = "多智能体应用开发系统"
    version: str = "1.0.0"
    
    # LLM配置
    default_llm: LLMConfig = field(default_factory=LLMConfig)
    
    # 智能体配置
    agents: Dict[str, AgentConfig] = field(default_factory=dict)
    
    # 状态管理
    state_persistence: bool = True
    state_storage: str = "./data/states"
    
    # 日志配置
    log_level: str = "INFO"
    log_file: str = "./logs/system.log"
    
    # 安全配置
    sandbox_enabled: bool = True
    max_execution_time: int = 300
    
    # 成本控制
    max_tokens_per_request: int = 8000
    max_requests_per_minute: int = 60
    monthly_budget: float = 1000.0
```

### 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `OPENAI_API_KEY` | OpenAI API密钥 | 必填 |
| `OPENAI_MODEL` | 默认模型 | gpt-4 |
| `OPENAI_TEMPERATURE` | 温度参数 | 0.3 |
| `LOG_LEVEL` | 日志级别 | INFO |
| `LOG_FILE` | 日志文件 | ./logs/system.log |
| `STATE_PERSISTENCE` | 状态持久化 | true |
| `SANDBOX_ENABLED` | 沙箱执行 | true |
| `MAX_EXECUTION_TIME` | 最大执行时间 | 300秒 |
| `MONTHLY_BUDGET` | 月度预算 | 1000美元 |

---

## 开发指南

### 添加新智能体

1. **创建目录结构**

```bash
mkdir -p agents/new_agent/tools
touch agents/new_agent/__init__.py
touch agents/new_agent/agent.py
touch agents/new_agent/state.py
touch agents/new_agent/prompts.py
```

2. **实现状态定义**

```python
# agents/new_agent/state.py
from typing import TypedDict

class NewAgentState(TypedDict):
    # 定义状态字段
    input: dict
    output: dict
    status: str
```

3. **实现智能体**

```python
# agents/new_agent/agent.py
from langchain.agents import AgentExecutor, create_openai_tools_agent
from .state import NewAgentState

class NewAgent:
    def __init__(self, config):
        self.llm = ChatOpenAI(model=config.get("model", "gpt-4"))
        self.tools = self._init_tools()
        self.agent = self._create_agent()
    
    def _init_tools(self):
        return [CustomTool1(), CustomTool2()]
    
    async def execute(self, input_data):
        # 实现执行逻辑
        return result
```

4. **注册到系统**

```python
# __init__.py
from .agents.new_agent import NewAgent
```

### 添加新工具

```python
from langchain.tools import BaseTool
from typing import Optional
from langchain_core.callbacks import CallbackManagerForToolRun

class CustomTool(BaseTool):
    name: str = "custom_tool"
    description: str = "工具描述"
    
    def _run(
        self,
        input_param: str,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> dict:
        # 实现工具逻辑
        result = {"output": "处理结果"}
        return result
    
    async def _arun(
        self,
        input_param: str,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> dict:
        import asyncio
        return await asyncio.to_thread(self._run, input_param, run_manager)
```

### 自定义提示词

```python
# agents/new_agent/prompts.py

CUSTOM_PROMPT = """
你是一位专业的{role}。

## 职责
{responsibilities}

## 输出要求
{output_requirements}

请以JSON格式输出结果。
"""
```

---

## 测试

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_requirements_agent.py

# 运行带覆盖率的测试
pytest --cov=agents --cov-report=html
```

### 测试结构

```python
import pytest
from agents.requirements import RequirementsAgent

class TestRequirementsAgent:
    @pytest.mark.asyncio
    async def test_analyze_requirements(self):
        agent = RequirementsAgent({"model": "gpt-4"})
        result = await agent.analyze_requirements("开发一个待办事项应用")
        
        assert result["status"] == "success"
        assert "requirements" in result
        assert len(result["requirements"]["functional_requirements"]) > 0
    
    @pytest.mark.asyncio
    async def test_get_state(self):
        agent = RequirementsAgent({"model": "gpt-4"})
        state = agent.get_state()
        
        assert state["status"] == "initialized"
```

### 测试覆盖率目标

| 模块 | 目标覆盖率 |
|------|------------|
| agents/requirements | ≥ 80% |
| agents/technical | ≥ 80% |
| agents/mvp | ≥ 80% |
| agents/code_review | ≥ 80% |
| agents/testing | ≥ 80% |
| agents/deployment | ≥ 80% |
| utils/ | ≥ 90% |
| config/ | ≥ 90% |

---

## 部署

### Docker部署

```bash
# 构建镜像
docker build -t multi-agent-system .

# 运行容器
docker run -d \
  --name multi-agent-system \
  -e OPENAI_API_KEY=your_api_key \
  -p 8000:8000 \
  multi-agent-system
```

### Docker Compose部署

```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### Kubernetes部署

```bash
# 创建命名空间
kubectl create namespace multi-agent

# 部署应用
kubectl apply -f k8s/

# 查看状态
kubectl get pods -n multi-agent

# 查看日志
kubectl logs -f deployment/multi-agent-system -n multi-agent
```

---

## 常见问题

### Q: 如何获取OpenAI API Key？

A: 访问 [OpenAI官网](https://platform.openai.com/) 注册账号并创建API Key。

### Q: 支持哪些模型？

A: 目前支持：
- GPT-4
- GPT-4 Turbo
- GPT-3.5 Turbo
- Claude（通过兼容接口）

### Q: 如何降低API成本？

A: 可以通过以下方式降低成本：
1. 使用 `gpt-3.5-turbo` 替代 `gpt-4`
2. 降低 `temperature` 参数
3. 限制 `max_tokens`
4. 启用缓存机制

### Q: 如何处理API限流？

A: 系统内置了重试机制和限流控制，可以通过配置调整：

```python
config = {
    "max_retries": 3,
    "retry_delay": 1,
    "requests_per_minute": 60
}
```

### Q: 如何扩展新的智能体？

A: 参考 [开发指南](#开发指南) 中的"添加新智能体"部分。

### Q: 状态如何持久化？

A: 状态会自动持久化到 `./data/states/` 目录，可以通过配置关闭：

```python
config = {"state_persistence": False}
```

---

## 更新日志

### v1.0.0 (2026-08-17)

- ✨ 初始版本发布
- ✨ 实现6个核心智能体
  - 需求分析师
  - 技术架构师
  - MVP开发者
  - 代码审查员
  - 测试工程师
  - 部署工程师
- ✨ 实现状态同步机制
- ✨ 实现错误恢复机制
- ✨ 实现进度监控
- ✨ 添加完整的测试用例
- ✨ 添加使用示例

---

## 贡献指南

### 如何贡献

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

### 代码规范

- 遵循 PEP 8 规范
- 使用类型注解
- 编写文档字符串
- 添加单元测试

### 提交规范

```
<type>(<scope>): <subject>

<body>

<footer>
```

类型：
- `feat`: 新功能
- `fix`: 修复bug
- `docs`: 文档更新
- `style`: 代码格式
- `refactor`: 重构
- `test`: 测试
- `chore`: 构建/工具

---

## 许可证

MIT License

Copyright (c) 2026 Multi-Agent System

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

---

## 联系方式

- 项目主页: [GitHub](https://github.com/your-org/multi-agent-system)
- 问题反馈: [Issues](https://github.com/your-org/multi-agent-system/issues)
- 邮箱: your-email@example.com

---

## 致谢

- [LangChain](https://langchain.com/) - 智能体框架
- [LangGraph](https://langchain.com/) - 状态管理
- [OpenAI](https://openai.com/) - 大语言模型
- [FastAPI](https://fastapi.tiangolo.com/) - Web框架
- [Docker](https://www.docker.com/) - 容器化
- [Kubernetes](https://kubernetes.io/) - 容器编排

---

**最后更新**: 2026-08-17

**版本**: 1.0.0
