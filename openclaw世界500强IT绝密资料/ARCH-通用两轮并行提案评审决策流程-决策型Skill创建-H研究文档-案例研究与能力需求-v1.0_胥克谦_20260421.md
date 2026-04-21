---
docLinks:
  schemaVersion: 1
  upstream:
  - kind: rule
    path: .claude/rules/文档头部关联链路标注规范.md
    relation: references
    ref:
      repo: .
      branch: docs
      commit: 249b7a8a2b114d9e8507f3f9c46d849c3f06405f
  - kind: rule
    path: .claude/rules/文档命名规范.md
    relation: references
    ref:
      repo: .
      branch: docs
      commit: fa58e7981a91f38b142d68f3b56b6c7e467c4cf6
  - kind: rule
    path: .claude/rules/文档组织规范.md
    relation: references
    ref:
      repo: .
      branch: docs
      commit: fa58e7981a91f38b142d68f3b56b6c7e467c4cf6
  - kind: doc
    path: CLAUDE.md
    relation: references
    ref:
      repo: .
      branch: docs
      commit: 65652b9fad41aa60f4dc3fdbdb7ab989f8fb05f1
  - kind: user_instruction
    summary: 2026-04-21 用户要求：用10个独立agent模拟两轮并行提案→并行评审→最终决策流程并落盘全过程文档，用于抽取通用流程/工具能力要点；同时把误生成产物作为第11个对比案例
    relation: originates_from
    ref:
      repo: .
      branch: docs
---

# 决策型 Skill 创建决策过程：通用“两轮并行提案→并行评审→最终决策”流程（案例研究与能力需求，v1.0）

## 0. 范围声明（非常重要）


### 0.1 背景与原始需求（正式化）

团队在日常研发/产品/内容生产中，经常需要在“多解、强约束、跨角色博弈”的问题上快速得到高质量结论。为此，你们长期使用一种 **Swarm 并行决策工作法**：

1) **提案轮（并行发散）**：由 3/5/更多个并行角色在同一输入合同下各自独立产出差异化方案（强调独立性与多样性）。
2) **汇总（主进程收敛）**：主进程将提案整理成可比较的 Option Cards + 对比矩阵 + 阻塞问题清单（Blocking Questions）。
3) **评审轮（全新并行裁决）**：由全新一组 3/5/更多并行角色对候选方案独立给出择优 verdict 与理由（含 trade-offs、风险与签字条件）。
4) **最终决策（主进程裁决）**：主进程基于 verdict 汇总做最终判断，输出可交付的决策报告；必要时将结果“交付到下一执行环节”（例如形成可执行的 handoff/checklist，或在授权下写回/生成后续任务）。

期望的交付报告通常包括：**最终选择与理由**、**验收与门禁**、**风险边界（fail-closed vs warn）**、以及（附录）**备选方案简述与优缺点对比**。

### 0.2 目标形态：可被复用/调用的通用决策流程能力（可 Skill 化）

你们希望把上述工作法抽象为一个通用能力模块（可作为“skill”被其它 skill/流程调用），以便：

- **手动触发**：当需要“快速发散→受约束收敛→独立裁决→最终报告”的闭环时，直接启动一个 run。
- **自动触发**：当上游流程（PRD/架构/开发计划/QA/审计/对外材料等）遇到阻塞问题、冲突、门禁 FAIL 且需要“方案裁决”时，自动进入决策闭环。
- **跨内容类型复用**：同一流程骨架可适配不同内容类型（Spec/ADR/Plan/QA/Ops/Sec/Analytics/Comms/Creative/Enablement），通过 profile 装配调整角色、rubric、门禁强度与产物合同。

### 0.3 本文范围（研究阶段）


- 本文处于“提出问题/抽取需求”的研究阶段，不进入执行/落地实现阶段。
- 本文的目标是：通过跨领域案例，抽取一个未来可复用的“通用两轮并行决策流程/工具（可 Skill 化并被其它流程调用）”的**最小可行能力集合**与风险边界。
- 本文会补齐“后续可生成 skill 资产”的上游冻结信息（Spec Pack：元信息/模板/机读 Schema/验收回归清单），但**不在本文中实际创建/写入 `.claude/skills/**`**。

## 1. 证据与复盘入口

本轮案例的全过程证据落盘在（注意：该目录默认被 gitignore 忽略，用于本地复盘与审计）：

- `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/`

每个案例目录结构（约定）：

- `00-input/`：冻结输入合同
- `10-ideation/`：提案轮（多角色独立提案）
- `20-synthesis/`：汇总（Option Cards + 对比矩阵）
- `30-judging/`：评审轮（全新角色独立 verdict）
- `40-final/decision-report.md`：最终决策报告
- `90-meta/trace.md`：过程记录
- `90-meta/requirements.md`：从该案例反推的能力要求（Must/Should/Nice-to-have）

## 2. 方法：30 个案例模拟

- Case 01-10：10 个独立问题域目标，跑完整闭环并落盘全过程文档。
- Case 11：主进程误触发导致的“过早产物”快照，仅作为对比反例，用于反推阶段切换/写入意图治理。
- Case 12-14：产品创意三案（冷启动 Doctor、成本透明、Review Pack 证据包）。
- Case 15-17：架构决策三案（EvidenceRoot v1、配置协议 v1、Resumable Task 状态机+ledger）。
- Case 18-20：写作创意三案（一页纸 Quickstart、决策型模板、指令型防误触发写法）。
- Case 21-30：内容类型实证十案（Spec/ADR/Plan/QA/Ops/Sec/Data/Comms/Creative/Enablement）。

> 说明：Case 11 不是最终设计结论，且其存在本身即是风险样例（应被流程/工具约束避免）。

### 2.1 文档修订记录（会话驱动的变更日志：指令→动作→证据→抽象）

> 本节以中立、客观的方式记录“从第一段需求提出到当前版本完成”的主要变更步骤与依据，便于回溯、审计与复盘。

- **数据来源**：
  - 会话中的阶段性要求（例如：先研究、禁止过早实现；要求并行模拟；要求新增案例与抽象；要求并发矩阵与独立使用模式等）。
  - 本轮 evidenceRoot 落盘日志：`docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/`（见 `INDEX.md` 与 `RUNBOOK.md`）。
- **时间说明（客观）**：下述时间点使用文件 `mtime` 作为“最后一次写入”参考，用于复盘排序，并不代表唯一修改时刻。

- **过程时间线（按落盘证据的可验证信号）**：
  - 2026-04-21 09:47：Case 11 反例快照目录落盘（过早产物误触发的对比证据），见 `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-11-previous-impl/README.md`。
  - 2026-04-21 09:48：模拟 Runbook 冻结（限定写入范围、目录结构、独立性约束、最小产物合同），见 `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/RUNBOOK.md`。
  - 2026-04-21 10:08～10:34：Case 01–10 的最终报告陆续落盘（示例：Case 01/10 的 `40-final/decision-report.md`），入口索引见 `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/INDEX.md`。
  - 2026-04-21 10:45：研究汇总主文档创建（随后进入持续补齐/整合/增量完善阶段），见本文档的文件创建时间。
  - 2026-04-21 11:20～11:58：Case 12–20（产品创意/架构决策/写作创意）最终报告落盘。
  - 2026-04-21 12:30～12:37：Case 21–30（10 类内容类型实证）最终报告落盘。
  - 2026-04-21 15:37～15:39：主文档最后一轮增强（并发矩阵/动态扩容/独立使用模式/命名调整）与索引引用同步更新。

- **会话要求 → 执行动作 → 产物（按逻辑链路复盘）**：
  1) **提出目标形态（Swarm 两轮并行决策工作法）**
     - 要求：并行提案（3/5/更多）→主进程汇总→全新并行评审→最终裁决→可交付到下一环节；报告需含最终选择/门禁/风险边界/备选对比。
     - 动作：将口语化需求正式化为可审计的“背景/目标形态/范围声明”。
     - 产物：本文 `0.1/0.2/0.3`（背景与原始需求、可复用目标形态、研究范围）。

  2) **阶段纠偏：明确当前为研究/提出问题阶段（禁止过早实现）**
     - 要求：不要直接生成/落地实现；先用案例模拟抽取能力要点；将误触发产物仅作为反例案例。
     - 动作：冻结“只研究不实现”的边界；将误触发产物归档为 Case 11（反向需求输入）。
     - 产物：`docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-11-previous-impl/README.md`；本文 `Case 11` 与“阶段/写入意图”相关结论聚类。

  3) **定义可复跑的模拟协议（Runbook）**
     - 要求：每个案例必须跑完整闭环并保留全过程文档；案例间互不读取；写入范围严格受限。
     - 动作：用 Runbook 固化输入合同/目录结构/最小产物合同与强制约束（可视为“研究版流程标准”）。
     - 产物：`docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/RUNBOOK.md`。

  4) **执行 Case 01–10：来自真实项目不同环节的“可验证问题/目标”闭环模拟**
     - 要求：10 个差异化目标；每案必须引用仓库内真实路径作为证据；按两轮并行+评审+最终报告闭环；保留过程文档。
     - 动作：为每个 case 落盘 `00-input/10-ideation/20-synthesis/30-judging/40-final/90-meta`；提案轮至少 5 角色，评审轮至少 3 verdict（与 Runbook 对齐）。
     - 产物：`docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-01`～`case-10`；入口索引 `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/INDEX.md`。

  5) **扩展 Case 12–20：产品创意×3、架构决策×3、写作创意×3**
     - 要求：增加三类领域的各 3 个案例，按相同流程真实跑闭环并落盘证据。
     - 动作：复用同一 Runbook 骨架，但让输入合同/门禁重点随内容类型变化；并将增量经验回写到横向结论与 Skill 化抽象章节。
     - 产物：`docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-12`～`case-20`；本文 `8.8 新增案例（Case 12–20）带来的增量结论`。

  6) **扩展 Case 21–30：10 类内容类型实证 + 三域需求样例**
     - 要求：穷举 10 种大的内容类型，覆盖研发/创意/企业市场；对每类都“真实跑一遍流程”并抽象最优化链路。
     - 动作：为每个内容类型冻结 profile v1（Must/Should/Fail-closed/验收清单/证据合同），并把“类型差异”沉到 profile/overlay，而不是污染通用骨架。
     - 产物：`docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-21`～`case-30`；本文 `9.* 内容类型扩展（10 类）`。

  7) **跨案例抽象：把案例输出沉淀为“通用流程/门禁/产物合同/可调旋钮”**
     - 要求：从各案例的日志与过程文档中抽象有效方法与边界，形成可复用的通用方案。
     - 动作：将逐案决策与横向结论整合到本文（概览表、逐案分析、环节级结论、内容类型 profile、Skill 化抽象）。
     - 产物：本文 `3（概览）/7（逐案）/8（环节结论）/9（内容类型）/10（面向 Skill 化抽象）`。

  8) **质量增强：反平庸/反保守 + 轻盈优雅优先 + 可调 TaskDials**
     - 要求：评估流程是否会产出平庸/保守结论；加入反平庸机制；同时引入“更简单更通用更复用”的高优先级维度；创意/风险/通用性/安全等维度可按次调参。
     - 动作：将机制固化为可装配条款与提示词旋钮（并区分“不可调安全不变量”与“可调严格度”）。
     - 产物：本文 `10.10/10.11/10.12`。

  9) **规模增强：并发配置矩阵 + 动态扩容（样本数可按目标到 50）**
     - 要求：补齐不同环节并发数量的约定；避免“可配置但实际固定默认值”；样本数应根据目标决定。
     - 动作：增加 riskClass×timeBudget 基线矩阵 + 触发信号/批次扩容/停止条件的自适应采样机制；并将 sampling 纳入 TaskDials。
     - 产物：本文 `6.3/6.4` 与 TaskDials 的 `sampling` 控制块。

  10) **独立使用模式：显性提示词输入 + 显性人读报告输出**
      - 要求：支持不依赖上游 skill 的独立启动；通过显性 prompt 触发；显性输出人读版报告文档。
      - 动作：新增 Standalone Run 的 Prompt Contract，并把 `decision-report.md` 升格为“无论是否落盘都必须输出的人读 SSOT”。
      - 产物：本文 `6.5` 与 `7) 交付形态`。

  11) **命名调整：让文档一眼可见“这是创建 Skill 的决策过程”**
      - 要求：方案命名应能体现“正在为创建 skill 做决策”。
      - 动作：调整文件名与主标题，将“Skill 创建决策过程”作为显性主题；同步更新 logs 索引指针。
      - 产物：本文标题与文件名；`docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/INDEX.md` 的研究汇总指针。

  12) **补齐 Skill-ready 缺口：冻结元信息/模板/Schema/验收回归（Spec Pack）**
      - 要求：复检文档是否达到“可用于生成 skill”的标准；补齐从研究文档到可直接生成 skill 资产的缺口，并记录本条修订。
      - 动作：新增 “Skill 生成输入包（Spec Pack）”章节，冻结 `skill.md` 元信息、canonical 产物布局与 compat 适配规则、模板清单、机读 Schema v0.1、动态扩容默认阈值与 P0 验收回归清单。
      - 产物：本文 `11.* Skill 生成输入包（Spec Pack）`；本文 `2.1` 新增本条修订记录。

- **关键决策链路（方案形成的主要判断路径）**：
  - **把问题变成可裁决对象**：优先冻结证据指针与边界（不足则进入 Blocking Questions，而不是直接“脑补补齐”）。
  - **用并行发散获得差异化候选**：先保证角色独立与视角覆盖，再谈方案优劣（避免群体思维与过早收敛）。
  - **把观点翻译成可比较选项**：以 Option Cards + 对比矩阵 + Blocking Questions 三件套收敛（可比较、可回放、可续跑）。
  - **用全新评审降低作者偏见**：评审输出以 pick+confidence+trade-offs+sign-off conditions 为核心（把风险变成“可签字条件”）。
  - **按信号决定是否扩容样本**：当多样性不足/证据不足/分歧过大/置信不足时，按批次扩容；当边际增益变小或风险闭环完成时停止（见 `6.4`）。
  - **以可执行交付收束**：FINAL 必须输出验收清单与 fail-closed/warn 边界；META 必须抽取 requirements 以支持未来装配与回归。

- **复盘入口建议（可选）**：
  - 先读 Runbook（约束/目录/产物合同）：`docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/RUNBOOK.md`。
  - 再按 INDEX 选 3 个案例精读：1 个常规（如 Case 01）、1 个安全/误触发反例（Case 11）、1 个对外/合规类（如 Case 28），入口：`docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/INDEX.md`。
  - 最后回到本文看抽象：先看 `8（环节结论）` 再看 `10（Skill 化抽象）`，把“案例→通用能力点”的映射建立起来。

## 3. 案例概览（浓缩版）

| Case | 问题域 | 一句话问题 | 最终决策（摘要） | 关键能力关键词 | 证据指针 |
| --- | --- | --- | --- | --- | --- |
| 01 | 文档组织/门禁范围 | 交付文档与外部输入散落在 root 等非标准位置，造成门禁范围不一致 | “docs 交付 + fixtures 外部输入 + logs 过程证据”，并对 root doc-like 资产 fail-closed | 目录政策、三类根目录、root 禁止、渐进迁移 | `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-01/40-final/decision-report.md` |
| 02 | docLinks 断链治理 | `ref.commit` 与 `path` 不一致导致断链（broken-path-at-commit） | Repair-first，Prune-last；broken-path 不允许降级为 warn | commit-aware 校验、writer 统一入口、强证明 | `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-02/40-final/decision-report.md` |
| 03 | 管理写入防误触发 | “讨论/引用”场景会触发管理命令写仓库，存在误写风险 | 默认 dry-run + 显式 apply；引入 Write-Intent Gate（fail-closed） | 阶段切换、写入意图、nonce 确认、回归负例 | `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-03/40-final/decision-report.md` |
| 04 | 并行边界（执行开发） | manifest validate=PASS，但并行写集合重叠导致冲突检查=BLOCKED | 三态裁决：PARALLEL_OK / SERIAL_ONLY / BLOCKED；SSOT 单写者 | 并行资格判定、写集合互斥证明、机读裁决 | `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-04/40-final/decision-report.md` |
| 05 | Web UAT 证据合同 | 证据采集→报告交付缺少可机读合同与 fail-closed 校验，报告易退化 | Manifest Directory + Gate；run-bundle 仍为执行 SSOT；默认摘要脱敏 | 证据合同、schema、路径规范、风险模式 | `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-05/40-final/decision-report.md` |
| 06 | Mock 隔离口径漂移 | 规则/实现/开发计划对 MSW 开关口径不一致，可能回流到二态开关与 bypass 误用 | Composite Plan：B+C 为骨架（Router/证据 + 合规门禁），A+D 为增量（入口纠偏 + 测试固化） | 合规门禁、SSOT 口径、证据回放、禁止降级 | `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-06/40-final/decision-report.md` |
| 07 | ToolInventory 契约 | core 与 device-agent 探测语义可能漂移，服务端校验不足 | Tool 探测 SSOT（core 复用）+ 服务端校验（allowlist+schema+限制） | 稳定接口契约、服务端边界、验收清单 | `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-07/40-final/decision-report.md` |
| 08 | Readiness（包管理器冲突） | pnpm monorepo 但存在 npm lockfile，造成探测歧义 | Hybrid（静态 SSOT + CI 运行态校验）+ 渐进收敛（WARN→FAIL） | SSOT、冲突集合、治理节奏、remediation | `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-08/40-final/decision-report.md` |
| 09 | Docker 探测稳健性 | 受限 PATH 下 allowlist 不完整会误判 docker 不存在，导致错误 fail-closed | override + 扩展 allowlist + 结构化诊断；明确 fail-closed/warn 边界 | override 校验、诊断证据、required/optional | `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-09/40-final/decision-report.md` |
| 10 | LLM 默认路由治理 | 未显式指定时 provider/model 会因环境漂移，成本/质量不可控 | 引入 policy SSOT（strict/compat）+ cost/quality guardrails（可阻断可审计） | policy、优先级冻结、预算门禁、审计元数据 | `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-10/40-final/decision-report.md` |
| 11 | 过早产物（反例） | 在仅“出方案”阶段就生成仓库产物，干扰决策并造成误写风险 | 仅作反例归档：必须靠阶段门禁/写入意图机制避免发生 | 阶段切换、write intent、fail-closed、输出合同 | `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-11-previous-impl/README.md` |
| 12 | 产品入口/诊断 | 冷启动阻塞：入口割裂、提示漂移、下一步不清晰 | 只读 `cubecoder doctor` + JSON/MD 双输出；readiness 为依赖 SSOT | 单入口、只读脱敏、确定性、fixtures 回归 | `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-12/40-final/decision-report.md` |
| 13 | 成本/预算 UX | 成本治理缺“默认可见 + 可行动 + 可审计”的闭环 | `cost-summary.json` 合同化 + budget preflight；默认展示可关闭 | 成本合同、预算护栏、remediation、脱敏 | `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-13/40-final/decision-report.md` |
| 14 | 单包证据分享 | 证据分散且缺统一入口，异步协作难审计且易泄漏 | 目录型 Review Pack（manifest+README）+ gate；zip/checksum 后置 | manifest、adapter、secrets 扫描、默认安全 | `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-14/40-final/decision-report.md` |
| 15 | EvidenceRoot 统一 | 多流程证据缺统一索引与 gate，覆盖/漂移风险高 | EvidenceRoot v1：`index.jsonl` + `gates/` + append-only；不替代各流程 SSOT | 统一索引、覆盖禁止、fixtures 迁移 | `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-15/40-final/decision-report.md` |
| 16 | 配置协议/审计 | 配置覆盖顺序与来源不可审计，strict 治理难落地 | strict/compat + `config-resolution.json`（effective/sources/warnings，脱敏） | 优先级冻结、resolution report、渐进 sources | `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-16/40-final/decision-report.md` |
| 17 | 续跑/并行安全 | 多轮续跑缺机读状态与 ledger，易歧义且不可回放 | 状态机 v1 + `ledger.jsonl` append-only + SSOT 单写者 + 负例回归 | 状态机、ledger、三态 decide、并行边界 | `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-17/40-final/decision-report.md` |
| 18 | 入口写作 | 缺少 2 分钟读懂 + 首次成功闭环的一页纸入口 | 双轨一页纸（框架+首次成功路径）+ 链接预算 + SAFE/DANGEROUS | 写作护栏、链接预算、稳定标题、默认安全 | `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-18/40-final/decision-report.md` |
| 19 | 决策型模板 | 文档结构不一导致决策不可回放/不可审计/不可机读 | 单文档 + Reader/Auditor 双视图 + strict/compat + 可选 `decision-pack.yaml` | 稳定结构、机读附录、分级治理 | `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-19/40-final/decision-report.md` |
| 20 | 指令型防误触发 | 命令示例易被误当执行授权，危险域风险高 | Execution Intent + 命令块标签 + 扫描门禁；高风险可加 token | 意图协议、fail-closed、迁移路线图、危险域隔离 | `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-20/40-final/decision-report.md` |
| 21 | 内容类型：Spec | Spec/契约类内容跨域易漂移且难验收（schema/examples/compat） | schema+examples 作为可回归合同，strict/compat + fail-closed 门禁（Option D） | schema SSOT、examples/fixtures、breaking change、脱敏 | `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-21/40-final/decision-report.md` |
| 22 | 内容类型：ADR | 选型/权衡难回放，容易变成口号或拍脑袋 | strict/compat（兼容采用率）+ strict 可选机读附录（Option C+B） | trade-offs、拒绝理由、revisit triggers、分级治理 | `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-22/40-final/decision-report.md` |
| 23 | 内容类型：Plan | 计划易缺依赖/门禁/验收，执行期返工 | 分阶段 gates + 并行资格机读裁决 + required/optional 边界（Option C+D） | stage gates、parallel eligibility、DoD、回滚 | `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-23/40-final/decision-report.md` |
| 24 | 内容类型：QA/Audit | 报告易退化/丢证据且有泄密风险 | evidence manifest 机读 SSOT + 默认脱敏 + 负例 fixtures（Option D） | evidence contract、脱敏、负例回归、claim→evidence | `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-24/40-final/decision-report.md` |
| 25 | 内容类型：Ops/Incident | runbook 高风险易误触发，且难回放/难对外同步 | Execution Intent + Danger Zone token + timeline/证据指针（Option D） | read-only vs write、token、timeline、沟通模板 | `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-25/40-final/decision-report.md` |
| 26 | 内容类型：Security/Compliance | controls 若不可验证就无法审计；restricted 证据易二次泄漏 | controls→gate + restricted 指针 + claim→evidence（Option D） | controls mapping、restricted、双视图、对外声明边界 | `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-26/40-final/decision-report.md` |
| 27 | 内容类型：Analytics | 分析/实验口径漂移且不可复跑，隐私风险高 | metrics 口径冻结（metricVersion）+ query pointers(restricted) + next steps（Option C+D） | metricVersion、可复跑、隐私、行动绑定 | `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-27/40-final/decision-report.md` |
| 28 | 内容类型：External Comms | 对外材料易越权承诺且事实不一致 | claim→evidence 表 + approvers/expiry/scope 审批块 + 边界（Option D） | claim-evidence、审批链路、过期策略、迁移/回滚 | `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-28/40-final/decision-report.md` |
| 29 | 内容类型：Creative Production | 创意发散易失控或踩合规雷，资产并行难对齐 | brief 必填字段 + deliverables manifest + Do-Not/授权 fail-closed（Option C+D） | brief、deliverables、Do-Not、授权素材 | `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-29/40-final/decision-report.md` |
| 30 | 内容类型：Enablement | onboarding/KB 易膨胀且命令示例易误触发 | 双轨结构 + SAFE/DANGEROUS 标签 + 链接预算 + 扫描回归（Option D） | first success、标签语法、链接预算、版本漂移治理 | `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-30/40-final/decision-report.md` |

> 每个案例的能力要求详见对应 `90-meta/requirements.md`。

## 4. 跨案例“通用流程/工具”能力需求（聚类）

以下聚类是从 Case 01-30（含 Case 11 反例）的 `requirements.md` 与 `decision-report.md` 抽取的共同点。

### 4.1 阶段与权限（防误触发的第一性问题）

- **阶段切换门禁（Must）**：必须把“讨论/方案阶段”与“执行/写入阶段”对象化，并默认 fail-closed。
- **写入意图（Must）**：凡涉及写仓库/改代码/生成索引的动作，必须显式确认（token/nonce/flag），且能审计。
- **范围化授权（Should）**：write intent 应支持 scope（允许写哪些文件/允许哪些命令族/有效期 TTL）。

### 4.2 独立性与角色体系（发散→收敛）

- **独立提案（Must）**：提案轮必须先独立输出，禁止互相引用后再写。
- **全新评审（Must）**：评审轮必须尽量与提案轮角色解耦，避免作者偏见。
- **Rubric 可配置（Should）**：评审维度与权重需可配置，并能为不同问题域装配 profile。

