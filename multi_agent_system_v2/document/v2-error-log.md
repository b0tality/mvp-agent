# V2 实时错误日志

记录V2开发过程中遇到的所有问题。

---

## 2026-08-18 | Phase 1-4 开发

Phase 1（Schema层）、Phase 2（BaseAgent/BaseTool）、Phase 3（RequirementsAgent）、Phase 4（完整流水线）全部实现完成。

### 遇到的问题

#### E01: orchestrator.py 拼写错误

**现象**: `self.DEPENCIES` 应为 `self.DEPENDENCIES`

**根因**: 手写代码拼写错误

**修复**: 立即修复为 `self.DEPENDENCIES`

**教训**: 写完代码应立即运行验证

#### E02: 完整流水线超时（10分钟）

**现象**: 6个Agent串联运行超过10分钟无输出

**根因**: 每个Agent调用LLM多次（3-6次），6个Agent合计约20-30次LLM调用，每次约30-60秒

**解决**: 这是预期行为，不是bug。可通过以下方式优化：
- 减少每个Agent的工具调用次数
- 使用更快的模型
- 并行执行无依赖的阶段

**验证**: 单独运行requirements+technical两个Agent成功（40.6s + 87.1s = 127.7s）

---

## 2026-08-18 | 并行执行优化

实现code_review和testing阶段并行执行。

### 遇到的问题

#### E03: AgentResult转Dict失败

**现象**: `result["agent_used"] = "primary"` 报错，AgentResult不支持item assignment

**根因**: `agent.execute()` 返回 `AgentResult`（Pydantic模型），但 `FallbackManager.execute()` 期望 `Dict`。Pydantic模型不支持 `[]` 赋值。

**修复**: 在 `_execute_stage` 中用 `primary_wrapper` 包装，调用 `result.model_dump()` 转为Dict。

**教训**: 接口契约要明确：如果期望Dict返回，就要在适配层转换。

#### E04: PipelineState.get()参数错误

**现象**: `PipelineState.get() takes 2 positional arguments but 3 were given`

**根因**: `_build_stage_kwargs` 中调用 `self.state.get("mvp", {})`，但 `PipelineState.get()` 只接受1个参数（已有默认值 `{}`）。

**修复**: 移除多余的第二个参数，改为 `self.state.get("mvp")`。

**教训**: 方法签名要与调用方式一致。

#### E05: 并行执行时间计算

**现象**: 测试显示总耗时10.0s（预期8s）

**根因**: 6个阶段，每个2s：
- 串行阶段：requirements(2s) + technical(2s) + mvp(2s) + deployment(2s) = 8s
- 并行阶段：[code_review, testing](2s) = 2s
- 总计：10s

这是正确的，不是bug。

---

## 2026-08-18 | 完整流水线测试

### 遇到的问题

#### E06: MVP Agent返回0个code_files

**现象**: MVP Agent返回 `code_files: []`，导致code_review和testing显示0.0s

**根因**: MVP Agent的Prompt没有明确要求生成代码文件，LLM返回了空的code_files列表

**修复**: 
1. 优化Prompt，明确要求"必须生成至少2-3个代码文件"
2. 添加fallback：如果code_files为空，返回默认骨架代码

**教训**: Prompt要明确指定输出要求，不能依赖LLM"自觉"

#### E07: 流水线执行时间过长

**现象**: 简化前每个Agent调用4个工具，总耗时超过15分钟

**根因**: 每个Agent调用多个工具（project, code, test, doc），每个工具一次LLM调用

**修复**: 简化Agent，每个Agent只调用1次LLM（合并多个工具为一次调用）

**教训**: 减少LLM调用次数是性能优化的关键

### 最终测试结果

```
状态: success
总耗时: 112.2s（约1.9分钟）

各阶段结果:
  requirements: success (72.3s, primary)
  technical: success (10.0s, primary)
  mvp: success (1.8s, primary)
  code_review: success (4.7s, primary)
  testing: success (4.3s, primary)
  deployment: success (23.4s, primary)
```

**并行效果**: code_review(4.7s) + testing(4.3s) 并行执行，实际耗时4.7s

---

## 2026-08-18 | 迭代优化循环

实现Agent间互相review并改进代码的迭代循环。

### 遇到的问题

#### E08: 迭代条件误触发

**现象**: 0个问题0个Bug时仍然触发迭代循环

**根因**: 
1. 初始条件 `if not approved or score < 70` 中，LLM返回 `approved: False` 即使没有问题
2. 改为 `if issues or score < 60` 后，LLM可能返回非空issues列表（即使实际无问题）

**修复**: 改为 `if len(issues) > 0 and score < 70`，同时满足才触发迭代

**教训**: LLM输出不稳定，条件判断要同时检查多个字段

#### E09: PipelineState.get()参数错误（再次）

**现象**: `_run_iteration` 中调用 `self.state.get("mvp", {})` 报错

**根因**: 与E04相同，`PipelineState.get()` 只接受1个参数

**修复**: 改为 `self.state.get("mvp").get("code_files", [])`

**教训**: 同样的错误不要犯两次，写完代码要grep检查所有调用点

### 迭代循环设计

```
MVP生成 → CodeReview审查 → 不通过? → MVP改进(带feedback) → 重新审查
                              ↓ 通过
                         Testing测试 → 有bug? → MVP修复(带feedback) → 重新测试
                              ↓ 通过
                           Deployment
```

**迭代条件**:
- code_review: issues非空 且 score < 70
- testing: 存在critical或major bug
- 最大迭代次数: 3

**数据流**:
- CodeReviewOutput.issues → MVPAgent.feedback.issues
- TestingOutput.bugs → MVPAgent.feedback.bugs
- 两个Agent的suggestions → MVPAgent.feedback.suggestions

---

## 2026-08-18 | 编译验证

实现代码生成后的编译验证，自动修复语法错误。

### 实现方案

**流程**：
```
MVP生成代码 → 写入临时目录 → AST解析 + py_compile → 有错误? → MVP修复 → 重新验证
                                ↓ 通过
                             继续流水线
```

**验证方式**：
1. AST解析：检测语法错误（括号、缩进、关键字）
2. py_compile：检测编译错误（导入、类型、语法）

**错误反馈**：
```python
{
    "compile_errors": [
        {"file": "main.py", "type": "syntax", "line": 3, "message": "'(' was never closed"},
        {"file": "main.py", "type": "compile", "message": "IndentationError: ..."}
    ]
}
```

### 测试结果

**编译验证工具测试**：
- 语法正确代码：Passed ✓
- 括号未闭合：检测到（line 3, syntax error）✓
- 缩进错误：检测到（line 2, IndentationError）✓

**完整流水线测试**：
```
状态: success
总耗时: 166.4s
迭代次数: 2

流程：
  mvp: 
    - 首次生成: success (2.9s)
    - 编译验证: 通过 ✓
    - 迭代1: 修复5个code_review问题 (11.2s)
    - 迭代2: 修复1个testing bug (21.2s)
```

### 修改文件

| 文件 | 修改内容 |
|------|---------|
| `tools/mvp_tools.py` | 新增 `CodeVerifierTool` |
| `agents/mvp.py` | 支持 `compile_errors` 反馈 |
| `pipeline/orchestrator.py` | 添加编译验证循环 |

---

（后续错误实时追加）
