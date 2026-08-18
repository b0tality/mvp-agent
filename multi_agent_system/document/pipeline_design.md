# 多智能体流水线编排器 - 完整项目方案

## 一、项目概述

### 1.1 背景

当前项目 `multi_agent_system/` 已实现6个独立Agent，但缺少统一的流水线编排器。`main.py` 仅调用需求分析Agent，完整流水线只在示例和README中演示。

### 1.2 目标

创建完整的6-Agent流水线编排器，支持：
- 从用户需求到部署的一键运行
- Agent间数据自动传递
- 条件回退（代码审查/测试不通过时回退）
- 进度追踪和状态持久化
- 灵活配置（跳过阶段、自定义参数）
- 故障保底（备用Agent + 规则降级）

### 1.3 核心价值

| 价值点 | 说明 |
|--------|------|
| **自动化** | 一键完成需求→部署全流程 |
| **可靠性** | 多层故障保底，确保流水线不中断 |
| **可追溯** | 完整执行历史和检查点 |
| **灵活性** | 支持跳过阶段、自定义配置 |

---

## 二、系统架构

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           PipelineOrchestrator                           │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                         PipelineState (共享状态)                     │ │
│  │  requirements → technical_solution → code_files → test_results → ..│ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                    │                                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│  │ Stage 1  │ │ Stage 2  │ │ Stage 3  │ │ Stage 4  │ │ Stage 5  │ │ Stage 6  │ │
│  │ 需求分析 │→│ 技术架构 │→│ MVP实现  │→│ 代码审查 │→│  测试   │→│  部署   │ │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘ │
│       │            │            │            │            │            │        │
│       └────────────┴────────────┴────────────┴────────────┴────────────┘        │
│                                    │                                            │
│                            ┌───────┴───────┐                                    │
│                            │  FallbackManager│                                   │
│                            │  (故障保底)     │                                   │
│                            └───────────────┘                                    │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 核心组件

```
pipeline/
├── __init__.py           # 模块导出
├── orchestrator.py       # PipelineOrchestrator 主编排器
├── state.py              # PipelineState 共享状态
├── config.py             # PipelineConfig 配置
├── stages.py             # Stage定义和执行逻辑
└── fallback.py           # FallbackManager 故障保底
```

### 2.3 数据流

```
用户输入
    │
    ▼
[1] RequirementsAgent.analyze_requirements(user_input)
    → requirements, user_stories, priority_matrix
    │
    ▼
[2] TechnicalAgent.design_technical_solution(requirements)
    → architecture, tech_stack, api_design, database_design
    │
    ▼
[3] MVPDeveloperAgent.develop_mvp(technical_solution, requirements)
    → code_files, test_files, docker_config
    │
    ▼
[4] CodeReviewAgent.review_code(code_files, project_info)
    → approved?, scores, issues
    │ (不通过则回退到Step 3)
    ▼
[5] TestingAgent.run_tests(code_files, project_info)
    → test_results, bugs, coverage
    │ (有严重bug则回退到Step 3)
    ▼
[6] DeploymentAgent.plan_deployment(code_files, technical_solution, test_results)
    → deployment_plan, configs
    │
    ▼
输出完整项目
```

---

## 三、核心设计

### 3.1 PipelineState（共享状态）

```python
class PipelineState:
    """聚合所有Agent状态的共享状态容器"""
    requirements: Dict[str, Any]      # Agent 1输出
    technical_solution: Dict[str, Any] # Agent 2输出
    mvp_result: Dict[str, Any]        # Agent 3输出
    code_review: Dict[str, Any]       # Agent 4输出
    test_results: Dict[str, Any]      # Agent 5输出
    deployment: Dict[str, Any]        # Agent 6输出
    current_stage: str                # 当前阶段
    history: List[StageRecord]        # 执行历史
    checkpoints: List[Checkpoint]     # 检查点列表
```

### 3.2 PipelineOrchestrator（编排器）

```python
class PipelineOrchestrator:
    """6-Agent流水线编排器"""
    
    async def run(self, user_input: str) -> PipelineResult:
        """完整流水线运行"""
        
    async def run_stage(self, stage: str, **kwargs) -> Dict:
        """运行单个阶段"""
        
    async def resume_from_checkpoint(self, checkpoint_path: str):
        """从检查点恢复（支持断点续跑）"""
        
    async def _run_requirements(self, user_input: str) -> Dict:
        """阶段1: 需求分析"""
        
    async def _run_technical(self, requirements: Dict) -> Dict:
        """阶段2: 技术架构"""
        
    async def _run_mvp(self, technical_solution: Dict, requirements: Dict) -> Dict:
        """阶段3: MVP实现"""
        
    async def _run_code_review(self, code_files: List, project_info: Dict) -> Dict:
        """阶段4: 代码审查（含回退逻辑）"""
        
    async def _run_testing(self, code_files: List, project_info: Dict) -> Dict:
        """阶段5: 测试（含回退逻辑）"""
        
    async def _run_deployment(self, code_files: List, technical_solution: Dict, test_results: Dict) -> Dict:
        """阶段6: 部署规划"""
```

### 3.3 PipelineConfig（配置）

```python
class PipelineConfig:
    """流水线配置"""
    model: str = "gpt-4"                    # 全局模型
    max_retries: int = 3                    # 最大回退次数
    skip_stages: List[str] = []             # 跳过的阶段
    stage_configs: Dict[str, Dict] = {}     # 各阶段独立配置
    persistence_path: Optional[str] = None  # 状态持久化路径
    cost_limit: float = 1.0                 # 成本限制（美元）
```

---

## 四、Agent间通信机制

### 4.1 通信架构

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ Requirements │────▶│  Technical  │────▶│    MVP      │
│   Agent      │     │   Agent     │     │   Agent     │
└──────┬───────┘     └──────┬──────┘     └──────┬──────┘
       │                    │                    │
       ▼                    ▼                    ▼
┌──────────────────────────────────────────────────────┐
│                   PipelineState                       │
│  requirements → technical_solution → code_files → ... │
└──────────────────────────────────────────────────────┘
       │                    │                    │
       ▼                    ▼                    ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ CodeReview   │────▶│  Testing    │────▶│ Deployment  │
│   Agent      │     │   Agent     │     │   Agent     │
└─────────────┘     └─────────────┘     └─────────────┘
```

### 4.2 通信规则

1. **PipelineState是唯一数据源**（Single Source of Truth）
2. **Orchestrator负责数据中转**：Agent间不直接通信
3. **Orchestrator负责格式转换**：将上游输出转换为下游输入格式
4. **每个阶段完成后更新PipelineState**

---

## 五、记忆机制设计

### 5.1 三层记忆架构

```
┌─────────────────────────────────────────┐
│ Layer 1: Agent内部记忆 (Agent Memory)    │
│ - conversation_history (对话历史)         │
│ - state_manager (当前状态)               │
│ - 生命周期：单次Agent调用                 │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│ Layer 2: 流水线记忆 (Pipeline Memory)    │
│ - PipelineState (共享状态)               │
│ - stage_history (阶段执行记录)            │
│ - rollback_stack (回退栈)                │
│ - 生命周期：单次流水线运行                │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│ Layer 3: 持久化记忆 (Persistent Memory)  │
│ - JSON文件持久化                          │
│ - 项目历史记录                            │
│ - 可跨会话恢复                            │
└─────────────────────────────────────────┘
```

### 5.2 检查点机制

```python
class PipelineCheckpoint:
    """流水线检查点"""
    stage: str                    # 完成的阶段
    timestamp: str                # 时间戳
    state_snapshot: Dict          # 状态快照
    agent_states: Dict[str, Dict] # 各Agent状态