### 4.3 SSOT 与证据合同（可回放、可复跑、可验收）

- **证据合同（Must）**：必须定义每类流程的最小机读产物（manifest/index/verdict/eligibility），并可校验。
- **Append-only（Must）**：证据与裁决应追加写，禁止覆盖；同一 runId 下的关键 kind 需唯一。
- **路径规范（Must）**：交付文档与合同字段必须 repo-relative，禁止绝对路径污染。
- **验收清单（Should）**：对关键决策输出，必须能给出可复跑的验收 checklist。

### 4.4 Fail-Closed 与分级治理（阻断 vs 警告）

- **required/optional（Must）**：每个依赖/证据项必须能标注 required/optional，决定 fail-closed vs warn。
- **渐进收敛（Should）**：支持 WARN→FAIL 的治理节奏（owner + deadline），避免长期“提示不收敛”。

### 4.5 并行边界与写集合互斥（可扩展到代码执行）

- **写集合互斥证明（Must）**：任何不确定都必须降级为串行；并行必须可证明互斥。
- **SSOT 单写者（Must）**：主进程是唯一 SSOT 写者；子进程只写 evidence。
- **机读并行资格裁决（Should）**：输出 `parallel-eligibility.json` 等机读裁决，避免执行器分叉。

### 4.6 安全/合规/隐私（默认安全）

- **默认安全（Must）**：证据采集默认脱敏/摘要；高风险模式必须显式启用并留痕。
- **allowlist + 限制（Should）**：对远端上报/外部输入（ToolInventory 等）必须服务端校验与资源限制。

### 4.7 成本与质量护栏（面向 LLM 场景）

- **预算门禁（Must）**：调用前预算检查可阻断；调用后审计可对账。
- **路由 SSOT（Must）**：默认 provider/model 必须由 policy 控制，避免环境漂移。


### 4.8 写作护栏与文档模板（来自 Case 18–20）

- **结构稳定（Must）**：稳定标题/稳定块让扫描与回归可行（Case 18/19/20）。
- **读者/审计双视图（Should）**：Reader View vs Auditor View 解决可读性与可审计性的冲突（Case 19）。
- **预算化写作（Should）**：链接预算/术语预算把“简洁”变成可检验约束（Case 18）。
- **执行意图协议（Must）**：文档级 Execution Intent + 命令块标签，降低“示例=授权”的误判（Case 20）。
- **兼容迁移（Should）**：warning→fail-closed + 白名单到期，避免一次性阻塞（Case 20）。

## 5. Case 11（过早产物）对流程的反向要求

Case 11 的存在直接说明：

- “只要提到某个概念就自动进入执行”是不可接受的默认行为。
- 流程/工具必须把“写入动作”从语言推断升级为显式授权。
- 输出合同必须被强制校验：缺任何关键产物就停在 WAIT/STOP 状态，不能“口头完成”。

## 6. 下一步（仍处于决策阶段，不执行）

建议将后续几十步决策拆成可审计的研究任务（示例）：

1) 冻结通用输入 schema（problem/context/constraints/success/nonGoals/rubric）
2) 冻结通用输出 schema（options/verdicts/decision-report/handoff）
3) 定义状态机：DISPATCH → WAIT_PROPOSALS → SYNTHESIS → WAIT_VERDICTS → FINAL
4) 定义 evidenceRoot 合同与目录布局（不写入 docLinks）
5) 定义 write intent 协议（对话/CLI/CI 三类场景）
6) 定义 profile 装配：不同问题域的角色集合与 rubric
7) 选 2-3 个高频问题域做“最小脚本化”验证（仅生成/校验证据，不触达代码）


## 7. 案例逐案分析（Case 01–10, 12–30）

> 说明：本节的写法刻意采用“环节视角”（输入合同→提案→汇总→评审→最终决策→Meta）复盘。
> - Best：本案验证最有效/最稳的做法
> - Pragmatic：可落地的折中做法（通常更易在团队中推进）
> - Anti-pattern/Boundary：负面模式或边界条件（踩中会退化或引发风险）
>
### 7.1 Case 01：文档组织/门禁范围（Doc Root Policy）

- 证据指针：
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-01/20-synthesis/options.md`
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-01/40-final/decision-report.md`
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-01/90-meta/requirements.md`
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-01/90-meta/trace.md`

- 输入合同：Best=用“规范文本 + 现状路径冲突”把问题钉死（docs/fixtures/logs 三类根目录 + root doc-like 硬禁止）；Pragmatic=只冻结关键证据路径与复跑命令；Anti-pattern/Boundary=只说“文档散落”不列路径/不列 Non-Goals，导致提案无限扩张。
- 提案轮：Best=角色目标函数显式分离（产品/架构/实现/QA/风控），Round 2 追加修订吸收约束但不改立场；Pragmatic=角色可减但必须保留 risk 视角；Anti-pattern/Boundary=提案互相引用或提前收敛，形成群体思维。
- 汇总：Best=Option A/B/C + 对比矩阵 + Blocking Questions（fixtures manifest、门禁范围、waiver 维护）；Pragmatic=允许给“短名单”，但必须写清拒绝理由；Anti-pattern/Boundary=没有阻塞问题清单，后续落地会出现“看似选了方案但缺关键部件”。
- 评审：Best=Tech/Product/Risk 独立 verdict（含签字条件/风险）；Pragmatic=≥3 份 verdict 即可，但必须包含“下一步验证”；Anti-pattern/Boundary=只表态不写 trade-offs、不给验收边界。
- 最终决策：Best=选择“双根 + 过程根”（docs=交付 SSOT、fixtures=外部输入、docs/todo/logs=过程留证）并明确 root 禁止；Pragmatic=先对新增变更 diff-scope fail-closed、存量走审计+迁移清单；Anti-pattern/Boundary=软约束 warn-only 会持续积累未纳管资产与断链债务。
- Meta：Best=requirements 把 diff-scope 门禁、waiver（owner+expiresAt+evidence）与 fixtures manifest 校验写成 MUST；Pragmatic=先在 CI 只对 PR diff 生效；Anti-pattern/Boundary=全仓强扫在存量未清时噪音过高，容易诱发“关门禁”。

### 7.2 Case 02：docLinks 断链治理（UPSTREAM_BROKEN_PATH_AT_COMMIT）

- 证据指针：
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-02/20-synthesis/options.md`
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-02/40-final/decision-report.md`
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-02/90-meta/trace.md`

- 输入合同：Best=把断链类型明确为“commit-aware 无法定位到 path”，并冻结可复现证据（scan 输出 + `git cat-file -e <commit>:<path>` 失败）；Pragmatic=扫描可分 scope（docs 排除 logs；rules/skills 单独扫）；Anti-pattern/Boundary=仅凭肉眼判断断链，缺少 commit 级强证明。
- 提案轮：Best=将“治理语义”先定清（Repair-first / Prune-last / 禁止降级 warn）再讨论工具细节；Pragmatic=短期允许人工逐条修复（writer 重写 commit）；Anti-pattern/Boundary=先写“新增 repair 子命令”但不先定义治理语义，会把争论推迟到实现期爆炸。
- 汇总：Best=将方案拆成 A(prune-first)/B(repair-first)/C(tooling upgrade) 并强调 B 为主干；Pragmatic=C 作为 backlog，不阻塞治理；Anti-pattern/Boundary=把 prune 当默认，会让溯源链路蒸发。
- 评审：Best=要求“验收不依赖全仓零缺口”，用“目标文件断言 + git 强证明”做可复跑验收；Pragmatic=先修关键规范文档（规则/机制）再扩面；Anti-pattern/Boundary=验收只看 scan 汇总，不做 `git cat-file` 会留下误判空间。
- 最终决策：Best=Repair-first（writer 刷新 `ref.commit`，默认 `commit-mode=file-last-change`）+ 兜底 Prune-last（同时补弱锚点说明）；Pragmatic=分批修复、每批都跑 scan+断言；Anti-pattern/Boundary=手工编辑 commit/path 或把临时目录写入 docLinks，会造成更隐蔽的断链。
- Meta：Best=trace 记录“先全仓搜索→发现会扫到 logs→改为显式排除 logs/指定 scope”的经验；Pragmatic=把“排除 logs”作为默认 managed-scope 策略；Anti-pattern/Boundary=允许 broken-path 通过配置 downgrade 为 warn，会使 docLinks 体系失信。

### 7.3 Case 03：管理写入防误触发（Write-Intent Gate）

- 证据指针：
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-03/40-final/decision-report.md`
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-03/90-meta/requirements.md`
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-03/90-meta/trace.md`

- 输入合同：Best=把“讨论/引用触发词”与“写仓库执行命令”明确区分，并把 write intent 定义为显式授权凭据；Pragmatic=先锁定风险面（`openskills sync-*`、agents-sync 相关链路）而非泛化到所有命令；Anti-pattern/Boundary=把“提到某概念/触发词”当作写入授权，会必然误写。
- 提案轮：Best=先决定 CLI 默认行为（默认 dry-run）再补对话侧 nonce（防误触发）与回归负例（防退化）；Pragmatic=分阶段 P0/P1/P2 推进；Anti-pattern/Boundary=只做对话侧确认但 CLI 仍默认写，会被脚本/自动化绕过。
- 汇总：Best=把方案拆成“止血主干（dry-run/--apply）+ 护栏（nonce/负例回归）+ 增强（2-factor+白名单）”；Pragmatic=把 O2 协议化（Write-Intent Protocol）列为后续，不阻塞 P0；Anti-pattern/Boundary=把安全增强（2-factor）当成唯一主干会显著增加摩擦、导致绕过。
- 评审：Best=要求每次写入输出最小证据（授权来源、diff 摘要、written files）；Pragmatic=先做 stdout 证据，后续再考虑落盘；Anti-pattern/Boundary=写入无证据导致“到底写了啥/谁授权的”不可追溯。
- 最终决策：Best=默认 dry-run + 显式 `--apply`，对话侧 nonce 确认作为强建议，非交互场景引入 2-factor 与白名单；Pragmatic=保持兼容（旧行为迁移到 `--apply`）并给迁移窗口；Anti-pattern/Boundary=环境变量常开等价于永久授权，会稀释安全性（需 TTL/scope）。
- Meta：Best=requirements 把“统一写入门禁/默认只读/证据可追溯/CI 可用”写成 MUST；Pragmatic=优先把误触发用例固化为回归合同；Anti-pattern/Boundary=只写文档不做负例回归，未来极易退化。

### 7.4 Case 04：并行边界（execute-dev / manifest / swarm）

- 证据指针：
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-04/40-final/decision-report.md`
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-04/90-meta/requirements.md`
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-04/90-meta/trace.md`

- 输入合同：Best=用“同一份 manifest 的 validate=PASS 但 overlap=BLOCKED”两份机读证据把争论从口头拉回可验证；Pragmatic=证据落 `00-input/evidence/`，供后续回归；Anti-pattern/Boundary=没有样例报告时并行争论容易变成“主观判断”。
- 提案轮：Best=围绕“信号解释权（BLOCKED 是不可执行还是不可并行）”提出可判定规则；Pragmatic=将规则转为三态表述，减少歧义；Anti-pattern/Boundary=只讨论实现细节（锁/合并/worktree）而不先冻结裁决语义，执行器会分叉。
- 汇总：Best=给出 A(严格阻断)/B(三态解耦)/C(乐观并行) 并明确 B 为推荐；Pragmatic=C 作为后置演进，不阻塞；Anti-pattern/Boundary=乐观并行需要复杂锁与合并策略，审计成本高，容易失控。
- 评审：Best=强制写集合互斥“可证明”才允许并行（不确定即串行）；Pragmatic=先输出 `parallel-eligibility.json` 机读裁决，执行器只消费该裁决；Anti-pattern/Boundary=让不同入口各自解释 overlap 报告，必然产生行为漂移。
- 最终决策：Best=三态裁决 `PARALLEL_OK / SERIAL_ONLY / BLOCKED`，并明确映射：overlap→默认 SERIAL_ONLY；合同自相矛盾/强制并行失败→BLOCKED；Pragmatic=固化 preflight 顺序（validate→conflict→eligibility）；Anti-pattern/Boundary=子代理写 SSOT（Todo/gates）会造成不可审计的状态腐化。
- Meta：Best=requirements 把“可执行性 vs 可并行性解耦、SSOT 单写者、机读证据”写成 MUST；Pragmatic=提供正反例 fixtures 作为回归合同；Anti-pattern/Boundary=缺少 fixtures 时并行资格判定容易被误改。

### 7.5 Case 05：Web UAT 证据合同（Manifest Directory + Gate）

- 证据指针：
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-05/40-final/decision-report.md`
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-05/90-meta/requirements.md`
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-05/90-meta/trace.md`

- 输入合同：Best=以“历史审计反例（报告退化/丢字段）+ 现有 evidence-contract/report-template/runner”构成证据链；Pragmatic=聚焦“证据采集→索引→报告”交付层，不扩到全链路重写；Anti-pattern/Boundary=只引用模板不引用反例证据，容易低估退化风险。
- 提案轮：Best=先明确 SSOT 分工（run-bundle=执行层 SSOT；manifest=证据目录 SSOT）再扩展 schema；Pragmatic=用里程碑 v1/v1.1/v1.2 分层推进 required 集合；Anti-pattern/Boundary=一上来就做打包/checksum/HAR，全量证据会拖慢落地并引入安全风险。
- 汇总：Best=Option A'/B/C/D 对比时，把“避免双 SSOT、fail-closed、路径可迁移、默认安全”作为核心量表；Pragmatic=先补 manifest+gate，再补 fixtures 回归；Anti-pattern/Boundary=停留在 Markdown 约定（非机读）会复发“丢字段/缺证据”。
- 评审：Best=强制区分 PREVIEW_ONLY vs EXECUTED 的 required 集合，并要求 gate 可机械校验；Pragmatic=browser 证据先做摘要（console/network summary + 最少 screenshot）；Anti-pattern/Boundary=默认落全量 headers/body/cookie/token，属于高风险默认。
- 最终决策：Best=Manifest Directory + Gate（run-bundle 仍为执行 SSOT），required 缺失/绝对路径污染/报告缺段落即 FAIL；Pragmatic=分版本演进 + fixtures 回归守住不退化；Anti-pattern/Boundary=没有 schema 版本化，后续迭代会破坏兼容。
- Meta：Best=requirements 把“机读入口、完整性 gate、路径规范、默认脱敏、版本化”写成 MUST；Pragmatic=提供 preview/executed-pass/executed-fail 三类 fixture；Anti-pattern/Boundary=缺少机读合同导致报告质量不可自动回归。

### 7.6 Case 06：Mock 隔离口径漂移（MSW 三态 / Router / 合规门禁）

- 证据指针：
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-06/20-synthesis/options.md`
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-06/40-final/decision-report.md`
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-06/90-meta/requirements.md`
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-06/90-meta/trace.md`

- 输入合同：Best=把“规则/实现已三态，但开发计划传播二态”定义为“口径漂移 + 缺自动门禁”而非“缺功能”，并冻结强约束（integration/e2e/uat 必须 mock-off）；Pragmatic=给出只读复核命令与 Rubric（合规/可验证性权重高）；Anti-pattern/Boundary=不写合规底线（bypass/strict 边界）会让方案倾向“为了通过而降级”。
- 提案轮：Best=将方案拆为互补维度（入口纠偏/合同化证据/合规门禁/测试固化），并在 Round 2 用 Blocking Questions 收敛；Pragmatic=最终采用组合方案（B+C 为骨架，A+D 为增量）；Anti-pattern/Boundary=只靠文档治理、只靠 grep 门禁或只靠测试都无法覆盖“文档传播+CI 配置漂移”。
- 汇总：Best=先矩阵再阻塞问题（SSOT 放置点、门禁误报与豁免、mock-off 最小验证、证据留存）；Pragmatic=把复杂验证分层（L1 单测、L2 低频浏览器 smoke）；Anti-pattern/Boundary=把 Router 膨胀成“所有 mock 的统一执行器”会失控。
- 评审：Best=三方一致选 Composite，但产品侧强调“先入口纠偏再上强门禁”；Pragmatic=把豁免做成结构化（owner/expiresAt/scope）避免反感；Anti-pattern/Boundary=无过期豁免会变永久后门。
- 最终决策：Best=SSOT 宣告 `VITE_MSW_MODE` 单口径；integration/e2e/uat 强制 off + mock-off 验证；导入禁令（生产模块禁 msw/faker/fixtures）；证据 schema 校验与 append-only；Pragmatic=分 Phase 0~4 渐进落地；Anti-pattern/Boundary=门禁误报若无 remediation 容易诱发绕过。
- Meta：Best=requirements 把“禁止降级/禁止代码内 mock/证据链/边界 strict-bypass-off”写成 MUST/MUST NOT + 自动检查清单；Pragmatic=静态扫描+导入禁令优先，运行态验证后置；Anti-pattern/Boundary=证据不可校验或可覆盖会让审计失效。

### 7.7 Case 07：ToolInventory 契约（探测 SSOT + 服务端校验）

- 证据指针：
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-07/20-synthesis/options.md`
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-07/40-final/decision-report.md`
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-07/30-judging/verdict-qa.md`

- 输入合同：Best=选题直击“同一语义多实现（core vs device-agent）导致漂移”，并明确 authOk 语义差异会升级为 execMode=tool 的功能阻断；Pragmatic=约束“不做真实 API 调用”（仅本机命令/文件/环境变量）；Anti-pattern/Boundary=不冻结语义（authOk 到底代表什么）会让实现期反复争论。
- 提案轮：Best=把 Option A 定义为“探测 SSOT（core 复用）+ 服务端 schema/allowlist/限制”；Pragmatic=短期可 Phase 1 先复用探测、Phase 2 再补体验增强；Anti-pattern/Boundary=Option B（两边对齐但仍重复实现）只能短期止血，长期必漂移。
- 汇总：Best=把“服务端把 ToolInventory 当不可信输入”作为必选项（不是体验优化）；Pragmatic=先补最小安全基线（allowlist、长度限制、outputFormats 规范化）；Anti-pattern/Boundary=只靠客户端自觉/只做文档澄清，无法建立安全边界。
- 评审：Best=Architect/QA/Ops&Security 三方一致要求：依赖注入纯函数探测 + 服务端强校验 + 对照契约测试写入 DoD；Pragmatic=先覆盖关键字段一致性，再扩 capabilities；Anti-pattern/Boundary=把 authOk 当“key 一定有效”或落真实 API 调用，会违反约束且不稳定。
- 最终决策：Best=Option A 分阶段同里程碑可验收，验收清单 ≥10 且覆盖一致性、服务端拒绝/降级、execMode gating；Pragmatic=execPath 脱敏可后置；Anti-pattern/Boundary=服务端 silent drop（无可观测拒绝原因）会让排障变地狱。
- Meta：Best=trace 把证据路径、角色提案/评审/验收清单全部落盘，便于后续进入执行阶段；Pragmatic=验收清单是“执行阶段的 contract tests 目录”；Anti-pattern/Boundary=无验收清单会导致实现无法对齐（尤其跨 core/cli/api 三仓组件）。

### 7.8 Case 08：Readiness（包管理器冲突：pnpm vs npm lockfile）

- 证据指针：
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-08/20-synthesis/options.md`
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-08/40-final/decision-report.md`
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-08/90-meta/requirements.md`

- 输入合同：Best=把“pnpm monorepo 声明”与“package-lock.json 冲突信号”作为可复跑证据，并强制 options 同时包含“纯静态”与“运行态”方案以便对比风险；Pragmatic=运行态安装校验仅建议在 CI 干净工作区；Anti-pattern/Boundary=本地执行 `pnpm install` 会写入/下载，污染与不确定性太高。
- 提案轮：Best=将问题框定为“SSOT 判定 + 冲突集合 + 治理节奏”，而不是争论某次 install 能不能跑；Pragmatic=引入 WARN→FAIL 迁移窗口提升落地概率；Anti-pattern/Boundary=只 WARN 没 owner/期限会永久拖延。
- 汇总：Best=Hybrid（静态强约束 + CI 运行态强校验）+ 渐进收敛（Option D）；Pragmatic=冲突扫描范围默认 root scope，递归需显式开关；Anti-pattern/Boundary=Option B（运行态优先）把门禁稳定性绑到网络/权限/镜像源上。
- 评审：Best=tech 选 Hybrid，risk 倾向静态 fail-closed，execution 强调治理节奏；Pragmatic=最终折中为 Hybrid 技术方案 + 渐进治理；Anti-pattern/Boundary=没有可执行 remediation（删除冲突锁文件/迁移方案）会引发对门禁的抵触。
- 最终决策：Best=SSOT=根 `package.json.packageManager`，冲突 lockfile 集合明确，Phase 0 WARN + owner/deadline，Phase 1 FAIL；Pragmatic=CI 侧加 `pnpm install --frozen-lockfile --ignore-scripts` 作为增强；Anti-pattern/Boundary=冲突信号不唯一会让依赖图分叉且难审计。
- Meta：Best=requirements 把“SSOT、冲突集合、remediation、治理节奏”写成 MUST；Pragmatic=把“冲突消费者排查”列为执行阶段第一步；Anti-pattern/Boundary=只给结论不落“如何验证/如何迁移”会让执行阶段无从下手。

### 7.9 Case 09：Docker 探测稳健性（受限 PATH / DOCKER_CMD）

- 证据指针：
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-09/20-synthesis/options.md`
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-09/40-final/decision-report.md`
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-09/90-meta/requirements.md`

- 输入合同：Best=用“规则要求路径检测”与“实现 allowlist 不完整 + 历史日志 DOCKER_CMD=/usr/local/bin/docker”构成可验证矛盾；Pragmatic=把目标限定为探测策略（不重写 readiness/test-execution 体系）；Anti-pattern/Boundary=只说“docker 找不到”不列出 allowlist 与历史证据，会变成用户环境锅。
- 提案轮：Best=围绕“override + allowlist 扩展 + 诊断输出 + required/optional 边界”提出最小可行修复；Pragmatic=Option B（脚本 SSOT）作为后置演进；Anti-pattern/Boundary=动态扫描（find/全盘搜索）安全/性能不可控。
- 汇总：Best=Option A 作为止血主干，明确三处同步点（rules/skills/python）并列出 Blocking Questions（override 名称、校验强度、required/optional SSOT、WSL2）；Pragmatic=先把常见路径补齐（/usr/local/bin、/opt/homebrew/bin）；Anti-pattern/Boundary=只改一处导致口径漂移。
- 评审：Best=tech/risk/execution_cost 一致选 Option A，且都强调 override 安全校验与 source 标注；Pragmatic=校验匹配可宽松但必须确保命令可执行；Anti-pattern/Boundary=override 不限制绝对路径/不校验输出会有路径注入风险。
- 最终决策：Best=探测顺序契约（env override→which→known paths），失败输出 tried sources + next steps；fail-closed/warn 绑定 required/optional；Pragmatic=optional 场景仅 warn 并留证；Anti-pattern/Boundary=optional 场景也 fail-closed 会造成无谓中止。
- Meta：Best=requirements 抽取为“探测契约、override 校验、结构化诊断、required/optional 边界”；Pragmatic=建议补最小回归用例（PATH 受限但 allowlist 命中）；Anti-pattern/Boundary=缺少同步点清单会反复回归。

### 7.10 Case 10：LLM 默认路由治理（Provider/Model policy + 成本/质量护栏）

- 证据指针：
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-10/20-synthesis/options.md`
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-10/40-final/decision-report.md`
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-10/90-meta/requirements.md`

- 输入合同：Best=把“文档口径（默认 MiniMax）”与“代码现实（env auto 顺序选择）”对照，明确风险是“隐式默认导致成本/合规不可控”；Pragmatic=限定为 v0 治理（不做 catalog/能力矩阵/TTL）；Anti-pattern/Boundary=只讨论“哪个模型更好”会偏离治理问题本质。
- 提案轮：Best=给出三选项：A(现状+展示)/B(strict-only)/C(policy strict/compat) 并把“strict 默认、compat 显式 opt-in”作为收敛方向；Pragmatic=把 onboarding 与可见性作为配套，否则 strict 体验会很差；Anti-pattern/Boundary=仅加展示不改默认决策 SSOT，治理目标无法达成。
- 汇总：Best=在 options 中显式列出阻塞问题（默认 mode、policy 存储/合并、compat 迁移期、reason 审计落点、护栏字段范围）；Pragmatic=v0 先做“调用前门禁 + 审计”，自动降档后置；Anti-pattern/Boundary=policy 合并规则过早复杂化会引入新歧义。
- 评审：Best=product/tech/cost 三方一致选 Option C，且都要求 strict 作为团队默认、reason/policyVersion 必须可审计；Pragmatic=compat 保留但必须风险提示与 reason=compat_auto；Anti-pattern/Boundary=compat 长期成为默认会让治理落空。
- 最终决策：Best=引入 `LlmRoutePolicy v0` SSOT（strict/compat）、冻结覆盖优先级（CLI>session>project>global>policy>env-auto-only-compat）、preflight（allowlist+budget+pricing）可阻断、telemetry 可对账；Pragmatic=分 Phase 1~4 渐进交付与测试矩阵；Anti-pattern/Boundary=缺 price 元数据会让成本护栏失效（需 strict 默认拒绝或显式降级策略）。
- Meta：Best=requirements 抽取为“路由 policy SSOT、优先级冻结、审计字段、成本/质量护栏”四类 MUST；Pragmatic=把验收写成 strict/compat 的测试矩阵合同；Anti-pattern/Boundary=没有 reason 审计将导致“文档说一套、运行时做一套”复发。

