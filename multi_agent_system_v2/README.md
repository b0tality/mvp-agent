# 多智能体应用开发系统 V2

基于Pydantic Schema + LLM Adapter架构的6-Agent协作开发流水线。

## 系统架构

### 分层架构

```
┌─────────────────────────────────────────────┐
│                 入口层 (main.py)              │
├─────────────────────────────────────────────┤
│             编排层 (pipeline/)                │
│  PipelineOrchestrator → FallbackManager      │
├─────────────────────────────────────────────┤
│             Agent层 (agents/)                │
│  Requirements → Technical → MVP →            │
│  CodeReview ∥ Testing → Deployment           │
├─────────────────────────────────────────────┤
│             工具层 (tools/)                   │
│  各Agent对应的工具集                           │
├─────────────────────────────────────────────┤
│             LLM抽象层 (llm/)                 │
│  LLMAdapter → OpenAIAdapter                  │
├─────────────────────────────────────────────┤
│             Schema层 (schemas/)              │
│  所有数据类型的Pydantic定义                    │
└─────────────────────────────────────────────┘
```

### 数据流

```
用户输入
    │
    ▼
[1] RequirementsAgent → RequirementsOutput (功能需求/用户故事/验收标准)
    │
    ▼
[2] TechnicalAgent → TechnicalOutput (架构/技术栈/API/数据库)
    │
    ▼
[3] MVPAgent → MVPCodeOutput (代码文件/测试文件)
    │
    ├──────────────────┐
    ▼                  ▼
[4] CodeReviewAgent   [5] TestingAgent    ← 并行执行
    │                  │
    └────────┬─────────┘
             ▼
[6] DeploymentAgent → DeploymentOutput (部署方案/Docker/K8s)
```

### 模块结构

```
multi_agent_system_v2/
├── schemas/                # Schema层：所有数据类型定义
│   ├── requirements.py     # 需求相关Schema
│   ├── technical.py        # 技术方案Schema
│   ├── code.py             # 代码相关Schema
│   ├── testing.py          # 测试相关Schema
│   ├── deployment.py       # 部署相关Schema
│   └── pipeline.py         # 流水线Schema
├── llm/                    # LLM抽象层
│   ├── adapter.py          # LLMAdapter抽象基类
│   └── openai_adapter.py   # OpenAI兼容适配器
├── agents/                 # Agent层
│   ├── base.py             # BaseAgent抽象基类
│   ├── requirements.py     # 需求分析Agent
│   ├── technical.py        # 技术架构Agent
│   ├── mvp.py              # MVP实现Agent
│   ├── code_review.py      # 代码审查Agent
│   ├── testing.py          # 测试Agent
│   └── deployment.py       # 部署Agent
├── tools/                  # 工具层
│   ├── base.py             # BaseTool抽象基类
│   ├── requirements_tools.py
│   ├── technical_tools.py
│   ├── mvp_tools.py
│   ├── code_review_tools.py
│   ├── testing_tools.py
│   └── deployment_tools.py
├── pipeline/               # 编排层
│   ├── orchestrator.py     # 流水线编排器（支持并行）
│   ├── state.py            # 流水线状态管理
│   └── fallback.py         # 故障处理
├── config/
│   └── settings.py         # 配置管理
├── tests/                  # 测试
├── document/               # 文档和错误日志
└── main.py                 # 入口
```

---

## 快速开始

### 环境要求

- Python 3.11+
- OpenAI兼容API（如小米MiMo）

### 安装

```bash
# 创建conda环境
conda create -n multi-agent python=3.11
conda activate multi-agent

# 安装依赖
pip install openai pydantic python-dotenv
```

### 配置

创建 `.env` 文件：

```bash
LOCAL_LLM_API_KEY=your-api-key
LOCAL_LLM_BASE_URL=https://api.xiaomimimo.com/v1
LOCAL_LLM_MODEL=mimo-v2.5
```

### 运行

```bash
# 运行完整流水线
python main.py --pipeline --input "开发一个博客系统"

# 只运行需求分析
python main.py --input "开发一个计算器"
```

---

## 使用示例

### 完整流水线

```bash
python main.py --pipeline --input "开发一个在线商城系统，支持用户注册、商品浏览、购物车、在线支付"
```

输出：

```
============================================================
运行完整流水线...
============================================================
  [requirements] 开始执行...
  [requirements] 完成: success (72.3s)
  [technical] 开始执行...
  [technical] 完成: success (10.0s)
  [mvp] 开始执行...
  [mvp] 完成: success (1.8s)
  [code_review, testing] 并行执行...
  [code_review] 完成: success (4.7s)
  [testing] 完成: success (4.3s)
  [deployment] 开始执行...
  [deployment] 完成: success (23.4s)

状态: success
总耗时: 112.2s
```

### 单独使用Agent

```python
import asyncio
from llm import OpenAIAdapter
from agents.requirements import RequirementsAgent

async def main():
    llm = OpenAIAdapter(
        api_key="your-key",
        base_url="https://api.xiaomimimo.com/v1",
        model="mimo-v2.5"
    )
    
    agent = RequirementsAgent(llm)
    result = await agent.execute(user_input="开发一个博客系统")
    
    print(f"状态: {result.status}")
    print(f"功能需求: {len(result.data.get('functional_requirements', []))} 条")

asyncio.run(main())
```

