# 多智能体系统重构方案 V2

## 一、V1 遇到的所有问题

### 1.1 问题清单

| # | 问题 | 根因 | 影响范围 | 严重程度 |
|---|------|------|---------|---------|
| 1 | 32个工具文件UTF-8编码损坏 | PowerShell批量替换未指定编码 | 全部工具 | 阻塞 |
| 2 | langchain API不兼容 | 直接依赖langchain具体API，版本升级后全部崩溃 | 全部Agent | 阻塞 |
| 3 | pydantic-settings解析失败 | List类型字段在新版本中行为变化 | 配置模块 | 阻塞 |
| 4 | LLM输出格式不稳定 | Prompt未约束JSON结构，LLM返回字符串而非对象 | 全部工具 | 阻塞 |
| 5 | agent.ainvoke返回格式不符预期 | langgraph返回AIMessage而非Dict | RequirementsAgent | 阻塞 |
| 6 | ChatPromptTemplate缺少import | 重写文件时遗漏 | 4个Agent | 阻塞 |
| 7 | fallback函数参数不匹配 | `*args`传参与函数签名不一致 | 流水线编排 | 阻塞 |
| 8 | cascade_handler误报 | `should_abort()`检查了`failed_stages`但`record_success()`只重置`consecutive_failures` | 流水线编排 | 阻塞 |
| 9 | skipped阶段未重置连续失败计数 | 跳过阶段时未调用`record_success()` | 流水线编排 | 阻塞 |
| 10 | MVP Agent返回无code_files | 工具调用失败后返回error而非code_files | 流水线依赖 | 阻塞 |

### 1.2 问题根因归类

| 根因类别 | 问题编号 | 本质原因 |
|---------|---------|---------|
| **外部依赖耦合** | 1,2,3 | 没有抽象层，直接依赖具体库版本 |
| **接口契约缺失** | 4,5,7 | Agent间数据传递靠"约定"而非"约束" |
| **代码质量** | 6 | 批量操作没有逐个验证 |
| **状态管理不一致** | 8,9 | 状态逻辑分散，行为不统一 |
| **集成测试缺失** | 10 | 没有端到端验证就推进下一步 |

---

## 二、V2 设计原则

### 2.1 核心原则

```
P1: 接口先行 — 先定义抽象基类和接口契约，再实现
P2: Schema强制 — 所有数据传递用Pydantic校验
P3: 依赖隔离 — LLM/外部库通过适配器接入，不直接依赖
P4: 组件独立 — 每个Agent可独立测试、独立替换
P5: 每步验证 — 写完一个组件就测试，不累积技术债
```

### 2.2 反模式清单（V1犯过的错，V2禁止）

| 反模式 | 说明 | V2做法 |
|--------|------|--------|
| 批量生成代码 | 一次生成35个文件不验证 | 每个文件写完立即验证 |
| 靠LLM"自觉"输出格式 | Prompt说"输出JSON"但不约束结构 | Pydantic Schema + structured_output |
| `*args`传参 | 用`*args`统一传参但函数签名不一致 | 每个函数显式参数 |
| 状态只增不减 | `failed_stages`只append不清除 | 状态管理逻辑统一 |
| 直接依赖具体库 | `from langchain.xxx import yyy` | 适配器模式隔离 |
| 写完再测 | 全部写完才跑 | 写一个测一个 |

---

## 三、V2 架构设计

### 3.1 分层架构

```
┌─────────────────────────────────────────────────┐
│                   入口层 (main.py)                │
├─────────────────────────────────────────────────┤
│               编排层 (Orchestrator)               │
│  PipelineOrchestrator → StageExecutor → Fallback │
├─────────────────────────────────────────────────┤
│               Agent层 (6个Agent)                 │
│  RequirementsAgent / TechnicalAgent / MVP / ...  │
├─────────────────────────────────────────────────┤
│               工具层 (Tools)                      │
│  RequirementParser / CodeGenerator / ...         │
├─────────────────────────────────────────────────┤
│               LLM抽象层 (Adapter)                │
│  LLMAdapter → LangChainAdapter / OpenAIAdapter   │
├─────────────────────────────────────────────────┤
│               Schema层 (Pydantic Models)         │
│  所有输入输出的类型定义                            │
└─────────────────────────────────────────────────┘
```

### 3.2 模块结构