```

**检查点触发时机**：
- 每个阶段完成时自动保存
- 流水线异常终止时保存
- 支持从检查点恢复（断点续跑）

---

## 六、故障保底机制

### 6.1 故障类型分类

| 故障类型 | 示例 | 处理策略 |
|---------|------|---------|
| **API调用失败** | OpenAI超时/限流 | 指数退避重试（3次） |
| **解析失败** | LLM输出非JSON | 重试+提示词修正 |
| **业务逻辑失败** | 代码审查不通过 | 条件回退 |
| **Agent初始化失败** | 配置错误 | 快速失败，报错退出 |
| **未知异常** | 内存溢出等 | 捕获+记录+降级 |

### 6.2 备用Agent方案

**三级备用机制**：
1. **主Agent**（GPT-4）→ 完整功能
2. **备用Agent 1**（GPT-3.5）→ 简化功能
3. **备用Agent 2**（规则引擎）→ 模板输出

**备用Agent策略**：

| 阶段 | 主Agent | 备用Agent 1 | 备用Agent 2 | 降级方案 |
|------|---------|-------------|-------------|---------|
| 需求分析 | GPT-4 | GPT-3.5-turbo | 规则解析器 | 返回模板需求 |
| 技术架构 | GPT-4 | GPT-3.5-turbo | 默认技术栈 | 返回默认架构 |
| MVP实现 | GPT-4 | GPT-3.5-turbo | 代码模板生成器 | 返回骨架代码 |
| 代码审查 | GPT-4 | GPT-3.5-turbo | 静态分析工具 | 跳过审查 |
| 测试 | GPT-4 | GPT-3.5-turbo | 基础测试模板 | 跳过测试 |
| 部署 | GPT-4 | GPT-3.5-turbo | 默认Docker配置 | 返回默认配置 |

### 6.3 备用Agent在工作流中的位置

```
用户输入
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│                    PipelineOrchestrator                       │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Stage 1: 需求分析                                     │   │
│  │  ┌─────────────┐    ┌─────────────┐    ┌───────────┐ │   │
│  │  │ 主Agent     │───▶│ 备用Agent   │───▶│ 规则引擎  │ │   │
│  │  │ (GPT-4)     │    │ (GPT-3.5)   │    │ (无LLM)   │ │   │
│  │  └─────────────┘    └─────────────┘    └───────────┘ │   │
│  └──────────────────────────────────────────────────────┘   │
│                          │ 成功                              │
│                          ▼                                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Stage 2: 技术架构                                     │   │
│  │  ┌─────────────┐    ┌─────────────┐    ┌───────────┐ │   │
│  │  │ 主Agent     │───▶│ 备用Agent   │───▶│ 规则引擎  │ │   │
│  │  │ (GPT-4)     │    │ (GPT-3.5)   │    │ (无LLM)   │ │   │
│  │  └─────────────┘    └─────────────┘    └───────────┘ │   │
│  └──────────────────────────────────────────────────────┘   │
│                          │                                   │
│                          ▼ ... (后续阶段同理)                 │
└─────────────────────────────────────────────────────────────┘
```

**关键点**：
- 备用Agent与主Agent**在同一阶段内**，不是独立阶段
- 每个阶段内部有完整的主→备用→规则降级链
- 降级是**阶段内**的，不是跨阶段的

### 6.4 备用Agent Prompt设计

**设计原则**：
- 备用Agent使用**简化版Prompt**，减少token消耗和复杂度
- 明确标注"备用模式"，让LLM知道输出需要更保守/稳定
- 降低temperature，提高输出确定性

**各阶段备用Prompt**：

| 阶段 | 主Prompt要点 | 备用Prompt要点 | 规则模板 |
|------|-------------|---------------|---------|
| 需求分析 | 详细分析、用户故事、验收标准 | 只提取核心功能（≤5个） | 关键词提取+模板填充 |
| 技术架构 | 完整架构、多方案对比 | 返回默认技术栈（FastAPI+React+PG） | 预定义技术栈映射 |
| MVP实现 | 完整代码生成 | 生成骨架代码（接口+模型） | 代码模板拼接 |
| 代码审查 | 6维度详细审查 | 只检查语法和基本规范 | 静态分析工具输出 |
| 测试 | 4类测试生成 | 只生成基础单元测试 | 测试模板生成 |
| 部署 | 完整部署方案 | 返回默认Docker配置 | 预置docker-compose模板 |

### 6.5 重试机制

| 维度 | 主Agent | 备用Agent | 规则引擎 |
|------|---------|----------|---------|
| **重试次数** | 3次 | 1-2次 | 0次（直接执行） |
| **重试延迟** | 指数退避(1s,2s,4s) | 固定延迟(1s) | 无 |
| **超时时间** | 120-300s | 60-120s | 5s |
| **错误处理** | 重试→备用→降级 | 重试→下一个备用 | 直接降级策略 |
| **Prompt修正** | 是（解析失败时修正提示） | 否（使用简化Prompt） | 无 |

### 6.6 完整故障处理流程

```
Agent执行
    │
    ├─ 成功 → 保存检查点 → 下一阶段
    │
    └─ 失败
        │
        ├─ 可重试错误 (API/解析)
        │   └─ 指数退避重试 (最多3次)
        │       ├─ 成功 → 继续
        │       └─ 仍失败 → 尝试备用Agent
        │
        ├─ 尝试备用Agent (按优先级)
        │   ├─ 备用Agent 1 (如GPT-3.5)
        │   │   ├─ 成功 → 继续
        │   │   └─ 失败 → 尝试下一个
        │   ├─ 备用Agent 2 (如规则引擎)
        │   │   ├─ 成功 → 继续
        │   │   └─ 失败 → 规则降级
        │   └─ 规则降级 (无需LLM)
        │       ├─ 成功 → 继续
        │       └─ 失败 → 检查降级策略
        │
        ├─ 业务逻辑失败 (审查/测试不通过)
        │   └─ 检查回退次数
        │       ├─ 未达上限 → 回退到上游阶段
        │       └─ 达到上限 → 降级处理
        │
        └─ 降级处理
            ├─ SKIP → 跳过该阶段，继续后续
            ├─ DEFAULT → 使用默认结果继续
            └─ ABORT → 终止流水线，返回已有结果
```

---

## 七、多Agent故障处理

### 7.1 场景分析

| 场景 | 故障Agent数 | 影响 | 处理策略 |
|------|------------|------|---------|
| **单点故障** | 1个 | 该阶段降级 | 备用Agent → 规则降级 |
| **双点故障** | 2个 | 两个阶段降级 | 独立降级，继续运行 |
| **级联故障** | 3个+ | 多阶段受影响 | 检查依赖关系，智能降级 |
| **全部故障** | 6个 | 流水线无法继续 | 终止，返回已有结果 |

### 7.2 依赖感知降级

```python
class StageDependency:
    """阶段依赖关系"""
    dependencies = {
        "requirements": [],                    # 无依赖
        "technical": ["requirements"],         # 依赖需求分析
        "mvp": ["requirements", "technical"],  # 依赖需求和技术
        "code_review": ["mvp"],                # 依赖MVP
        "testing": ["mvp"],                    # 依赖MVP
        "deployment": ["mvp", "testing"]       # 依赖MVP和测试
    }
    
    def get_minimal_deps(self, stage: str) -> List[str]:
        """获取最小依赖（降级时使用）"""
        minimal_deps = {
            "mvp": ["requirements"],           # 只需需求，技术可降级
            "code_review": ["mvp"],
            "testing": ["mvp"],
            "deployment": ["mvp"]              # 只需MVP，测试可跳过
        }
        return minimal_deps.get(stage, self.dependencies[stage])