### 7.11 Case 12：产品创意（Doctor 一键诊断：只读 + 结构化报告）

- 证据指针：
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-12/20-synthesis/options.md`
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-12/40-final/decision-report.md`
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-12/90-meta/requirements.md`
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-12/90-meta/trace.md`

- 输入合同：Best=把“入口割裂/冷启动阻塞”钉在 readiness/onboarding/config 的真实路径证据上，并把“只读/脱敏/确定性输出”写成硬约束；Pragmatic=先冻结 schema+fixtures 再接真实探测；Anti-pattern/Boundary=直接引入 `--fix` 写入能力会把讨论阶段拖入 write-intent/授权泥潭。
- 提案轮：Best=把 A(文档) B(doctor 只读) C(auto-fix) D(onboarding) 四类选项并列，且 Round 2 聚焦 schema/脱敏/next steps 的合同；Pragmatic=角色可减但必须保留 risk 视角；Anti-pattern/Boundary=只讨论 UI 文案而不冻结机读合同会导致无法回归。
- 汇总：Best=Option Cards 明确 doctor 与 readiness 的 SSOT 边界、双输出（json+md）与 fixtures；Pragmatic=v0 仅做 Top blockers+行动清单；Anti-pattern/Boundary=把 readiness 结论“渲染成文字”但不保留结构化字段会造成解释漂移。
- 评审：Best=tech/product/risk 一致 pick B，且签字条件集中在“只读/脱敏/确定性”；Pragmatic=把 profile 推断与高级参数后置；Anti-pattern/Boundary=评审不写“next validation（fixtures）”会导致执行期无基线。
- 最终决策：Best=doctor 只读聚合 + readiness 仍为依赖 SSOT；输出合同 versioned + 排序稳定；Pragmatic=先接 readiness dry-run；Anti-pattern/Boundary=把 doctor 变成“万能修复器”会引入不可控副作用。
- Meta：Best=requirements 强调单入口、SSOT 边界、脱敏、确定性与 remediation 可复跑；Pragmatic=用 fixtures 回归守住不退化；Anti-pattern/Boundary=没有脱敏回归会导致证据外泄风险。

### 7.12 Case 13：产品创意（成本透明 + 预算护栏 UX）

- 证据指针：
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-13/20-synthesis/options.md`
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-13/40-final/decision-report.md`
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-13/90-meta/requirements.md`

- 输入合同：Best=以 core 的预算/recorder/gateway 等真实路径为证据，框定为“默认可见 + 可行动 + 可审计”的体验闭环，而非“加 UI”；Pragmatic=先冻结 summary schema 与 fixtures（OK/warn/exceeded）；Anti-pattern/Boundary=把问题简化为“换模型省钱”会越权且不可审计。
- 提案轮：Best=明确 fail-closed（exceeded 必阻断）与提示行动性（current/limit/remaining+remediation），并在 Round 2 讨论噪音控制与关闭开关；Pragmatic=v0 不做跨 provider/model 的降档建议；Anti-pattern/Boundary=没有单一生成点（DTO/渲染复用）会导致 CLI/TUI/API 漂移。
- 汇总：Best=Composite（D 骨架：`cost-summary.json` 合同化 + preflight）+（B 体验：默认展示可关闭）；Pragmatic=把 pricing missing 作为显式原因而非静默误算；Anti-pattern/Boundary=只做“展示”而不冻结机读合同，回归与对账无法成立。
- 评审：Best=cost/product/tech 对齐“可审计合同 + 可行动提示 + 噪音控制”；Pragmatic=将仪表盘后置；Anti-pattern/Boundary=评审不写“关闭开关/CI 场景”会导致落地阻力。
- 最终决策：Best=`cost-summary.json` v1 作为 SSOT，exceeded fail-closed、warning 强提示；Pragmatic=默认展示频率先从任务结束/会话退出做起；Anti-pattern/Boundary=缺少脱敏边界会把 key/baseURL/绝对路径带入报告。
- Meta：Best=requirements 抽取默认可见、行动性、机读合同与 fail-closed 边界；Pragmatic=fixtures 做回归断言；Anti-pattern/Boundary=没有 pricing 缺失解释会削弱成本可信度。

### 7.13 Case 14：产品创意（Review Pack：单包证据分享 + 默认安全）

- 证据指针：
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-14/40-final/decision-report.md`
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-14/90-meta/requirements.md`

- 输入合同：Best=把需求写成“异步协作的单包证据形态”，并冻结高风险默认（脱敏、secrets 扫描 gate、绝对路径禁止）；Pragmatic=v1 只做目录型 pack，不做 zip/checksum；Anti-pattern/Boundary=默认收集全量日志/截图会立即触发隐私与体积风险。
- 提案轮：Best=围绕 manifest/README 的最小合同、adapter 复用、复制策略（小文件复制/大文件引用）发散并在 Round 2 收敛；Pragmatic=先支持 1 条主链路（UAT Web）验证价值；Anti-pattern/Boundary=先做远端上传平台会把合规/权限复杂度拉爆。
- 汇总：Best=Option B（目录型 pack）作为主干，明确 gate 触发条件（required/绝对路径/敏感词命中 fail-closed）；Pragmatic=把 zip/checksum 明确为 v2+；Anti-pattern/Boundary=没有 adapter registry 与版本化会导致各流程格式漂移。
- 评审：Best=risk 强签字条件（敏感模式命中直接 FAIL、高风险 artifacts 默认禁）；Pragmatic=README 固定段落降低阅读成本；Anti-pattern/Boundary=评审只谈“好分享”不谈默认安全，必然泄漏。
- 最终决策：Best=manifest+README 作为单入口、默认安全、跨流程 adapter 映射；Pragmatic=v1 仅复制小文件、引用大文件；Anti-pattern/Boundary=把 pack 做成“全量自包含”会导致风险与成本失控。
- Meta：Best=requirements 把 manifest schema 版本化、gate、默认安全、跨流程复用写成 MUST；Pragmatic=fixtures（preview/executed/fail）做回归；Anti-pattern/Boundary=没有 secrets 扫描回归会让 pack 成为泄漏载体。

### 7.14 Case 15：架构决策（EvidenceRoot v1：统一索引 + append-only）

- 证据指针：
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-15/40-final/decision-report.md`
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-15/90-meta/requirements.md`

- 输入合同：Best=把问题锚定在“多流程证据无法复用/覆盖风险/泄漏风险难控”，并以现有 runner/gate 真实路径为证据；Pragmatic=只做 v1 最小合同（index.jsonl + gates + append-only）；Anti-pattern/Boundary=先做共享 SDK/DB 会把讨论拖向实现载体而非合同。
- 提案轮：Best=明确 EvidenceRoot 与各流程内部 SSOT 的边界（不替代 run-bundle/report），并提出唯一键覆盖检测；Pragmatic=先接入两条主链路验证一致性；Anti-pattern/Boundary=不定义覆盖禁止会导致并行写入不可审计。
- 汇总：Best=Option B（统一合同）作为推荐，Blocking Questions 聚焦 event schema/唯一键/gate 集合；Pragmatic=required/optional 分层避免 gate 过严；Anti-pattern/Boundary=只写“约定”不产出机读 index，会复发格式漂移。
- 评审：Best=评审把“append-only/覆盖禁止/绝对路径检测”写成签字条件；Pragmatic=sha256 后置；Anti-pattern/Boundary=评审不要求 fixtures，会导致迁移无法回归。
- 最终决策：Best=EvidenceRoot v1（index.jsonl 事件流 + gates）+ 覆盖禁止；Pragmatic=渐进接入与 adapter；Anti-pattern/Boundary=让各流程各写各的会持续漂移。
- Meta：Best=requirements 强调统一索引、覆盖禁止、最小 gate、SSOT 边界；Pragmatic=每流程 PASS/FAIL fixtures；Anti-pattern/Boundary=无覆盖检测会让证据被无意覆盖。

### 7.15 Case 16：架构决策（Config Protocol v1：strict/compat + Resolution Report）

- 证据指针：
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-16/40-final/decision-report.md`
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-16/90-meta/requirements.md`

- 输入合同：Best=以 core loader/schema 与 CLI config 命令为证据，把问题表述为“优先级协议缺失 + effective config 不可审计”，而不是“加一个打印命令”；Pragmatic=先交付 effective 展示止血；Anti-pattern/Boundary=只写文档无法阻止覆盖顺序漂移。
- 提案轮：Best=把优先级冻结、合并语义冻结、strict/compat 分级与 `config-resolution.json`（sources/warnings/effective 脱敏）作为一体化方案；Pragmatic=sources 先覆盖高风险字段渐进扩面；Anti-pattern/Boundary=strict-only 直接上会破坏依赖 env 的用法，落地阻力大。
- 汇总：Best=Option D（strict/compat + resolution report）收敛，并把 allowlist/迁移窗口写进阻塞问题；Pragmatic=先输出 warnings + remediation；Anti-pattern/Boundary=不输出 sources 会让审计仍然猜测。
- 评审：Best=tech/risk/cost 共同要求 strict 默认、compat 显式 opt-in；Pragmatic=compat 保留但必须可审计并提示风险；Anti-pattern/Boundary=让 env 任意覆盖会把治理目标打回原形。
- 最终决策：Best=冻结 precedence 与 merge 语义，输出脱敏 resolution report（effective/sources/warnings）；Pragmatic=Phase 0 先止血、Phase 1 加模式、Phase 2 扩 sources；Anti-pattern/Boundary=不做脱敏会泄漏 apiKeys。
- Meta：Best=requirements 抽取为“协议冻结/分级治理/report/脱敏”，并用 fixtures 矩阵验收 precedence；Pragmatic=高风险字段先覆盖；Anti-pattern/Boundary=没有 fixtures 会导致 precedence 回归。

### 7.16 Case 17：架构决策（Resumable Task：状态机 + ledger + SSOT 单写者）

- 证据指针：
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-17/40-final/decision-report.md`
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-17/90-meta/requirements.md`

- 输入合同：Best=以 resumable-task 规则与脚本为证据，把问题锚定在“并行/多轮续跑的歧义与不可审计”，并冻结“机读状态机 + ledger + 单写者协议”；Pragmatic=先做 schema+负例 fixtures；Anti-pattern/Boundary=只靠人工纪律无法覆盖并行边界。
- 提案轮：Best=把状态机字段、三态 decide 输出、ledger 事件流与 gate 组合成最小闭环；Pragmatic=worktree 隔离作为后置增强；Anti-pattern/Boundary=并行推进 SSOT 状态会造成不可回放腐化。
- 汇总：Best=Option B（状态机+ledger）为主干，Blocking Questions 聚焦 active pointer/锁/脱敏；Pragmatic=先覆盖 2 个 surface（execute-dev + resumable-task）；Anti-pattern/Boundary=引入 DB 违背约束且增加运维成本。
- 评审：Best=把“负例回归（active pointer 缺失/指向不存在/并发写 SSOT）必须稳定 FAIL”写成签字条件；Pragmatic=状态推进串行、执行可并行；Anti-pattern/Boundary=评审不落负例，后续极易退化。
- 最终决策：Best=状态机 v1 + ledger.jsonl append-only + SSOT 单写者；Pragmatic=文件锁/串行化保证；Anti-pattern/Boundary=让子进程写 todo/active pointer 会破坏 SSOT。
- Meta：Best=requirements 以负例回归为核心；Pragmatic=从 ledger 回放进度作为验收；Anti-pattern/Boundary=没有 ledger 将无法解释“为什么续跑到这里”。

### 7.17 Case 18：写作创意（一页纸 Quickstart：双轨结构 + 写作护栏）

- 证据指针：
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-18/20-synthesis/options.md`
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-18/40-final/decision-report.md`
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-18/90-meta/requirements.md`

- 输入合同：Best=把“2 分钟读懂/首次成功闭环”写成可验收目标，并引用 `CLAUDE.md` 与文档规则作为 SSOT；Pragmatic=只冻结最少链接候选与 SAFE 边界；Anti-pattern/Boundary=不写“禁止修改受管理文档”会把写作讨论拖入执行阶段。
- 提案轮：Best=product（四问）、architect（心智模型）、implementation（命令块合同）、qa（可测验收）、ops_security（默认安全）五视角覆盖全面；Pragmatic=Round 2 聚焦链接预算/稳定标题/非 TUI 路径等阻塞点；Anti-pattern/Boundary=只堆命令或只讲愿景都会失败。
- 汇总：Best=Option C（双轨一页纸）并显式吸收护栏（链接预算、SAFE/DANGEROUS、稳定标题/块）；Pragmatic=先冻结结构合同再写正文；Anti-pattern/Boundary=链接洪泛会把一页纸变成目录页。
- 评审：Best=tech/product/risk 一致选择双轨，并把“扫描/回归可行”作为签字条件；Pragmatic=把非 TUI 等价路径作为 open question；Anti-pattern/Boundary=评审不写验证方式会造成文案争论。
- 最终决策：Best=双轨结构 + 预算化写作 + 默认安全；Pragmatic=只读命令为首次成功路径；Anti-pattern/Boundary=提供危险写操作命令会造成误触发风险。
- Meta：Best=requirements 强调链接预算/稳定合同/安全默认；Pragmatic=静态扫描标题/命令块；Anti-pattern/Boundary=不做扫描回归会快速漂移。

### 7.18 Case 19：写作创意（决策型文档模板：双视图 + strict/compat + 可机读附录）

- 证据指针：
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-19/20-synthesis/options.md`
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-19/40-final/decision-report.md`
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-19/90-meta/requirements.md`

- 输入合同：Best=把“决策可回放/可审计/可机读”写成成功标准，并引用 docLinks 与文档规则作为约束；Pragmatic=先给模板合同不落地到 docs；Anti-pattern/Boundary=把模板做成目录型会过重且降低采用率。
- 提案轮：Best=读者效率（product）与审计完整（architect/qa/security）与机读自动化（implementation）形成张力，促成双视图与模式化分级；Pragmatic=Round 2 讨论 strict/compat 与反臃肿；Anti-pattern/Boundary=一上来强制 YAML 会降低采用率。
- 汇总：Best=Option B（机读附录）+ Option C（双视图）组合，并把 strict/compat 作为落地策略；Pragmatic=compat 必须显式标注；Anti-pattern/Boundary=compat 默默成为默认会让模板退化。
- 评审：Best=tech/product/execution 给出不同优先级，最终路线是“先采用率，再升级自动化”；Pragmatic=定义升级触发条件；Anti-pattern/Boundary=没有一致性检查会导致 Reader/Auditor 自相矛盾。
- 最终决策：Best=稳定标题 + 双视图 + strict/compat + 可选 `decision-pack.yaml`；Pragmatic=先落最小必填字段；Anti-pattern/Boundary=模板复杂到作者绕过则失效。
- Meta：Best=requirements 抽取稳定结构约束、分级治理、证据指针分级；Pragmatic=先覆盖高价值字段；Anti-pattern/Boundary=强制复制敏感证据进正文有泄漏风险。

### 7.19 Case 20：写作创意（指令型文档防误触发：Execution Intent + 标签 + 门禁）

- 证据指针：
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-20/20-synthesis/options.md`
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-20/40-final/decision-report.md`
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-20/90-meta/requirements.md`

- 输入合同：Best=把“示例被误当授权”的风险钉在 execute-development/docker-path/mock-isolation 等真实规则证据上；Pragmatic=先定义写作合同与接口点，不实现扫描器；Anti-pattern/Boundary=只靠文案提示无法覆盖自动执行场景。
- 提案轮：Best=意图协议（architect）+ 最小语法（implementation）+ 负例回归（qa）+ 危险域隔离（security）形成互补；Pragmatic=Round 2 补迁移路线图与高风险 token；Anti-pattern/Boundary=标签集合过多会失控。
- 汇总：Best=Option C（标签语法 + 扫描门禁）为默认，并把 compat 迁移与白名单到期写入方案；Pragmatic=从高收益低误报规则开始（无标签命令块/裸 docker）；Anti-pattern/Boundary=Phase 1 永远不结束会长期不安全。
- 评审：Best=risk 强调 fail-closed + token；product 强调渐进；tech 选择门禁为主；Pragmatic=明确 Phase 2 截止日期与 owner；Anti-pattern/Boundary=无截止日期会拖延。
- 最终决策：Best=Execution Intent + 命令块标签 + 门禁；高风险可加 token；Pragmatic=先 warning→再 fail-closed；Anti-pattern/Boundary=在规范阶段输出可执行危险命令序列会制造新风险。
- Meta：Best=requirements 强调“意图与授权分离、可扫描结构、fail-closed”；Pragmatic=兼容迁移机制；Anti-pattern/Boundary=允许通过删标签绕过会破坏治理。

### 7.20 Case 21：内容类型实证（Spec：技术规格/接口契约/数据模型）

- 证据指针：
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-21/20-synthesis/options.md`
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-21/40-final/decision-report.md`
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-21/90-meta/requirements.md`
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-21/90-meta/trace.md`

- 输入合同：Best=把“研发/创意/企业市场”三域需求同时冻结为可裁决对象，并用 repo 内真实路径证据限定边界；同时把该内容类型的失败模式写成约束（schema/examples 机读合同 + strict/compat + breaking change gate）；Pragmatic=先冻结最小必填字段与风险底线，再把增强点放入 Should；Anti-pattern/Boundary=只给愿景不冻结证据/验收，评审只能投票。
- 提案轮：Best=五视角覆盖采用率/SSOT/机读/验收/安全边界，并在 Round 2 仅回答阻塞问题；Pragmatic=角色数可减但必须保留 risk/ops_security（内容型风险更依赖该视角）；Anti-pattern/Boundary=提案互相引用或提前收敛导致同质化。
- 汇总：Best=Option Cards + 对比矩阵 + Blocking Questions，把“schema/examples 机读合同 + strict/compat + breaking change gate”显式写入候选差异，并把组合方案（Composite）作为一等公民；Pragmatic=短名单可接受，但必须写清拒绝理由与迁移路线图；Anti-pattern/Boundary=没有阻塞问题清单会导致执行期发现关键缺口。
- 评审：Best=tech/product/risk verdict 都写 pick+confidence+tradeoffs+top risks+next validation，并把签字条件/DoD 作为核心产物；Pragmatic=≥3 份 verdict 足够但必须含 risk；Anti-pattern/Boundary=只表态不写条件会把风险推迟到执行期爆雷。
- 最终决策：Best=冻结该内容类型 profile（Must/Should/Fail-closed gates/Acceptance checklist），把最小机读落点与默认安全边界写清；Pragmatic=给 warning→fail-closed 迁移与白名单到期；Anti-pattern/Boundary=compat 默默成为默认会让治理落空。
- Meta：Best=requirements 抽取 profile 装配、证据指针、分级治理与不可退化边界；Pragmatic=先把最关键 5 条 MUST 写清；Anti-pattern/Boundary=缺 trace 会导致“为何如此选”不可复盘。

### 7.21 Case 22：内容类型实证（ADR：选型/权衡/决策记录）

- 证据指针：
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-22/20-synthesis/options.md`
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-22/40-final/decision-report.md`
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-22/90-meta/requirements.md`
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-22/90-meta/trace.md`

- 输入合同：Best=把“研发/创意/企业市场”三域需求同时冻结为可裁决对象，并用 repo 内真实路径证据限定边界；同时把该内容类型的失败模式写成约束（trade-offs/拒绝理由 + revisit triggers + strict/compat）；Pragmatic=先冻结最小必填字段与风险底线，再把增强点放入 Should；Anti-pattern/Boundary=只给愿景不冻结证据/验收，评审只能投票。
- 提案轮：Best=五视角覆盖采用率/SSOT/机读/验收/安全边界，并在 Round 2 仅回答阻塞问题；Pragmatic=角色数可减但必须保留 risk/ops_security（内容型风险更依赖该视角）；Anti-pattern/Boundary=提案互相引用或提前收敛导致同质化。
- 汇总：Best=Option Cards + 对比矩阵 + Blocking Questions，把“trade-offs/拒绝理由 + revisit triggers + strict/compat”显式写入候选差异，并把组合方案（Composite）作为一等公民；Pragmatic=短名单可接受，但必须写清拒绝理由与迁移路线图；Anti-pattern/Boundary=没有阻塞问题清单会导致执行期发现关键缺口。
- 评审：Best=tech/product/risk verdict 都写 pick+confidence+tradeoffs+top risks+next validation，并把签字条件/DoD 作为核心产物；Pragmatic=≥3 份 verdict 足够但必须含 risk；Anti-pattern/Boundary=只表态不写条件会把风险推迟到执行期爆雷。
- 最终决策：Best=冻结该内容类型 profile（Must/Should/Fail-closed gates/Acceptance checklist），把最小机读落点与默认安全边界写清；Pragmatic=给 warning→fail-closed 迁移与白名单到期；Anti-pattern/Boundary=compat 默默成为默认会让治理落空。
- Meta：Best=requirements 抽取 profile 装配、证据指针、分级治理与不可退化边界；Pragmatic=先把最关键 5 条 MUST 写清；Anti-pattern/Boundary=缺 trace 会导致“为何如此选”不可复盘。

### 7.22 Case 23：内容类型实证（Plan：交付计划/里程碑/排期）

- 证据指针：
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-23/20-synthesis/options.md`
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-23/40-final/decision-report.md`
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-23/90-meta/requirements.md`
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-23/90-meta/trace.md`

- 输入合同：Best=把“研发/创意/企业市场”三域需求同时冻结为可裁决对象，并用 repo 内真实路径证据限定边界；同时把该内容类型的失败模式写成约束（阶段门禁 + 并行资格机读裁决 + required/optional）；Pragmatic=先冻结最小必填字段与风险底线，再把增强点放入 Should；Anti-pattern/Boundary=只给愿景不冻结证据/验收，评审只能投票。
- 提案轮：Best=五视角覆盖采用率/SSOT/机读/验收/安全边界，并在 Round 2 仅回答阻塞问题；Pragmatic=角色数可减但必须保留 risk/ops_security（内容型风险更依赖该视角）；Anti-pattern/Boundary=提案互相引用或提前收敛导致同质化。
- 汇总：Best=Option Cards + 对比矩阵 + Blocking Questions，把“阶段门禁 + 并行资格机读裁决 + required/optional”显式写入候选差异，并把组合方案（Composite）作为一等公民；Pragmatic=短名单可接受，但必须写清拒绝理由与迁移路线图；Anti-pattern/Boundary=没有阻塞问题清单会导致执行期发现关键缺口。
- 评审：Best=tech/product/risk verdict 都写 pick+confidence+tradeoffs+top risks+next validation，并把签字条件/DoD 作为核心产物；Pragmatic=≥3 份 verdict 足够但必须含 risk；Anti-pattern/Boundary=只表态不写条件会把风险推迟到执行期爆雷。
- 最终决策：Best=冻结该内容类型 profile（Must/Should/Fail-closed gates/Acceptance checklist），把最小机读落点与默认安全边界写清；Pragmatic=给 warning→fail-closed 迁移与白名单到期；Anti-pattern/Boundary=compat 默默成为默认会让治理落空。
- Meta：Best=requirements 抽取 profile 装配、证据指针、分级治理与不可退化边界；Pragmatic=先把最关键 5 条 MUST 写清；Anti-pattern/Boundary=缺 trace 会导致“为何如此选”不可复盘。

### 7.23 Case 24：内容类型实证（QA/Audit：测试/验收/审计报告）

- 证据指针：
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-24/20-synthesis/options.md`
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-24/40-final/decision-report.md`
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-24/90-meta/requirements.md`
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-24/90-meta/trace.md`

