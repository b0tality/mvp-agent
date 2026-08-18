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

## 2026-08-19 | 真实验证驱动的收敛闭环（P1–P3）

目标：把多智能体从「形同虚设」改造成真正互相监督、互相补充、真实收敛到可用 MVP 的流水线。
验收口径（P2/P3 更严）：真实测试全过 + 行覆盖率 ≥80% + 验收标准 100% 通过 + 无 critical/major 审查问题。

### 遇到的问题

#### E10: 多智能体「形同虚设」——各 Agent 只是独立 LLM 调用

**现象**: 名义上是多智能体协作，实际每个 Agent 把需求文本丢给 LLM 各写各的，结果要么互相印证错误，要么彼此不一致，产出的代码不一定能跑。

**根因**:
1. 没有「真实执行」这个客观信号——testing 让 LLM「假装」测试，code_review 让 LLM「假装」审查。
2. 各 Agent 之间只靠文本传递，没有把真实结果（退出码、覆盖率、断言差异）作为数据流回灌。

**解决**:
1. testing 改为真实执行：临时沙箱 + `pytest` 子进程 + `coverage` + `TestClient` 冒烟探活（GET /openapi.json）。
2. code_review 接入真实测试结果（`test_results`），审查建立在真实失败上而非空想。
3. 新增 acceptance Agent：把需求阶段的「考卷」（acceptance_criteria）逐条转成可执行 pytest，真实运行核对「需求说返回 400，代码到底是不是 400」。
4. 迭代闭环：真实失败（测试 bug / 验收失败 / critical-major 审查问题）回灌 MVP 修复。

**避免**: 任何「验证类」「审查类」Agent 必须落地到可观测信号（退出码、覆盖率、断言差异），严禁用 LLM 自评代替真实执行。

#### E11: 需求「非数字返回 400」vs 代码返回 422

**现象**: calculator 验收要求非数字输入返回 400，代码却返回 422，验收测试失败 `assert 422 == 400`。

**根因**: FastAPI/Pydantic 的默认请求校验返回 422，而需求明确要求 400。框架默认值 ≠ 需求值。

**解决**: acceptance 真实跑测试抓住了差距；MVP 端显式处理（手动校验或加 `RequestValidationError` 异常处理器返回 400）。

**避免**: 验收标准必须包含具体状态码/边界值；代码实现时，凡需求指定的状态码与框架默认值冲突（典型 422 vs 400），都要显式处理，不能「让框架兜底」。

#### E12: 验收标准「考卷变简单」——丢失「400」具体性

**现象**: 验收标准本该写「非数字返回 400」，却退化成了「返回错误提示」，导致验收测不到真实差距。

**根因**: 验收标准从「二次加工后的 user_stories」生成，而非原始需求，逐层加工把具体可验证细节（状态码、边界长度）稀释掉了。

**解决**: `AcceptanceCriteriaTool` 改为锚定 raw `user_input` + `requirements`，强制保留具体可验证细节。

**避免**: 验收标准（考卷）必须直接对**原始需求**生成，保留具体数字/状态码/边界，不做二次抽象。

#### E13: MVP 迭代修不动 bug（8 个 bug 跨迭代持久）

**现象**: 迭代循环能触发，但每次 MVP 大幅重写，改好一个又破坏另一个，8 个 bug 反复横跳无法收敛。

**根因**: 没有「质量回退」护栏——MVP 拿到反馈后倾向整体重写而非定点修复，方向发散。

**解决**:
1. `_quality_worse` 护栏：比较两轮真实指标（失败数、覆盖率），新版本更差则回退上一版并停止迭代。
2. `_improve_code` 提示改为「最小修改，不要重写已通过的代码」。

**避免**: 迭代必须用**客观指标**（测试失败数、验收通过数、覆盖率）做收敛判断，允许回退更差版本，提示词强制「定点最小修改」。

#### E14: tech_stack 不一致（Node.js vs FastAPI）

**现象**: technical Agent 自由发挥选了 Node.js 等无法在本系统验证的技术栈。

**根因**: 没有约束可选技术栈，而系统只能真实运行/验证 Python 代码。

**解决**: 约束 technical 提示词只生成 Python/FastAPI。

**避免**: **可验证性优先**——只有能被真实跑起来验证的技术栈才允许进入流水线。

#### E15: project_name 带空格（"Calculator API"）

**现象**: 项目名含空格导致落盘路径异常。

**解决**: `re.sub` 消毒，仅保留 `[0-9a-zA-Z_]`。

**避免**: 一切落盘路径在写入前统一消毒。

#### E16: 缺少 requirements.txt

**现象**: 某些运行 LLM 没生成 requirements.txt。

**解决**: `save_generated_code` 兜底写入默认依赖。

**避免**: 关键产物（依赖清单、入口文件）必须有无条件兜底。

