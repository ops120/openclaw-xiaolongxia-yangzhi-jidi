# 花巨资框评：Qwen3.8-27B 在 RTX 4090 48G 上的框架对比评测（vLLM 0.19.1 vs llama.cpp）

> **本报告是"同一台机器、两个推理框架、两个批次"的对比评测。**
> - **vLLM 侧**（2026-08-28，3h21m 实例）：完全基于《花巨资测试_Qwen3.8-27B_RTX4090-48G_vLLM_投机解码对比.md》及其三份数据源（`../vllm平台测试/4090_48G_192k_mtp3 (2).log` 1.44 MB 主日志、nginx 访问日志、vllm-monitor jsonl）。配置：vLLM 0.19.1 / FP8 W8A8 / fp8 KV / MTP3 / 192000 ctx / max_num_seqs=2。
> - **llama.cpp 侧**（2026-08-29）：完全基于本目录 5 份 Ridge-3.7bpw 实测日志 + `部署备份-20260829/data/` 监控快照与历史。配置：llama-server / Qwen3.8-27B-Ridge-3.7bpw.gguf（11.72 GiB）/ 192000 ctx / 4 slots。
> - **机器**：两次测试为同一台 48G 版 RTX 4090（49,140 MiB，驱动 570.211.01，sm89，450W），gpushare i-1 机器（vLLM 批次容器内运行，llama 批次宿主机直跑）。
>
> **本报告不引入未在两侧日志/快照中出现过的数字；跨卡数据（5090/参考报告）只作反事实参照并单独标注。两批的量化格式不同（FP8 vs Ridge-3.7bpw GGUF），所有对比都带此口径警告。**

---

## 0. 结论

### 0.1 一句话

> **在这台 4090 48G 上，两个框架的强项完全错开：100K+ 长上下文 decode，llama.cpp 跑出 42.3 tok/s、vLLM 0.19.1 只有 1.8–3.2 tok/s（~13–24× 差距）；但大 prompt 灌入（prefill），vLLM 10.2K–15.6K tok/s、llama.cpp 只有 1.45K–2.4K（~7–10× 差距）。vLLM 的长上下文慢不是框架绝症——同族 0.26.1rc1 在 5090 上 192K 能跑 ~70 tok/s——是"0.19.1 的 GDN/fla kernel × Ada × FP8"这个组合的病理（同一个 kernel 路径 3h21m 后还把进程崩了）。选型不是二选一，是按场景分流量。**

### 0.2 选型矩阵（先看这张表）

| 你的场景 | 选谁 | 一句话依据 |
|---|---|---|
| **100K+ 长上下文对话/阅读/单流 Agent** | **llama.cpp Ridge** | 本机上唯一能在 100K+ decode 到 40+ tok/s 的路线（42.3 @140K ctx）；vLLM 同档 1.8–3.2 |
| **大 prompt 批量灌入 / RAG 入库 / TTFT 敏感** | **vLLM** | prefill 10.2–15.6K tok/s，~102K prompt TTFT ≈ 8–10 s；llama 同量 95 s |
| **短/中上下文多用户并发（Agent/Tool Calling）** | **vLLM** | continuous batching 双流 51.2 tok/s（峰值 80.8）+ tool-call parser + prefix cache；llama 并发 decode 本批未测 |
| **显存还要留一半干别的** | **llama.cpp** | 24,078 MiB（49.0%）恒定；vLLM 峰值 46,286 MiB（94.2%）|
| **稳定性优先、无人值守长跑** | **暂判 llama.cpp**（证据窗口短，见 §5.3）| vLLM 0.19.1 在 142.8K 混合批触发 GDN CUDA assert 崩溃；llama 79.5 min 窗口零崩溃 |
| **输出质量敏感** | **都没资格选** | 两批都只测了速度，FP8 vs Ridge-3.7bpw 的精度差异未评测（§8 欠账）|

### 0.3 核心指标正面对比