- 输入合同：Best=把“研发/创意/企业市场”三域需求同时冻结为可裁决对象，并用 repo 内真实路径证据限定边界；同时把该内容类型的失败模式写成约束（evidence manifest + 默认脱敏 + 负例 fixtures）；Pragmatic=先冻结最小必填字段与风险底线，再把增强点放入 Should；Anti-pattern/Boundary=只给愿景不冻结证据/验收，评审只能投票。
- 提案轮：Best=五视角覆盖采用率/SSOT/机读/验收/安全边界，并在 Round 2 仅回答阻塞问题；Pragmatic=角色数可减但必须保留 risk/ops_security（内容型风险更依赖该视角）；Anti-pattern/Boundary=提案互相引用或提前收敛导致同质化。
- 汇总：Best=Option Cards + 对比矩阵 + Blocking Questions，把“evidence manifest + 默认脱敏 + 负例 fixtures”显式写入候选差异，并把组合方案（Composite）作为一等公民；Pragmatic=短名单可接受，但必须写清拒绝理由与迁移路线图；Anti-pattern/Boundary=没有阻塞问题清单会导致执行期发现关键缺口。
- 评审：Best=tech/product/risk verdict 都写 pick+confidence+tradeoffs+top risks+next validation，并把签字条件/DoD 作为核心产物；Pragmatic=≥3 份 verdict 足够但必须含 risk；Anti-pattern/Boundary=只表态不写条件会把风险推迟到执行期爆雷。
- 最终决策：Best=冻结该内容类型 profile（Must/Should/Fail-closed gates/Acceptance checklist），把最小机读落点与默认安全边界写清；Pragmatic=给 warning→fail-closed 迁移与白名单到期；Anti-pattern/Boundary=compat 默默成为默认会让治理落空。
- Meta：Best=requirements 抽取 profile 装配、证据指针、分级治理与不可退化边界；Pragmatic=先把最关键 5 条 MUST 写清；Anti-pattern/Boundary=缺 trace 会导致“为何如此选”不可复盘。

### 7.24 Case 25：内容类型实证（Ops/Incident：运维/事故响应/复盘）

- 证据指针：
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-25/20-synthesis/options.md`
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-25/40-final/decision-report.md`
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-25/90-meta/requirements.md`
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-25/90-meta/trace.md`

- 输入合同：Best=把“研发/创意/企业市场”三域需求同时冻结为可裁决对象，并用 repo 内真实路径证据限定边界；同时把该内容类型的失败模式写成约束（Execution Intent + Danger Zone token + timeline/证据指针）；Pragmatic=先冻结最小必填字段与风险底线，再把增强点放入 Should；Anti-pattern/Boundary=只给愿景不冻结证据/验收，评审只能投票。
- 提案轮：Best=五视角覆盖采用率/SSOT/机读/验收/安全边界，并在 Round 2 仅回答阻塞问题；Pragmatic=角色数可减但必须保留 risk/ops_security（内容型风险更依赖该视角）；Anti-pattern/Boundary=提案互相引用或提前收敛导致同质化。
- 汇总：Best=Option Cards + 对比矩阵 + Blocking Questions，把“Execution Intent + Danger Zone token + timeline/证据指针”显式写入候选差异，并把组合方案（Composite）作为一等公民；Pragmatic=短名单可接受，但必须写清拒绝理由与迁移路线图；Anti-pattern/Boundary=没有阻塞问题清单会导致执行期发现关键缺口。
- 评审：Best=tech/product/risk verdict 都写 pick+confidence+tradeoffs+top risks+next validation，并把签字条件/DoD 作为核心产物；Pragmatic=≥3 份 verdict 足够但必须含 risk；Anti-pattern/Boundary=只表态不写条件会把风险推迟到执行期爆雷。
- 最终决策：Best=冻结该内容类型 profile（Must/Should/Fail-closed gates/Acceptance checklist），把最小机读落点与默认安全边界写清；Pragmatic=给 warning→fail-closed 迁移与白名单到期；Anti-pattern/Boundary=compat 默默成为默认会让治理落空。
- Meta：Best=requirements 抽取 profile 装配、证据指针、分级治理与不可退化边界；Pragmatic=先把最关键 5 条 MUST 写清；Anti-pattern/Boundary=缺 trace 会导致“为何如此选”不可复盘。

### 7.25 Case 26：内容类型实证（Security/Compliance：安全/合规评估）

- 证据指针：
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-26/20-synthesis/options.md`
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-26/40-final/decision-report.md`
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-26/90-meta/requirements.md`
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-26/90-meta/trace.md`

- 输入合同：Best=把“研发/创意/企业市场”三域需求同时冻结为可裁决对象，并用 repo 内真实路径证据限定边界；同时把该内容类型的失败模式写成约束（controls→gate + restricted 指针 + claim→evidence）；Pragmatic=先冻结最小必填字段与风险底线，再把增强点放入 Should；Anti-pattern/Boundary=只给愿景不冻结证据/验收，评审只能投票。
- 提案轮：Best=五视角覆盖采用率/SSOT/机读/验收/安全边界，并在 Round 2 仅回答阻塞问题；Pragmatic=角色数可减但必须保留 risk/ops_security（内容型风险更依赖该视角）；Anti-pattern/Boundary=提案互相引用或提前收敛导致同质化。
- 汇总：Best=Option Cards + 对比矩阵 + Blocking Questions，把“controls→gate + restricted 指针 + claim→evidence”显式写入候选差异，并把组合方案（Composite）作为一等公民；Pragmatic=短名单可接受，但必须写清拒绝理由与迁移路线图；Anti-pattern/Boundary=没有阻塞问题清单会导致执行期发现关键缺口。
- 评审：Best=tech/product/risk verdict 都写 pick+confidence+tradeoffs+top risks+next validation，并把签字条件/DoD 作为核心产物；Pragmatic=≥3 份 verdict 足够但必须含 risk；Anti-pattern/Boundary=只表态不写条件会把风险推迟到执行期爆雷。
- 最终决策：Best=冻结该内容类型 profile（Must/Should/Fail-closed gates/Acceptance checklist），把最小机读落点与默认安全边界写清；Pragmatic=给 warning→fail-closed 迁移与白名单到期；Anti-pattern/Boundary=compat 默默成为默认会让治理落空。
- Meta：Best=requirements 抽取 profile 装配、证据指针、分级治理与不可退化边界；Pragmatic=先把最关键 5 条 MUST 写清；Anti-pattern/Boundary=缺 trace 会导致“为何如此选”不可复盘。

### 7.26 Case 27：内容类型实证（Analytics：指标/实验/分析报告）

- 证据指针：
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-27/20-synthesis/options.md`
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-27/40-final/decision-report.md`
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-27/90-meta/requirements.md`
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-27/90-meta/trace.md`

- 输入合同：Best=把“研发/创意/企业市场”三域需求同时冻结为可裁决对象，并用 repo 内真实路径证据限定边界；同时把该内容类型的失败模式写成约束（metrics 口径冻结（metricVersion）+ query pointers(restricted) + next steps）；Pragmatic=先冻结最小必填字段与风险底线，再把增强点放入 Should；Anti-pattern/Boundary=只给愿景不冻结证据/验收，评审只能投票。
- 提案轮：Best=五视角覆盖采用率/SSOT/机读/验收/安全边界，并在 Round 2 仅回答阻塞问题；Pragmatic=角色数可减但必须保留 risk/ops_security（内容型风险更依赖该视角）；Anti-pattern/Boundary=提案互相引用或提前收敛导致同质化。
- 汇总：Best=Option Cards + 对比矩阵 + Blocking Questions，把“metrics 口径冻结（metricVersion）+ query pointers(restricted) + next steps”显式写入候选差异，并把组合方案（Composite）作为一等公民；Pragmatic=短名单可接受，但必须写清拒绝理由与迁移路线图；Anti-pattern/Boundary=没有阻塞问题清单会导致执行期发现关键缺口。
- 评审：Best=tech/product/risk verdict 都写 pick+confidence+tradeoffs+top risks+next validation，并把签字条件/DoD 作为核心产物；Pragmatic=≥3 份 verdict 足够但必须含 risk；Anti-pattern/Boundary=只表态不写条件会把风险推迟到执行期爆雷。
- 最终决策：Best=冻结该内容类型 profile（Must/Should/Fail-closed gates/Acceptance checklist），把最小机读落点与默认安全边界写清；Pragmatic=给 warning→fail-closed 迁移与白名单到期；Anti-pattern/Boundary=compat 默默成为默认会让治理落空。
- Meta：Best=requirements 抽取 profile 装配、证据指针、分级治理与不可退化边界；Pragmatic=先把最关键 5 条 MUST 写清；Anti-pattern/Boundary=缺 trace 会导致“为何如此选”不可复盘。

### 7.27 Case 28：内容类型实证（External Comms：对外材料）

- 证据指针：
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-28/20-synthesis/options.md`
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-28/40-final/decision-report.md`
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-28/90-meta/requirements.md`
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-28/90-meta/trace.md`

- 输入合同：Best=把“研发/创意/企业市场”三域需求同时冻结为可裁决对象，并用 repo 内真实路径证据限定边界；同时把该内容类型的失败模式写成约束（claim→evidence + approvers/expiry/scope + 未批准承诺 fail-closed）；Pragmatic=先冻结最小必填字段与风险底线，再把增强点放入 Should；Anti-pattern/Boundary=只给愿景不冻结证据/验收，评审只能投票。
- 提案轮：Best=五视角覆盖采用率/SSOT/机读/验收/安全边界，并在 Round 2 仅回答阻塞问题；Pragmatic=角色数可减但必须保留 risk/ops_security（内容型风险更依赖该视角）；Anti-pattern/Boundary=提案互相引用或提前收敛导致同质化。
- 汇总：Best=Option Cards + 对比矩阵 + Blocking Questions，把“claim→evidence + approvers/expiry/scope + 未批准承诺 fail-closed”显式写入候选差异，并把组合方案（Composite）作为一等公民；Pragmatic=短名单可接受，但必须写清拒绝理由与迁移路线图；Anti-pattern/Boundary=没有阻塞问题清单会导致执行期发现关键缺口。
- 评审：Best=tech/product/risk verdict 都写 pick+confidence+tradeoffs+top risks+next validation，并把签字条件/DoD 作为核心产物；Pragmatic=≥3 份 verdict 足够但必须含 risk；Anti-pattern/Boundary=只表态不写条件会把风险推迟到执行期爆雷。
- 最终决策：Best=冻结该内容类型 profile（Must/Should/Fail-closed gates/Acceptance checklist），把最小机读落点与默认安全边界写清；Pragmatic=给 warning→fail-closed 迁移与白名单到期；Anti-pattern/Boundary=compat 默默成为默认会让治理落空。
- Meta：Best=requirements 抽取 profile 装配、证据指针、分级治理与不可退化边界；Pragmatic=先把最关键 5 条 MUST 写清；Anti-pattern/Boundary=缺 trace 会导致“为何如此选”不可复盘。

### 7.28 Case 29：内容类型实证（Creative Production：创意 Brief/脚本/指引）

- 证据指针：
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-29/20-synthesis/options.md`
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-29/40-final/decision-report.md`
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-29/90-meta/requirements.md`
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-29/90-meta/trace.md`

- 输入合同：Best=把“研发/创意/企业市场”三域需求同时冻结为可裁决对象，并用 repo 内真实路径证据限定边界；同时把该内容类型的失败模式写成约束（brief 必填 + deliverables manifest + Do-Not/授权 fail-closed）；Pragmatic=先冻结最小必填字段与风险底线，再把增强点放入 Should；Anti-pattern/Boundary=只给愿景不冻结证据/验收，评审只能投票。
- 提案轮：Best=五视角覆盖采用率/SSOT/机读/验收/安全边界，并在 Round 2 仅回答阻塞问题；Pragmatic=角色数可减但必须保留 risk/ops_security（内容型风险更依赖该视角）；Anti-pattern/Boundary=提案互相引用或提前收敛导致同质化。
- 汇总：Best=Option Cards + 对比矩阵 + Blocking Questions，把“brief 必填 + deliverables manifest + Do-Not/授权 fail-closed”显式写入候选差异，并把组合方案（Composite）作为一等公民；Pragmatic=短名单可接受，但必须写清拒绝理由与迁移路线图；Anti-pattern/Boundary=没有阻塞问题清单会导致执行期发现关键缺口。
- 评审：Best=tech/product/risk verdict 都写 pick+confidence+tradeoffs+top risks+next validation，并把签字条件/DoD 作为核心产物；Pragmatic=≥3 份 verdict 足够但必须含 risk；Anti-pattern/Boundary=只表态不写条件会把风险推迟到执行期爆雷。
- 最终决策：Best=冻结该内容类型 profile（Must/Should/Fail-closed gates/Acceptance checklist），把最小机读落点与默认安全边界写清；Pragmatic=给 warning→fail-closed 迁移与白名单到期；Anti-pattern/Boundary=compat 默默成为默认会让治理落空。
- Meta：Best=requirements 抽取 profile 装配、证据指针、分级治理与不可退化边界；Pragmatic=先把最关键 5 条 MUST 写清；Anti-pattern/Boundary=缺 trace 会导致“为何如此选”不可复盘。

### 7.29 Case 30：内容类型实证（Enablement：培训/知识库）