```
multi_agent_system_v2/
├── schemas/                    # Schema层：所有数据类型定义
│   ├── __init__.py
│   ├── requirements.py         # 需求相关Schema
│   ├── technical.py            # 技术方案Schema
│   ├── code.py                 # 代码相关Schema
│   ├── testing.py              # 测试相关Schema
│   ├── deployment.py           # 部署相关Schema
│   └── pipeline.py             # 流水线Schema
├── llm/                        # LLM抽象层
│   ├── __init__.py
│   ├── adapter.py              # LLMAdapter抽象基类
│   ├── openai_adapter.py       # OpenAI适配器
│   └── config.py               # LLM配置
├── agents/                     # Agent层
│   ├── __init__.py
│   ├── base.py                 # BaseAgent抽象基类
│   ├── requirements.py         # 需求分析Agent
│   ├── technical.py            # 技术架构Agent
│   ├── mvp.py                  # MVP实现Agent
│   ├── code_review.py          # 代码审查Agent
│   ├── testing.py              # 测试Agent
│   └── deployment.py           # 部署Agent
├── tools/                      # 工具层
│   ├── __init__.py
│   ├── base.py                 # BaseTool抽象基类
│   ├── requirements_tools.py   # 需求工具集
│   ├── technical_tools.py      # 技术工具集
│   ├── mvp_tools.py            # MVP工具集
│   ├── code_review_tools.py    # 代码审查工具集
│   ├── testing_tools.py        # 测试工具集
│   └── deployment_tools.py     # 部署工具集
├── pipeline/                   # 编排层
│   ├── __init__.py
│   ├── orchestrator.py         # 流水线编排器
│   ├── stage.py                # 阶段定义
│   ├── state.py                # 流水线状态
│   └── fallback.py             # 故障处理
├── config/                     # 配置
│   ├── __init__.py
│   └── settings.py
├── tests/                      # 测试
│   ├── test_schemas.py
│   ├── test_llm_adapter.py
│   ├── test_agents.py
│   ├── test_tools.py
│   └── test_pipeline.py
├── main.py
├── requirements.txt
└── .env.example
```

---

## 四、核心组件设计

### 4.1 Schema层（解决 #4 输出格式不稳定）

**所有Agent间传递的数据都用Pydantic定义，不靠LLM自觉。**

```python
# schemas/requirements.py
from pydantic import BaseModel, Field
from typing import List

class RequirementItem(BaseModel):
    """单个需求项"""
    id: str = Field(description="需求ID，如FR-001")
    title: str = Field(description="需求标题")
    description: str = Field(description="需求描述")

class RequirementsOutput(BaseModel):
    """需求分析输出Schema"""
    functional_requirements: List[RequirementItem] = Field(
        default_factory=list, description="功能需求列表"
    )
    non_functional_requirements: List[RequirementItem] = Field(
        default_factory=list, description="非功能需求列表"
    )
    constraints: List[str] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
```

**关键点**：
- 每个字段类型明确，不接受"字符串或字典"模糊类型
- `Field(description=...)` 同时用于文档和structured_output
- 所有Schema集中管理在`schemas/`目录

### 4.2 LLM抽象层（解决 #2 依赖耦合）

```python
# llm/adapter.py
from abc import ABC, abstractmethod
from typing import Type, TypeVar
from pydantic import BaseModel

T = TypeVar('T', bound=BaseModel)

class LLMAdapter(ABC):
    """LLM适配器抽象基类"""
    
    @abstractmethod
    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        """生成文本响应"""
        pass
    
    @abstractmethod
    async def generate_structured(
        self, 
        system_prompt: str, 
        user_prompt: str, 
        output_schema: Type[T]
    ) -> T:
        """生成结构化响应（强制Schema）"""
        pass

# llm/openai_adapter.py
class OpenAIAdapter(LLMAdapter):
    """OpenAI兼容API适配器"""
    
    def __init__(self, api_key: str, base_url: str, model: str):
        from openai import AsyncOpenAI
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.model = model
    
    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        return response.choices[0].message.content
    
    async def generate_structured(
        self, system_prompt: str, user_prompt: str, output_schema: Type[T]
    ) -> T:
        # 使用OpenAI的response_format约束输出
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": output_schema.__name__,
                    "schema": output_schema.model_json_schema()
                }
            }
        )
        return output_schema.model_validate_json(response.choices[0].message.content)
```

