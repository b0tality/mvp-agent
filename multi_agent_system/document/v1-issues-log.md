# V1 问题日志 - 完整记录

生成时间: 2026-08-18

---

## 问题清单

### P01: 工具文件UTF-8编码损坏 (32个文件)

**现象**: Python报 `UnicodeDecodeError: 'utf-8' codec can't decode bytes`

**根因**: 使用PowerShell的 `Get-Content` + `Set-Content` 批量替换 `from langchain.prompts import` 时，未指定 `-Encoding UTF8`。Windows PowerShell默认使用GBK编码，导致中文字符损坏。

**触发场景**: 批量更新langchain导入语句时

**影响范围**: 32个工具文件（requirements/tools, technical/tools, mvp/tools, code_review/tools, testing/tools, deployment/tools）

**修复方式**: 用Python脚本重新生成所有文件

**教训**: 
- Windows环境下批量文件操作必须显式指定UTF-8编码
- 批量操作后必须逐个验证文件完整性

---

### P02: langchain API不兼容

**现象**: `ImportError: cannot import name 'AgentExecutor' from 'langchain.agents'`

**根因**: langchain v1.3+ 移除了 `AgentExecutor`、`create_openai_tools_agent` 等旧API，迁移到 `create_agent` 新API。原代码直接依赖这些具体API。

**触发场景**: 创建新的conda环境安装最新langchain后运行

**影响范围**: 全部6个Agent的 `_create_agent()` 方法

**修复方式**: 改用 `create_agent()` 新API

**教训**:
- 不应该直接依赖框架的具体API，应该有抽象层
- 升级依赖版本前应该先检查breaking changes

---

### P03: pydantic-settings解析失败

**现象**: `pydantic_settings.exceptions.SettingsError: error parsing value for field "cors_origins"`

**根因**: pydantic-settings v2.15 对 `List[str]` 类型字段的处理方式变化。旧版本可以自动解析逗号分隔的字符串，新版本要求JSON格式或使用validator。

**触发场景**: 运行main.py加载.env配置时

**影响范围**: SecuritySettings中的 `cors_origins`、`cors_methods`、`allowed_file_extensions` 字段

**修复方式**: 将字段类型改为 `str`，添加 `@property` 方法返回列表

**教训**:
- 依赖库的小版本升级也可能有breaking changes
- 配置字段类型应该尽量简单，复杂类型用property转换

---

### P04: LLM输出格式不稳定

**现象**: `'str' object does not support item assignment`

**根因**: Prompt只说"功能需求列表"，没有指定列表元素的结构。LLM有时返回 `[{"id": "FR-1", "title": "..."}]`（对象列表），有时返回 `["需求1", "需求2"]`（字符串列表）。代码假设返回对象列表，对字符串列表执行 `req["id"]` 就报错。

**触发场景**: 调用 `RequirementParserTool._add_ids()` 时

**影响范围**: 所有使用LLM输出的工具

**修复方式**: 使用 Pydantic Schema + `with_structured_output()` 强制输出格式

**教训**:
- 不能靠LLM"自觉"输出特定格式，必须用Schema强制
- Prompt应该明确指定每个字段的类型和结构

---

### P05: agent.ainvoke返回格式不符预期

**现象**: `'AIMessage' object has no attribute 'get'`

**根因**: langgraph的 `create_agent` 返回的 `CompiledStateGraph` 的 `ainvoke()` 方法返回的是状态对象（包含messages列表），不是简单的字典。代码用 `result.get("messages")` 访问，但result本身是AIMessage对象。

**触发场景**: RequirementsAgent的 `analyze_requirements` 方法调用 `self.agent.ainvoke()` 时

**影响范围**: RequirementsAgent

**修复方式**: 改为直接调用工具方法，不通过agent.ainvoke()

**教训**:
- 新API的返回格式需要先测试确认
- 不应该假设返回格式与旧API一致

---

### P06: ChatPromptTemplate缺少import

**现象**: `name 'ChatPromptTemplate' is not defined`

**根因**: 重写Agent文件使用新API时，移除了旧的 `from langchain.prompts import ChatPromptTemplate` 导入，但代码中仍然使用 `ChatPromptTemplate.from_messages()`。

**触发场景**: 调用Agent的内部方法（如 `_generate_data_models`）时

**影响范围**: requirements/agent.py, technical/agent.py, code_review/agent.py, deployment/agent.py

**修复方式**: 添加 `from langchain_core.prompts import ChatPromptTemplate`