- 证据指针：
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-30/20-synthesis/options.md`
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-30/40-final/decision-report.md`
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-30/90-meta/requirements.md`
  - `docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-30/90-meta/trace.md`

- 输入合同：Best=把“研发/创意/企业市场”三域需求同时冻结为可裁决对象，并用 repo 内真实路径证据限定边界；同时把该内容类型的失败模式写成约束（双轨+SAFE/DANGEROUS 标签+链接预算+版本漂移回归）；Pragmatic=先冻结最小必填字段与风险底线，再把增强点放入 Should；Anti-pattern/Boundary=只给愿景不冻结证据/验收，评审只能投票。
- 提案轮：Best=五视角覆盖采用率/SSOT/机读/验收/安全边界，并在 Round 2 仅回答阻塞问题；Pragmatic=角色数可减但必须保留 risk/ops_security（内容型风险更依赖该视角）；Anti-pattern/Boundary=提案互相引用或提前收敛导致同质化。
- 汇总：Best=Option Cards + 对比矩阵 + Blocking Questions，把“双轨+SAFE/DANGEROUS 标签+链接预算+版本漂移回归”显式写入候选差异，并把组合方案（Composite）作为一等公民；Pragmatic=短名单可接受，但必须写清拒绝理由与迁移路线图；Anti-pattern/Boundary=没有阻塞问题清单会导致执行期发现关键缺口。
- 评审：Best=tech/product/risk verdict 都写 pick+confidence+tradeoffs+top risks+next validation，并把签字条件/DoD 作为核心产物；Pragmatic=≥3 份 verdict 足够但必须含 risk；Anti-pattern/Boundary=只表态不写条件会把风险推迟到执行期爆雷。
- 最终决策：Best=冻结该内容类型 profile（Must/Should/Fail-closed gates/Acceptance checklist），把最小机读落点与默认安全边界写清；Pragmatic=给 warning→fail-closed 迁移与白名单到期；Anti-pattern/Boundary=compat 默默成为默认会让治理落空。
- Meta：Best=requirements 抽取 profile 装配、证据指针、分级治理与不可退化边界；Pragmatic=先把最关键 5 条 MUST 写清；Anti-pattern/Boundary=缺 trace 会导致“为何如此选”不可复盘。

## 8. 环节级通用结论（从 Case 01–10, 12–30 横向抽取）

### 8.1 输入合同（00-input/input.md）：把问题变成“可裁决对象”

- Best
  - **最小可验收结构**：Problem / Evidence(≥2 repo 路径) / Constraints / Success / Non-Goals / Rubric。
  - **证据可复跑**：给出只读复核命令或机读样例（Case 02/04 的 scan 输出与 cat-file/报告样例效果最好）。
  - **边界先行**：提前写出 fail-closed 底线（Case 06 合规、Case 09 required/optional、Case 10 strict 默认）。
- Pragmatic
  - 不确定信息用“假设分支”标注 DRAFT，允许在 Round 2 作为 Blocking Questions 逐条回答。
- Anti-pattern/Boundary
  - 没有 Non-Goals → scope creep；没有证据路径 → 空谈；证据不可复跑 → 评审只能“投票”。

### 8.2 提案轮（10-ideation）：先发散，再允许“受约束的收敛”

- Best
  - **独立写作**：每个角色先独立成稿，再汇总（多案 trace 明确强调）。
  - **角色目标函数**：产品/架构/实现/QA/风控（或等价集合）必须覆盖“可落地/可验证/风险边界”。
  - **Round 2 的正确用法**：围绕 Blocking Questions 收敛，而不是“重新发散”。
- Pragmatic
  - 角色数可从 5 缩到 3，但必须保留 risk 或 ops/security 视角（Case 03/08/09 对该视角依赖很强）。
- Anti-pattern/Boundary
  - 提案互相引用导致同质化；提案直接写实现补丁会跨越阶段（Case 11 反例）。

### 8.3 汇总（20-synthesis/options.md）：把“观点”变成“可比较选项”

- Best
  - **Option Cards + 对比矩阵 + Blocking Questions** 是最稳定的三件套（Case 01/04/05/06/08/10）。
  - **允许组合方案**：当单一 option 有明显缺口时，显式从“互斥”升级为“组合”（Case 06 的 Composite Plan 是典型）。
- Pragmatic
  - 给短名单可以，但必须保留“不选项”的拒绝理由（避免执行阶段反复翻案）。
- Anti-pattern/Boundary
  - 没有矩阵/量表 → 结论不可复盘；没有阻塞问题清单 → 方案看似闭环但实际缺关键部件。

### 8.4 评审（30-judging）：用“新角色”做二次独立裁决

- Best
  - **评审角色与作者解耦**：尽量用新 judgeRole（tech/product/risk/cost 等），输出 pick+confidence+tradeoffs+top risks+next validation。
  - **签字条件**：把“接受条件/DoD”写进 verdict（Case 07 QA/ops_security 的写法对执行阶段最有价值）。
- Pragmatic
  - ≥3 份 verdict 足够，但必须包含至少 1 份 risk 侧评审。
- Anti-pattern/Boundary
  - 评审只表态不写条件；或以“拍脑袋最顺手”为标准，导致执行阶段成本/风险爆雷。

### 8.5 最终决策报告（40-final/decision-report.md）：输出可交付、可验收、可审计

- Best
  - **SSOT 宣告**：明确唯一口径/唯一事实源（Case 01/06/09/10）。
  - **fail-closed vs warn 边界**：必须写清“什么时候停/什么时候提示继续”（Case 05/06/09/10）。
  - **分阶段落地**：Phase 0 止血→Phase 1 强门禁→Phase 2 证据闭环→Phase 3 回归固化（Case 06/10）。
  - **验收清单**：把验证步骤写成 checklist（Case 07 ≥10 条的写法最强）。
- Pragmatic
  - 先把验收做成可复跑脚本/用例目录（哪怕是手工步骤），再逐步自动化。
- Anti-pattern/Boundary
  - 只有结论没有验收 → 无法移交；只写“建议”不写边界 → 执行阶段会出现隐式降级。

### 8.6 Meta（90-meta/trace.md + requirements.md）：把流程变成可回放合同

- Best
  - trace 必须说明独立性策略、合并方法与关键取舍；requirements 必须抽取 Must/Should/Nice-to-have 与验收点（Case 04/05/06/08/09/10）。
  - 对“踩坑经验”（例如 scan 不应遍历 logs、并行 SSOT 单写者）要写入 trace，供流程固化。
- Pragmatic
  - requirements 先从“本案最关键 5 条 MUST”写起，避免空泛。
- Anti-pattern/Boundary
  - 缺少 requirements 会导致后续“泛化能力点”不可落；缺少 trace 会导致“为什么这么选”不可复盘。

### 8.7 建议的通用流程骨架（DRAFT，仅研究结论，不进入实现）

- 状态机（建议最小闭环）：
  1) FREEZE_INPUT（生成 `00-input/input.md`）
  2) DISPATCH_R1（生成 `10-ideation/round1/*.md`）
  3) SYNTHESIS_R1（生成 `20-synthesis/options.md` + Blocking Questions）
  4) DISPATCH_R2（生成 `10-ideation/round2/*.md`，仅回答阻塞问题）
  5) JUDGING（生成 `30-judging/*.md`）
  6) FINAL（生成 `40-final/decision-report.md` + handoff/checklist）
  7) META（生成 `90-meta/trace.md` + `90-meta/requirements.md`）

- 各阶段 fail-closed 触发（研究建议）：
  - 缺少输入合同或证据路径不足（<2）→ BLOCKED
  - 缺少 options 矩阵或 Blocking Questions → BLOCKED
  - 缺少 ≥3 份 verdict 或缺 risk 视角 verdict → BLOCKED
  - 缺少验收清单/边界声明（SSOT / fail-closed vs warn）→ BLOCKED

- 证据落盘（研究建议）：
  - evidenceRoot 必须 append-only；同一 runId+kind 禁止覆盖。
  - 主进程写 SSOT（options/final），子进程只写各自 evidence（对应 Case 04 的并行边界结论）。

### 8.8 新增案例（Case 12–20）带来的增量结论

- 输入合同：写作类必须把“链接预算/SAFE-DANGEROUS/Execution Intent”写进约束（Case 18/20）；产品/架构类应在 input 就冻结“机读输出合同 + 脱敏边界”（Case 12–17）。
- 提案：对“输出合同/默认安全/迁移策略”必须至少有 1 个角色专门负责，否则容易被忽略（Case 14/16/20）。
- 汇总：最常见的最优解是 Composite + 路线图（v1 先目录/manifest，v2 才 zip/checksum；strict/compat 分级；warning→fail-closed 迁移）（Case 13/14/16/19/20）。
- 评审：把“默认安全 + 可回归（fixtures/扫描）”写成签字条件，比“选哪个”更能降低执行期返工（Case 12/14/15/17/20）。
- 最终决策：新增案例强化了三种跨域通用证据形态：
  - `*.json` + `*.md` 双输出（机读为 SSOT，人读由渲染生成）（Case 12/13/14）。
  - `*.jsonl` index/ledger 追加写事件流（Case 15/17）。
  - resolution report（effective + sources + warnings）作为可审计中间层（Case 16）。
- Meta：负例 fixtures（故意失败样例）是最强防退化手段，应优先覆盖并行/覆盖/脱敏三类风险（Case 14/15/17/20）。


### 8.9 内容类型实证（Case 21–30）带来的增量结论

- **内容类型 profile（Must）**：不同内容类型对“角色集合/门禁强度/证据形态”差异显著，需要显式 profile 装配，而不是一套 rubric 走到底（Case 21–30）。
- **审批链路与过期策略（Must for 对外材料）**：对外内容必须把 approvers/expiry/scope 写成合同字段，否则会漂移且不可追责（Case 28）。
- **claim→evidence 映射（Must for 对外/合规）**：关键 claim 必须绑定 evidence 指针与适用范围，缺失应 fail-closed（Case 26/28）。
- **restricted 证据指针（Must）**：安全/合规/数据分析类内容默认禁止复制敏感证据，优先指针/摘要/脱敏片段（Case 26/27）。
- **Danger Zone 与执行意图协议（Must for 运维/指令型）**：runbook/操作型文档必须把 read-only 与 write（requires approval）分离，并把 token/回滚/验证写成强制段落（Case 25/30）。
- **机读合同的类型化（Should）**：
  - Spec → schema/examples pack（Case 21）
  - QA/Audit → evidence manifest（Case 24）
  - Ops → timeline/pointers + 授权 token（Case 25）
  - Analytics → metricVersion + queries pointers（Case 27）
  - Creative → deliverables manifest + Do-Not（Case 29）
- **负例库优先级提升（Should）**：内容类负例 fixtures（泄密/越权承诺/缺证据/无标签命令块）在治理上与代码测试同等重要（Case 24/25/26/28/30）。
## 9. 内容类型扩展（10 类）与三域需求案例（实证：Case 21–30）

> 目的：穷举并实证验证更多“内容类型（content types）”，用于反推不同内容类型的最优 profile 装配。
> 实证说明：Case 21–30 已按同一 Runbook 跑完整闭环（两轮并行提案→并行评审→最终决策），并为每类内容冻结 profile v1（仍处于研究阶段，不进入实现）。
> 证据指针：`docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/INDEX.md`

### 9.1 技术规格/接口契约/数据模型（Spec）

- 通用性机会：强约束（兼容性/安全/性能）+ 强证据（schema/样例/对比）+ 可验收（fixtures/contract test）。
- 需求案例
  - 研发：为某核心协议新增字段，需要在兼容旧客户端的前提下冻结 schema、迁移策略与回归 fixtures。
  - 创意：为设计系统定义 token 命名与 JSON schema（颜色/字号/间距），要求可自动校验与版本化迁移。
  - 企业市场：为企业客户集成定义 SSO(SAML)/SCIM 字段映射与错误码规范，要求对接团队可直接验收。
- 关键边界：必须输出机读合同（schema+examples），并明确 strict/compat 与 breaking-change 门禁。

- 实证结果（Case 21）
  - 推荐 profile v1：Option D（strict/compat + 扫描门禁 + 负例 fixtures，fail-closed）。
  - Must：机读契约为 SSOT；required examples/fixtures（正/反/边界）；breaking change 判定口径 + 迁移/废弃时间线。
  - Fail-Closed：缺 schema/examples；breaking change 无迁移策略/废弃窗口；示例命中敏感模式（token/key/绝对路径）。
  - 证据指针：`docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-21/40-final/decision-report.md`

### 9.2 决策记录（ADR/RFC/选型/权衡）

- 通用性机会：选项空间大且争议多，最需要“独立发散→可比较选项→独立评审→可回放决策”。
- 需求案例
  - 研发：在 `jsonl` 事件流 vs `sqlite` 状态库之间做架构抉择，要求把成本/并发/审计/迁移的 trade-off 固化。
  - 创意：在“品牌主叙事/视觉风格/语气”多个方向之间选定主线，要求解释为何不选其它路线并可回放。
  - 企业市场：在定价/包装（seat vs usage）与渠道策略（PLG vs enterprise）之间做决策，要求带证据与风险边界。
- 关键边界：决策必须绑定验收与复盘触发条件（什么时候推翻/迭代）。

- 实证结果（Case 22）
  - 推荐 profile v1：Option C（strict/compat）+（strict 可选）机读附录。
  - Must：标题集合（Background/Final Decision/Options/Trade-offs/Risks/Validation/Decision History）；options≥2 且写拒绝理由；revisit triggers + owner；compat 显式标注且保留最小必填。
  - Fail-Closed：缺 Final Decision/Options；没有 trade-offs/拒绝理由；没有 revisit triggers/owner。
  - 证据指针：`docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-22/40-final/decision-report.md`

### 9.3 研发交付计划/里程碑/资源排期（Plan）

- 通用性机会：依赖复杂、约束多、容易 scope creep；两轮流程可把“阻塞问题/依赖/验收”前置。
- 需求案例
  - 研发：为一个跨模块能力做 3 阶段交付计划，要求每阶段都有门禁、证据产物与回滚策略。
  - 创意：为一次大型 campaign 做资产生产计划（脚本/视觉/视频/落地页），要求可并行、可审计、可追责。
  - 企业市场：为企业版发布做 GTM+销售 enablement 排期，要求与研发里程碑绑定并能输出对外承诺边界。
- 关键边界：并行必须可证明写集合互斥；计划必须有 required/optional 与 fail-closed 边界。

- 实证结果（Case 23）
  - 推荐 profile v1：Option C（strict/compat）+ D（关键门禁与并行裁决 fail-closed）。
  - Must：每阶段 Deliverables/Gates/Acceptance/Rollback/Evidence Pointers；并行资格机读裁决（≥三态，不确定降级串行）；required/optional 与 fail-closed/warn 边界；对外承诺（日期/范围/价格）标注审批状态。
  - Fail-Closed：阶段缺 Gates/Acceptance；并行写集合不互斥仍标注可并行；对外承诺未标注审批状态。
  - 证据指针：`docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-23/40-final/decision-report.md`

### 9.4 测试/验收/质量与审计报告（QA/Audit）

- 通用性机会：天然需要 rubric 与证据；评审轮可强制“签字条件/DoD/负例”。
- 需求案例
  - 研发：为新增命令/能力设计验收矩阵（strict/compat、不同 OS、受限 PATH），要求能复跑并出报告。
  - 创意：为品牌合规（禁用词/视觉规范/版权）定义检查清单与抽检流程，要求可量化与可回归。
  - 企业市场：为客户 POC 定义验收用例与证据包结构，要求销售/交付/客户三方可对齐。
- 关键边界：报告必须机读（manifest/index），且默认脱敏；缺证据一律 fail-closed。

- 实证结果（Case 24）
  - 推荐 profile v1：Option D（evidence manifest + 默认脱敏 + 负例 fixtures，fail-closed）。
  - Must：`evidence-manifest.json` 机读 SSOT；固定段落（Summary/Scope/Environment/Results/Evidence/Risks）；required 缺失/绝对路径/敏感模式→阻断；至少 1 个 FAIL fixture 并写修复路径。
  - Fail-Closed：required artifacts 缺失；正文/manifest 出现绝对路径或 secrets；claim 无 evidence 指针。
  - 证据指针：`docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-24/40-final/decision-report.md`

### 9.5 运维 Runbook/事故响应/复盘（Ops/Incident）

- 通用性机会：高风险、高时效；需要“只读诊断→分级响应→可回放证据→复盘改进”。
- 需求案例
  - 研发：定义服务降级/回滚 runbook 与事故复盘模板，要求把监控信号、应急操作、恢复验证固化。
  - 创意：内容发布管线出错需要回滚/替换资产，要求分级权限、回滚窗口与对外沟通模板。
  - 企业市场：客户生产事故升级流程（SLA/沟通节奏/证据包）需要标准化，要求可审计且不泄密。
- 关键边界：必须区分 read-only vs write 操作；危险操作需显式授权与证据留痕。

- 实证结果（Case 25）
  - 推荐 profile v1：Option D（Execution Intent + Danger Zone + token + timeline/pointers，fail-closed）。
  - Must：Execution Intent（none/read-only/write(requires approval)）；Danger Zone 写操作必须含影响面/回滚/前置检查/验证并要求 token；timeline + evidence pointers；对外沟通模板与技术状态同步。
  - Fail-Closed：写操作缺授权条件（token/批准）；写操作缺回滚/验证；缺 timeline/pointers。
  - 证据指针：`docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-25/40-final/decision-report.md`

### 9.6 安全/隐私/合规评估（Security/Compliance）

- 通用性机会：风险权重极高且结论需要可追溯证据；适合用评审轮强制“签字条件+阻断规则”。
- 需求案例
  - 研发：对“外部工具执行/网络访问/日志导出”做威胁建模与控制面边界，要求形成可验证的 gate 清单。
  - 创意：对生成内容的版权/素材许可/用户隐私做合规评估，要求给出可执行的审查与留证策略。
  - 企业市场：面对客户的安全问卷/SOC2 证据请求，需要生成可分享的证据包与声明边界。
- 关键边界：Restricted 证据必须默认只给指针/摘要；不可把敏感材料复制进正文。

- 实证结果（Case 26）
  - 推荐 profile v1：Option D（controls→gate + restricted 指针 + claim→evidence，fail-closed）。
  - Must：威胁建模最小结构（Assets/Threats/Controls/Residual Risks/Evidence Pointers）；restricted 默认只给指针/脱敏摘要；每条 control 至少 1 个验证步骤；对外 claims 必须带 evidence 指针 + 适用范围/免责声明。
  - Fail-Closed：对外 claim 无 evidence/适用范围；正文出现 secrets/敏感配置/绝对路径；controls 无验证步骤。
  - 证据指针：`docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-26/40-final/decision-report.md`

### 9.7 指标/数据分析/实验报告（Analytics/Experiment）

- 通用性机会：需要把“假设→实验设计→数据→结论→下一步”闭环固化；提案轮适合产出多种分析路径。
- 需求案例
  - 研发：对模型路由策略做成本/质量实验，要求冻结指标、采样方法、统计口径与回归基线。
  - 创意：对文案/海报做 A/B 实验，要求明确受众、指标、实验周期与停止条件。
  - 企业市场：对漏斗转化/流失原因做分析与实验路线图，要求把结论绑定到可执行动作。
- 关键边界：必须声明数据口径与偏差来源；结论必须给出可复跑的查询/统计证据指针。

- 实证结果（Case 27）
  - 推荐 profile v1：Option C（strict/compat）+ D（metricVersion + 证据扫描回归）。
  - Must：结构（Hypothesis/Metrics/Design/Data Sources/Results/Limitations/Next Steps）；关键指标声明 metricVersion；查询/脚本用指针引用（restricted），正文只给脱敏摘要；结论写置信度/不确定性并绑定行动。
  - Fail-Closed：缺 Metrics definition 或缺 Data Sources；正文包含原始敏感数据/用户标识；结论无 next steps/owner。
  - 证据指针：`docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-27/40-final/decision-report.md`

### 9.8 对外沟通材料（Release/Announcement/One-pager/Pitch）

- 通用性机会：多受众（开发者/客户/市场/法务），需要多角色评审避免“承诺越权/事实不一致”。
- 需求案例
  - 研发：发布 breaking change 的 Release Notes + Migration Guide，需要冻结“影响面/迁移步骤/回滚边界”。
  - 创意：官网/视频的产品叙事脚本，需要在品牌语气与事实准确之间平衡。
  - 企业市场：销售一页纸、battlecard、RFP response 骨架，需要 claim→evidence 的可追溯映射。
- 关键边界：对外 claim 必须可追溯到证据；不可输出未经批准的时间/价格/合规承诺。

- 实证结果（Case 28）
  - 推荐 profile v1：Option D（claim→evidence + 审批链路 + 边界门禁，fail-closed）。
  - Must：claim→evidence 映射表；审批块 Approvers/Date/Expiry/Scope；对外承诺（日期/价格/合规）标注已批准/待确认；breaking change 含 Migration/Rollback/Compatibility Matrix。
  - Fail-Closed：关键 claim 缺 evidence；缺 Approvers/Expiry/Scope；出现未批准承诺。
  - 证据指针：`docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-28/40-final/decision-report.md`

### 9.9 创意 Brief/内容脚本/文案与视觉指引（Creative Production）

- 通用性机会：发散空间大但需要强约束（品牌/受众/渠道/合规）；两轮流程适合先极限探索再用 rubric 收敛。
- 需求案例
  - 研发：准备一次技术演示（demo script + story），要求 5 分钟内讲清价值并可复用为培训材料。
  - 创意：产出 campaign brief（核心概念/产物清单/禁用项/风格参照），要求可指导多团队并行生产。
  - 企业市场：为关键客户定制解决方案叙事与高管演示脚本，要求与可交付范围严格对齐。
- 关键边界：必须有禁用项（合规/品牌/安全），并把“可交付范围”写成硬边界防止过度承诺。

- 实证结果（Case 29）
  - 推荐 profile v1：Option C（strict/compat）+ D（合规与资产清单门禁，fail-closed）。
  - Must：Brief 必备字段（Audience/Message/Deliverables/Do-Not/Constraints/Review Rubric）；deliverables 清单含 owner/截止/验收；Do-Not 必须阻断；对外脚本声明可交付范围与限制条件。
  - Fail-Closed：缺 Deliverables 或缺 Do-Not；对外脚本缺范围/限制；素材来源不明或无授权说明。
  - 证据指针：`docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-29/40-final/decision-report.md`

### 9.10 培训/Enablement/知识库（Onboarding/FAQ/Playbook）

- 通用性机会：需要“可执行步骤 + 失败恢复 + 版本漂移治理”；与 Case 18/20 的写作护栏强相关。
- 需求案例
  - 研发：新成员 onboarding（环境/测试/调试/贡献流程），要求 1 小时内完成首次成功闭环并可自证。
  - 创意：品牌写作规范 + prompt library，需要可审计的更新流程与示例库回归。
  - 企业市场：客户 onboarding playbook + 支持知识库，要求分级权限、脱敏与可分享证据包。
- 关键边界：命令/操作必须带 Execution Intent；危险操作必须显式授权；链接/术语预算避免 KB 膨胀。

- 实证结果（Case 30）
  - 推荐 profile v1：Option D（双轨结构 + 安全标签 + 扫描回归，fail-closed）。
  - Must：双轨（Mental Model + First Success Path）；命令块带 Execution Intent 标签（EXAMPLE/READ-ONLY/DANGEROUS）；链接预算/术语预算可检查；失败恢复段落（常见失败→最短恢复入口→验证）。
  - Fail-Closed：无标签命令块；出现危险写操作但无授权说明；链接预算超限且无理由。
  - 证据指针：`docs/todo/logs/swarm-decision-sim/spd-sim-20260421-run01/case-30/40-final/decision-report.md`

### 9.11 其它候选内容类型（未纳入以上 10 类）

- 法务/条款：合同、SLA、DPA、隐私声明、许可合规清单
- 采购/选型：供应商评估、RFP 对比、TCO/License 风险清单
- 组织管理：会议纪要/决议、OKR/绩效复盘、招聘 JD/面试 rubric
- 客户成功：实施方案、QBR 报告、续费与扩容策略
- 财务经营：预算/成本控制策略、定价测算、毛利模型说明

### 9.12 从“内容类型扩展”反推的增量能力点（实证：Case 21–30）

- **内容类型 profile（Must）**：同一套流程需要按内容类型装配不同 rubric/角色/门禁强度/证据形态（Case 21–30）。
- **审批链路与过期策略（Must）**：对外材料必须把 Approvers/Expiry/Scope 写成合同字段，缺失应 fail-closed（Case 28）。
- **claim→evidence 映射（Must）**：对外/合规类内容必须把关键 claim 绑定 evidence 指针与适用范围/免责声明（Case 26/28）。
- **restricted 指针策略（Must）**：安全/合规/数据分析类内容默认禁止复制敏感证据，正文优先指针/摘要/脱敏片段（Case 26/27）。
- **Danger Zone + Execution Intent（Must）**：运维与指令型内容必须把 read-only 与 write(requires approval) 分离，并把 token/回滚/验证写成强制段落（Case 25/30）。
- **机读合同的类型化（Should）**：不同内容类型需要不同最小机读产物（schema/examples、evidence-manifest、analysis-pack、creative-manifest、approval block）。
- **负例库与扫描回归（Should）**：内容类负例 fixtures（泄密/越权承诺/缺证据/无标签命令块）是最强防退化手段，应与代码测试同优先级治理（Case 24/25/26/28/30）。
- **双视图输出（Should）**：公开版/内部版分流能同时满足协作与泄漏风险控制（Case 24/26/28/30）。

## 10. 面向 Skill 化的抽象：要点与环节步骤（基于 Case 01–30）

> 重要声明：本章仍处于研究/决策阶段，仅抽象“skill 需要具备的流程、门禁、产物合同与集成方式”，不进入实现。

### 10.1 Skill 的目标与边界（从案例反推）

- 目标（Must）
  - 把“问题/目标”冻结为**可裁决对象**，并用可复盘的两轮并行流程输出可交付结论。
  - 产出可被下游消费的**最小可验收合同**（Acceptance Checklist + fail-closed 边界 + evidence pointers）。
  - 默认安全：避免过早写入、误触发执行、二次泄漏、越权承诺。
- 不做什么（Must Not）
  - 不在“出方案/讨论阶段”写入交付目录或修改代码；任何写入必须受 write-intent gate 控制。
  - 不把 restricted 证据复制进正文；以指针/摘要/脱敏片段替代。

### 10.2 总体架构（模块分解）

- `Orchestrator`：状态机驱动（INIT→FREEZE_INPUT→R1→SYNTHESIS→R2→JUDGING→FINAL→META）。
- `Profile Engine`：按 `contentType × riskClass` 装配 roles/rubric/gates/artifacts。
- `Gate Engine`：fail-closed 门禁与降级策略（warning→fail-closed 路线图 + waiver）。
- `EvidenceRoot Manager`：统一落盘结构、append-only、SSOT 单写者、索引与可续跑。
- `Agent Dispatcher`：并行分派（强约束写集合不重叠；子代理仅写自己文件）。
- `Synthesis/Report Generator`：options 矩阵/阻塞问题/最终报告/机读摘要。
- `Safety Layer`：write-intent gate + restricted 指针 + 扫描门禁（secrets/绝对路径/未批准承诺/无标签命令块）。
- `Integration Adapter`：与 PRD/架构/开发计划/门禁/语义修正等技能的接口（触发与回传）。

### 10.3 标准流程链路（建议 v1 固定骨架）

- Stage 0：`INIT`（生成 runId + 装配 profile）
- Stage 1：`FREEZE_INPUT`（输入合同：Problem/Evidence/Constraints/Success/Non-Goals/Rubric/Safety）
- Stage 2：`DISPATCH_R1`（多角色独立提案）
- Stage 3：`SYNTHESIS_R1`（Option Cards + 对比矩阵 + Blocking Questions）
- Stage 4：`DISPATCH_R2`（仅回答阻塞问题，不允许二次发散）
- Stage 5：`JUDGING`（全新角色独立 verdict：pick+confidence+tradeoffs+risks+sign-off+next validation）
- Stage 6：`FINAL`（最终裁决：冻结 profile v1 + 验收清单 + 交接）
- Stage 7：`META`（trace + requirements，把经验抽象为 MUST/SHOULD）

### 10.4 必须门禁（fail-closed）与降级策略（跨类型通用）

- 输入合同门禁：Evidence pointers < 2 / 缺 Non-Goals / 缺安全底线 → BLOCKED（可进入 R1 但必须在 R2 前补齐，否则阻断 JUDGING）。
- 汇总门禁：缺 options 矩阵或缺 Blocking Questions → BLOCKED。
- 评审门禁：verdict < 3 或缺 risk verdict / verdict 无签字条件 → BLOCKED。
- 最终报告门禁：缺 Acceptance Checklist / 未声明 SSOT 与 fail-closed vs warn 边界 → BLOCKED。
- 并行边界：写集合不互斥→默认 SERIAL_ONLY；发现冲突或 scope 不清→BLOCKED。

### 10.5 证据与产物合同（SSOT 策略）

- evidenceRoot 建议沿用 `docs/todo/logs/<topic>/<runId>/` 结构；append-only + SSOT 单写者。
- 机读为 SSOT（建议 P0 就做）：`options.json`、`verdicts.json`、`decision.json`；人读 `*.md` 作为解释层。
- restricted 默认：正文不粘贴敏感证据；使用 `evidencePointers[]`（含 sensitivity/access/summary）。
- fixtures：必须包含跨类型通用负例 + 各 contentType 的 fail-closed 负例（防退化优先级≈代码测试）。

### 10.6 Profile 体系（内容类型 × 风险叠加）

- Base：固定流程骨架 + 最小产物集合 + 五视角提案/三视角评审。
- Overlay 优先级：Risk Overlay > ContentType Overlay > Org/Repo Policy > Task Override（仅允许收紧；放宽需 waiver）。
- strict/compat：compat 必须显式标注且保留最小必填字段；compat 使用需要原因/范围/到期记录。
- 10 类内容类型的 typeSpecific.must（Case 21–30 实证）：
  - Spec：schema+examples pack + breaking change 迁移窗口
  - ADR：trade-offs/拒绝理由 + revisit triggers
  - Plan：阶段 gates/acceptance/rollback + 并行资格机读裁决
  - QA/Audit：evidence-manifest SSOT + 默认脱敏 + 负例
  - Ops：Execution Intent + Danger Zone token + timeline/pointers
  - Sec：controls→gate + restricted + claim→evidence
  - Analytics：metricVersion + query pointers(restricted) + next steps/owner
  - External：claim→evidence + approvers/expiry/scope + 未批准承诺阻断
  - Creative：Brief 必填 + deliverables manifest + Do-Not/授权
  - Enablement：双轨 + 命令标签 + 链接/术语预算 + 漂移回归

### 10.7 安全与合规（必须内置而非“靠人”）

- Write-Intent Gate：默认 dry-run；写入需 `--apply` + nonce/token + scope + TTL；缺任一项 fail-closed。
- 扫描门禁：secrets/绝对路径/未批准对外承诺/无标签命令块/危险命令无授权说明 → fail-closed。
- 对外材料必须具备审批块（Approvers/Date/Expiry/Scope）+ claim→evidence；缺失即阻断。

### 10.8 集成与 UX（被其它技能调用）

- 触发模式：手动（start/resume）与自动（上游生成器出现阻塞问题/门禁 FAIL 需裁决/语义修正候选裁决）。
- 交互三段式：Start（freeze input）→ Run（两轮+评审）→ Apply（可选，严格受控）。
- 回传形态：`decision-report.md` + `decision.json`（可选但建议）+ `requirements.md`，供 PRD/架构/计划/审计等技能消费。

### 10.9 渐进落地路线图（避免“一上来过度工程化”）

- Phase 0：只落盘 evidenceRoot + 报告，门禁以 warnings 为主；同时补齐 fixtures（含负例）。
- Phase 1：对 PR diff-scope fail-closed（仅阻断新增/变更的违规）；引入 waiver（owner+expiry）。
- Phase 2：扩大覆盖面；把关键类型（External/Sec/Ops/QA/Enablement）升级为严格 fail-closed。
- Phase 3：固化为默认策略；白名单必须到期。



### 10.10 反平庸 / 反保守机制（可装配，非强制一刀切）

> 目的：让两轮并行流程在“可落地/可安全”之外，仍能系统性地产出**非平庸、非保守**的高杠杆选项；同时把大胆选项变成“可控风险”，而不是“禁止”。

- **Option 多样性门禁（Must for 创意/战略类；Should for 其它）**
  - 在 `20-synthesis/options.md` 中要求：至少包含 1 个“高杠杆/反直觉/高风险高回报”的候选 option（可标注 `moonshot=true`）。
  - 若所有 option 本质同质化（只是实现细节差异）→ 回退到 R1 补 1 个“方向性不同”的 option。
- **禁止“平均融合”当默认（Must）**
  - synthesis 允许 Composite（组合方案），但必须把组合写成明确 option，并记录 trade-offs；禁止把多个方案“揉成一团”变成模糊折中。
- **创新目标与风险预算显式化（Must）**
  - 输入合同必须声明：本次追求的创新程度（novelty target）与可接受风险预算（risk budget）。
  - FINAL 报告必须回答：我们接受了哪些风险、换取了什么收益、如何验证/回滚。
- **“大胆但可控”的实验门禁（Must for moonshot option）**
  - 任何 moonshot option 若要进入短名单或被选中，必须同时提供：最小可验证实验（MVE）、灰度/回滚策略、成功/失败判据、验证证据指针。
- **Champion/Challenger 机制（Should）**
  - 对每个短名单 option 指定 champion 与 challenger：champion 必须写“为何它更好”；challenger 必须写“它会失败在哪里/如何证伪”。
- **新颖性量表进入 rubric（Should，可调权重）**
  - rubric 增加 `novelty_or_leverage` 维度（新颖性/杠杆），用于抵消“只因更安全就获胜”的惯性。

### 10.11 轻盈优雅优先级（高优先级维度：复用现有能力，避免造轮子）

> 目的：在保证质量的前提下，把流程做得更简单、更通用、更易落地；优先复用仓库已有规则/技能/产物合同，减少新增复杂度。

- **Reuse-first 原则（Must）**
  - 每个 option 必须包含：`Reuse`（可直接复用的 repo 内能力/规则/技能/已有产物）与 `New Build`（必须新增的最小部分）。
  - 若一个 option 的 New Build 过大但缺少“为什么现有能力不够”的证据指针 → 在 judging 中默认扣分或阻断进入 FINAL。
- **轻量产物优先（Must）**
  - 默认只要求“通用骨架最小产物”（00/10/20/30/40/90）；除非 contentType profile 明确要求，否则不新增新的文件类型/复杂协议。
  - 机读合同采取渐进策略：先把最小 `decision.json/options.json/verdicts.json` 做成 SSOT，再逐步引入 typeSpecific pack（spec-pack/evidence-manifest/claims 等）。
- **按风险与目标伸缩角色与门禁（Must）**
  - 低风险/高时效任务允许降级角色数与评审数（但仍保留 risk/ops_security 视角）；高风险或对外材料必须全量门禁。
- **不重复发明扫描/门禁（Should）**
  - 优先复用现有规则与门禁技能（例如 doc-quality-gate / doc-semantic-repair / repo rules），仅在缺口明确且复用不可行时才提出新增扫描器。
- **时间/复杂度预算（Should）**
  - 输入合同声明 timeBudget（例如 fast/normal/thorough），Orchestrator 按 budget 控制：角色数量、输出长度、阻塞问题数量上限，避免流程官僚化。

### 10.12 可调旋钮（Prompt Dials）：一次任务如何声明“我要高创意/高风险/高通用/高安全”

> 目的：让创意创新、风险、通用性、安全、成本/时效等维度可在“同一流程骨架”下按次调参；通过提示词/输入合同中的控制块，把偏好变成可裁决对象。

- **建议在 `00-input/input.md` 顶部加入“控制块”（可纯文本或 YAML）**
  - 示例（仅示意，字段可按需裁剪）：

```yaml
TaskDials:
  mode: strict            # strict|compat
  goal:
    creativity: high      # low|medium|high
    riskTolerance: high   # low|medium|high|critical
    generality: medium    # narrow|medium|broad
    speed: normal         # fast|normal|thorough
  priorities:
    reuseFirst: true      # 轻盈优雅优先
    evidenceStrength: high
    innovationOverlay: on # on|off（要求至少 1 个 moonshot option）
  safety:
    invariants:           # 不可调：永远 fail-closed
      - no_secrets
      - no_untagged_dangerous_commands
    strictness: high      # 可调：对外/审批/扫描覆盖范围的强度
  output:
    views: [internal]     # internal|public|both
    machineReadable: minimal  # none|minimal|full
  sampling:
    policy: auto              # auto|fixed（auto=按并发矩阵+动态扩容；fixed=手动指定）
    r1:
      min: 3
      baseline: auto          # auto|number
      max: 50
      batch: 5
    judging:
      minVerdicts: 3
      baseline: auto
      maxVerdicts: 11
      batch: 2
```

- **旋钮→装配映射（Must）**
  - `creativity=high` → 启用 Option 多样性门禁 + innovation overlay（至少 1 个 moonshot option）+ rubric 提高 novelty 权重。
  - `riskTolerance=low` → judging 侧提升 risk 权重、要求更强的验证/回滚；moonshot option 只能作为备选附录。
  - `generality=broad` → 要求每个 option 明确适用范围/不可适用范围（避免“看似通用其实不可落地”）。
  - `speed` / `sampling` → 依据 6.3 基线矩阵 + 6.4 动态扩容，决定 `roles.r1[]/roles.judging[]` 的规模与批次；若选择 `sampling.policy=fixed`，必须在 trace 中说明理由与上限。
  - `reuseFirst=true` → 每个 option 强制输出 Reuse/New Build 清单，并把“复用率/新增复杂度”纳入 rubric。
  - `output.views` 与 `safety.strictness` → 装配公开版/内部版、审批块、restricted 指针策略与扫描门禁强度。

- **安全可调的边界（Must）**
  - “安全”分两层：
    - **不可调安全不变量**：secrets/危险命令误触发/对外越权承诺等必须 fail-closed。
    - **可调安全严格度**：对外材料的审批链路强度、扫描覆盖范围、公开版/内部版的粒度可按 task 调整。

### 10.13 并行分析记录（5 个 Agent 输出）

以下为本轮并行分析的原文记录（用于复盘与后续决策拆解）。

## 并行分析 Agent #1（流程/状态机）原文

## 1) 目标：把 Case 01–30 的“实证闭环”抽象为可复用链路（流程/状态机）

该类流程的核心不是“多写几份提案”，而是**把问题冻结成可裁决对象**，再用**两轮独立发散 + 新角色独立裁决**，最终输出**可交付/可验收/可审计**的决策报告，并把全过程证据以 **append-only** 方式落到 evidenceRoot。

---

## 2) 状态机（可续跑、可并行、可降级）

### 2.1 推荐最小状态机（v1）
1) `INIT`：创建 run 上下文（runId、evidenceRoot、profile 装配结果）
2) `FREEZE_INPUT`：冻结输入合同（00-input）
3) `DISPATCH_R1`：第一轮并行提案（10-ideation/round1）
4) `SYNTHESIS_R1`：主进程汇总 + 阻塞问题（20-synthesis）
5) `DISPATCH_R2`：第二轮并行收敛（仅回答阻塞问题）（10-ideation/round2）
6) `JUDGING`：全新评审角色并行 verdict（30-judging）
7) `FINAL`：主进程做最终裁决并冻结 profile v1（40-final）
8) `META`：全过程 trace + requirements（90-meta）
9) `DONE`

### 2.2 可续跑策略（来自 Case 17/15 的抽象）
- 每个状态进入前写 `state`（机读），完成后写 `state.completedAt`；任何中断都可从最后一个完成态继续。
- 所有关键产物采用 **append-only**（或以 runId+stage 唯一命名）；禁止覆盖“同一 runId 的 SSOT 文件”。
- 允许 `RETRY_STAGE(stage)`：重跑某一阶段时必须写入“新的 attemptId”，旧 attempt 保留，仅由 SSOT 指针选择生效版本。

---

## 3) 每步输入/输出（最小必需产物）

> 约定：子角色只写“各自文件”；主进程写 SSOT（options/final/requirements 之类）。

### 3.1 `INIT`
- 输入：用户目标（problem statement）、内容类型 `contentType`、风险等级 `riskClass`、适用域（研发/创意/企业市场）
- 输出（Must）：
  - `run.json`（runId、evidenceRoot、profileId、strict/compat、roleSet、rubric、gates 开关）
  - `ledger.jsonl`（可选但强烈建议，用于审计/续跑）

### 3.2 `FREEZE_INPUT`（00-input）
- 输入：需求描述 + repo 内证据路径/规则指针
- 输出（Must）：`00-input/input.md`
  - Problem / Evidence(≥2 repo 路径指针) / Constraints / Success / Non-Goals / Rubric / Safety（脱敏、restricted）
- 输出（Should）：`00-input/input.json`（机读输入合同，用于门禁与 profile 装配）

### 3.3 `DISPATCH_R1`（第一轮提案）
- 输入：`00-input/input.md`
- 输出（Must）：`10-ideation/round1/{role}.md`（至少 3–5 个角色）
  - 每份必须含：推荐方案、拒绝理由、风险、验收/证据、迁移/降级（如适用）

### 3.4 `SYNTHESIS_R1`（汇总）
- 输入：round1 全部提案
- 输出（Must）：`20-synthesis/options.md`
  - Option Cards + 对比矩阵 + Blocking Questions（阻塞问题清单）
- 输出（Should）：`20-synthesis/options.json`（机读：options、criteria、blockingQuestions）

### 3.5 `DISPATCH_R2`（第二轮收敛）
- 输入：`20-synthesis/options.md` 的阻塞问题
- 输出（Must）：`10-ideation/round2/{role}.md`
  - 仅回答 blocking questions；不得引入全新方案（除非声明“新增 option”并触发回退门禁）

### 3.6 `JUDGING`（独立评审）
- 输入：options + round2
- 输出（Must）：`30-judging/verdict-{judgeRole}.md`（≥3 份，必须含 risk）
  - pick + confidence + trade-offs + top risks + sign-off conditions + next validation
- 输出（Should）：`30-judging/verdicts.json`（机读 verdict 汇总）

### 3.7 `FINAL`（最终决策冻结）
- 输入：options + verdicts
- 输出（Must）：`40-final/decision-report.md`
  - Final Decision / Rationale / Must-Should / Fail-Closed Gates / Acceptance Checklist / Handoff / Alternatives
- 输出（Must）：把 **“该 contentType 的 profile v1”** 冻结为可引用条目（写入 report 或单独机读附录）

### 3.8 `META`（可回放合同）
- 输入：全链路产物
- 输出（Must）：
  - `90-meta/trace.md`（独立性策略、合并方法、关键取舍、风险事件）
  - `90-meta/requirements.md`（Must/Should/Nice-to-have + 验收点）
- 输出（Should）：`90-meta/requirements.json`（机读能力点）

---

## 4) fail-closed 门禁点（BLOCK 条件 + 降级策略）

### 4.1 输入合同门禁（FREEZE_INPUT）
- BLOCK：
  - Evidence 指针 < 2（无法复核，评审只能投票）
  - 缺 Non-Goals（scope creep 风险）
  - 缺风险底线（例如 secrets/restricted/危险操作边界）
- 降级：
  - 允许先进入 `DISPATCH_R1` 但必须将缺失项列入 Blocking Questions，并在 R2 前补齐；否则阻断进入 JUDGING。

### 4.2 提案轮门禁（DISPATCH_R1/R2）
- BLOCK：
  - 提案互相引用/抄写导致同质化（违反独立性）
  - R2 引入全新方案但未回退到 `SYNTHESIS_R1` 更新 options
- 降级：
  - 角色数可从 5 降到 3，但必须保留 `risk/ops_security` 视角（Case 03/25/26/28/30 强依赖）。

### 4.3 汇总门禁（SYNTHESIS_R1）
- BLOCK：
  - 缺 Option Cards 或缺对比矩阵
  - 缺 Blocking Questions（R2 无法“受约束收敛”）
- 降级：
  - 允许短名单，但必须写拒绝理由与“仍待验证的关键假设”。

### 4.4 评审门禁（JUDGING）
- BLOCK：
  - verdict < 3 或缺 risk verdict
  - verdict 无 sign-off conditions / next validation（不可移交）
- 降级：
  - 若时间不足，可减少 judgeRole，但 risk verdict 仍必需；否则阻断 FINAL。

### 4.5 最终报告门禁（FINAL）
- BLOCK：
  - 缺 Acceptance Checklist（无法执行/验收）
  - 未声明 SSOT / fail-closed vs warn 边界
- 降级：
  - 允许先输出 DRAFT，但必须标注“不可执行/不可落地”，并禁止进入后续执行类流程（防 Case 11）。

### 4.6 内容类型特有门禁（来自 Case 21–30）
- Spec：缺 schema/examples 或 breaking change 无迁移窗口 → BLOCK
- QA/Audit：manifest 缺 required artifacts、出现绝对路径/secrets → BLOCK
- Ops：write 操作缺 token/回滚/验证 → BLOCK
- Sec/Comms：claim 无 evidence/approvers/expiry/scope → BLOCK
- Enablement：无标签命令块/危险命令无授权说明 → BLOCK

---

## 5) 并行边界与 SSOT 单写者规则（来自 Case 04/17/23）

### 5.1 写集合互斥（Hard Rule）
- 子进程（并行角色）只能写入：
  - `10-ideation/round*/{role}.md`
  - `30-judging/verdict-*.md`
- 主进程唯一写入（SSOT）：
  - `20-synthesis/options.*`
  - `40-final/decision-report.md`
  - `90-meta/*`
- 任何尝试写入 SSOT 文件（非主进程）→ **BLOCKED**

### 5.2 并行资格裁决（Plan/执行类强制）
- 输出机读裁决：`PARALLEL_OK / SERIAL_ONLY / BLOCKED`
- 若无法证明写集合互斥：默认降级 `SERIAL_ONLY`
- 若发现冲突或 scope 不清：`BLOCKED`（必须回到输入合同补证据/补边界）

---

## 6) 最小配置参数（供 skill 装配/复用）

### 6.1 必需参数（Must）
- `runId`（唯一）
- `evidenceRoot`（落盘根）
- `contentType`（如 Spec/ADR/Plan/QA/Ops/Sec/Analytics/Comms/Creative/Enablement）
- `riskClass`（Low/Med/High；决定 gate 强度与角色集）
- `mode`：`strict|compat`（strict 默认；compat 必须显式标注）
- `roles.r1[]` 与 `roles.judging[]`（两轮解耦）
- `rubric`（维度与权重：可落地性/可验证性/风险/成本/采用率/合规等）
- `gates`（启用哪些 fail-closed 检查）
- `redactionPolicy`（脱敏、restricted 指针策略、公开版/内部版分流）

### 6.2 建议参数（Should）
- `timeBudget`（每阶段时间上限，防止无限发散）
- `minEvidencePointers`（默认 2）
- `minVerdicts`（默认 3，且必须含 risk）
- `allowCompositeOption`（默认 true）
- `warningToFailClosedPlan`（治理迁移节奏：warning→fail-closed + 白名单到期）

### 6.3 并发规模配置矩阵（可配置默认值：可伸缩，但不等于“近似硬编码”）

> 目的：把“并发数量/样本数”从经验拍脑袋，升级为 **可解释、可调、可审计** 的配置决策；同时保留动态扩容机制，避免所有 run 都落回一个固定默认值。

- **6.3.1 基线矩阵（riskClass × timeBudget）**
  - 说明：该矩阵用于生成“起步的基线规模（baseline）”，随后仍需结合 contentType/profile 与 TaskDials 做修正（见 6.3.2），并允许按 6.4 动态扩容。

  | riskClass / timeBudget | fast | normal | thorough |
  | --- | --- | --- | --- |
  | Low | R1=3，J=3 | R1=5，J=3 | R1=7，J=5 |
  | Med | R1=5，J=3 | R1=7，J=5 | R1=11，J=7 |
  | High | R1=7，J=5 | R1=9，J=7 | R1=15，J=9 |

  - `R1`：提案轮并行角色数（即 `len(roles.r1[])`）。角色应覆盖产品/架构/实现/QA/风险（或等价集合）。
  - `J`：评审轮 verdict 数（即 `len(roles.judging[])`），且必须满足 `minVerdicts` 与“必须含 risk verdict”的不变量（见 4.4）。
  - `R2`：不单独作为“新增样本数”计入矩阵；其定位是对 `Blocking Questions` 的补答（防止二次发散）。默认沿用 R1 角色集合输出更短的补充；也允许只派出需要补答的子集（必须在 `trace.md` 说明子集选择理由）。

- **6.3.2 contentType/profile 与 TaskDials 的修正规则（避免“一刀切”）**
  - 目标：同样的 riskClass，在不同内容类型/目标偏好下，“需要的发散广度（R1）”与“需要的裁决严谨度（J）”不同；本节提供可解释的修正范式。

  在 6.3.1 baseline 上，按以下规则修正（示例，具体阈值可由 profile 固化）：

  - **Creative / 市场 / 品牌 / 写作创意类**：探索空间大，优先增加 `R1`（发散广度），例如 `R1 × (1.5~3)`；`J` 通常保持 baseline 或 +2（用于把“大胆选项”变成“可控风险”的签字条件）。
  - **Sec / Comms / 对外承诺 / 合规敏感类**：风险权重高，优先增加 `J`（裁决严谨度），例如 `J +2` 或 `J × 1.5`；并强制加入 `ops_security`（必要时再加“legal-like/PR-like” judgeRole），将签字条件/审批块作为 verdict 核心产物。
  - **Spec / ADR / Plan（工程决策类）**：`R1` 通常中等；当涉及 breaking change / 跨团队接口 / 外部依赖时，`J` 至少 7（需要更多独立裁决与签字条件）。
  - **Analytics / 数据分析路径类**：优先增加 `R1`（多条分析路线与反证路径），并要求至少 1 个“反直觉假设/反证方案”；若结论对外影响大，再叠加 `J`。

  TaskDials 方向性建议（与 10.12 对齐）：

  - `goal.creativity=high` 或 `goal.generality=broad` → **优先增大 `R1`**（更广搜索）。
  - `mode=strict` 或 `goal.riskTolerance=low/critical` 或 `safety` 强约束 → **优先增大 `J`**（更严裁决 + 更强签字条件）。
  - `priorities.reuseFirst=true` → 不一定减少样本数，但要求每个新增角色必须“带来新的差异化视角/证据路径”，否则视为噪音。

- **6.3.3 防“默认值固化”规则（过程可审计）**
  - **显式性（Should，强建议）**：在 `00-input/input.md` 或 `RUNBOOK.md` 中必须写出本次采用的 `roles.r1[]`、`roles.judging[]` 与数量，以及“为何如此定”的一句话理由。
  - **可追溯（Should）**：在 `90-meta/trace.md` 记录：baseline→修正→最终数量（含是否触发动态扩容、扩容批次与停止条件）。
  - **拒绝静默回落（Must，研究建议）**：如果系统判定需要扩容但被 timeBudget/预算限制阻断，必须在 FINAL 报告中显式标注“样本不足风险”，并把该风险作为 revisit trigger。

### 6.4 并发规模动态决策机制（按目标特征决定 5 还是 50）

> 核心思想：把“并发数量/样本数”当成一种 **自适应采样（adaptive sampling）** 问题，而不是固定常量。流程先用 baseline 起跑，然后用可审计的信号决定是否继续加样本，直到满足停止条件或触达预算上限。

- **6.4.1 评估结论：当前基线可能样本偏少的场景**
  - 当前文档中常见的 `R1≈5、J≈3` 仅是**最小闭环的可落地基线**（便于普适接入），并不保证对所有目标都足够。
  - 对以下目标类型，固定小样本很容易导致“同质化/漏解/过早收敛”，需要按机制扩容：
    - 追求高创意/高杠杆（需要更广的搜索空间）
    - 行业/场景不熟或信息不完备（需要更多“假设分支/反证路径”）
    - 影响面大且风险复杂（需要更多独立裁决与更强签字条件）
    - 需要跨多域视角（产品×工程×合规×市场×安全）同时满足

- **6.4.2 动态扩容触发信号（Signals）**

  提案轮（R1）典型触发信号（任一命中即可加样本）：

  - **多样性不足**：options 中缺少“方向性不同”的候选（仅实现细节差异），或未满足必须出现的类别（例如 `reuse-first` / `moonshot` / `risk-first` 之一）。
  - **证据不足**：关键 claim 只有观点没有证据指针（尤其对 Sec/Comms/Ops），导致 judging 只能“投票”。
  - **不确定性仍高**：Blocking Questions 数量超阈值，且集中在“决定方向的关键问题”上（不是细枝末节）。
  - **视角缺失**：缺少关键域角色（例如没有 ops/security、没有 adoption/enablement 视角），或已有角色产出明显同质化。

  评审轮（J）典型触发信号：

  - **分歧过大**：judge pick 分散、trade-off 争议集中且无法靠证据裁决。
  - **置信不足**：多数 verdict 的 `confidence` 偏低，且 sign-off conditions 仍无法闭环。
  - **高风险未被“签字条件化”**：风险被描述但没有验证/回滚/审批条件，导致 FINAL 不可移交。

- **6.4.3 扩容方式（Progressive Widening：分批加样本，而非一上来 50）**
  - **分批扩容（Should）**：按批次追加角色，而不是一次性拉满。
    - 建议批次：R1 每批 +3/+5/+10（按 timeBudget）；J 每批 +2（更易收敛与控成本）。
  - **角色生成约束（Must）**：每个新增角色必须声明其差异化“目标函数/视角”，避免“同一脑回路复制 10 份”。
  - **保持独立性（Must）**：新增角色默认不读其它提案，只读输入合同与已有 options（如果允许读 options，也必须限制为结构化字段，禁止读其它角色全文）。

- **6.4.4 停止条件（Stop Conditions：何时不用再加样本）**

  提案轮停止条件（满足其一即可停止扩容）：

  - **边际增益变小**：最近一批新增角色没有带来新的 option 类别/新的证据路径/新的关键风险揭示。
  - **覆盖达标**：已满足 profile 要求的必需类别（例如 1 个稳健增量 + 1 个高杠杆 + 1 个合规/风控最优），且 Blocking Questions 收敛到可在 R2 解答的范围。
  - **预算触顶**：timeBudget/成本预算达到上限（必须显式标注样本不足风险，见 6.3.3）。

  评审轮停止条件（满足其一即可停止扩容）：

  - **结论稳定**：新增 judge 不改变 top-1/top-2 的相对排序，且 sign-off conditions 已完整。
  - **风险闭环**：高风险项都已被“验证/回滚/审批”条件化，并可进入验收清单。

- **6.4.5 何时需要到 50（明确边界，避免滥用）**

  达到 `R1≈25~50` 的典型条件（至少满足两条，且 timeBudget=thorough 或明确允许成本上升）：

  - 任务目标是“生成通用方法/框架/策略”，且希望覆盖大量行业差异与反例边界（高 generality + 高 creativity）。
  - 行业/市场/用户研究型问题，需要广泛枚举不同商业模型/渠道/定价/增长路径（探索空间远大于工程实现空间）。
  - 你们明确希望做“多路径并行搜索”（而不是快速决策），并愿意用后续 judging 强化筛选与风险条件化。

  反例（不建议上来 50）：

  - 明显是工程执行细节、且风险边界清晰的问题；此时更应把精力放在证据/验收/门禁，而不是增加样本数。

### 6.5 独立使用模式（Standalone Run）：显性 Prompt 输入 → 显性人读报告输出

> 适用：不依赖上游 skill/门禁链路，仅通过一次“显性提示词”启动完整闭环；常见于创意提案、方案比选、跨团队争议裁决等场景。

- **启动方式（Must）**：提示词必须显式包含“启动决策闭环”的意图标记 + 关键参数；否则一律按“讨论/咨询”处理，不进入 run（防误触发与阶段越权）。
- **Prompt Contract（Must）**：建议按下列模板输入（缺项会触发 FREEZE_INPUT 门禁阻断，或被列入 Blocking Questions 等待 R2 补齐）：

```markdown
[SwarmDecisionRun: start]   # 必须：显性意图标记（或等价）
contentType: <Spec|ADR|Plan|QA|Ops|Sec|Analytics|Comms|Creative|Enablement>
riskClass: <Low|Med|High>
timeBudget: <fast|normal|thorough>
mode: <strict|compat>

Problem:
Context:
Evidence:
- <repo path or restricted pointer>
- <repo path or restricted pointer>
Constraints:
Success Criteria:
Non-Goals:
Rubric:
- <dimension>: <weight>
TaskDials:
  goal: { creativity: <low|medium|high>, riskTolerance: <low|medium|high|critical>, generality: <narrow|medium|broad>, speed: <fast|normal|thorough> }
  sampling: { policy: <auto|fixed>, r1: { max: 50, batch: 5 }, judging: { minVerdicts: 3, maxVerdicts: 11, batch: 2 } }
Output:
  views: <internal|public|both>
  requireDecisionReport: true
```

- **输出要求（Must）**：无论是否落盘，必须产出一份完整的 `decision-report.md`（人读 SSOT）。
  - 落盘场景：写入 `40-final/decision-report.md`。
  - 非落盘场景：在对话中输出等价 Markdown，并在首行显式标注 `# decision-report.md`（便于复制落地与审计）。
- **报告结构（Must）**：至少包含：Executive Summary / Decision / Option Cards / Comparison Matrix / Verdict Summary / Risks & Sign-off / Acceptance Checklist / Revisit Triggers / Appendix（备选方案简述）。

---

## 7) 交付形态（最小闭环）
对外（给下游流程消费）的“最小闭环交付”应是：
- `40-final/decision-report.md`（人读 SSOT，Must；独立使用模式也必须输出，见 6.5）
- 报告建议固定章节：Executive Summary / Decision / Option Cards / Matrix / Verdict Summary / Risks & Sign-off / Acceptance Checklist / Appendix
- + 关键机读 SSOT（至少 options/verdicts/profile 摘要之一）
- + `Acceptance Checklist`（可执行的 DoD）
- + `evidenceRoot` 指针（可回放审计）

以上就是基于 Case 01–30 抽象出的流程/状态机设计要点，可直接作为“skill 的运行链路定义”进入你们下一步的决策拆解。


## 并行分析 Agent #2（产物/机读合同）原文

下面是基于 Case 01–30（尤其 Case 05/14/15/17/21–30 对“证据合同/机读产物/脱敏与 restricted 指针”的实证）抽象出来的“产物与机读合同”建议清单，可直接落到方案文档里作为 skill 的 **EvidenceRoot/Artifacts Contract** 章节。

## 1) 推荐 EvidenceRoot 目录结构与命名（可续跑 + 可审计 + 可回放）

- **EvidenceRoot 根**：建议固定到一个“默认被忽略/不入库”的根，例如你们现有模式 `docs/todo/logs/<topic>/<runId>/`（Case 实证里已验证可用）。
- **runId 命名**：`<topic>-YYYYMMDD-runNN`（你们已用 `spd-sim-20260421-run01`），要求全局唯一且可排序。
- **单 run 的顶层必备文件**
  - `RUNBOOK.md`：冻结本次运行规则（独立性、门禁、角色集合、写集合规则）。
  - `INDEX.md`：入口索引（按 case、按内容类型、按最终报告链接）。
  - （可选增强）`run-meta.json`：机读 run 元信息（见第 2 节）。
- **case 目录结构（建议保持你们已验证的分层约定）**
  - `case-XX/00-input/`：冻结输入合同（input.md + 可选 input.json）
  - `case-XX/10-ideation/round1/`：多角色独立提案（每个角色 1 文件）
  - `case-XX/20-synthesis/`：汇总产物（options + 矩阵 + blocking questions）
  - `case-XX/10-ideation/round2/`：第二轮（只回答阻塞问题/补齐缺口）
  - `case-XX/30-judging/`：评审轮（全新角色 verdict，每个 1 文件）
  - `case-XX/40-final/`：最终决策（decision-report 为主）
  - `case-XX/90-meta/`：trace + requirements（抽象能力点与边界）
- **落盘原则（强建议）**
  - **Append-only**：同一 runId 下的关键机读产物禁止覆盖；如需修订，新增版本号或追加事件（Case 15/17 经验）。
  - **SSOT 单写者**：主进程只写 SSOT（例如 options/final/index）；子进程只写各自提案/评审证据，避免并行写冲突（Case 04/17）。

## 2) 关键机读产物清单（最小集合）+ 字段要点（可校验）

> 目标：让“是否完成闭环/是否可验收/是否可审计”可以机械判断，而不是靠人读。

### 2.1 run 级（建议）
- `run-meta.json`（建议）
  - `schemaVersion`
  - `runId`, `topic`
  - `createdAt`, `timezone`
  - `repo`（repo 根、branch、commit 可选）
  - `policy`（strict/compat 默认、failClosed 策略摘要）
  - `redactionPolicyId`（脱敏策略版本）
  - `cases[]`（case 列表与 contentType 映射）

### 2.2 case 级（Must）
- `case-meta.json`（Must）
  - `schemaVersion`
  - `caseId`（如 `case-21`）、`title`
  - `contentType`（Spec/ADR/Plan/QA/Ops/Sec/Analytics/Comms/Creative/Enablement…）
  - `riskClass`（例如 low/medium/high 或自定义）
  - `profileId` + `profileVersion`（该 case 使用的 profile）
  - `status`（state machine 当前状态：FREEZE_INPUT/DISPATCH_R1/…/FINAL/META）
  - `ssot`：指向该 case 的 SSOT 产物路径（options/final）
- `input.json`（建议与 `input.md` 配对，机读更稳）
  - `problem`, `successCriteria`, `constraints`, `nonGoals`
  - `evidencePointers[]`（至少 2 个；每个含 `kind/path/why/sensitivity`）
  - `rubric`（评审维度与权重，或引用 profile 的 rubric）
- `options.json`（Must；对应 `20-synthesis/options.md` 的机读版）
  - `options[]`：每个 option 含 `id/name/summary/pros/cons/risks/costs/gates`
  - `comparisonMatrix`：维度、分值、解释
  - `blockingQuestions[]`：每条含 `question/owner/neededEvidence`
- `verdicts.json`（Must；聚合评审轮）
  - `verdicts[]`：`judgeRole`（tech/product/risk…）、`pick`、`confidence`、`tradeoffs`、`topRisks`、`requiredValidations`、`signOffConditions`
  - `missingVerdictsPolicy`：缺 role 时是否 BLOCK
- `decision.json`（Must；最终裁决机读 SSOT）
  - `finalPick`（optionId 或 composite）
  - `must/should/niceToHave`（条目化）
  - `failClosedGates[]`（阻断条件列表）
  - `acceptanceChecklist[]`（DoD）
  - `handoff`（移交到下一环节需要的输入/责任人/下一步验证）
  - `alternatives[]`（备选简述 + 取舍）
- `trace.jsonl`（Should；事件流/过程回放，append-only）
  - event 形态：`timestamp`, `stage`, `actor`, `artifactRef`, `decisionRef`, `note`
  - 价值：用于“为什么这么选/哪里被门禁卡住/如何续跑”（Case 17）。

### 2.3 内容类型专用机读附录（按 profile 装配，Should→Must 可渐进）
- Spec（Case 21）：`spec-pack.json`（schemaVersion + schemaRef + examplesIndex + compatRules）
- QA/Audit（Case 24）：`evidence-manifest.json`（required/optional artifacts + summary + pointers）
- Analytics（Case 27）：`analysis-pack.json`（metricVersion + queryPointers + resultsSummary）
- Creative（Case 29）：`creative-manifest.json`（deliverables + owners + deadlines + constraints + licensing)
- External Comms（Case 28）：`claims.json`（claim→evidence + approvers/expiry/scope）

## 3) 人读 vs 机读 SSOT 策略（防退化、可渲染）

- **原则**：机读为 SSOT，人读由渲染生成或至少可从机读校验一致性（Case 05/24 的“报告退化风险”证明这点关键）。
- **建议落点**
  - 机读：`decision.json/options.json/verdicts.json` 为 SSOT
  - 人读：`decision-report.md/options.md/verdict-*.md` 作为解释层
- **一致性校验（门禁思想）**
  - 人读里的关键字段（Final Pick、Must/Fail-Closed、Approvers、claims）必须能映射回机读字段；缺失即 FAIL 或至少 BLOCK 发布/对外使用（Case 28）。
- **双视图（public/internal）**
  - public：更强脱敏、只给 restricted 指针
  - internal：保留更多审计信息但仍不粘贴 secrets/原始日志（Case 26/27）。

## 4) 证据指针 / 脱敏 / restricted 机制（必须合同化）

- **Evidence Pointer（统一结构，推荐机读）**
  - `kind`：`doc|rule|code|log|screenshot|dataset|external`
  - `ref`：repo-relative path 或外部存储的 locator
  - `commitRef`（可选）：用于“在某 commit 上可复现/可定位”（Case 02 经验）
  - `summary`：一行摘要（避免必须打开敏感内容）
  - `sensitivity`：`public|internal|restricted`
  - `access`：如何获取（owner/系统/审批方式）
- **restricted 默认策略（Case 26/27/28）**
  - 正文禁止粘贴：密钥、配置片段、原始日志、用户数据样本
  - 用“指针 + 脱敏摘要 + 哈希/校验”替代复制
- **脱敏规则（建议最小可执行合同）**
  - secrets 模式（token/key/password/authorization header）
  - 绝对路径模式（避免泄露机器信息与不可复现引用）
  - PII/用户标识
  - 对外材料的“未经批准承诺”（日期/价格/合规措辞）
- **建议补充一个机读脱敏清单（Should）**
  - `redaction-report.json`：命中规则、位置、处理方式（remove/mask/pointer-only）、残余风险

## 5) 必须的回归 fixtures（正例/负例，防退化优先级=代码测试）

> Case 24/25/26/28/30 的共同结论：没有负例库就一定会退化。

- **fixtures 目录建议**
  - `fixtures/pass/`：最小合规样例（每种 contentType 1 份）
  - `fixtures/fail/`：每条 fail-closed gate 对应 1 个故意失败样例
  - `fixtures/expected/`：预期 gate 结果（PASS/FAIL + reason codes）
- **通用负例（跨内容类型）**
  - 缺证据指针（<2）→ BLOCK（Case 01/08 类问题）
  - 提案互引/非独立（可用 trace 规则检测）→ BLOCK（独立性门禁）
  - 缺 risk verdict 或 verdict<3 → BLOCK（Case 08/09/10 的风险依赖）
  - options 无矩阵/无 blocking questions → BLOCK（Case 01/04/06）
- **内容类型负例（Case 21–30 直接对应）**
  - Spec：breaking change 无迁移/废弃窗口；缺 examples/fixtures
  - QA/Audit：claim 无 evidence；manifest required 缺失；含绝对路径/secret
  - Ops/Incident：出现 write 操作但无 Execution Intent/token/rollback/verify
  - Security/Compliance：controls 无验证步骤；对外 claim 无适用范围/证据
  - Analytics：缺 metric definition/metricVersion；正文含敏感数据样本；无 next step/owner
  - External Comms：缺 Approvers/Expiry/Scope；出现未批准价格/日期承诺
  - Creative：缺 Do-Not；素材无授权说明；deliverables 无 owner/验收
  - Enablement：无标签命令块；危险命令无授权说明；链接预算超限无理由

如果只允许我给一句“最小落地建议”：把 **`decision.json/options.json/verdicts.json + evidencePointers（含 sensitivity）+ fixtures/fail`** 作为该 skill 的 P0 “机读合同”，其余（渲染、pack、扫描器）都可以在 strict/compat 与 warning→fail-closed 的路线图里逐步升级。


## 并行分析 Agent #3（安全/权限/边界）原文

# 安全/权限/边界：面向“并行提案→并行评审→最终决策”流程的 Skill 设计要点（基于 Case 01–30，重点 03/11/20/25/26/28/30）

> 目标：把“研究/决策阶段”与“执行/写入阶段”强隔离；把泄密/误触发/越权承诺/危险操作的风险从“靠人记住”提升为“默认 fail-closed + 可审计”。

---

## 0) 威胁模型（这类 Skill 最常见的 6 个失效模式）
1) **过早写入**：用户只是讨论/要方案，系统却生成文件、改仓库、触发管理命令（Case 11/03）。
2) **误把示例当执行**：文档里出现命令块或操作步骤，被复制执行或被自动化当成可执行脚本（Case 20/30/25）。
3) **证据二次泄漏**：把 logs/配置/token/绝对路径等敏感信息粘进正文或对外材料（Case 24/26/27/28）。
4) **越权承诺**：对外材料出现未经审批的日期/价格/合规承诺或“绝对化承诺”（Case 28）。
5) **权限不可追责**：谁批准、何时批准、批准范围是什么、是否过期不可审计（Case 25/28/03）。
6) **治理退化**：从“严”逐步变成“随便”，warn-only 长期存在，最终失信（Case 06/10/20/28/30 的共性边界）。

---

## 1) 防过早写入/误触发：Write-Intent Gate（Must）
### 1.1 两阶段总原则（必须内置在 Skill 的控制面）
- **默认研究态（DISCUSSION/RESEARCH）**：只允许读/分析/生成“提案与决策文档草案（在 evidenceRoot）”，禁止写入仓库交付区、禁止修改代码、禁止运行破坏性命令。
- **显式执行态（APPLY/EXECUTION）**：只有在满足“写入意图协议”后，才允许任何写操作或可执行动作。

### 1.2 写入意图协议（Write-Intent Protocol）
- **dry-run 默认**：任何“可能写”的动作都先输出 plan + diff-scope + 将写入的文件清单（write set），不落盘或只落盘到临时区。
- **显式 apply**：必须由用户给出 `--apply` 或等价的“确认信号”才允许写入。
- **nonce/token**（用于防对话误触发）：生成一次性 nonce，用户需回填；高风险动作使用更强 token（可带 TTL）。
- **scope 约束**：授权必须是“范围化的”——允许写哪些目录/文件类型/最大文件数/是否允许覆盖/是否允许执行外部命令。
- **fail-closed**：缺少 apply/nonce/scope 任一项 → **阻断**，不得“降级继续”。

### 1.3 SSOT 单写者 + 并行边界（与 Case 04/17 一致）
- **主进程唯一写 SSOT**：`options.md`、`decision-report.md`、最终汇总等只能由主进程写；子代理只写各自 `round*/`、`verdict-*.md` 等独立产物。
- **并行写集合互斥证明**：如果写集合可能重叠，必须降级为串行或阻断（避免并行写冲突导致“部分写入/错写入”）。

---

## 2) restricted 证据策略：指针化/双视图（Must）
### 2.1 “正文不粘敏感证据”的默认策略
- **默认只写 evidence pointers**：日志、配置、客户材料、数据样本等敏感物一律不进入正文；正文仅保留摘要与指针。
- **restricted 指针的最小合同字段**：
  - `kind`（log/config/screenshot/query/contract/approval…）
  - `location`（路径/对象存储键/工单号）
  - `access`（restricted/public）
  - `owner`、`expiresAt`（可选但强建议）
  - `redaction`（脱敏规则/是否仅摘要）

### 2.2 双视图输出（对外/对内）
- **内部审计版（Auditor/Internal）**：更多指针、更细的验证步骤，但仍不直接粘贴 secrets。
- **对外发布版（External/Public）**：更强的脱敏、范围声明、审批块；任何未批准承诺必须不存在（或显式标注“待确认”且可被 gate 阻断）。

---

## 3) 扫描门禁：secrets/绝对路径/越权承诺/危险命令块（Must）
> 核心：把“内容安全”做成可回归的 gate，而不是靠审稿人肉眼。

### 3.1 secrets / 敏感模式扫描（所有类型通用）
- 命中 token/key/密码/私钥/连接串等模式 → **FAIL**。
- 命中“客户识别信息/用户标识/原始数据样本” → **FAIL**（尤其 Analytics/Sec/QA/External）。

### 3.2 绝对路径污染扫描（QA/Audit、Logs、Runbook、KB 强相关）
- 文档/报告/manifest 出现绝对路径（含用户目录、CI workspace）→ **FAIL** 或至少高优先级阻断（Case 24）。

### 3.3 越权承诺扫描（External Comms 特化，Case 28）
- 对外字段（日期/价格/合规承诺/SLA）如果未绑定审批块或标注“未批准” → **FAIL**。
- 绝对化措辞（如“永远/100%/保证”）可设为 warn→fail-closed 的迁移策略。

### 3.4 危险命令块/操作指令扫描（Runbook/KB/指令型写作，Case 20/25/30）
- **无标签命令块 → FAIL**（必须带 Execution Intent 标签：EXAMPLE/READ-ONLY/DANGEROUS）。
- 出现写操作命令但没有“requires approval / token / rollback / verify”段落 → **FAIL**。
- 对 `DANGEROUS` 块要求额外：影响面、回滚、验证、授权条件齐全，否则阻断。

---

## 4) 授权范围化（scope/TTL）与审计（Must）
### 4.1 Scope（范围）建议维度
- `pathsAllowlist`：允许写入的目录/文件模式（例如只允许写 `docs/todo/logs/...` 或指定 evidenceRoot）。
- `commandsAllowlist`：允许执行的命令族（研究阶段通常为空）。
- `maxWrites` / `noOverwrite`：写入数量与覆盖策略。
- `network`：是否允许网络访问（多数决策阶段不需要；需要则必须可审计且可关闭）。

### 4.2 TTL（有效期）与审批人链路
- 所有授权都带 `expiresAt`（默认短 TTL），过期自动失效。
- 对外材料必须有 **Approvers/Date/Expiry/Scope**（Case 28 的审批块合同化）。

### 4.3 审计日志（Audit Log）的最小要素
- 谁（actor）、何时（timestamp）、做了什么（action）、基于哪个输入合同（input hash/runId）、写了哪些路径（write set）、批准凭据是什么（token/nonce，不记录明文但记录指纹/哈希）、结果（pass/fail + 原因）。

---

## 5) 负例库与回归策略（Should→Must，按风险等级升级）
### 5.1 为什么负例是“内容治理的单元测试”
- 内容风险（泄密/越权/误触发）很容易在迭代中“悄悄退化”，负例 fixtures 是最强的防退化手段（Case 24/25/26/28/30）。

### 5.2 必备负例类型（建议按 contentType 维护）
- **通用负例**：含 secrets、含绝对路径、缺 evidence pointers、缺 Non-Goals、缺阻塞问题清单、仅口号无 trade-offs。
- **External**：未审批的日期/价格/合规承诺；claim 无 evidence；缺 Approvers/Expiry/Scope。
- **Ops/KB**：无标签命令块；危险命令无授权/回滚/验证；把 DANGEROUS 放在 read-only 段落。
- **Security/Analytics**：把敏感日志/样本直接粘贴进正文；restricted 不生效；controls 无验证步骤。

### 5.3 回归触发点（推荐）
- 每次调整 profile/rubric/gates/扫描规则 → 必跑负例回归。
- 每次新增内容类型或新增“对外输出模板” → 必跑 External 负例集。

---

## 6) 明确边界（Skill 不该做什么）
- **不应在研究阶段创建/修改交付文档或代码**（除 evidenceRoot 的过程性证据，且仍需 write-intent）。
- **不应自动发布对外材料**；对外材料只能生成 draft，并必须通过审批块与 gate。
- **不应把 restricted 证据“复制进正文”来追求自包含**；自包含应通过“指针 + 摘要 + 验证步骤”实现。

---

如果你需要，我可以把以上内容进一步压缩成“可直接贴入方案末尾的 Agent #3 日志格式”（含：Must/Should/Fail-Closed 清单 + 建议字段表），方便主进程汇总对齐。


## 并行分析 Agent #4（profile/内容类型装配）原文

## 1) Profile 体系目标（为什么要“装配”而不是一套 rubric 走到底）
基于 Case 01–20 的通用结论 + Case 21–30 内容类型实证，可以把 profile 体系的目标定为：

- **同一条两轮并行流程骨架不变**（Freeze Input → R1 ideation → synthesis → R2 answers → judging → final → meta），但
- **按 `contentType × riskClass` 装配不同的**：角色集合、rubric 权重、必交付产物、fail-closed 门禁强度、restricted/审批策略、扫描规则与负例 fixtures。

核心原则：**“类型化最小合同 + 风险叠加层”**（type-first, risk-overlay）。

---

## 2) Profile 的最小数据模型（建议 YAML/JSON）
下面是“能驱动装配 + 能做门禁 + 能落证据”的最小字段集合（可 YAML/JSON 等价表达）：

```yaml
profileId: "contentType/spec@v1"
profileVersion: "1.0.0"         # semver；变更影响门禁/产物时需 bump
contentType: "spec"             # enum：spec/adr/plan/qa_audit/ops_incident/security_compliance/analytics/comms/creative/enablement
riskClass: "high"               # enum：low/medium/high/critical