| 维度 | vLLM 0.19.1（8/28）| llama.cpp（8/29）| 胜者 |
|---|---|---|---|
| 权重格式 / 体积 | FP8 W8A8 block-128，**28.95 GiB**（含 MTP drafter）| Ridge-3.7bpw GGUF，**11.72 GiB**（3.69 bpw 实测）| —（口径差异源头，2.47×）|
| 短上下文 decode（单流）| 中位 32.6（≤~35K/请求）| **中位 41.5**（无投机，全上下文混合）；MTP2 小 ctx 峰值 **98.39** | **llama**（+27% 基线，2.4× 峰值）|
| 短上下文 decode（双流）| **中位 51.2 / 峰值 80.8** | 未测（4 slots 具备能力，无数据）| **vLLM**（缺省）|
| **100K+ 长上下文 decode** | **1.8–3.2 tok/s** | **42.3–43.6 tok/s**（102K–140K ctx）| **llama，~13–24×** |
| Prefill | **10,182–15,635 tok/s** | 1,458 中位 / 2,384 峰值（138K 大 prompt 内衰减至 1,449）| **vLLM，~7–10×** |
| 投机解码 | MTP3：接受率 61.1%，mean len 2.9 | MTP2：接受率 47.7%（KV 争用下），mean len 1.95 | 接受率 vLLM 高；加速上限 llama 高 |
| 显存占用 | 峰值 46,286 / 49,140 MiB（**94.2%**）| **24,078 MiB 恒定（49.0%）** | **llama，余 25 GiB** |
| 稳定性 | 3h21m 后 GDN fla kernel CUDA assert **崩溃**，42× 5xx | 79.5 min 观察窗口**零崩溃**（MTP2 档有 KV 争用降批但不死）| 暂判 llama（窗口不等长，§5.3）|
| 并发模型 | continuous batching，max_num_seqs=2，prefix cache 命中率 48% | 4 slots + LCP 前缀复用，任务级调度 | 各有适用面 |
| Tool Calling / reasoning 处理 | `--tool-call-parser qwen3_coder` + `--reasoning-parser qwen3` 实装 | 日志仅见 "chat template supports preserving reasoning" 提示，未实测 | vLLM 功能面更全 |

### 0.4 两侧启动配置

```bash
# vLLM 侧（8/28 实例，../vllm平台测试 报告 §0.4）
vllm serve /hy-tmp/models/Qwen3.8-27B-FP8 \
  --max-model-len 192000 --kv-cache-dtype fp8 --gpu-memory-utilization 0.95 \
  --max-num-seqs 2 --reasoning-parser qwen3 --enable-prefix-caching \
  --enable-auto-tool-choice --tool-call-parser qwen3_coder \
  --speculative-config '{"method":"mtp","num_speculative_tokens":3}' \
  --served-model-name qwen3.8-27b-fp8 --host 0.0.0.0 --port 8000

# llama.cpp 侧（8/29 基线实例，本目录 研究报告 §0.4）
llama-server \
  --model Qwen3.8-27B-Ridge-3.7bpw.gguf \
  --host 0.0.0.0 --port 8000 \
  --ctx-size 192000 -np 4 --flash-attn 1
```

---

## TL;DR

| 维度 | 结论 |
|---|---|
| **长上下文 decode** | llama.cpp 42.3 @140K ctx，vLLM 1.8–3.2 @100K+ —— 本场最大分差（~13–24×）|
| **Prefill** | vLLM 10.2–15.6K vs llama 1.45–2.4K —— 反向最大分差（~7–10×），138K prompt：vLLM ≈10 s / llama 95 s |
| **分差归因** | 权重体积 2.47×（28.95 vs 11.72 GiB）只解释一小半；大头是 vLLM 0.19.1 的 fla/GDN Triton kernel 在 sm89 上的病理——同一 kernel 还引发了崩溃 |
| **反事实** | vLLM 0.26.1rc1 + NVFP4 在 5090 上 192K 无投机 ~70 tok/s——**框架不是不行，是"0.19.1 × Ada × 该 kernel"不行** |
| **投机解码** | vLLM MTP3 接受率 61.1%（k=3 第 3 位掉到 0.51）；llama MTP2 接受率 47.7% 但短 ctx 峰值 98.39——两者都证明 MTP 在这模型上有效，k=2 更划算两边都成立 |
| **显存** | llama 49.0% vs vLLM 94.2% —— 48G 卡上 vLLM 这套配置已经把显存吃死，llama 还剩 25 GiB |
| **稳定性** | vLLM 3h21m 崩（142.8K 混合批，已知路径）；llama 79.5 min 零崩溃（窗口短，不作长期结论）|
| **坑点实录** | `192_mtp3.log` / `192_mtp3 (1).log` 两份 **vLLM 日志混在 llama 目录里**（是 8/28 主日志的截断副本）——两平台同机轮跑的物证 |