#### E17: Review 评分门太吵（score<80 误判失败）

**现象**: 代码客观指标全过，但 LLM 主观评分 <80 导致误判失败、空转迭代。

**根因**: LLM 主观评分噪声大，不是稳定信号。

**解决**: 把 `score < 80` 从迭代条件和验收门中移除，只保留 critical/major 作为审查硬信号，评分降级为参考。

**避免**: **客观信号做主判，LLM 主观评分只做参考**，不用在门槛上。

#### E18: output 目录残留旧文件

**现象**: 上一次运行的 `index.html`/`test_acceptance.py` 残留，混入最新产物。

**解决**: 覆盖写之前 `shutil.rmtree(project_dir)` 清理。

**避免**: 落盘前先清目标目录，避免「看似最新实则混杂」。

#### E19: testing 把「0 个测试」当成「全部通过」（假阳性）

**现象**: todo 应用最终代码没生成测试文件，pytest 输出「no tests ran in 0.00s」、覆盖率 0%，但 `all_passed` 却是 `True`，测试门被蒙混通过。

**根因**: `all_passed = failed == 0 and smoke_passed`——当 0 个测试被收集时 `failed==0` 恒真，`smoke` 又通过，于是「没跑任何测试」被当成了「全部通过」。

**解决**:
1. `all_passed` 增加 `passed > 0` 且非 no-tests 的前提。
2. `_extract_bugs` 在 `passed==0 and failed==0` 时产出 critical「未收集到测试」。
3. `_coverage_report` 无数据视为 0%（而非 -1 跳过门槛）。

**避免**: **「0 个测试」绝不等于「全部通过」**——任何「通过」都要有真实执行过的测试作为证据；无数据覆盖率按 0% 处理。

#### E20: acceptance 结果解析「前缀冲突」

**现象**: 原始 pytest 明明 8 通过 5 失败，结果却被报成 5 通过 8 失败；`AC-001`、`AC-004` 这些本身通过的用例被错标为失败。

**根因**: 解析正则 `test_ac_<id>\S*` 的 `\S*` 贪婪匹配，使 `AC-001` 前缀命中了 `AC-001_ERROR_EMPTY_TITLE` 等兄弟测试（后者 FAILED），污染了前者。

**解决**: 改用 `::test_ac_<id>\s+` 精确匹配完整函数名（`::` 锚定 + 要求名字后紧跟空白）。

**避免**: 任何从文本解析结果的代码，都要**精确匹配完整 token**，警惕前缀/子串误匹配；写完用带「兄弟命名」的用例做回归测试。

#### E21: 迭代时 MVP 丢失测试文件

**现象**: 首轮 MVP 生成了 14 个测试且全过，但迭代一次后测试文件消失，下一轮 code_review 报「no tests」。

**根因**: `_run_iteration` 只把 `code_files` 传给 MVP 的 `_improve_code`，而测试文件在 `test_files` 字段——改进时 MVP 看不到测试，于是只重新输出 `code_files`，把 `tests/test_api.py` 丢了。

**解决**:
1. `_run_iteration` 合并 `code_files + test_files` 一起传给 MVP。
2. `_improve_code` 提示词显式要求「输出 test_files 字段，重新生成 tests/test_api.py」。

**避免**: 迭代/改进时必须传递**完整上下文**（代码 + 测试），并在提示词里显式要求输出所有必要产物，不靠 LLM「自觉」。

---

## 避坑清单（下次开发如何避免同类问题）

1. **验证必须真实执行**：测试、审查、验收全部落地到退出码 / 覆盖率 / 断言差异，严禁 LLM 自评。
2. **客观信号做门槛，主观评分只做参考**：测试失败数、验收通过数、覆盖率是硬门槛；LLM 评分不作为硬判据。
3. **「0 个测试」≠「全部通过」**：任何「通过」都要有真实执行过的测试证据；无数据覆盖率按 0% 处理。
4. **验收标准（考卷）锚定原始需求**：直接对 raw 输入生成，保留具体状态码 / 边界值 / 数字。
5. **状态码冲突显式处理**：需求指定的状态码与框架默认值冲突（如 422 vs 400）时，显式加处理器，不让框架兜底。
6. **迭代用客观指标收敛 + 回退护栏**：比较失败数/覆盖率，更差即回退；提示词强制「最小修改」。
7. **迭代传递完整上下文**：代码 + 测试一起传，显式要求输出测试文件。
8. **解析器精确匹配**：警惕前缀/子串误匹配，用 `::` 锚定 + 完整 token + 边界断言。
9. **可验证性优先**：只允许能被真实跑起来验证的技术栈。
10. **落盘前清理 + 关键产物兜底**：覆盖写前 `rmtree`，requirements.txt 等必须有兜底。

---

（后续错误实时追加）