modes:                          # strict/compat（Case 10/21/22/23）
  default: "strict"
  compatPolicy:
    allowed: true
    requiresExplicitLabel: true
    compatMinFields: ["finalDecision", "options>=2", "risks", "validation"]  # 示例：ADR

roles:                          # 两轮角色装配（Case 01-20 通用）
  ideationR1: ["product", "architect", "implementation", "qa", "risk_security"]
  ideationR2: ["product", "architect", "implementation", "qa", "risk_security"]
  judging: ["judge_tech", "judge_product", "judge_risk"]
  roleOverlays:                 # 按内容类型/风险叠加
    add: ["legal"]              # 如 comms/security
    remove: []

rubric:                         # 可配置维度+权重（Case 04/08/10）
  dimensions:
    - id: "adoption"            # 采用率/摩擦
      weight: 0.1
    - id: "ssot_evidence"       # SSOT/证据可回放
      weight: 0.25
    - id: "verifiability"       # 可验收/可复跑
      weight: 0.25
    - id: "risk_boundary"       # 风险边界/合规/授权
      weight: 0.25
    - id: "cost_time"           # 成本/时效
      weight: 0.15
  requiredVerdictFields: ["pick", "confidence", "tradeoffs", "topRisks", "nextValidation", "signOffConditions"]