---

## 1. 对比口径与差异声明（读任何数字前先看这节）

### 1.1 两批不是受控对照，是"同机先后两批"

| 口径项 | vLLM 批次（8/28）| llama.cpp 批次（8/29）| 对对比的影响 |
|---|---|---|---|
| **量化** | FP8 W8A8 block-128（28.95 GiB 含 drafter）| Ridge-3.7bpw GGUF（11.72 GiB，3.69 bpw）| **权重体积差 2.47×**——decode 是带宽活，这一项天然偏向 llama |
| 版本 | 0.19.1（V1 engine）| 未记录构建号（日志无 version 行）| 无法锚定 llama 侧 kernel 版本；vLLM 侧已知 0.20+ 默认 CUDA 13 构建与驱动 570.211.01 冲突，升级需 CUDA 12.8 构建或源编译（有路但加成本）|
| 并发设定 | max_num_seqs=2 continuous batching | 4 slots，任务级；decode 数据以单流为主 | 双流对比只有 vLLM 有数据 |
| 测量粒度 | 引擎 10 s 窗口（loggers 行，全请求聚合）| 单行 `tg`（~3 s 粒度）+ 任务收尾 `eval time` | vLLM 是"池子吞吐"，llama 是"单任务速率"，长上下文对比时已按每请求口径对齐 |
| 流量 | 真实混合（15K–156K prompt 反复，prefix 命中 4.3%→48%）| 基线档同类混合；256k_mtp2 档为单任务 138K prompt | 都不是实验室扫频，是"用出来的数" |
| 观察窗 | 3h21m（至崩溃）| 基线 79.5 min + 若干短档 | **稳定性对比窗口不等长，结论降级为"暂判"** |
| 机器 | gpushare i-1，48G 版 4090，容器内 | 同一台机器，宿主机直跑 | 硬件变量已控住 |

### 1.2 目录里的"混血"证据

本目录（`llama平台测试/`）里的 `192_mtp3.log`（578,823 B）与 `192_mtp3 (1).log`（1,097,743 B）**不是 llama.cpp 日志**：内容是 vLLM 0.19.1 的 `Engine 000` 窗口行与 `SpecDecoding metrics`，即 8/28 那个 192K+MTP3 实例主日志的**截断副本**（止于 23:51:48，崩溃段在被截掉的 `../vllm平台测试/4090_48G_192k_mtp3 (2).log` 尾部）。它们的存在恰好证明：**同一台机器，8/28 跑 vLLM、8/29 跑 llama.cpp**——这份框评的"同机"前提就写在目录结构里。

### 1.3 证据强度

| 数据块 | 来源 | 强度 |
|---|---|:---:|
| vLLM 全部数字 | 同目录树 `../vllm平台测试/` 已交付报告 + 三份原始数据 | ★★★★★（原始日志在案）|
| llama 基线 / MTP2 / 256k_mtp2 | 本目录 5 份日志 + 监控快照 + jsonl | ★★★★★ |
| 归因分析（§3 因子分解）| 两侧实测 + 5090 参考报告反事实 | ★★★（推理成分，单独标注）|
| 质量对比 | **无** | ☆（未测，不作任何断言）|

---

## 2. 逐项对决

### 2.1 短/中上下文 decode（每请求 ≤~70K）

| 指标 | vLLM 0.19.1 + MTP3 | llama.cpp（无投机 / MTP2）|
|---|---:|---|
| 单流中位 | 32.6（≤~35K，n=436 窗口）| **41.5**（全 ctx 混合，tg n=1006；任务 eval n=121 中位 43.6，monitor 42.4，三口径互证）|
| 单流峰值 | 59.5（单请求窗口）| **59.99**（几乎打平）|
| 双流中位 / 峰值 | **51.2 / 80.8**（≤~35K 双请求；中 ctx ~35–70K 双流 44–55）| 未测 |
| MTP 小 ctx 上限 | — | **98.39**（MTP2，task 9 @ctx 3,786，持续 86.6–86.7）|