**教训**:
- 批量重写文件后必须逐个验证语法
- 使用IDE或linter检查未定义的名称

---

### P07: fallback函数参数不匹配

**现象**: `TypeError: code_review_fallback() takes 2 positional arguments but 3 were given`

**根因**: `execute_with_fallback` 用 `*args` 统一传递参数给所有函数。`_run_code_review` 传 `(code_files, project_info)`，但 `code_review_fallback(self, code_files)` 只接受1个参数。参数数量不匹配导致TypeError，被catch后触发 `record_failure()`。

**触发场景**: code_review阶段调用rule-based fallback时

**影响范围**: code_review, testing, deployment阶段

**修复方式**: 所有fallback函数加 `**kwargs` 接受多余参数

**教训**:
- 用 `*args` 传参时必须确保所有函数签名一致
- 或者用 `**kwargs` 让函数忽略多余参数

---

### P08: CascadeFailureHandler误报

**现象**: 流水线在code_review和testing被跳过后仍然abort

**根因**: `should_abort()` 检查两个条件：
1. `consecutive_failures >= max_consecutive_failures`
2. `any(stage in failed_stages for stage in critical_stages)`

但 `record_success()` 只重置 `consecutive_failures`，不清除 `failed_stages`。一旦某个阶段被加入 `failed_stages`，`should_abort()` 就永远返回True。

**触发场景**: code_review阶段主Agent失败→fallback成功→record_success()→但failed_stages仍有记录

**影响范围**: 整个流水线

**修复方式**: `should_abort()` 只检查 `consecutive_failures`，`failed_stages` 仅用于报告

**教训**:
- 状态管理逻辑必须一致：如果record_success()重置了计数器，should_abort()就不应该检查累积列表
- 决策逻辑和报告逻辑应该分离

---

### P09: skipped阶段未重置连续失败计数

**现象**: code_review和testing被跳过后，consecutive_failures仍然累加

**根因**: 流水线在跳过阶段时（依赖不满足或配置跳过），没有调用 `cascade_handler.record_success()`。跳过的阶段既不算成功也不算失败，但cascade_handler把它当作"没有记录"，保持之前的连续失败计数。

**触发场景**: MVP阶段返回fallback→code_review依赖检查→跳过→consecutive_failures未重置

**影响范围**: 流水线依赖检查

**修复方式**: 跳过阶段时调用 `record_success()` 重置计数

**教训**:
- 所有退出路径（成功、失败、跳过）都应该有明确的状态更新
- 状态机的所有状态转换都必须覆盖

---

### P10: MVP Agent返回无code_files

**现象**: MVP Agent返回 `{"status": "error", "error": "name 'ChatPromptTemplate' is not defined"}`

**根因**: MVP Agent的 `_generate_data_models` 等内部方法使用 `ChatPromptTemplate` 但缺少import（P06），导致异常。异常被捕获后返回error状态，没有code_files字段。下游的code_review和testing阶段依赖code_files，拿到空列表后fallback也失败。

**触发场景**: MVP Agent执行时

**影响范围**: code_review, testing, deployment阶段

**修复方式**: 修复import问题（P06）

**教训**:
- 一个组件的错误不应该导致整个流水线崩溃
- 下游组件应该能处理上游返回error的情况

---

## 根因分析总结

### 根因分类

| 类别 | 问题编号 | 占比 |
|------|---------|------|
| **外部依赖耦合** | P01, P02, P03 | 30% |
| **接口契约缺失** | P04, P05, P07 | 30% |
| **状态管理不一致** | P08, P09 | 20% |
| **代码质量** | P06, P10 | 20% |

### 共性根因

1. **没有抽象层**: 直接依赖langchain/pydantic的具体API，版本升级就崩
2. **靠"约定"不靠"约束"**: Agent间数据传递没有Schema强制
3. **批量操作不验证**: 一次改35个文件，没有逐个验证
4. **状态逻辑不一致**: 不同方法对同一状态的理解不一致
5. **缺少单元测试**: 没有在每步验证，问题滚雪球

### 改进方向

| 根因 | V2改进 |
|------|--------|
| 外部依赖耦合 | LLMAdapter抽象层 |
| 接口契约缺失 | Pydantic Schema强制 |
| 批量操作不验证 | 每个文件写完立即验证 |
| 状态逻辑不一致 | 统一状态管理，决策与报告分离 |
| 缺少单元测试 | 每个Phase都有验证清单 |