**关键点**：
- Agent不直接依赖langchain或openai，只依赖`LLMAdapter`接口
- 换LLM provider只需实现新的Adapter
- `generate_structured()` 强制Schema输出，不靠Prompt约束

### 4.3 BaseAgent抽象基类（解决 #5 返回格式不一致）

```python
# agents/base.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pydantic import BaseModel
from llm.adapter import LLMAdapter

class AgentResult(BaseModel):
    """Agent统一返回格式"""
    status: str  # success / error / fallback
    data: Dict[str, Any] = {}
    error: Optional[str] = None
    agent_used: str = "primary"
    duration_seconds: float = 0.0

class BaseAgent(ABC):
    """Agent抽象基类"""
    
    def __init__(self, llm: LLMAdapter):
        self.llm = llm
    
    @abstractmethod
    async def execute(self, **kwargs) -> AgentResult:
        """执行Agent任务，返回统一格式"""
        pass
    
    def _success(self, data: Dict[str, Any], duration: float = 0) -> AgentResult:
        return AgentResult(status="success", data=data, duration_seconds=duration)
    
    def _error(self, error: str, duration: float = 0) -> AgentResult:
        return AgentResult(status="error", error=error, duration_seconds=duration)
    
    def _fallback(self, data: Dict[str, Any], duration: float = 0) -> AgentResult:
        return AgentResult(status="fallback", data=data, agent_used="fallback", duration_seconds=duration)
```

**关键点**：
- 所有Agent返回`AgentResult`，格式统一
- Orchestrator只依赖`AgentResult`，不关心内部实现
- `_success()/_error()/_fallback()` 辅助方法避免格式不一致

### 4.4 BaseTool抽象基类（解决 #7 参数不匹配）

```python
# tools/base.py
from abc import ABC, abstractmethod
from typing import Dict, Any
from pydantic import BaseModel
from llm.adapter import LLMAdapter

class BaseTool(ABC):
    """工具抽象基类"""
    
    def __init__(self, llm: LLMAdapter):
        self.llm = llm
    
    @abstractmethod
    async def run(self, **kwargs) -> Dict[str, Any]:
        """执行工具，返回字典"""
        pass
```

**关键点**：
- 所有工具用`**kwargs`接收参数，不存在签名不匹配问题
- 返回统一为`Dict[str, Any]`

### 4.5 Fallback设计（解决 #7 #8 #9）

```python
# pipeline/fallback.py
from typing import Dict, Any, Callable, Awaitable, List

class FallbackManager:
    """故障处理管理器"""
    
    def __init__(self, max_consecutive_failures: int = 2):
        self.max_consecutive_failures = max_consecutive_failures
        self.consecutive_failures = 0
    
    async def execute(
        self,
        stage_name: str,
        primary_func: Callable[..., Awaitable[Dict[str, Any]]],
        fallback_func: Callable[..., Dict[str, Any]],
        **kwargs  # 统一用**kwargs
    ) -> Dict[str, Any]:
        """带降级的执行"""
        # 1. 尝试主函数
        try:
            result = await primary_func(**kwargs)
            self._record_success()
            return result
        except Exception:
            pass
        
        # 2. 尝试降级函数
        try:
            result = fallback_func(**kwargs)  # 同样的kwargs
            self._record_success()
            result["agent_used"] = "fallback"
            return result
        except Exception:
            pass
        
        # 3. 全部失败
        self._record_failure()
        return {"status": "error", "error": f"阶段 {stage_name} 全部失败"}
    
    def _record_success(self):
        self.consecutive_failures = 0
    
    def _record_failure(self):
        self.consecutive_failures += 1
    
    def should_abort(self) -> bool:
        return self.consecutive_failures >= self.max_consecutive_failures
```

**关键点**：
- `primary_func`和`fallback_func`都用`**kwargs`接收参数，签名一致
- `should_abort()`只检查`consecutive_failures`，不检查`failed_stages`
- 没有"记录失败阶段"的逻辑干扰决策

### 4.6 Orchestrator设计