> **单流基线 llama 快 ~27%（41.5 vs 32.6）**，权重体积差（2.47×）和 MTP 档位数差（k2 vs k3）都在帮 llama；但注意 llama 的"短上下文"样本与 ≤~35K 池不完全同构（它是全 ctx 混合中位数）。**双流场景 vLLM 拿缺省胜——不是因为它快，是因为 llama 侧没数据**，而 4 slots 理论上接得住（§8 补测项）。

### 2.2 100K+ 长上下文 decode —— 本场决胜局

| 证据 | vLLM | llama.cpp |
|---|---|---|
| 实测值 | **1.8–3.2 tok/s**（20:47:38–20:48:48，双请求）；00:04 段混合批 0.8–2.5 | **42.3–43.6**（task 137557，ctx 102,386）；**42.3 平台**（256k_mtp2 档，~140K ctx，tg 41.94–52.26，n=31）|
| MTP 状态 | mean len 仍有 2.1–2.9（投机在干活）| MTP2 档同任务（98.4 峰值档）|
| 结论 | 慢**不是投机失效**，是 GDN/fla kernel 长上下文 decode 路径本身 | 混合注意力模型 decode 权重带宽主导，GDN 状态定长 → ctx 增大几乎不掉速（41.5 全 ctx 中位 ≈ 42.3 @140K）|

> **差距 ~13–24×，这是整份框评最重要的一个数。** 两侧"长上下文不掉速/掉速"的形态差异说明：不是模型在 100K+ 天然慢（llama 证明了它可以 42+），而是 vLLM 0.19.1 这条 kernel 路径在 Ada 上慢。因子分解见 §3。

### 2.3 Prefill —— vLLM 的主场

| 指标 | vLLM | llama.cpp |
|---|---:|---:|
| 大窗口速率 | **10,182–15,635 tok/s**（chunked prefill，28 个 ≥5000 窗口）| 1,458 中位 / **2,384 峰值**（≥1000 tok 请求 n=39）|
| 138K 级 prompt 用时 | ~102K token TTFT ≈ **8–10 s** | 138,107 token = **95.29 s**（均值 1,449，起点 2,492 → 终点 1,449，**同请求内随 ctx 增长衰减 42%**）|
| 倍率 | **~7–10×** 领先 | — |

> llama 的 prefill 衰减形态（2,492 → 1,449）与它 decode 的"平坦"形成镜像：prefill 是算力活，注意力部分随 ctx 变贵；decode 是带宽活，权重定长。**选框架先问业务形状：请求是"长进长出"（选 vLLM）还是"长进短出/持续对话"（选 llama）。**

### 2.4 投机解码实现对比（MTP）

| 项 | vLLM MTP3 | llama.cpp MTP2 |
|---|---|---|
| 实现 | 引擎级投机，drafter 共享 embedding/lm_head，权重随主模型载入（28.95 GiB 含 drafter）| `common_speculative_init_result` 对 target 建 draft ctx；**MTP 头内嵌在同一份 GGUF**（`blk.64.nextn.*`），零额外文件 |
| k | 3 | 2（文件命名；接受率统计口径见下）|
| 接受率 | **61.1%**（199,376/326,292，993 窗口汇总）| **47.7%**（7 行收尾统计 2,048/4,290；生成≥50 tok 的 4 任务 2,042/4,284 同率）|
| Mean acceptance length | 中位 2.9（上限 4 = 1+3）| 中位 1.95 |
| 逐位衰减 | pos1 0.782 / pos2 0.625 / pos3 **0.510** —— k=3 惩罚明确 | （样本不足分位）|
| 速度产出 | 短 ctx 双流 51.2（其 FP8 无投机 baseline 未测，无法给本批加速比）| 峰值 98.39 / 基线中位 41.5 → **短 ctx 上限 ~2.4×** |
| 工况警告 | 3h21m 混合流量，样本充分 | **7.5 min 且全程 KV 争用**（44× `failed to prepare attention ubatches`、43× KV 满重试、6× ctx 超限）——47.7% 是被污染的下限，不是实现质量结论 |