artifacts:                      # 每阶段“必交付最小产物”
  inputContract:
    required: ["00-input/input.md"]
  synthesis:
    required: ["20-synthesis/options.md"]   # Option Cards + matrix + Blocking Questions
  judging:
    minVerdicts: 3
    required: ["30-judging/verdict-*.md"]
    mustInclude: ["judge_risk"]
  final:
    required: ["40-final/decision-report.md"]
  meta:
    required: ["90-meta/trace.md", "90-meta/requirements.md"]

gates:                          # fail-closed vs warn（Case 05/06/09/10/24/28）
  failClosed:
    - id: "missingEvidencePaths"
      when: "input.evidencePaths < 2"
      message: "输入合同证据不足"
    - id: "noBlockingQuestions"
      when: "synthesis.blockingQuestions == 0"
  warn:
    - id: "compatUsed"
      when: "mode == compat"
      message: "compat 模式：需标注并限制使用范围"

securityPolicy:                 # Case 03/11/20/25/26/28/30
  writeIntent:
    default: "dry-run"          # 默认不写入；apply 才写入
    requireTokenFor: ["high", "critical"]
    scopeWhitelistRequired: true
    ttlRequired: true
  restrictedEvidence:
    default: "pointer_only"     # 正文只允许指针/摘要/脱敏片段
    publicVsInternalViews: true
  scanners:
    blockPatterns: ["secrets", "absolute_paths", "unapproved_claims", "untagged_commands"]
    allowlistWithExpiry: true

parallelPolicy:                 # Case 04/17：并行写集合/SSOT 单写者
  ssotWriter: "main_process"
  childAgentsWriteScope: "own_files_only"
  eligibility:
    states: ["PARALLEL_OK", "SERIAL_ONLY", "BLOCKED"]
    defaultOnUncertain: "SERIAL_ONLY"

