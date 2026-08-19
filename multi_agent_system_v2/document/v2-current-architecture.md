# V2 当前架构总结（重构前存档）

> 本文档是重构（spec-driven）之前对 V2 现状的忠实快照，作为对照基准。
> 生成日期：2026-08-19。后续重构见 `architecture-v3.md`（待写）。

## 一、分层

```
main.py（入口）→ pipeline/（编排）→ agents/（7 个 Agent）→ tools/（执行器）→ llm/（适配器）→ schemas/（Pydantic）
```

LLM：小米 MiMo（`mimo-v2.5`，OpenAI 兼容），经 `LLMAdapter → OpenAIAdapter` 抽象。

## 二、主流水线（实际串行，7 阶段）

```
requirements → technical → mvp(BuilderAgent) → testing → code_review → acceptance → deployment
                                                            ↑ 迭代（最多 4 轮）┘
```

- 顺序由 `pipeline/orchestrator.py` 的 `STAGES` + `DEPENDENCIES` 决定，**单 for 循环串行**（README 写的"并行"已失真）。
- `code_review` 依赖 `testing` 的结果，两者已无法并行。

## 三、两层收敛闭环

**内层**：BuilderAgent function-calling 循环 `write_code → verify_code → run_tests → 定点修`（max_rounds=8，工具带状态，闭包读 `self.code_files`）。

**外层**：Orchestrator 迭代——testing/code_review/acceptance 产出 feedback → 问题签名加权（审查*1 + bug*2 + 验收*3）→ 签名未改善则停（防振荡）→ 质量回退则回滚上一版。

## 四、硬门槛 vs 软信号

| 类型 | 信号 |
|---|---|
| 硬门槛 | 作者测试 `all_passed`、行覆盖率 ≥80%、验收 `all_passed`、确定性不变式测试 |
| 软信号 | code_review issues/评分（只喂 builder，不挡部署） |

验收门在 `orchestrator._check_acceptance`：测试全过 + 覆盖率≥80 + 验收全过，才放行 deployment。

## 五、环境自愈（执行层）

`ensure_deps`（requirements.txt → 哈希缓存）+ `_self_heal_loop`（检测 `ModuleNotFoundError` → 区分缺依赖/本地模块/stdlib/ImportError → 自动补装 → 重跑，最多 3 轮）。ANSI 码（`FORCE_COLOR=3`）解析前剥离。

## 六、当前信任模型的问题（重构动因）

**真相被拆成 6 份 LLM 文本，靠软链接互相传**：

| 环节 | 产出者 | 性质 |
|---|---|---|
| 需求 | LLM | 软 |
| 技术方案 | LLM | 软 |
| 代码 | LLM | 软 |
| 作者测试 | LLM | 软 |
| code_review | LLM | 软 |
| 验收测试 | LLM | 软 |
| 不变式测试 | 代码 | 唯一硬的 |

三个明确弱环：
1. **需求忠实度**：需求 agent（LLM）可能读错/漏读原始需求（E12 只缓解）。
2. **验收测试翻译**：acceptance agent 用 LLM 把考卷翻成 pytest，可能"放水"。
3. **builder↔technical 无契约**：软同步 + 验收间接对齐，无 schema 级 API 契约校验；只有出现在验收标准里的端点才会被对齐。

## 七、已知文档/代码债

- README 写"6-Agent / 并行 / 模块结构"已过时（实际 7-Agent / 串行 / 部分 tools 文件已不存在）。
- `agents/mvp.py`（旧 MVPAgent）、`agents/testing.py` 的对抗测试函数是死代码。

## 八、重构方向（spec-driven）

把"真相"收拢成一份机器可查的 Spec，LLM 只剩两处：`NL → Spec`、`Spec → 代码`；验证全部由确定性代码从 Spec 推导。详见重构后的架构文档。