> 两边殊途同归地验证了同一件事：**MTP 对 Qwen3.8-27B 有效，但 k 越大边际越差**（vLLM pos3=0.51；llama k=2 档的 mean 1.95 反而更"实"）。**不接受的对比**：拿 61.1% vs 47.7% 直接说 vLLM 的 MTP 实现更好——llama 的样本是在 262144×4slot 超卖、KV 反复爆的工况下采的。

### 2.5 显存与资源

| 项 | vLLM | llama.cpp |
|---|---:|---:|
| 权重 | 28.95 GiB | 11.72 GiB |
| KV 池 | 14.04 GiB / 107,200 token / 2.00x | 192000 ctx × 4 slots 实配（快照：显存恒定）|
| 运行占用 | 峰值 **46,286 MiB（94.2%）** | **24,078 MiB（49.0%）恒定**（history 420 条同值）|
| 余量 | ~2.8 GiB | **~25 GiB**——同卡再跑一个服务/留突发余量都够 |
| GPU 利用率 | —（日志未录）| util_gpu 中位 92%（峰值 100%）|

> 48G 卡对 vLLM 这套 192K+MTP3 配置是"刚好装下"（0.95 利用率吃满）；对 llama 是"用了不到一半"。**如果这台机器还要干别的，选框架前先算这笔账。**

---

## 3. 长上下文差距的因子分解（归因，★★★）

**待解释差距**：100K+ decode，42.3 vs 1.8–3.2 tok/s ≈ **13–24×**。

| 因子 | 贡献 | 证据 |
|---|---|---|
| ① 权重体积（decode 带宽项）| **~2.5×** | 28.95 / 11.72 = 2.47；decode 每步读一遍权重 |
| ② vLLM 0.19.1 fla/GDN Triton kernel 在 sm89 的病理 | **~6–9×（残差）** | 同一 `chunk_gated_delta_rule_fwd` 路径 3h21m 后直接 device-side assert（崩溃堆栈与慢路径同源）；llama 侧同架构模型 decode 平坦证明模型本身不该这么慢 |
| ③ 混合批 / chunked prefill 拖累 | 少量 | 00:04 段 142.8K chunked prefill 与 decode 同批，步长被拉到 0.8–2.5 |

**反事实锚点**（不作为本机结论，只证"框架非绝症"）：

- vLLM **0.26.1rc1** + NVFP4 在 **5090（Blackwell）** 上 192K 无投机 ≈ **70 tok/s**（参考报告 `1.log`）。同一框架、更新版本、换卡，192K decode 从 ~2 量级回到 ~70 量级——**差距是"版本 × kernel × 卡"组合的，不是 vLLM 本质的**。注意该锚点同时换了量化（NVFP4）和卡，只能作量级参照。
- 旁证：另一批 4090 24G 上 llama.cpp NVFP4-GGUF（Q5_K）短 ctx 43.4 tok/s（MTP2），与本批 4090 48G 的 41.5 基线一致——**llama.cpp 路线在 Ada 上的表现是可复现的**。

**行动含义**：把 vLLM 升到 0.20+（GDN 路径有修复）之后复测长上下文，是性价比最高的一次复测。升级路径已知麻烦：0.20+ 默认 CUDA 13 构建与驱动 570.211.01（上限 CUDA 12.8）冲突，需要 CUDA 12.8 构建或源编译，且**升级前先在容器内验证驱动兼容性**（与源报告 §复测建议 一致）。

---

## 4. Prefill 差距为什么是反方向

- **vLLM 强在批**：chunked prefill + CUDA graph + fp8 GEMM，把 100K+ token 当批次算力活干，10–15.6K tok/s。
- **llama 弱在批**：ubatch 粒度小（日志显示推进速率随 ctx 衰减：2,492 → 1,449），且 4 个 slot 共享同一份推进。
- **业务映射**：
  - 知识库入库 / 长文档首问 / 代码库级 prompt → vLLM，**10 s vs 95 s 的 TTFT 差距是产品级的**；
  - 已经在上下文里的持续对话（prefix 命中）→ 两者差距缩小，llama 的 LCP 前缀复用同样吃得到重复前缀。