```

### 7.3 级联故障处理

```python
class CascadeFailureHandler:
    """级联故障处理器"""
    
    def __init__(self, max_consecutive_failures: int = 2):
        self.max_consecutive_failures = max_consecutive_failures
        self.consecutive_failures = 0
        self.failed_stages = []
    
    def should_abort(self) -> bool:
        """检查是否应该终止"""
        # 连续失败过多
        if self.consecutive_failures >= self.max_consecutive_failures:
            return True
        
        # 关键阶段失败
        critical_stages = ["requirements", "mvp"]
        if any(stage in self.failed_stages for stage in critical_stages):
            return True
        
        return False
```

### 7.4 降级策略配置

```python
class MultiAgentFailureConfig:
    """多Agent故障处理配置"""
    
    # 级联故障阈值
    max_consecutive_failures: int = 2
    
    # 关键阶段（失败即终止）
    critical_stages: List[str] = ["requirements", "mvp"]
    
    # 可跳过阶段
    skippable_stages: List[str] = ["code_review", "deployment"]
    
    # 降级策略
    degradation_policies: Dict[str, str] = {
        "requirements": "abort",      # 需求分析失败必须终止
        "technical": "default",       # 技术架构可用默认值
        "mvp": "abort",              # MVP失败必须终止
        "code_review": "skip",       # 代码审查可跳过
        "testing": "skip",           # 测试可跳过
        "deployment": "default"      # 部署可用默认配置
    }
```

---

## 八、成本分析

### 8.1 成本构成

| 组件 | 主Agent成本 | 备用Agent成本 | 规则引擎成本 |
|------|------------|--------------|------------|
| **API调用** | GPT-4: ~$0.03/1K tokens | GPT-3.5: ~$0.002/1K tokens | $0 |
| **重试成本** | 3次 × 主Agent成本 | 2次 × 备用Agent成本 | $0 |
| **时间成本** | 120-300s | 60-120s | <5s |
| **开发成本** | 高（完整Prompt） | 中（简化Prompt） | 低（模板） |

### 8.2 场景成本对比

| 场景 | 成本 | 增幅 |
|------|------|------|
| **正常运行**（全部成功） | ~$0.54 | 基准 |
| **单点故障**（1阶段降级） | ~$0.574 | +6.3% |
| **双点故障**（2阶段降级） | ~$0.608 | +12.6% |
| **多点故障**（3阶段降级） | ~$0.642 | +18.9% |
| **最坏场景**（全部降级） | ~$0.744 | +37.8% |

### 8.3 成本优化策略

```python
class CostOptimization:
    """成本优化配置"""
    
    # 1. 动态模型选择（根据阶段重要性）
    stage_models = {
        "requirements": "gpt-4",      # 关键阶段，用GPT-4
        "technical": "gpt-4",         # 关键阶段
        "mvp": "gpt-4",              # 关键阶段
        "code_review": "gpt-3.5-turbo",  # 可降级
        "testing": "gpt-3.5-turbo",      # 可降级
        "deployment": "gpt-3.5-turbo"    # 可降级
    }
    
    # 2. 成本限制
    max_cost_per_run: float = 1.0    # 单次运行最大成本
    max_cost_per_stage: float = 0.2  # 单阶段最大成本
    
    # 3. 智能降级（根据预算动态调整）
    def get_agent_config(self, stage: str, remaining_budget: float):
        if remaining_budget < 0.1:
            # 预算不足，直接用规则降级
            return RuleBasedConfig()
        elif remaining_budget < 0.3:
            # 预算紧张，用GPT-3.5
            return AgentConfig(model="gpt-3.5-turbo")
        else:
            # 预算充足，用主Agent
            return self.stage_configs[stage].primary
```

### 8.4 成本监控

```python
class CostTracker:
    """成本追踪器"""
    
    def __init__(self):
        self.total_tokens = 0
        self.total_cost = 0.0
        self.stage_costs = {}
        self.fallback_costs = {}
    
    def record_usage(self, stage: str, agent_type: str, tokens: int, cost: float):
        """记录使用量"""
        self.total_tokens += tokens
        self.total_cost += cost
        
        if stage not in self.stage_costs:
            self.stage_costs[stage] = 0
        self.stage_costs[stage] += cost
        
        if agent_type != "primary":
            key = f"{stage}_{agent_type}"
            if key not in self.fallback_costs:
                self.fallback_costs[key] = 0
            self.fallback_costs[key] += cost
    
    def get_report(self) -> Dict:
        """生成成本报告"""
        return {
            "total_cost": self.total_cost,
            "total_tokens": self.total_tokens,
            "stage_breakdown": self.stage_costs,
            "fallback_overhead": sum(self.fallback_costs.values()),
            "fallback_percentage": (sum(self.fallback_costs.values()) / self.total_cost * 100) if self.total_cost > 0 else 0
        }