```python
# pipeline/orchestrator.py
class PipelineOrchestrator:
    """流水线编排器"""
    
    def __init__(self, agents: Dict[str, BaseAgent], config: PipelineConfig):
        self.agents = agents
        self.config = config
        self.state = PipelineState()
        self.fallback = FallbackManager(config.max_consecutive_failures)
    
    async def run(self, user_input: str) -> PipelineResult:
        stages = [
            ("requirements", self._run_requirements),
            ("technical", self._run_technical),
            ("mvp", self._run_mvp),
            ("code_review", self._run_code_review),
            ("testing", self._run_testing),
            ("deployment", self._run_deployment),
        ]
        
        results = {}
        for stage_name, stage_func in stages:
            if self.config.should_skip(stage_name):
                results[stage_name] = {"status": "skipped"}
                continue
            
            if self.fallback.should_abort():
                return PipelineResult(status="aborted", results=results)
            
            result = await stage_func()
            results[stage_name] = result
            
            if result.get("status") == "error":
                # 检查依赖是否满足
                if not self._can_continue(stage_name, results):
                    break
        
        return PipelineResult(status="success", results=results)
```

---

## 五、V1→V2 迁移策略

### 5.1 迁移原则

```
1. 不修改V1代码 — V1保持可用，V2独立开发
2. 逐Agent迁移 — 每迁移一个Agent就测试验证
3. 复用Prompt — V1的Prompt模板直接复用
4. 复用配置 — .env配置格式不变
```

### 5.2 迁移顺序

```
Phase 1: 基础层
  - schemas/ (所有Pydantic模型)
  - llm/adapter.py + llm/openai_adapter.py
  - agents/base.py + tools/base.py
  → 验证：写一个mock测试确认接口可用

Phase 2: 单Agent验证
  - agents/requirements.py
  - tools/requirements_tools.py
  → 验证：跑通需求分析，确认输出格式正确

Phase 3: 流水线
  - pipeline/orchestrator.py
  - pipeline/fallback.py
  - pipeline/state.py
  → 验证：跑通单Agent流水线

Phase 4: 剩余Agent
  - 逐个迁移technical/mvp/code_review/testing/deployment
  → 验证：每个Agent独立测试通过

Phase 5: 集成
  - main.py
  - 完整流水线测试
  → 验证：6个Agent串联运行
```

### 5.3 验证清单

| Phase | 验证项 | 通过标准 |
|-------|--------|---------|
| 1 | Schema序列化/反序列化 | 所有Schema可正确转换 |
| 1 | LLMAdapter调用 | 能调通MiMo API |
| 2 | 需求分析Agent | 返回AgentResult，data包含正确Schema |
| 3 | 单Agent流水线 | 需求分析阶段完整跑通 |
| 4 | 6个Agent独立测试 | 每个Agent单独调用成功 |
| 5 | 完整流水线 | 6个Agent串联运行，输出完整结果 |

---

## 六、关键改进对比

| 维度 | V1 | V2 |
|------|----|----|
| **LLM依赖** | 直接依赖langchain | LLMAdapter抽象层 |
| **数据格式** | 靠LLM自觉 | Pydantic Schema强制 |
| **Agent接口** | 各自不同 | 统一BaseAgent + AgentResult |
| **工具接口** | 各自参数签名 | 统一**kwargs |
| **Fallback逻辑** | 状态管理混乱 | 简化为consecutive_failures |
| **测试方式** | 只能端到端 | 每层可独立测试 |
| **错误处理** | 捕获后继续 | 统一AgentResult.status |

---

## 七、文件清单

### Phase 1: 基础层（5个文件）
- `schemas/__init__.py`
- `schemas/requirements.py`
- `llm/__init__.py`
- `llm/adapter.py`
- `llm/openai_adapter.py`

### Phase 2: Agent基础（3个文件）
- `agents/__init__.py`
- `agents/base.py`
- `tools/__init__.py`
- `tools/base.py`

### Phase 3: 首个Agent（2个文件）
- `agents/requirements.py`
- `tools/requirements_tools.py`

### Phase 4: 流水线（4个文件）
- `pipeline/__init__.py`
- `pipeline/orchestrator.py`
- `pipeline/state.py`
- `pipeline/fallback.py`

### Phase 5: 剩余Agent（10个文件）
- `agents/technical.py` + `tools/technical_tools.py`
- `agents/mvp.py` + `tools/mvp_tools.py`
- `agents/code_review.py` + `tools/code_review_tools.py`
- `agents/testing.py` + `tools/testing_tools.py`
- `agents/deployment.py` + `tools/deployment_tools.py`

### Phase 6: 入口和配置（3个文件）
- `config/settings.py`
- `main.py`
- `requirements.txt`

**总计：~25个文件**（V1是~45个文件，减少44%）