---

## 5. 稳定性与运维

### 5.1 事件对比

| 项 | vLLM | llama.cpp |
|---|---|---|
| 运行时长 | 3h21m | 基线档 79.5 min（+ MTP2 7.5 min / 256k_mtp2 3.6 min，后者日志中途截断）|
| 致命事件 | **00:05:14 GDN fla kernel CUDA device-side assert**，EngineCore 死亡，其后 42× 5xx | **零崩溃** |
| 非致命异常 | 9× 400（疑似超 192K 上限）、10× 499（客户端等不住断连）| 1× 请求拒绝（192,205 > 192,000，明确报错）；MTP2 档 44× ubatch 失败 + 43× KV 重试 + 6× ctx 超限——**但全部优雅降级，进程活着** |
| 启动耗时 | 启动→就绪 ≈ 2m15s（torch.compile 55.8 s）| 秒级（`0.06` 时刻 model loaded + listening）|
| 部署面 | pip 生态，但 **0.20+ 默认 CUDA 13 构建与驱动 570.211.01（上限 CUDA 12.8）冲突，需 CUDA 12.8 构建或源编译**——升级有路，加成本 | 单二进制 + 单 GGUF；代价是自己选量化、自己记录构建号（本批就没记，欠账）|

### 5.2 故障形态差异（比"谁崩了"更重要）

> vLLM 的失败模式是**脆断**：特定混合批触发 kernel assert，整个引擎死，需要重启。
> llama.cpp 的失败模式是**萎降**：KV 不够就降批、重试、拒绝单请求，服务不死。
> 对无人值守场景，"萎降"通常比"脆断"好接——但前提是接受它在 KV 超卖时吞吐会塌（MTP2 档 tg_3s 掉到 0.78–0.93 就是塌的样子）。

### 5.3 必须说的限制

> **79.5 min 对 3h21m，稳定性对比不对等。** "零崩溃"是观察窗口事实，不是长期证明；vLLM 的崩溃是**特定路径**（大上下文混合批 × MTP3 × 0.19.1），不是每次必现。两边的稳定性结论都应该等 24h 级 soak 再升级。

---

## 6. 功能面速览（只列日志/配置里能看见的）

| 功能 | vLLM 0.19.1 | llama.cpp（本批）|
|---|---|---|
| OpenAI 兼容 API | ✅ | ✅（llama-server 原生）|
| Tool Calling | ✅ `--tool-call-parser qwen3_coder` 实装并走流量 | 未实测 |
| Reasoning 处理 | ✅ `--reasoning-parser qwen3` | 日志提示 "chat template supports preserving reasoning"（有开关，未开）|
| Prefix 复用 | ✅ 显式 `--enable-prefix-caching`，命中率爬到 48% | ✅ LCP-similarity 复用（无显式命中率输出）|
| 并发调度 | continuous batching | slot 任务制 |
| 监控 | 自有 logger + Prometheus 口径 | 需自建（本批的 monitor 快照即自建）|

> 功能面 vLLM 更全是事实；但注意 Tool Calling 的解析正确性两边都没做**行为级**验证，只确认了"开关存在且走流量"。

---

## 7. 场景选型矩阵（§0.2 的展开版）

| 场景 | 首选 | 次选 / 条件 | 依据 |
|---|---|---|---|
| 长文档问答 / 100K+ 持续对话（单流）| **llama.cpp Ridge + MTP2** | vLLM 仅在升版复测通过后考虑 | §2.2：42.3 vs 1.8–3.2 |
| 大批量知识入库 / 长 prompt 首问 | **vLLM** | — | §2.3：TTFT 8–10 s vs 95 s |
| Agent / Tool Calling 多用户（短中 ctx）| **vLLM** | llama 补测多 slot 并发后可再议 | §2.1：双流 51.2 + tool parser |
| 同卡混部（推理 + 别的负载）| **llama.cpp** | — | §2.5：49% vs 94.2% |
| 无人值守长跑 | **先补两边 24h soak 再定**；现状暂倾向 llama | — | §5.3 窗口限制 |
| 质量敏感业务 | **先做精度评测再谈框架** | — | 两批均未测质量 |
| 预算型买卡延伸结论 | 48G 版 4090 的硬价值 = 让 192K+MTP 装得下（两框架都成立）| 长上下文速度需求高则上 Blackwell | vLLM 报告 §7 + 本框评 §3 反事实 |