typeSpecific: {}                # contentType 特有字段（见第4节）
```

> 解释：`typeSpecific` 用来放 Spec 的 schema/exmaples 要求、QA 的 evidence-manifest、Comms 的审批块等，避免把“类型差异”硬塞进通用层导致过度工程化。

---

## 3) 默认 profile 与覆盖（override）规则
### 3.1 默认（Base）策略
- **Base 流程**：固定 7 状态机骨架（你们文档 8.7），所有类型共享。
- **Base 产物**：固定 00/10/20/30/40/90 目录的最小集合（Case 15/17/14 的证据根思路）。
- **Base 角色**：R1/R2 五视角（product/architect/implementation/qa/risk_security），Judging 三视角（tech/product/risk）。

### 3.2 覆盖（Overlay）优先级（建议从高到低）
1) **Risk Overlay（风险叠加层）**：`riskClass` 决定门禁强度、restricted、审批/授权、扫描规则与负例库强制性。
2) **ContentType Overlay（内容类型层）**：`typeSpecific` + 角色增删 + 必交付机读合同（如 schema/manifest/approval block）。
3) **Org/Repo Policy Overlay（组织/仓库层）**：例如 doc root policy、strict/compat policy SSOT、允许的外部引用域、默认脱敏规则等（Case 01/10/16）。
4) **Task Override（任务级）**：仅允许“收紧”而非“放宽”（fail-closed 原则）；放宽必须走 waiver（owner+expiresAt+evidence）。

### 3.3 “不确定信息”的处理
- 输入合同允许 DRAFT 假设分支，但 **门禁裁决要 fail-closed**：不确定→降级串行 / 阻断（Case 09/23 的精神）。

---

## 4) 10 类内容类型的差异化装配要点（Case 21–30 实证）
（原文较长，已在并行分析输出中详述：Spec/ADR/Plan/QA/Ops/Sec/Analytics/Comms/Creative/Enablement 的 typeSpecific.must 与 gates.failClosed 差异。）

---

## 5) Profile 演进/版本化策略（strict/compat、warning→fail-closed）
### 5.1 版本化原则（建议 semver）
- **MAJOR**：改变必交付产物/门禁含义/字段语义（会导致旧证据不再通过）。
- **MINOR**：新增可选字段、新增门禁但默认 warn、扩展角色集合（不破坏旧的 pass 条件）。
- **PATCH**：文案/渲染/错误提示等不影响裁决的修订。

### 5.2 warning→fail-closed 迁移节奏（Case 06/08/10/20 的共同模式）
- Phase 0：只生成报告与 warnings（不阻断），同时落盘 fixtures（含负例）。
- Phase 1：对 **PR diff-scope** 生效的 fail-closed（仅阻断新增/变更的违规）。
- Phase 2：扩大到全仓或关键目录；引入 waiver（owner+expiry+evidence）。
- Phase 3：固定为默认 fail-closed；兼容白名单必须带到期。

### 5.3 strict/compat 的治理
- compat 不是“偷懒模式”，而是 **明确标注的低风险路径**：
  - compat 允许减少机读附录/部分段落，但不得移除“Final Decision/Options/Risks/Validation/边界声明”。
- **compat 的使用需要记录**：原因、范围、到期时间（避免长期退化）。

---

## 6) 如何保持跨域通用性，又避免过度工程化（落地建议）
- **先把“通用骨架 + 10 个 contentType overlay”做薄**：只冻结每类 5–10 条 MUST + 3–5 条 FAIL 门禁；其它放 SHOULD。
- **类型差异放在 `typeSpecific`，通用不被污染**：通用层只管状态机、独立性、SSOT、证据根、并行边界、写入意图、安全扫描框架。
- **把“机读合同”限定为最小**：Spec/QA/Comms 等确实需要机读 SSOT；其它类型先 “人读+可选机读附录”，避免一次性全类型强制。
- **把“成本/摩擦”纳入 rubric 并可权重化**：低风险任务不要被 critical 的流程拖慢；靠 riskOverlay 调整门禁与产物，而不是人为删流程。
- **负例 fixtures 是最强防退化，但要按类型选取**：例如 enablement 的“无标签命令块”、comms 的“未批准承诺”、security 的“敏感证据粘贴”等，避免泛滥。

---

如果主进程需要我把上述内容进一步“压缩成可直接粘贴到方案末尾的 1–2 页附录格式”（含一个 profile YAML 模板 + 10 类 overlay 表格），我也可以再输出一个更“文档化”的版本。


## 并行分析 Agent #5（生态集成/触发/UX）原文

# 并行分析 Agent #5：生态集成 / 触发 / UX（面向“被其它流程调用”的决策流程 Skill）

> 目标：把“通用两轮并行提案→并行评审→最终决策”的能力做成**可被 PRD/架构/开发计划/审计等 Skill 自动或手动调用**的基础设施能力，同时**不干扰主流程**、**默认安全**、**可审计可回放**。

---

## 1) 触发时机：手动 / 自动，以及与阶段门禁的关系

### 1.1 手动触发（人明确表达“要决策闭环”）
适用：问题尚不明确、需要发散；或跨团队争议需要可回放裁决。
- Prompt 入口（独立使用）：按 6.5 的 Prompt Contract 显式输入 `[SwarmDecisionRun: start]` + `contentType/riskClass/timeBudget/TaskDials`，系统才进入 FREEZE_INPUT；否则按“讨论/咨询”处理不启动 run。
- CLI 入口（可选）：`start-decision`（创建 runId + freeze input）/ `resume-decision`（续跑）。
- 必须满足：**输入合同冻结**（Problem/Evidence/Constraints/Success/Rubric/Non-Goals）。
- 输出（Must）：`decision-report.md`（人读 SSOT；独立使用模式与被调用模式一致，落点为 `40-final/decision-report.md`）。
- 与阶段门禁关系：
  - 明确处于 **方案/研究阶段**：只允许生成“提案/评审/报告/证据指针”，禁止落地实现与写仓库（除非显式 write-intent）。

### 1.2 自动触发（由上游 Skill 在特定节点调用）
适用：上游 Skill 的输出**不满足门禁**或**存在多解且需裁决**，自动进入“决策闭环”。
- 推荐自动触发点（典型）：
  - 上游生成器（PRD/架构/开发计划）出现**阻塞问题**：信息缺失、冲突、不可验收、风险边界不清。
  - 门禁技能（doc-quality-gate）判定 FAIL 且需要“方案裁决”（不是纯修补）时：比如 fail-closed 边界、目录政策、对外 claim 合规等。
  - 语义修正（doc-semantic-repair）进入“候选集→裁决”阶段，需要多角色裁决候选修补路径。
- 自动触发必须是 **fail-closed 可控**：
  - 默认不写入上游产物，只在 `docs/todo/logs/.../runId/` 产出证据与报告；上游选择是否采纳（apply）。

### 1.3 与“阶段门禁”的硬约束（防误触发/不越权）
- 方案闭环输出 ≠ 执行授权：任何“改代码/改文档/生成索引”必须二次确认（write-intent / apply token）。
- 自动触发只允许进入 **FREEZE_INPUT→IDEATION→JUDGING→FINAL→META**；禁止进入“实施/写回”阶段，除非上游显式切换到执行阶段并携带授权。

---

## 2) 与现有 Skill 的接口点（如何被调用/如何回传）

### 2.1 与 `prd-doc-generator` 的接口
- 调用时机：
  - PRD 产出遇到关键争议（目标用户/范围/成功指标/风险边界）或缺少可验收口径。
- 输入：PRD 草稿/阻塞问题列表 + 证据指针（竞品/研究/历史决策/规则）。
- 输出回传（给 prd-doc-generator 消费）：
  - `decision-report.md`（最终裁决与 trade-offs）
  - `requirements.md`（Must/Should、验收清单）
  - 可选：`decision-pack.yaml/json`（机读决策摘要，供后续生成器引用）

### 2.2 与 `arch-doc-generator` / `arch-pre-tech-selection` 的接口
- 调用时机：
  - 技术选型存在多解且权衡复杂（成本/安全/迁移/兼容），或需要 strict/compat 决策。
- 输出回传：
  - ADR 型裁决（含 revisit triggers、拒绝理由、验收与迁移）
  - 对“必须门禁/不可降级边界”的冻结条目（供架构文档落地）

### 2.3 与 `dev-plan-generator` / `execute-dev` 的接口
- 调用时机：
  - 开发计划缺阶段门禁/验收/依赖，或并行边界不清（SSOT 单写者、写集合互斥）。
- 输出回传：
  - `plan` 类型裁决：阶段结构、Gates/Acceptance/Rollback、并行资格裁决（≥三态）
  - 交接块（handoff checklist），供执行阶段严格照单

### 2.4 与 `doc-quality-gate` / `doc-semantic-repair` 的接口
- `doc-quality-gate`：
  - 若 FAIL 原因是“内容不足以裁决/存在冲突”，应把 FAIL 结构化为 Blocking Questions，自动触发决策闭环生成“补齐路线图”，而不是直接修正文档。
- `doc-semantic-repair`：
  - “候选集→裁决→修补”天然对应并行裁决：可把候选修补方案作为 ideation 输入，评审轮输出选择理由与回归条件。

---

## 3) CLI / 交互体验（以“最少打扰 + 强约束”为设计目标）

### 3.1 入口体验：三段式（Start → Run → Apply）
- Start（创建 runId，冻结输入合同）：
  - 引导用户补齐最小输入字段；要求至少 2 条证据指针（repo 内路径/规则/日志索引）。
- Run（两轮并行 + 汇总 + 并行评审）：
  - Round 1：多角色独立提案
  - Synthesis：自动生成 Option Cards + 对比矩阵 + Blocking Questions
  - Round 2：仅回答 Blocking Questions（防止二次发散）
  - Judging：全新角色输出 verdict（pick+confidence+tradeoffs+risks+DoD）
- Apply（可选，严格受控）：
  - 默认 **不写回**上游文档/代码；只提供“可应用补丁/变更建议清单”。
  - 需要显式 `--apply` + scope + TTL 或一次性 token。

### 3.2 阻塞问题收集与收敛机制
- UI/交互必须把 Blocking Questions 当作“第二轮唯一输入”：
  - 提供按问题逐条回答的表单式体验（不允许长篇重写提案）。
  - 未回答阻塞问题：直接 BLOCKED，不进入评审。

### 3.3 短名单 / 组合方案（Composite）的一等支持
- UX 要求：
  - 允许“Option C + D”这种组合裁决，并自动生成迁移路线图（warning→fail-closed、白名单到期）。
  - 强制记录“不选其它 option 的拒绝理由”，避免执行期翻案。

### 3.4 报告渲染与多视图输出
- 默认输出：
  - 人读 `decision-report.md`
  - 机读摘要（可选，但建议）：用于被其它 skill 消费
- 双视图（强建议，特定类型必需）：
  - 内部审计版（含更多证据指针）
  - 对外/公开版（更强脱敏 + restricted 指针）

---

## 4) 指标与质量度量：可审计、可回放、采用率友好

### 4.1 过程质量（Process Quality）
- 独立性：提案轮互不引用（可用 trace 证明）
- 完整性：是否生成 Options+矩阵+阻塞问题；是否有 ≥3 verdict 且含 risk 视角
- 可续跑：任一步骤中断后能从 state 恢复，不重写历史产物（append-only）

### 4.2 产物质量（Artifact Quality）
- 决策可回放：trade-offs、拒绝理由、revisit triggers 是否齐全
- 可验收：是否有 DoD/checklist；是否明确 fail-closed vs warn 边界
- 证据质量：claim→evidence 映射（对外/合规）是否完整；restricted 策略是否遵守

### 4.3 采用率与价值（Adoption & Value）
- Time-to-decision（从冻结输入到最终裁决）
- 返工率（执行阶段因缺门禁/验收导致的返工次数）
- 漂移率（同类内容类型的 profile 被绕过/降级的比例）
- 安全事件数（泄密/越权承诺/危险命令误触发的拦截次数）

---

## 5) 风险清单：对主流程干扰 / 成本 / 泄密，以及控制策略

### 5.1 干扰主流程（“一调用就把流程拖长”）
- 风险：自动触发频繁导致 PRD/架构/计划生成链路变慢。
- 控制：
  - 只在 FAIL 且属于“需要裁决”类别触发；纯修补走 semantic-repair。
  - 允许轻量 compat 模式（但必须显式标注 + 保留最小必填）。

### 5.2 成本膨胀（并行角色过多、输出过长）
- 风险：角色数固定 5+3 可能成本过高。
- 控制：
  - profile 配置可降级角色集合，但必须保留 risk/ops_security。
  - 强制“Round 2 只回答阻塞问题”，限制 token 与篇幅预算。

### 5.3 样本不足（并发规模过小导致漏解/过早收敛）
- 风险：若提案轮/评审轮的并发规模过小，容易出现同质化、漏掉关键 option、或在证据不足时被迫“投票式决策”。
- 控制：
  - 采用 6.4 动态扩容：以“多样性不足/证据不足/分歧过大/置信不足”为触发信号，按批次追加角色直到满足停止条件或触达预算上限。
  - 对 Creative/战略类启用 Option 多样性门禁（至少 1 个 moonshot）；对 Sec/Comms/Ops 类优先增大 `J` 并强制 risk/ops_security judgeRole。
  - 若预算限制无法扩容：FINAL 必须显式标注“样本不足风险”，并把其作为 revisit trigger（见 6.3.3）。

### 5.4 泄密与二次扩散（证据复制进正文、对外承诺越权）
- 风险：日志/密钥/绝对路径、客户敏感信息进入报告；对外材料出现未批准承诺。
- 控制：
  - 默认 restricted：正文只摘要 + 指针；敏感证据不复制。
  - 对外内容强制审批块（Approvers/Expiry/Scope）+ claim→evidence，缺失 fail-closed。
  - 扫描门禁 + 负例 fixtures 回归（secrets/绝对路径/危险命令/绝对化承诺等）。

---

## 11. Skill 生成输入包（Spec Pack）：从“研究文档”到“可直接生成 skill 资产”的冻结规格

> 本节把本文抽象的流程/门禁/产物合同进一步收敛为“可直接生成 `.claude/skills/<name>/` 目录资产”的上游输入包（Spec Pack）。
>
> 注意：本文仍不执行生成/落地实现；本节只冻结字段、模板与机读合同，作为后续实现与验收的 SSOT。

### 11.1 冻结项总览（生成 skill 的最小输入）

- Skill 元信息（用于 `skill.md` Front Matter）：`name/description/keywords/tags/trigger_phrases/docLinks`
- canonical EvidenceRoot 与产物布局（strict）+ compat 适配策略（迁移期/消费旧证据）
- 模板集合（`templates/`：Prompt Contract / Proposal / Verdict / Decision Report / Runbook）
- 机读 Schema 集合（`schemas/`：`case-meta/input/options/verdicts/decision/trace`）
- 默认策略冻结：采样（R1/J 扩容阈值与批次）、门禁（fail-closed 点位）、脱敏（restricted 指针）、写入意图（Write-Intent Gate）
- P0 验收/回归清单（正例/负例 fixtures），用于“生成 skill 后是否可用”的机械判断

### 11.2 目标 skill 元信息冻结（建议值，可直接转写为 `skill.md`）

> 约束：`name` 必须 kebab-case；触发词避免过宽；需与现有 `.claude/skills/*` 名称/触发词保持低冲突（避免误触发）。

建议冻结为：

```yaml
name: swarm-decision
description: 通用“两轮并行提案→并行评审→最终裁决”的决策闭环（可续跑、可审计、默认安全）
keywords: [Swarm, 并行决策, 提案, 评审, 裁决, Option Cards, Decision Report, EvidenceRoot, Profile, TaskDials]
tags: [决策流程, 元流程, 文档工程, 开发工具]
trigger_phrases:
  - "并行决策闭环"
  - "Swarm 决策"
  - "两轮并行提案评审"
  - "生成决策报告"
  - "start swarm decision"
  - "swarm decision run"
docLinks:
  schemaVersion: 1
  upstream:
    - kind: rule
      path: .claude/rules/文档头部关联链路标注规范.md
      relation: references
      ref: { repo: ".", commit: "<由 doc_links_writer 填充>", branch: "<由 doc_links_writer 填充>" }
    - kind: doc
      path: docs/00-研究设计/ARCH-通用两轮并行提案评审决策流程-决策型Skill创建-H研究文档-案例研究与能力需求-v1.0.md
      relation: references
      ref: { repo: ".", commit: "<由 doc_links_writer 填充>", branch: "<由 doc_links_writer 填充>" }
```

- 命名备选（可选但不推荐）：`swarm-decision-run`（更明确但偏长）；`decision-swarm`（可读性略差）。
- 触发词冲突规避原则（冻结）：
  - 禁止使用过宽触发词：例如单独 “并行”“决策”“方案”“评审”。
  - 触发词必须至少包含：`并行决策` 或 `Swarm` 或 `两轮并行` 之一（否则极易误触发其它技能链路）。

### 11.3 canonical EvidenceRoot 与产物布局（strict）+ compat 适配策略（冻结）

#### 11.3.1 EvidenceRoot 默认位置（建议）

- 默认（生产）：`docs/todo/logs/swarm-decision/<runId>/`
- 本文研究实证使用：`docs/todo/logs/swarm-decision-sim/<runId>/`（仅为模拟 run；生产默认不使用 `-sim`）

#### 11.3.2 strict canonical 布局（输出与校验的 SSOT）

> 设计目标：在不牺牲可审计/可回放的前提下，保持资产尽量少（轻盈优雅优先），并确保可被程序校验（fail-closed）。

```
<evidenceRoot>/
├── RUNBOOK.md
├── INDEX.md
├── run-meta.json                         # 可选（Should）
└── case-XX/
    ├── case-meta.json                    # Must
    ├── 00-input/
    │   ├── input.md                      # Must（人读合同）
    │   └── input.json                    # Should（机读合同）
    ├── 10-ideation/
    │   ├── round1/<roleId>.md            # Must（并行提案证据）
    │   └── round2/<roleId>.md            # 条件 Must（仅回答 Blocking Questions）
    ├── 20-synthesis/
    │   ├── options.json                  # Must（机读 SSOT）
    │   └── options.md                    # Must（人读渲染；与 options.json 一致性校验）
    ├── 30-judging/
    │   ├── verdict-<judgeId>.md          # Must（并行裁决证据）
    │   └── verdicts.json                 # Must（机读 SSOT，聚合 verdict）
    ├── 40-final/
    │   ├── decision.json                 # Must（机读 SSOT）
    │   └── decision-report.md            # Must（人读 SSOT）
    └── 90-meta/
        ├── trace.md                      # Must（过程记录）
        ├── trace.jsonl                   # Should（事件流；append-only）
        └── requirements.md               # Must（反推能力点）
```

- `roleId/judgeId`（冻结）：建议 kebab-case，且与 profile 中的 id 完全一致；否则触发 `compat` 或 BLOCK（按 riskClass）。
- Append-only（冻结）：
  - `trace.jsonl` 只追加；
  - SSOT JSON（`options.json/verdicts.json/decision.json`）如需修订，默认不覆盖：新增 `*-v2.json` 并在 `trace` 记录“替换关系”事件（Case 15/17）。

#### 11.3.3 compat 适配策略（仅用于迁移/消费旧证据）

- compat 的定位（冻结）：**允许读旧结构，但输出仍必须满足 strict canonical**（避免长期双标准导致治理退化）。
- 典型映射规则（示例，冻结为“允许但必须落痕”）：
  - 若发现 `case-XX/10-ideation/*.md` 且缺 `round1/`：映射为 `round1/`；`roleId` 由文件名推断，推断失败则置 `unknown-role-<n>` 并写入 `trace`。
  - `case-XX/30-judging/verdict-*.md` 与 `<judgeId>.md`：统一归一为 `verdict-<judgeId>.md`，并以 `verdicts.json` 作为聚合 SSOT。
  - 若缺 `options.json` 仅有 `options.md`：允许在 compat 中通过解析生成 `options.json`（并在 `trace` 记录 `generatedFrom: options.md`），但 strict 模式下缺 `options.json` 直接 BLOCK。

### 11.4 模板资产清单（`templates/`）与最小内容合同（冻结）

> 模板的目标是：让不同内容类型在不改通用骨架的前提下，只靠 profile/TaskDials 就能产出一致、可校验的最小闭环产物。

建议模板文件（未来落地到 `.claude/skills/swarm-decision/templates/`）：

- `prompt-contract.md`：Standalone Run 输入合同（对应本文 6.5）
- `proposal.md`：提案轮输出模板（Round 1/2 共用；Round 2 仅允许回答 Blocking Questions）
- `synthesis.md`：汇总模板（Option Cards + 对比矩阵 + Blocking Questions）
- `verdict.md`：评审 verdict 模板（judgeRole/pick/置信度/签字条件）
- `decision-report.md`：最终报告模板（人读 SSOT）
- `runbook.md`：RUNBOOK 模板（写集合互斥、门禁、采样策略、脱敏策略、strict/compat）

模板必须包含的最小字段（冻结摘要）：

- `proposal.md`：`OptionSeeds`（候选 id+摘要）、`EvidencePointers`、`KeyRisks`、`Assumptions`、`BlockingQuestions`
- `verdict.md`：`judgeRole`、`pick`、`confidence`、`tradeoffs`、`topRisks`、`requiredValidations`、`signOffConditions`、`rejectReasons`
- `decision-report.md`：Executive Summary / Decision / Option Cards / Comparison Matrix / Verdict Summary / Risks & Sign-off / Acceptance Checklist / Revisit Triggers / Appendix

### 11.5 机读 Schema v0.1（字段级约束 + 枚举 + 版本化策略，冻结）

> 目标：生成 skill 后可以用程序做 fail-closed 校验；同时允许 strict/compat 与 warning→fail-closed 演进（但必须可审计）。

#### 11.5.1 版本化策略（冻结）

- 每个机读文件必须包含 `schemaVersion`（整数）。
- 破坏性变更（字段改名/语义变更/枚举收紧）→ `schemaVersion` 主版本 +1（例如 `1`→`2`）。
- 兼容性新增字段 → `schemaVersion` 不变；reader 必须忽略未知字段。
- strict 模式只接受当前主版本；compat 模式可接受 allowlist（必须写入 `trace`，并在 FINAL 报告中标注 compat 输入来源）。

#### 11.5.2 公共类型：EvidencePointer（所有 schema 复用，冻结）

| 字段 | 类型 | 必填 | 约束/枚举 | 说明 |
| --- | --- | --- | --- | --- |
| `id` | string | ✅ | 建议 `ev-<n>` | 指针 id（用于引用与去重） |
| `kind` | string | ✅ | `repo_path|log|config|screenshot|query|ticket|contract|approval|external_url|other` | 指针类型 |
| `location` | string | ✅ | 必须 repo-relative 或 restricted 指针；禁止绝对路径 | 证据位置 |
| `why` | string | ✅ | 非空 | 为什么需要它 |
| `sensitivity` | string | ✅ | `public|internal|restricted` | 脱敏/可见性策略 |
| `redaction` | object |  |  | `{ policyId, notes }` |
| `owner` | string |  |  | 指针责任人 |
| `expiresAt` | string |  | RFC3339 | 指针有效期（对外/合规强建议） |

#### 11.5.3 核心机读文件（v0.1 必需字段摘要，冻结）

> 注：本文不在此阶段提供完整 JSON Schema 文件；但字段级约束已冻结，可直接转写为 `schemas/*.schema.json`。

- `case-meta.json`（Must）
  - `schemaVersion`（int, =1）
  - `caseId`（string，如 `case-21`）
  - `title`（string）
  - `contentType`（enum：`spec|adr|plan|qa_audit|ops_incident|security_compliance|analytics|comms|creative|enablement`；允许输入别名但 strict 输出必须归一化为 canonical）
  - `riskClass`（enum：`low|medium|high|critical`；允许输入别名但 strict 输出必须归一化为 canonical）
  - `profileId`（string）+ `profileVersion`（string/int）
  - `status`（enum：`FREEZE_INPUT|DISPATCH_R1|SYNTHESIS|DISPATCH_R2|JUDGING|FINAL|META|BLOCKED`）
  - `ssot`（object，必填）：
    - `optionsJson`（string，指向 `20-synthesis/options.json`）
    - `verdictsJson`（string，指向 `30-judging/verdicts.json`）
    - `decisionJson`（string，指向 `40-final/decision.json`）

- `input.json`（Should；缺失时必须至少有 `input.md`）
  - `schemaVersion`（int, =1）
  - `problem`（string）
  - `context`（string, optional）
  - `successCriteria[]`（string[], min 1）
  - `constraints[]`（string[]）
  - `nonGoals[]`（string[]）
  - `evidencePointers[]`（EvidencePointer[], min 2）
  - `rubric[]`（object[], min 1）：`{ dimension: string, weight: number(0~1) }`
  - `taskDials`（object, optional）：对应 6.5 的 goal/sampling 等结构

- `options.json`（Must；机读 SSOT）
  - `schemaVersion`（int, =1）
  - `options[]`（array, min 2）每项：
    - `id`（string，唯一；建议 `opt-01`）
    - `name`（string）
    - `summary`（string）
    - `pros[]/cons[]`（string[]）
    - `risks[]`（object[]）：`{ risk: string, severity: low|medium|high, mitigations?: string[] }`
    - `evidencePointers[]`（EvidencePointer[]，min 1；至少 1 条必须为 `repo_path` 或 `log`）
    - `gates[]`（string[]，列出必须通过的门禁/验证）
  - `comparisonMatrix`（object, Must）：`{ dimensions: string[], rows: { optionId: string, scores: number[], notes: string[] }[] }`
  - `blockingQuestions[]`（object[], Must）：`{ id: string, question: string, ownerRoleId?: string, neededEvidence?: EvidencePointer[], status: open|answered, answerRef?: string }`

- `verdicts.json`（Must；机读 SSOT）
  - `schemaVersion`（int, =1）
  - `verdicts[]`（array, min 3，且必须包含 1 条 `judgeRole=risk` 或等价 role）：
    - `judgeId`（string）
    - `judgeRole`（string，建议枚举：`tech|product|risk|ops_security|finance|legal_like|comms|research`）
    - `pick`（string，optionId 或 composite 表达式）
    - `confidence`（number, 0~1）
    - `tradeoffs[]`（string[]）
    - `topRisks[]`（string[]）
    - `requiredValidations[]`（string[]）
    - `signOffConditions[]`（string[]）
    - `rejectReasons[]`（string[]，对 top-2 以外至少给 1 条拒绝理由）

- `decision.json`（Must；机读 SSOT）
  - `schemaVersion`（int, =1）
  - `finalPick`（string）
  - `rationale`（string）
  - `failClosedGates[]`（string[]）
  - `acceptanceChecklist[]`（string[]，min 3）
  - `handoff`（object, Must）：`{ nextStage: string, owners: string[], inputs: string[], exitCriteria: string[] }`
  - `alternatives[]`（object[]）：`{ optionId: string, whyNot: string, whenRevisit: string }`

- `trace.jsonl`（Should；append-only）
  - 每行事件：`{ timestamp, stage, actor, kind, artifactRef, note }`

### 11.6 动态扩容（Auto Sampling）默认阈值与批次策略（冻结）

> 目标：避免“看似可配置，但实际固定默认值”；auto 采样必须可解释、可审计，并允许通过 TaskDials 逐次调整。

- 默认 policy：`sampling.policy=auto`（Standalone Run 可显式指定 `fixed`）
- 默认批次（冻结建议值，可被 profile 覆盖）：
  - R1：`batch=5`（每次新增 5 个角色），`max=50`
  - Judging：`batch=2`（每次新增 2 个 judge），`max=11`（High-risk 可提升到 15，但需显式）
- 触发信号（冻结为“至少命中其一才扩容”，否则容易无限加样本）：
  1) **多样性不足**：`options.json` 中 option 类别（`category` 或隐式聚类）少于 3，或缺少 profile 要求的类别（如 Creative 必须至少 1 个 moonshot）。
  2) **证据不足**：每个 option 的 `evidencePointers` 平均 < 1.5，或出现 “关键 claim 无证据指针”。
  3) **分歧过大**：`verdicts.json` 的 top-1 票占比 < 0.6，或出现“高风险项未被条件化”的 judge 明确反对。
  4) **置信不足**：平均 `confidence` < 0.6，且 blocking questions 仍未收敛为可回答集合。
- 停止条件：沿用本文 6.4.4（边际增益变小 / 覆盖达标 / 预算触顶），并要求把 stop reason 写入 `trace` 与 `decision-report.md`。

### 11.7 P0 验收与回归清单（生成 skill 后的“是否可用”标准，冻结）

> 目标：让“是否达标”可机械判断；不依赖评审者个人经验。

- **Skill 资产基本项**
  - `skill.md` Front Matter 满足 `name/description` 必填，且 `name` kebab-case。
  - `trigger_phrases` 至少 3 个，且不包含过宽触发词（见 11.2 冻结原则）。
  - `docLinks` 存在且可被 `doc_links_writer.py` 回写为可追溯 commit/branch。
- **strict canonical 产物合同**
  - strict run 产物必须包含：`case-meta.json/options.json/verdicts.json/decision.json/decision-report.md`。
  - `decision-report.md` 必含固定章节（Executive Summary / Decision / Option Cards / Matrix / Verdict Summary / Risks & Sign-off / Acceptance Checklist / Appendix）。
- **fail-closed 门禁**
  - 缺 risk verdict 或 `verdicts<3` → BLOCK。
  - 缺 `acceptanceChecklist` 或缺 `failClosedGates` 边界 → BLOCK。
  - 文档/机读产物命中 secrets/绝对路径/危险命令未授权 → BLOCK（见 Agent #3 负例库）。
- **Write-Intent Gate（反 Case 11）**
  - 未显式 `--apply`/token/scope/TTL → 禁止任何写入上游交付区与代码区（只能写 evidenceRoot）。
- **compat 输入落痕**
  - compat 模式消费旧结构时，必须在 `trace` 与最终报告标注“compat 输入来源与归一化动作”。

### 11.8 生成 Skill 的最小资产集合（仅列清单，不在本文执行）

> 本清单用于后续“生成 skill”阶段的 DoD；本文只提供规格，不创建文件。

- `.claude/skills/swarm-decision/skill.md`（按 11.2 元信息 + 本文抽象的流程/输出/边界）
- `.claude/skills/swarm-decision/templates/*.md`（按 11.4）
- `.claude/skills/swarm-decision/examples/`（至少 2 个：工程决策 1 个 + Creative 1 个，且含负例说明）
- （可选）`.claude/skills/swarm-decision/schemas/*.schema.json`（按 11.5 v0.1 字段冻结直接转写）

## 结论（给主进程的可落盘要点）
- 这个决策流程 skill 的“生态价值”不在于替代 PRD/架构/计划生成器，而在于：**在关键分歧/缺证据/高风险内容类型**场景，提供一个**可回放、可审计、默认安全**的裁决闭环，并通过 **profile 装配**把它“无缝嵌入”现有技能链路中。