```

---

## 九、实现步骤

### Step 1: 创建 `pipeline/state.py`
- PipelineState 数据类
- StageRecord 执行记录
- PipelineCheckpoint 检查点
- 状态序列化/反序列化

### Step 2: 创建 `pipeline/config.py`
- PipelineConfig 配置类
- StageConfig 阶段配置
- RetryConfig 重试配置
- CostOptimization 成本优化
- 验证逻辑

### Step 3: 创建 `pipeline/stages.py`
- Stage 枚举定义
- StageExecutor 阶段执行器
- StageDependency 依赖关系
- Stage间数据转换

### Step 4: 创建 `pipeline/fallback.py`
- FallbackManager 故障保底管理器
- FallbackAgentConfig 备用Agent配置
- RuleBasedFallback 规则降级
- CascadeFailureHandler 级联故障处理
- CostTracker 成本追踪

### Step 5: 创建 `pipeline/orchestrator.py`
- PipelineOrchestrator 主类
- 6个阶段执行方法
- 条件回退逻辑
- 检查点管理
- 进度回调

### Step 6: 更新 `main.py`
- 集成PipelineOrchestrator
- 支持 `--pipeline` 参数运行完整流水线
- 保留单Agent运行模式

### Step 7: 创建 `examples/pipeline_example.py`
- 完整流水线示例
- 各阶段独立运行示例
- 回退场景示例
- 成本监控示例

---

## 十、修改文件清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `pipeline/__init__.py` | 新建 | 模块导出 |
| `pipeline/state.py` | 新建 | 共享状态、检查点、执行记录 |
| `pipeline/config.py` | 新建 | 流水线配置、阶段配置、重试配置 |
| `pipeline/stages.py` | 新建 | 阶段定义、执行器、依赖关系 |
| `pipeline/fallback.py` | 新建 | 故障保底、备用Agent、规则降级、成本追踪 |
| `pipeline/orchestrator.py` | 新建 | 主编排器、阶段执行、回退逻辑 |
| `main.py` | 修改 | 集成流水线、新增CLI参数 |
| `examples/pipeline_example.py` | 新建 | 使用示例 |

---

## 十一、验证方式

### 11.1 单元测试
- PipelineState 序列化/反序列化
- PipelineConfig 验证逻辑
- RetryPolicy 重试机制
- CostTracker 成本计算

### 11.2 集成测试
- 完整流水线运行（6阶段）
- 阶段间数据传递
- 检查点保存和恢复

### 11.3 故障测试
- 模拟API调用失败，验证重试机制
- 模拟代码审查失败，验证回退逻辑
- 模拟多阶段故障，验证级联处理
- 模拟全部故障，验证降级策略

### 11.4 成本测试
- 正常场景成本计算
- 故障场景成本计算
- 成本限制触发测试

### 11.5 示例验证
- 运行 `examples/pipeline_example.py`
- 验证输出格式和内容

---

## 十二、关键文件参考

| 文件 | 说明 |
|------|------|
| `agents/requirements/agent.py` | RequirementsAgent 接口 |
| `agents/technical/agent.py` | TechnicalAgent 接口 |
| `agents/mvp/agent.py` | MVPDeveloperAgent 接口 |
| `agents/code_review/agent.py` | CodeReviewAgent 接口 |
| `agents/testing/agent.py` | TestingAgent 接口 |
| `agents/deployment/agent.py` | DeploymentAgent 接口 |
| `utils/state_manager.py` | 通用状态管理器（可复用） |
| `config/settings.py` | 配置管理模块 |

---

## 十三、风险和注意事项

### 13.1 技术风险
- **LLM输出不稳定**：JSON解析可能失败，需要 robust 的解析逻辑
- **API限流**：OpenAI可能限流，需要重试和退避机制
- **成本超支**：多次重试可能导致成本飙升，需要成本限制

### 13.2 设计风险
- **过度设计**：备用Agent和规则降级可能过于复杂，需要权衡
- **状态管理复杂**：多层状态（Agent内部、Pipeline、持久化）可能混乱

### 13.3 缓解措施
- 从简单开始，逐步增加复杂度
- 充分测试每个组件
- 监控成本和性能
- 提供配置选项，允许用户调整策略

---

## 十四、详细实现规格

### 14.1 `pipeline/__init__.py` 实现规格

```python
"""
多智能体流水线编排器模块
"""

from .state import PipelineState, StageRecord, PipelineCheckpoint
from .config import PipelineConfig, StageConfig, RetryConfig
from .stages import Stage, StageExecutor, StageDependency
from .fallback import FallbackManager, RuleBasedFallback, CascadeFailureHandler, CostTracker
from .orchestrator import PipelineOrchestrator, PipelineResult

__all__ = [
    "PipelineState",
    "StageRecord", 
    "PipelineCheckpoint",
    "PipelineConfig",
    "StageConfig",
    "RetryConfig",
    "Stage",
    "StageExecutor",
    "StageDependency",
    "FallbackManager",
    "RuleBasedFallback",
    "CascadeFailureHandler",
    "CostTracker",
    "PipelineOrchestrator",
    "PipelineResult",
]
```

### 14.2 `pipeline/state.py` 实现规格

```python
"""
流水线状态管理
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json


@dataclass
class StageRecord:
    """阶段执行记录"""
    stage: str
    status: str  # success/failed/skipped/degraded
    started_at: str
    completed_at: str
    duration_seconds: float
    agent_used: str  # primary/fallback_1/fallback_2/rule_based
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineCheckpoint:
    """流水线检查点"""
    stage: str
    timestamp: str
    state_snapshot: Dict[str, Any]
    agent_states: Dict[str, Dict[str, Any]]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage": self.stage,
            "timestamp": self.timestamp,
            "state_snapshot": self.state_snapshot,
            "agent_states": self.agent_states
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PipelineCheckpoint":
        return cls(**data)


class PipelineState:
    """流水线共享状态"""
    
    def __init__(self):
        self.requirements: Dict[str, Any] = {}
        self.technical_solution: Dict[str, Any] = {}
        self.mvp_result: Dict[str, Any] = {}
        self.code_review: Dict[str, Any] = {}
        self.test_results: Dict[str, Any] = {}
        self.deployment: Dict[str, Any] = {}
        self.current_stage: str = "pending"
        self.history: List[StageRecord] = []
        self.checkpoints: List[PipelineCheckpoint] = []
        self.rollback_stack: List[Dict[str, Any]] = []
    
    def update(self, stage: str, data: Dict[str, Any]) -> None:
        """更新阶段数据"""
        setattr(self, stage, data)
    
    def get(self, stage: str) -> Dict[str, Any]:
        """获取阶段数据"""
        return getattr(self, stage, {})
    
    def add_history(self, record: StageRecord) -> None:
        """添加执行记录"""
        self.history.append(record)
    
    def add_checkpoint(self, checkpoint: PipelineCheckpoint) -> None:
        """添加检查点"""
        self.checkpoints.append(checkpoint)
    
    def add_rollback(self, rollback_info: Dict[str, Any]) -> None:
        """添加回退信息"""
        self.rollback_stack.append(rollback_info)
    
    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典"""
        return {
            "requirements": self.requirements,
            "technical_solution": self.technical_solution,
            "mvp_result": self.mvp_result,
            "code_review": self.code_review,
            "test_results": self.test_results,
            "deployment": self.deployment,
            "current_stage": self.current_stage,
            "history": [
                {
                    "stage": r.stage,
                    "status": r.status,
                    "started_at": r.started_at,
                    "completed_at": r.completed_at,
                    "duration_seconds": r.duration_seconds,
                    "agent_used": r.agent_used,
                    "error": r.error,
                    "metadata": r.metadata
                }
                for r in self.history
            ],
            "checkpoints": [c.to_dict() for c in self.checkpoints],
            "rollback_stack": self.rollback_stack
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PipelineState":
        """从字典反序列化"""
        state = cls()
        state.requirements = data.get("requirements", {})
        state.technical_solution = data.get("technical_solution", {})
        state.mvp_result = data.get("mvp_result", {})
        state.code_review = data.get("code_review", {})
        state.test_results = data.get("test_results", {})
        state.deployment = data.get("deployment", {})
        state.current_stage = data.get("current_stage", "pending")
        state.rollback_stack = data.get("rollback_stack", [])
        
        for r_data in data.get("history", []):
            state.history.append(StageRecord(**r_data))
        
        for c_data in data.get("checkpoints", []):
            state.checkpoints.append(PipelineCheckpoint.from_dict(c_data))
        
        return state
    
    def save_to_file(self, filepath: str) -> None:
        """保存到文件"""
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
    
    @classmethod
    def load_from_file(cls, filepath: str) -> "PipelineState":
        """从文件加载"""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)
