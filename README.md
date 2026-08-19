# 多智能体应用开发系统

从自然语言需求**自动生成可运行的 FastAPI 应用**：你说需求，系统产出代码、测试、契约校验报告和部署配置。

- **LLM**：小米 MiMo（`mimo-v2.5`，OpenAI 兼容）
- **输出**：`output/<project_name>/`，含代码 + 测试 + `spec.json` + `summary.json` + Docker 配置

## 两种运行模式

| 模式 | 命令 | LLM 边界 | 验证方式 | 状态 |
|------|------|---------|---------|------|
| **spec-driven（主推）** | `--spec` | 2 处 | 全部确定性推导 + 硬契约校验 | ✅ 新架构 |
| 6-Agent 流水线（旧） | `--pipeline` | 6 处 | 软信号 + 硬门槛混合 | 保留，非主推 |

## spec-driven 架构

这是 V2 的重构方向，核心思想一句话：**Spec 是代码，不是散文；LLM 只当写码工，不当裁判。**

```
自然语言需求
     │  LLM #1（SpecAgent，全系统唯一一次"理解需求"）
     ▼
┌──────────────┐
│  ProjectSpec  │  ← 机器可校验的唯一真相源（端点 + 规则）
└──────────────┘
     │  人工审阅节点（通过 / 放弃 / 给修改意见回灌重生成）
     ├───────────────┬───────────────┐
     ▼               ▼               ▼
 确定性推导验收   契约校验          不变式测试
 (spec_derive)   (contract_check)  (invariant_tests)
     └───────────────┼───────────────┘
                     ▼
             LLM #2（BuilderAgent，只写代码，实现 Spec）
                     ▼
            确定性验证（真实运行 pytest + 覆盖率 + OpenAPI 比对）
                     ▼
            硬门槛：测试全过 + 覆盖率 ≥ 80% + 契约完全匹配
                     ▼
                DeploymentAgent（部署配置）
```

**为什么这样改**：旧架构有 6 个 LLM 源（需求/技术/代码/作者测试/审查/验收）靠"软链接"互相对齐，LLM 之间的翻译会漂移、放水，同一类问题反复出现。spec-driven 把验证从 LLM 手里收回，全部交给确定性代码从 Spec/OpenAPI 机械推导——同一份 Spec 永远生成同一份测试，不漂移、不放水。

- **人工审阅是唯一该拍板的点**：Spec 生成后渲染成可读清单，你只需判断"端点全了吗、规则对了吗、有没有臆造我没要的功能"。
- **契约校验是硬门槛**：`contract_check` 真实 import 生成的 app，比对 Spec 端点 vs `app.openapi()` 路径，builder 漏实现/多实现端点都会被拦下。

## 快速开始

### 环境

- Python 3.11+
- OpenAI 兼容 API（小米 MiMo）

### 配置

在 `multi_agent_system/.env`（已 gitignore）中填：

```bash
LOCAL_LLM_API_KEY=your-api-key
LOCAL_LLM_BASE_URL=https://api.xiaomimimo.com/v1
LOCAL_LLM_MODEL=mimo-v2.5
```

### 运行

```bash
cd multi_agent_system_v2

# spec-driven（主推）：生成 Spec → 人工审阅 → 确定性验证
python main.py --spec --input "开发一个待办事项应用：能新增待办（标题）、列出全部待办、按 id 删除待办；标题为空应返回 422"

# 旧 6-Agent 流水线
python main.py --pipeline --input "开发一个博客系统"

# 只看需求分析
python main.py --input "开发一个计算器"
```

`--spec` 运行时会先打印可读的 Spec 清单，等你确认：

```
【API 端点】(3)
  1. POST /todos  →  201
     示例请求: {"title": "买牛奶"}
  2. GET /todos  →  200
  3. DELETE /todos/{id}  →  204

【校验规则】(2)
  1. POST /todos  期望 422   标题为空
  2. POST /todos  期望 422   标题字段缺失
```

输入 `y` 继续、`n` 放弃、或直接输入修改意见（如"加一个 PUT /todos/{id} 端点"）重新生成。

## 仓库结构

```
agent/
├── multi_agent_system_v2/   # V2：Pydantic Schema + LLM Adapter（当前主攻，含 spec-driven）
├── multi_agent_system/      # V1：LangChain 版（已完成，停止演进）
├── MULTI_AGENT_PROJECT_REPORT.md
└── 多智能体应用开发系统_项目报告.md
```

V2 的 spec-driven 关键模块：

| 模块 | 作用 |
|------|------|
| `schemas/spec.py` | `ProjectSpec` / `EndpointSpec` / `RuleSpec` 契约定义 |
| `agents/spec_agent.py` | LLM #1：自然语言 → ProjectSpec |
| `agents/builder.py` | LLM #2：spec 模式，只写代码实现契约 |
| `tools/spec_derive.py` | 确定性推导：验收测试 + 契约校验 |
| `tools/invariant_tests.py` | 从 OpenAPI 推导不变式测试（非 LLM） |
| `tools/spec_render.py` | Spec 可读化渲染（人工审阅用） |
| `pipeline/spec_pipeline.py` | spec-driven 编排器 |

更多细节见 [`multi_agent_system_v2/README.md`](multi_agent_system_v2/README.md) 与 [`multi_agent_system/README.md`](multi_agent_system/README.md)。

## 测试

确定性核心（零 LLM、零联网）可离线验证：

```bash
cd multi_agent_system_v2
python -m pytest tests/test_spec_derive.py tests/test_invariant_tests.py tests/test_spec_review.py -q
```

## 许可证

MIT