---

## V2 改进点

### 1. Schema强制输出（解决JSON格式不稳定）

**V1问题**：靠Prompt约束输出格式，LLM有时返回字符串列表而非对象列表

**V2方案**：Pydantic Schema + API层强制

```python
# schemas/requirements.py
class RequirementItem(BaseModel):
    id: str
    title: str
    description: str

class RequirementsOutput(BaseModel):
    functional_requirements: List[RequirementItem]
    non_functional_requirements: List[RequirementItem]
```

```python
# 使用structured_output强制格式
result = await llm.generate_structured(
    system_prompt, user_prompt, RequirementsOutput
)
# result 一定是 RequirementsOutput 类型
```

### 2. LLM抽象层（解决依赖耦合）

**V1问题**：直接依赖langchain，版本升级全崩

**V2方案**：LLMAdapter接口，换provider只改适配器

```python
# llm/adapter.py
class LLMAdapter(ABC):
    @abstractmethod
    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        pass
    
    @abstractmethod
    async def generate_structured(self, system_prompt: str, user_prompt: str, output_schema: Type[T]) -> T:
        pass
```

```python
# llm/openai_adapter.py
class OpenAIAdapter(LLMAdapter):
    def __init__(self, api_key: str, base_url: str, model: str):
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.model = model
```

### 3. 统一Agent接口（解决返回格式不一致）

**V1问题**：各Agent返回格式不同，Orchestrator需要特殊处理

**V2方案**：BaseAgent + AgentResult

```python
# agents/base.py
class AgentResult(BaseModel):
    status: str          # success/error/fallback
    data: Dict[str, Any]
    error: Optional[str]
    agent_used: str      # primary/fallback
    duration_seconds: float

class BaseAgent(ABC):
    @abstractmethod
    async def execute(self, **kwargs) -> AgentResult:
        pass
```

### 4. 并行执行（解决性能问题）

**V1问题**：所有阶段串行执行

**V2方案**：无依赖的阶段并行执行

```python
# pipeline/orchestrator.py
PARALLEL_GROUPS = [
    ["requirements"],
    ["technical"],
    ["mvp"],
    ["code_review", "testing"],  # 并行
    ["deployment"],
]

# 组内并行
if len(executable) > 1:
    tasks = [self._execute_stage(name) for name in executable]
    results = await asyncio.gather(*tasks)
```

### 5. 统一kwargs（解决参数不匹配）

**V1问题**：`*args`传参与函数签名不匹配

**V2方案**：所有函数统一用`**kwargs`

```python
# tools/base.py
class BaseTool(ABC):
    @abstractmethod
    async def run(self, **kwargs) -> Dict[str, Any]:
        pass

# agents/base.py
class BaseAgent(ABC):
    @abstractmethod
    async def execute(self, **kwargs) -> AgentResult:
        pass
```

### 6. 简化Fallback（解决状态管理混乱）

**V1问题**：`should_abort()`检查`failed_stages`导致误报

**V2方案**：只检查`consecutive_failures`

```python
# pipeline/fallback.py
class FallbackManager:
    def should_abort(self) -> bool:
        return self.consecutive_failures >= self.max_consecutive_failures
```

---

## V1 vs V2 对比

| 维度 | V1 | V2 |
|------|----|----|
| **文件数** | ~45 | ~33 |
| **运行时间** | >15分钟（超时） | ~2分钟 |
| **JSON格式** | 靠LLM自觉 | Pydantic强制 |
| **LLM依赖** | 直接依赖langchain | LLMAdapter抽象 |
| **Agent接口** | 各自不同 | 统一BaseAgent |
| **工具参数** | 各自签名 | 统一**kwargs |
| **并行支持** | 无 | code_review+testing并行 |
| **测试方式** | 只能端到端 | 每层可独立测试 |
| **错误处理** | 级联失败 | 统一fallback |

---

## 性能数据

| 阶段 | 耗时 | 说明 |
|------|------|------|
| requirements | ~72s | 1次LLM调用 |
| technical | ~10s | 1次LLM调用 |
| mvp | ~2s | 1次LLM调用 |
| code_review | ~5s | 1次LLM调用（并行） |
| testing | ~4s | 1次LLM调用（并行） |
| deployment | ~23s | 1次LLM调用 |
| **总计** | **~112s** | **约1.9分钟** |

---

## 扩展指南

### 添加新Agent

1. 在 `schemas/` 定义输出Schema
2. 在 `tools/` 实现工具（继承BaseTool）
3. 在 `agents/` 实现Agent（继承BaseAgent）
4. 在 `pipeline/orchestrator.py` 注册阶段和依赖

### 换LLM Provider

1. 在 `llm/` 实现新的Adapter（继承LLMAdapter）
2. 在 `config/settings.py` 添加配置
3. 在 `main.py` 使用新Adapter

---

## 错误日志

开发过程中遇到的所有问题记录在 `document/v1-issues-log.md` 和 `document/v2-error-log.md`。

---

## 许可证

MIT