```

### 14.3 `pipeline/config.py` 实现规格

```python
"""
流水线配置
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


@dataclass
class RetryConfig:
    """重试配置"""
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 30.0
    exponential_base: float = 2.0


@dataclass
class StageConfig:
    """阶段配置"""
    model: str = "gpt-4"
    temperature: float = 0.3
    max_tokens: int = 4000
    timeout: int = 180
    retry: RetryConfig = field(default_factory=RetryConfig)
    fallback_model: str = "gpt-3.5-turbo"
    fallback_timeout: int = 120
    fallback_retry: RetryConfig = field(default_factory=lambda: RetryConfig(max_retries=2))


@dataclass
class PipelineConfig:
    """流水线配置"""
    model: str = "gpt-4"
    max_retries: int = 3
    skip_stages: List[str] = field(default_factory=list)
    persistence_path: Optional[str] = None
    cost_limit: float = 1.0
    
    stage_configs: Dict[str, StageConfig] = field(default_factory=lambda: {
        "requirements": StageConfig(model="gpt-4", temperature=0.3, timeout=120),
        "technical": StageConfig(model="gpt-4", temperature=0.2, timeout=180),
        "mvp": StageConfig(model="gpt-4", temperature=0.4, timeout=300, max_tokens=8000),
        "code_review": StageConfig(model="gpt-4", temperature=0.1, timeout=180),
        "testing": StageConfig(model="gpt-4", temperature=0.2, timeout=240),
        "deployment": StageConfig(model="gpt-4", temperature=0.2, timeout=180),
    })
    
    critical_stages: List[str] = field(default_factory=lambda: ["requirements", "mvp"])
    skippable_stages: List[str] = field(default_factory=lambda: ["code_review", "deployment"])
    max_consecutive_failures: int = 2
    
    degradation_policies: Dict[str, str] = field(default_factory=lambda: {
        "requirements": "abort",
        "technical": "default",
        "mvp": "abort",
        "code_review": "skip",
        "testing": "skip",
        "deployment": "default"
    })
    
    def get_stage_config(self, stage: str) -> StageConfig:
        return self.stage_configs.get(stage, StageConfig())
    
    def should_skip(self, stage: str) -> bool:
        return stage in self.skip_stages
    
    def is_critical(self, stage: str) -> bool:
        return stage in self.critical_stages
    
    def get_degradation_policy(self, stage: str) -> str:
        return self.degradation_policies.get(stage, "abort")
```

### 14.4 `pipeline/stages.py` 实现规格

```python
"""
阶段定义和执行
"""

from enum import Enum
from typing import Dict, List, Any, Optional, Callable, Awaitable
from dataclasses import dataclass


class Stage(str, Enum):
    """流水线阶段枚举"""
    REQUIREMENTS = "requirements"
    TECHNICAL = "technical"
    MVP = "mvp"
    CODE_REVIEW = "code_review"
    TESTING = "testing"
    DEPLOYMENT = "deployment"


@dataclass
class StageDependency:
    """阶段依赖关系"""
    dependencies: Dict[str, List[str]] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = {
                Stage.REQUIREMENTS: [],
                Stage.TECHNICAL: [Stage.REQUIREMENTS],
                Stage.MVP: [Stage.REQUIREMENTS, Stage.TECHNICAL],
                Stage.CODE_REVIEW: [Stage.MVP],
                Stage.TESTING: [Stage.MVP],
                Stage.DEPLOYMENT: [Stage.MVP, Stage.TESTING]
            }
    
    def can_proceed(self, stage: str, completed_stages: List[str]) -> bool:
        deps = self.dependencies.get(stage, [])
        return all(dep in completed_stages for dep in deps)
    
    def get_minimal_deps(self, stage: str) -> List[str]:
        minimal_deps = {
            Stage.MVP: [Stage.REQUIREMENTS],
            Stage.CODE_REVIEW: [Stage.MVP],
            Stage.TESTING: [Stage.MVP],
            Stage.DEPLOYMENT: [Stage.MVP]
        }
        return minimal_deps.get(stage, self.dependencies.get(stage, []))


class StageExecutor:
    """阶段执行器"""
    
    def __init__(self):
        self._executors: Dict[str, Callable[..., Awaitable[Dict[str, Any]]]] = {}
    
    def register(self, stage: str, executor: Callable[..., Awaitable[Dict[str, Any]]]) -> None:
        self._executors[stage] = executor
    
    async def execute(self, stage: str, **kwargs) -> Dict[str, Any]:
        if stage not in self._executors:
            raise ValueError(f"未注册的阶段: {stage}")
        return await self._executors[stage](**kwargs)
    
    def has_executor(self, stage: str) -> bool:
        return stage in self._executors
```

### 14.5 `pipeline/fallback.py` 实现规格

```python
"""
故障保底机制
"""

import asyncio
from typing import Dict, List, Any, Optional, Type, Callable, Awaitable
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class RetryPolicy:
    """重试策略"""
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 30.0
    exponential_base: float = 2.0
    
    async def execute_with_retry(self, func: Callable[..., Awaitable[Any]], *args, **kwargs) -> Any:
        last_exception = None
        for attempt in range(self.max_retries):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    delay = min(self.base_delay * (self.exponential_base ** attempt), self.max_delay)
                    await asyncio.sleep(delay)
        raise last_exception


@dataclass
class AgentConfig:
    """Agent配置"""
    agent_class: Type
    model: str
    temperature: float = 0.3
    max_tokens: int = 4000
    timeout: int = 180


@dataclass
class FallbackAgentConfig:
    """备用Agent配置"""
    stage: str
    primary: AgentConfig
    fallbacks: List[AgentConfig] = field(default_factory=list)
    primary_retry: RetryPolicy = field(default_factory=RetryPolicy)
    fallback_retry: RetryPolicy = field(default_factory=lambda: RetryPolicy(max_retries=2))


class RuleBasedFallback:
    """基于规则的降级方案（不依赖LLM）"""
    
    def requirements_fallback(self, user_input: str) -> Dict[str, Any]:
        keywords = [word for word in user_input.split() if len(word) > 3][:5]
        return {
            "functional_requirements": [
                {"id": f"FR-{i+1}", "title": kw, "description": f"从输入提取的功能: {kw}"}
                for i, kw in enumerate(keywords)
            ],
            "non_functional_requirements": [
                {"id": "NFR-1", "category": "performance", "description": "基本性能要求"},
                {"id": "NFR-2", "category": "security", "description": "基本安全要求"}
            ],
            "status": "fallback"
        }
    
    def technical_fallback(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "tech_stack": {"backend": "Python/FastAPI", "frontend": "React", "database": "PostgreSQL"},
            "architecture": {"pattern": "monolith", "description": "单体架构（降级方案）"},
            "api_design": {"style": "REST", "endpoints": []},
            "database_design": {"type": "relational", "tables": []},
            "status": "fallback"
        }
    
    def mvp_fallback(self, technical_solution: Dict[str, Any], requirements: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "code_files": [
                {"path": "main.py", "content": "from fastapi import FastAPI\napp = FastAPI()\n\n@app.get('/')\ndef root():\n    return {'message': 'Hello World'}\n", "language": "python"},
                {"path": "requirements.txt", "content": "fastapi==0.104.1\nuvicorn==0.24.0\n", "language": "text"}
            ],
            "test_files": [],
            "docker_config": {},
            "status": "fallback"
        }
    
    def code_review_fallback(self, code_files: List[Dict[str, Any]]) -> Dict[str, Any]:
        return {
            "overall_score": 70,
            "file_reviews": [{"file_path": f.get("path", "unknown"), "score": 70, "issues": []} for f in code_files],
            "issues": [],
            "approved": True,
            "status": "fallback"
        }
    
    def testing_fallback(self, code_files: List[Dict[str, Any]]) -> Dict[str, Any]:
        return {
            "test_suites": [],
            "coverage": {"line": 0, "branch": 0, "function": 0},
            "bugs": [],
            "security_vulnerabilities": [],
            "test_report": {"summary": "降级模式：跳过详细测试"},
            "status": "fallback"
        }
    
    def deployment_fallback(self, technical_solution: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "deployment_plan": {"strategy": "rolling", "environments": ["development", "production"]},
            "docker_config": {"Dockerfile": "FROM python:3.11-slim\nWORKDIR /app\nCOPY requirements.txt .\nRUN pip install -r requirements.txt\nCOPY . .\nCMD [\"uvicorn\", \"main:app\", \"--host\", \"0.0.0.0\", \"--port\", \"8000\"]"},
            "kubernetes_config": {},
            "cicd_config": {},
            "monitoring_config": {},
            "status": "fallback"
        }


class CascadeFailureHandler:
    """级联故障处理器"""
    
    def __init__(self, max_consecutive_failures: int = 2, critical_stages: List[str] = None):
        self.max_consecutive_failures = max_consecutive_failures
        self.critical_stages = critical_stages or ["requirements", "mvp"]
        self.consecutive_failures = 0
        self.failed_stages: List[str] = []
    
    def record_failure(self, stage: str) -> None:
        self.consecutive_failures += 1
        self.failed_stages.append(stage)
    
    def record_success(self) -> None:
        self.consecutive_failures = 0
    
    def should_abort(self) -> bool:
        if self.consecutive_failures >= self.max_consecutive_failures:
            return True
        if any(stage in self.failed_stages for stage in self.critical_stages):
            return True
        return False
    
    def get_abort_reason(self) -> Optional[str]:
        if self.consecutive_failures >= self.max_consecutive_failures:
            return f"连续{self.consecutive_failures}个阶段失败"
        critical_failed = [s for s in self.failed_stages if s in self.critical_stages]
        if critical_failed:
            return f"关键阶段失败: {', '.join(critical_failed)}"
        return None


class CostTracker:
    """成本追踪器"""
    
    COST_PER_1K_TOKENS = {
        "gpt-4": 0.03,
        "gpt-3.5-turbo": 0.002,
        "gpt-4-turbo": 0.01
    }
    
    def __init__(self):
        self.total_tokens = 0
        self.total_cost = 0.0
        self.stage_costs: Dict[str, float] = {}
        self.fallback_costs: Dict[str, float] = {}
    
    def record_usage(self, stage: str, agent_type: str, model: str, tokens: int) -> None:
        cost_per_1k = self.COST_PER_1K_TOKENS.get(model, 0.03)
        cost = (tokens / 1000) * cost_per_1k
        self.total_tokens += tokens
        self.total_cost += cost
        if stage not in self.stage_costs:
            self.stage_costs[stage] = 0
        self.stage_costs[stage] += cost
        if agent_type != "primary":
            key = f"{stage}_{agent_type}"
            if key not in self.fallback_costs:
                self.fallback_costs[key] = 0
            self.fallback_costs[key] += cost
    
    def get_report(self) -> Dict[str, Any]:
        return {
            "total_cost": round(self.total_cost, 4),
            "total_tokens": self.total_tokens,
            "stage_breakdown": {k: round(v, 4) for k, v in self.stage_costs.items()},
            "fallback_overhead": round(sum(self.fallback_costs.values()), 4),
            "fallback_percentage": round((sum(self.fallback_costs.values()) / self.total_cost * 100) if self.total_cost > 0 else 0, 2)
        }
    
    def is_within_budget(self, budget: float) -> bool:
        return self.total_cost <= budget


class FallbackManager:
    """故障保底管理器"""
    
    def __init__(self, config: "PipelineConfig"):
        self.config = config
        self.rule_based = RuleBasedFallback()
        self.cascade_handler = CascadeFailureHandler(
            max_consecutive_failures=config.max_consecutive_failures,
            critical_stages=config.critical_stages
        )
        self.cost_tracker = CostTracker()
    
    async def execute_with_fallback(
        self,
        stage: str,
        primary_func: Callable[..., Awaitable[Dict[str, Any]]],
        fallback_funcs: List[Callable[..., Awaitable[Dict[str, Any]]]],
        rule_fallback_func: Callable[..., Dict[str, Any]],
        *args,
        **kwargs
    ) -> Dict[str, Any]:
        stage_config = self.config.get_stage_config(stage)
        
        # 1. 尝试主Agent
        try:
            result = await self._execute_with_retry(primary_func, stage_config.primary_retry, stage, "primary", stage_config.model, *args, **kwargs)
            self.cascade_handler.record_success()
            return result
        except Exception:
            self.cascade_handler.record_failure(stage)
        
        # 2. 尝试备用Agent
        for i, fallback_func in enumerate(fallback_funcs):
            try:
                result = await self._execute_with_retry(fallback_func, stage_config.fallback_retry, stage, f"fallback_{i+1}", stage_config.fallback_model, *args, **kwargs)
                self.cascade_handler.record_success()
                return result
            except Exception:
                continue
        
        # 3. 规则降级
        try:
            result = rule_fallback_func(*args, **kwargs)
            self.cost_tracker.record_usage(stage, "rule_based", "none", 0)
            self.cascade_handler.record_success()
            result["agent_used"] = "rule_based"
            return result
        except Exception:
            pass
        
        # 4. 所有方式都失败
        return self._apply_degradation_policy(stage)
    
    async def _execute_with_retry(self, func, retry_policy, stage, agent_type, model, *args, **kwargs):
        async def wrapper():
            result = await func(*args, **kwargs)
            estimated_tokens = len(str(result)) // 4
            self.cost_tracker.record_usage(stage, agent_type, model, estimated_tokens)
            result["agent_used"] = agent_type
            return result
        return await retry_policy.execute_with_retry(wrapper)
    
    def _apply_degradation_policy(self, stage: str) -> Dict[str, Any]:
        policy = self.config.get_degradation_policy(stage)
        if policy == "abort":
            return {"status": "aborted", "error": f"阶段 {stage} 失败，流水线终止"}
        elif policy == "skip":
            return {"status": "skipped", "message": f"阶段 {stage} 已跳过"}
        elif policy == "default":
            return {"status": "default", "message": f"阶段 {stage} 使用默认值"}
        else:
            return {"status": "failed", "error": f"阶段 {stage} 失败"}
    
    def should_abort(self) -> bool:
        return self.cascade_handler.should_abort()
    
    def get_abort_reason(self) -> Optional[str]:
        return self.cascade_handler.get_abort_reason()
```

### 14.6 `pipeline/orchestrator.py` 实现规格

```python
"""
流水线编排器
"""

import asyncio
from typing import Dict, List, Any, Optional, Callable, Awaitable
from dataclasses import dataclass, field
from datetime import datetime

from .state import PipelineState, StageRecord, PipelineCheckpoint
from .config import PipelineConfig
from .stages import Stage, StageExecutor, StageDependency
from .fallback import FallbackManager


@dataclass
class PipelineResult:
    """流水线结果"""
    status: str  # success/partial/failed/aborted
    results: Dict[str, Dict[str, Any]]
    failed_stages: List[str]
    degraded_stages: List[str]
    abort_reason: Optional[str] = None
    cost_report: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "results": self.results,
            "summary": {
                "total_stages": 6,
                "success_stages": len([r for r in self.results.values() if r.get("status") == "success"]),
                "failed_stages": len(self.failed_stages),
                "degraded_stages": len(self.degraded_stages)
            },
            "failed_stages": self.failed_stages,
            "degraded_stages": self.degraded_stages,
            "abort_reason": self.abort_reason,
            "cost_report": self.cost_report
        }


class PipelineOrchestrator:
    """6-Agent流水线编排器"""
    
    def __init__(self, config: PipelineConfig, agents: Dict[str, Any]):
        self.config = config
        self.agents = agents
        self.state = PipelineState()
        self.fallback_manager = FallbackManager(config)
        self.stage_executor = StageExecutor()
        self.stage_dependency = StageDependency()
        self._register_stage_executors()
    
    def _register_stage_executors(self) -> None:
        self.stage_executor.register(Stage.REQUIREMENTS, self._run_requirements)
        self.stage_executor.register(Stage.TECHNICAL, self._run_technical)
        self.stage_executor.register(Stage.MVP, self._run_mvp)
        self.stage_executor.register(Stage.CODE_REVIEW, self._run_code_review)
        self.stage_executor.register(Stage.TESTING, self._run_testing)
        self.stage_executor.register(Stage.DEPLOYMENT, self._run_deployment)
    
    async def run(self, user_input: str) -> PipelineResult:
        """完整流水线运行"""
        self.state.current_stage = "started"
        results = {}
        failed_stages = []
        degraded_stages = []
        
        stages = [Stage.REQUIREMENTS, Stage.TECHNICAL, Stage.MVP, Stage.CODE_REVIEW, Stage.TESTING, Stage.DEPLOYMENT]
        
        for stage in stages:
            if self.config.should_skip(stage):
                results[stage] = {"status": "skipped"}
                continue
            
            completed = [s for s in results if results[s].get("status") in ["success", "fallback", "default"]]
            if not self.stage_dependency.can_proceed(stage, completed):
                minimal_deps = self.stage_dependency.get_minimal_deps(stage)
                if not all(dep in completed for dep in minimal_deps):
                    results[stage] = {"status": "skipped", "reason": "依赖不满足"}
                    continue
            
            if self.fallback_manager.should_abort():
                abort_reason = self.fallback_manager.get_abort_reason()
                return PipelineResult(status="aborted", results=results, failed_stages=failed_stages, degraded_stages=degraded_stages, abort_reason=abort_reason, cost_report=self.fallback_manager.cost_tracker.get_report())
            
            self.state.current_stage = stage
            started_at = datetime.now()
            
            try:
                result = await self.stage_executor.execute(
                    stage,
                    user_input=user_input if stage == Stage.REQUIREMENTS else None,
                    requirements=self.state.requirements if stage != Stage.REQUIREMENTS else None,
                    technical_solution=self.state.technical_solution if stage in [Stage.MVP, Stage.DEPLOYMENT] else None,
                    code_files=self.state.mvp_result.get("code_files", []) if stage in [Stage.CODE_REVIEW, Stage.TESTING, Stage.DEPLOYMENT] else None,
                    project_info=self.state.mvp_result if stage in [Stage.CODE_REVIEW, Stage.TESTING] else None,
                    test_results=self.state.test_results if stage == Stage.DEPLOYMENT else None
                )
                
                self.state.update(stage, result)
                results[stage] = result
                
                if result.get("agent_used") != "primary":
                    degraded_stages.append(stage)
                
                completed_at = datetime.now()
                duration = (completed_at - started_at).total_seconds()
                self.state.add_history(StageRecord(stage=stage, status=result.get("status", "success"), started_at=started_at.isoformat(), completed_at=completed_at.isoformat(), duration_seconds=duration, agent_used=result.get("agent_used", "primary")))
                self._save_checkpoint(stage)
                
            except Exception as e:
                failed_stages.append(stage)
                results[stage] = {"status": "failed", "error": str(e)}
        
        if failed_stages:
            status = "failed" if len(failed_stages) == len(stages) else "partial"
        else:
            status = "success"
        
        return PipelineResult(status=status, results=results, failed_stages=failed_stages, degraded_stages=degraded_stages, cost_report=self.fallback_manager.cost_tracker.get_report())
    
    async def run_stage(self, stage: str, **kwargs) -> Dict[str, Any]:
        return await self.stage_executor.execute(stage, **kwargs)
    
    async def resume_from_checkpoint(self, checkpoint_path: str) -> PipelineResult:
        self.state = PipelineState.load_from_file(checkpoint_path)
        # 从最后一个检查点继续
        pass
    
    def _save_checkpoint(self, stage: str) -> None:
        checkpoint = PipelineCheckpoint(stage=stage, timestamp=datetime.now().isoformat(), state_snapshot=self.state.to_dict(), agent_states={})
        self.state.add_checkpoint(checkpoint)
        if self.config.persistence_path:
            self.state.save_to_file(self.config.persistence_path)
    
    async def _run_requirements(self, user_input: str, **kwargs) -> Dict[str, Any]:
        agent = self.agents["requirements"]
        return await self.fallback_manager.execute_with_fallback(Stage.REQUIREMENTS, agent.analyze_requirements, [], self.fallback_manager.rule_based.requirements_fallback, user_input)
    
    async def _run_technical(self, requirements: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        agent = self.agents["technical"]
        return await self.fallback_manager.execute_with_fallback(Stage.TECHNICAL, agent.design_technical_solution, [], self.fallback_manager.rule_based.technical_fallback, requirements)
    
    async def _run_mvp(self, technical_solution: Dict[str, Any], requirements: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        agent = self.agents["mvp"]
        return await self.fallback_manager.execute_with_fallback(Stage.MVP, agent.develop_mvp, [], lambda ts, req: self.fallback_manager.rule_based.mvp_fallback(ts, req), technical_solution, requirements)
    
    async def _run_code_review(self, code_files: List[Dict[str, Any]], project_info: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        agent = self.agents["code_review"]
        result = await self.fallback_manager.execute_with_fallback(Stage.CODE_REVIEW, agent.review_code, [], self.fallback_manager.rule_based.code_review_fallback, code_files, project_info)
        if result.get("overall_score", 100) < 80:
            self.state.add_rollback({"from_stage": Stage.CODE_REVIEW, "to_stage": Stage.MVP, "reason": "quality_score_below_threshold", "feedback": result.get("issues", [])})
        return result
    
    async def _run_testing(self, code_files: List[Dict[str, Any]], project_info: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        agent = self.agents["testing"]
        result = await self.fallback_manager.execute_with_fallback(Stage.TESTING, agent.run_tests, [], self.fallback_manager.rule_based.testing_fallback, code_files, project_info)
        bugs = result.get("bugs", [])
        if any(bug.get("severity") == "critical" for bug in bugs):
            self.state.add_rollback({"from_stage": Stage.TESTING, "to_stage": Stage.MVP, "reason": "critical_bugs_found", "feedback": bugs})
        return result
    
    async def _run_deployment(self, code_files: List[Dict[str, Any]], technical_solution: Dict[str, Any], test_results: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        agent = self.agents["deployment"]
        return await self.fallback_manager.execute_with_fallback(Stage.DEPLOYMENT, agent.plan_deployment, [], self.fallback_manager.rule_based.deployment_fallback, code_files, technical_solution, test_results)
```

### 14.7 `main.py` 更新规格

```python
"""
多智能体应用开发系统入口
"""

import asyncio
import argparse
from dotenv import load_dotenv

from agents.requirements import RequirementsAgent
from agents.technical import TechnicalAgent
from agents.mvp import MVPDeveloperAgent
from agents.code_review import CodeReviewAgent
from agents.testing import TestingAgent
from agents.deployment import DeploymentAgent
from config.settings import get_default_config
from pipeline import PipelineOrchestrator, PipelineConfig


async def run_pipeline(user_input: str) -> None:
    """运行完整流水线"""
    load_dotenv()
    config = get_default_config()
    
    agents = {
        "requirements": RequirementsAgent(config),
        "technical": TechnicalAgent(config),
        "mvp": MVPDeveloperAgent(config),
        "code_review": CodeReviewAgent(config),
        "testing": TestingAgent(config),
        "deployment": DeploymentAgent(config)
    }
    
    pipeline_config = PipelineConfig(model=config.get("model", "gpt-4"), persistence_path="./pipeline_state.json")
    orchestrator = PipelineOrchestrator(pipeline_config, agents)
    
    print("\n" + "=" * 60)
    print("开始运行完整流水线...")
    print("=" * 60)
    
    result = await orchestrator.run(user_input)
    
    print("\n" + "=" * 60)
    print("流水线运行结果:")
    print("=" * 60)
    print(f"状态: {result.status}")
    print(f"成功阶段: {result.results.keys()}")
    print(f"失败阶段: {result.failed_stages}")
    print(f"降级阶段: {result.degraded_stages}")
    print(f"成本报告: {result.cost_report}")
    print("\n" + "=" * 60)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="多智能体应用开发系统")
    parser.add_argument("--input", "-i", type=str, help="用户需求输入")
    parser.add_argument("--interactive", action="store_true", help="交互模式")
    parser.add_argument("--pipeline", action="store_true", help="运行完整流水线")
    
    args = parser.parse_args()
    
    if args.pipeline:
        if args.input:
            asyncio.run(run_pipeline(args.input))
        else:
            example_input = "我想开发一个在线商城系统，主要功能包括用户注册、商品浏览、购物车、在线支付、订单管理"
            asyncio.run(run_pipeline(example_input))
    elif args.interactive:
        print("多智能体应用开发系统 - 交互模式")
        print("输入 'quit' 或 'exit' 退出")
        while True:
            user_input = input("\n请输入您的需求: ").strip()
            if user_input.lower() in ["quit", "exit"]:
                break
            if user_input:
                asyncio.run(run_pipeline(user_input))
    elif args.input:
        asyncio.run(run_pipeline(args.input))
    else:
        example_input = "我想开发一个在线商城系统，主要功能包括用户注册、商品浏览、购物车、在线支付、订单管理"
        asyncio.run(run_pipeline(example_input))


if __name__ == "__main__":
    main()
```

### 14.8 `examples/pipeline_example.py` 实现规格

```python
"""
流水线使用示例
"""

import asyncio
import json
from pipeline import PipelineOrchestrator, PipelineConfig


async def example_full_pipeline():
    """完整流水线示例"""
    print("=" * 60)
    print("示例1: 完整流水线运行")
    print("=" * 60)
    
    config = PipelineConfig(model="gpt-4", cost_limit=1.0, persistence_path="./example_state.json")
    agents = {}  # 需要实际初始化
    orchestrator = PipelineOrchestrator(config, agents)
    
    user_input = "开发一个博客系统，支持用户认证、文章发布、评论功能"
    result = await orchestrator.run(user_input)
    
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))


async def example_single_stage():
    """单阶段运行示例"""
    print("\n" + "=" * 60)
    print("示例2: 单阶段运行")
    print("=" * 60)
    
    config = PipelineConfig()
    agents = {}
    orchestrator = PipelineOrchestrator(config, agents)
    
    result = await orchestrator.run_stage("requirements", user_input="开发一个待办事项应用")
    print(json.dumps(result, ensure_ascii=False, indent=2))


async def example_resume_from_checkpoint():
    """从检查点恢复示例"""
    print("\n" + "=" * 60)
    print("示例3: 从检查点恢复")
    print("=" * 60)
    
    config = PipelineConfig(persistence_path="./checkpoint.json")
    agents = {}
    orchestrator = PipelineOrchestrator(config, agents)
    
    result = await orchestrator.resume_from_checkpoint("./checkpoint.json")
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))


async def main():
    """主函数"""
    print("多智能体流水线编排器 - 使用示例")
    print("=" * 60)
    
    await example_full_pipeline()
    await example_single_stage()
    await example_resume_from_checkpoint()
    
    print("\n" + "=" * 60)
    print("所有示例执行完成!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
```

---

## 十五、实现优先级

### P0（必须实现）
1. `pipeline/state.py` - 基础状态管理
2. `pipeline/config.py` - 基础配置
3. `pipeline/stages.py` - 阶段定义
4. `pipeline/orchestrator.py` - 核心编排逻辑
5. `main.py` 更新 - 集成流水线

### P1（应该实现）
1. `pipeline/fallback.py` - 故障保底机制
2. 检查点保存和恢复
3. 成本追踪

### P2（可以实现）
1. 备用Agent配置
2. 规则降级方案
3. 级联故障处理
4. 完整示例

---

## 十六、测试策略

### 16.1 单元测试

```python
# tests/test_pipeline_state.py
def test_pipeline_state_serialization():
    state = PipelineState()
    state.requirements = {"test": "data"}
    serialized = state.to_dict()
    deserialized = PipelineState.from_dict(serialized)
    assert deserialized.requirements == {"test": "data"}

# tests/test_pipeline_config.py
def test_pipeline_config_validation():
    config = PipelineConfig()
    assert config.should_skip("code_review") == False
    assert config.is_critical("requirements") == True

# tests/test_fallback.py
def test_rule_based_fallback():
    fallback = RuleBasedFallback()
    result = fallback.requirements_fallback("开发一个博客系统")
    assert result["status"] == "fallback"
    assert len(result["functional_requirements"]) > 0
```

### 16.2 集成测试

```python
# tests/test_pipeline_integration.py
async def test_full_pipeline():
    config = PipelineConfig()
    agents = create_mock_agents()
    orchestrator = PipelineOrchestrator(config, agents)
    result = await orchestrator.run("开发一个测试应用")
    assert result.status in ["success", "partial"]
    assert len(result.results) == 6
```

### 16.3 故障测试

```python
# tests/test_pipeline_failure.py
async def test_api_failure_retry():
    # 模拟API失败
    pass

async def test_cascade_failure():
    # 模拟多阶段失败
    pass
```

---

## 十七、部署和运行

### 17.1 环境要求

```bash
# Python 3.9+
pip install -r requirements.txt
```

### 17.2 运行方式

```bash
# 完整流水线
python main.py --pipeline --input "开发一个博客系统"

# 交互模式
python main.py --interactive --pipeline

# 单阶段运行
python main.py --stage requirements --input "开发一个博客系统"

# 从检查点恢复
python main.py --resume ./pipeline_state.json
```

### 17.3 配置文件

```json
{
  "model": "gpt-4",
  "cost_limit": 1.0,
  "skip_stages": [],
  "persistence_path": "./pipeline_state.json",
  "stage_configs": {
    "requirements": {"model": "gpt-4", "temperature": 0.3},
    "technical": {"model": "gpt-4", "temperature": 0.2},
    "mvp": {"model": "gpt-4", "temperature": 0.4}
  }
}
```