---

## 8. 复测清单（按性价比排序）

| # | 复测项 | 为什么 | 怎么验 |
|---|---|---|---|
| 1 | **vLLM 0.20+ 长上下文复测** | §3 归因的最大残差项（~6–9×）可能就是一次版本修复的事 | 找 CUDA ≤12.8 的 0.20+ wheel（或自编译），同 192K/FP8/MTP3 配置，复投 100K+ prompt，看 decode 是否回到 30+ |
| 2 | **llama 24h soak** | 把"79.5 min 零崩溃"升级成可用结论 | 持续混合流量，监控 tg 分布漂移与显存 |
| 3 | **llama MTP2 干净 A/B @192K 单流** | 本批 mtp2 被 KV 超卖污染，47.7% 是下限不是真值 | 1 slot / 192000 ctx / k=2，对照无投机基线 |
| 4 | **llama 多 slot 并发 decode** | 双流场景现在只有 vLLM 数据 | 2–4 并发同长上下文任务，记 tg 与互扰 |
| 5 | **同量化对照**（FP8 GGUF × llama vs FP8 × vLLM）| 消掉 2.47× 权重体积变量，纯化框架对比 | 找/转 FP8 GGUF 复跑本目录流程 |
| 6 | **精度评测**（Ridge-3.7bpw vs FP8）| 当前最大的未回答问题是质量 | 固定题库，双盲打分 |
| 7 | **记录构建号** | 本批 llama.cpp 版本成谜，复现性欠账 | 启动加 `--version` 输出入日志 |

---

## 9. 局限

1. **不同量化对比**：FP8 vs Ridge-3.7bpw，2.47× 体积差混在所有 decode 数字里；本报告已在每处标注，但无法拆开。
2. **窗口不等长**：稳定性与接受率的置信度两侧不对等（§5.3、§2.4）。
3. **测量粒度不同**：10 s 引擎窗口（聚合）vs 3 s tg 行（单任务），已按每请求口径对齐，但双流场景无 llama 数据。
4. **llama 构建未记录**：无法锚定 kernel 版本，复现要靠同一二进制。
5. **归因有推理成分**：§3 的因子分解是"实测 + 反事实"推断（★★★），不是消融实验。
6. **跨卡参照**：5090/5070 参考数据只作反事实锚点，口径（卡、量化、版本）全不同。
7. **质量未测**：本框评没有任何输出质量结论，也不应有。

---

## 10. 一句话收尾

> **这台 48G 4090 上：要"长"（100K+ decode）用 llama.cpp + Ridge，要"快进"（大 prompt 灌入）和"多人"（并发 + 工具链）用 vLLM；vLLM 的长上下文之慢是 0.19.1 × Ada × GDN-kernel 的组合病，升级复测是下一个动作，不是放弃 vLLM 的理由。两个框架谁也没赢——赢的是按场景分流量的部署方式。**

---

> 数据来源：
> - vLLM 侧：`../vllm平台测试/花巨资测试_Qwen3.8-27B_RTX4090-48G_vLLM_投机解码对比.md` 及 `4090_48G_192k_mtp3 (2).log`、nginx/monitor 数据（同目录树）；本目录 `192_mtp3*.log` 为其截断副本（§1.2）
> - llama.cpp 侧：本目录 5 份 `Qwen3.8-27B-Ridge-3.7bpw-*.log` + `部署备份-20260829/data/`（monitor 快照 + history jsonl）
> - 姊妹篇：《花巨资测试_Qwen3.8-27B_RTX4090-48G_llama.cpp_Ridge-3.7bpw_研究报告.md》（llama 侧全证据链）
> - 反事实参照：`docs/ref_RTX5070-32G_花巨资测试_投机解码对比.md`（5090/vLLM 0.26.1rc1）
> - 解析脚本：`tmp/analyze_llama_4090.py`（tg/接受率/时长统计，可复跑）
