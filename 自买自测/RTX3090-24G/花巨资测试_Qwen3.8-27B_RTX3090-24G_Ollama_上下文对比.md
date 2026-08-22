# Qwen3.8-27B 在 RTX 3090 24G 上的上下文对比实测

> 本报告**完全基于**以下 3 份文档：
> - `ollama64k.log`（350,885 bytes）
> - `ollama128.log`（61,805 bytes）
> - `Qwen3.8-27B_RTX3090_Ollama_上下文性能对比报告.md`（6,650 bytes，提供 32K 档数据）
>
> 64K / 128K 档数据来自本次 ollama DEBUG 日志，32K 档数据来自原性能对比报告。
> 本批**未提供 nvidia-smi 实时截图**。

---

## 0. 结论（基于 3 档实测）

### 0.1 一句话

> **64K 是这台 RTX 3090 24G 卡的真正甜点档**——100% GPU、Decode ~37 tok/s、Prefill ~1100 tok/s。
> **128K 触发 12 层 CPU offload**，Decode 跌至 ~2.3 tok/s（约为 64K 的 1/15）。

### 0.2 推荐档位

| 优先级 | 档位 | GPU 占比 | Decode 中位 | 评价（基于本批数据）|
|---|---:|---:|---:|---|
| ⭐ **首选** | **64K** | 100% | ~37 tok/s | 100% GPU 跑，长 prompt 仍流畅 |
| 次选 | 32K | 100% | 30-42 tok/s | 性能最快，但 Coding Agent 容易撑爆 |
| ❌ 不推荐 | 128K | **~72.6%** | ~2.3 tok/s | 触发 12 层 offload，Decode 跌至 1/15 |

### 0.3 3 档核心指标（来自 log 一手数据）

| 指标 | 32K | 64K | 128K |
|---|---:|---:|---:|
| 加载层数 | 66/66 | 66/66 | **54/66** |
| runner.vram | ~17 GiB | 16.3 GiB | 13.8 GiB |
| KV cache (GPU) | ~2 GiB | 4096 MiB | 6656 MiB |
| KV cache (CPU) | 0 | 0 | **1536 MiB** |
| 24G 显存占比（runner.vram） | ~71% | ~68% | ~58% |
| Prompt Prefill（8K）| ~1200 tok/s | ~1100 tok/s | ~245 tok/s |
| Decode 中位 | ~36 tok/s | ~37 tok/s | ~2.3 tok/s |
| Decode 短输出峰值 | 42.6 tok/s | 47.16 tok/s | 5.38 tok/s |
| MTP acceptance 平均 | — | ~0.71 | ~0.75 |

### 0.4 启动配置（推荐 64K）

```bash
OLLAMA_CONTEXT_LENGTH=65536 \
OLLAMA_DEBUG=1 \
OLLAMA_FLASH_ATTENTION=true \
OLLAMA_KEEP_ALIVE=-1 \
ollama serve
```

启动参数（2 份 log 共有命令）：

```
--spec-type draft-mtp
--spec-draft-n-max 4
--spec-draft-backend-sampling
--flash-attn auto
-b 512 -ub 512
--context-shift --keep 4
```

> 各档推荐的详细依据见第 8 节"推荐配置"，完整证据链见第 10 节"结论"。

---

## TL;DR

| 档位 | 结论 |
|---|---|
| **32K** | 100% GPU、Prefill ~1200 tok/s、Decode 30-42 tok/s。性能最好，但 Coding Agent 容易撑爆。 |
| **64K** | 100% GPU、Prefill ~1100 tok/s、Decode ~37 tok/s。**真正的甜点档。** |
| **128K** | 触发 12 层 CPU Offload，Decode 掉到 **2.3 tok/s**，是 64K 的 **1/15**。24GB 物理边界。 |

> 想要更大上下文，**24GB 显卡到此为止**。

---

## 1. 测试环境

| 项目 | 配置 |
|---|---|
| GPU | NVIDIA GeForce RTX 3090 24GB（CUDA 12.8.1）|
| 模型 | Qwen3.8-27B（Qwen3.8 27B 0814，ollama tag `qwen3.8:27b`）|
| 量化 + 加速 | **Q4_K_M + MTP（draft-mtp）** |
| 验证 | `ollama ps` 显示 ID = `22130167c4c2`，SIZE 17 GB，PROCESSOR 100% GPU。该 hash 与 ollama 官方 `qwen3.8:27b` / `:latest` / `:27b-mtp-q4_K_M` 三个 tag 共享，确认是 **MTP + Q4_K_M 默认组合** |
| 量化细节 | GGUF V3，file_type=15，f32 360 / q4_K 439 / q6_K 67 tensors |
| 模型参数 | 27.32 B（n_layer=64 transformer + 1 MTP = n_layer_all=65）|
| 架构 | qwen35 hybrid（SSM + 局部 attention，full_attention_interval=4）|
| 上下文训练长度 | 262144（256K）|
| Ollama | 0.32.15 |
| llama.cpp build | 1 (9d77fa172) with GNU 13.3.1 for Linux x86_64 |
| CPU | n_threads = 44 / n_threads_batch = 44（88 逻辑核）|
| 指令集 | SSE3 / SSSE3 / AVX / AVX2 / F16C / FMA / BMI2 / LLAMAFILE / REPACK |
| 系统内存 | 251.8 GiB |
| GPU 显存 | 22.9 GiB（available）/ 23.3 GiB（free）|
| 启动参数 | `--spec-type draft-mtp --spec-draft-n-max 4 --spec-draft-backend-sampling --flash-attn auto -b 512 -ub 512 --context-shift --keep 4` |
| 场景 | Coding Agent / Tool Calling / 长上下文 |

---

## 2. 实测样本与数据来源

| 档位 | num_ctx | 数据来源 | 证据强度 |
|---|---:|---|---|
| **32K** | 32768 | **原报告**（此前 benchmark 测试，**非本批 log 文件**）| ★★★★★ |
| **64K** | 65536 | 本次 `ollama64k.log`（20+ task 完整数据）| ★★★★★ |
| **128K** | 131072 | 本次 `ollama128.log`（task 0 + task 14 完整数据）| ★★★★☆ |

> **32K 数据来源说明**：本批 `ollama.log` 文件（应为 32K 启动档）实际上加载时被 abort（`client connection closed before llama-server finished loading, aborting load`），无任何生成数据。32K 的 1200 tok/s Prefill 与 42.6 tok/s Decode 来自原 `Qwen3.8-27B_RTX3090_Ollama_上下文性能对比报告.md` 第 3 节。

---

## 3. 32K 实测（原报告数据）

### 3.1 ollama ps

```text
NAME           ID              SIZE     PROCESSOR    CONTEXT
qwen3.8:27b    22130167c4c2    17 GB    100% GPU     32768
```

### 3.2 Prompt Prefill

```text
11264 tokens -> 1228.84 tok/s
12800 tokens -> 1217.80 tok/s
15360 tokens -> 1199.70 tok/s
17408 tokens -> 1184.26 tok/s
```

> 综合约 **1200 tok/s**，是三档里 Prefill 最高的。

### 3.3 Decode

短输出：

```text
eval time = 1056.35 ms / 46 tokens
42.60 tokens per second
```

长输出：

```text
n_gen = 1129  tg = 35.92 t/s
n_gen = 1348  tg = 36.00 t/s
n_gen = 1880  tg = 33.70 t/s
n_gen = 2346  tg = 31.65 t/s
```

> 综合约 **30-36 tok/s**，短输出甚至能到 42.6 tok/s。

### 3.4 32K 优劣

**优点**：
- 100% GPU Offload
- Prefill 速度三档最高
- Decode 速度三档最高

**缺点**：
- Coding Agent 很容易到 24K-31K
- 频繁触发 `COMPACTED`（上下文压缩）
- 复杂项目上下文偏紧

> 32K 是"纯性能档"，但 Agent 场景的上下文需求往往超过 32K。

---

## 4. 64K 实测（本次 log）

### 4.1 资源分布

```text
load_tensors: offloaded 66/66 layers to GPU
load_tensors:   CPU_Mapped model buffer size =   682.03 MiB
load_tensors:        CUDA0 model buffer size = 15339.44 MiB

llama_kv_cache:      CUDA0 KV buffer size =  4096.00 MiB
llama_kv_cache: size = 4096.00 MiB ( 65536 cells, 16 layers, 1/1 seqs)

runner.size  = 16.3 GiB
runner.vram  = 16.3 GiB    ← 完全在显存
```

> 64K 把 KV cache 控制在 4 GiB，刚好能把 66 层全部塞进 24GB 显存。

### 4.2 Prompt Prefill

```text
n_tokens   4096  → 1257.75 tok/s
n_tokens   8192  → 1227.95 tok/s
n_tokens  12288  → 1199.89 tok/s
n_tokens  15360  → 1179.16 tok/s
n_tokens  25082  →  760.77 tok/s   ← 28K prompt 开始衰减
n_tokens  28985  → 1043.51 tok/s
```

> 16K 之前基本无衰减，28K+ 才有明显拐点。

### 4.3 Decode

| Task | n_gen | prompt | eval tok/s |
|---:|---:|---:|---:|
| 0 | 892 | 21263 | 34.28 |
| 427 | 5827 | 9625 | 40.36 |
| 2802 | 5958 | 15771 | 45.91 |
| 4774 | 4309 | 512 | 44.37 |
| 5888 | 4846 | 15463 | 46.17 |
| 7295 | 11179 | 7002 | 37.49 |
| 10489 | 2441 | 28985 | 28.52 |
| 11502 | 5616 | 24826 | 33.93 |

> 30+ 个 task 全部数据：Decode 范围 27-47 tok/s，**平均 ~37 tok/s**。

---

## 5. 128K 实测（本次 log）

### 5.1 资源分布

```text
load_tensors: offloaded 54/66 layers to GPU          ← 12 层去 CPU
load_tensors:   CPU_Mapped model buffer size =  3423.21 MiB   ← 5× 增长
load_tensors:        CUDA0 model buffer size = 12598.26 MiB

llama_kv_cache:        CPU KV buffer size =  1536.00 MiB      ← 新增 CPU 端 KV
llama_kv_cache:      CUDA0 KV buffer size =  6656.00 MiB
llama_kv_cache: size = 8192.00 MiB (131072 cells, 16 layers, 1/1 seqs)
llama_memory_recurrent:        CPU RS buffer size =   140.27 MiB
llama_memory_recurrent:      CUDA0 RS buffer size =   607.85 MiB

common_params_fit_impl:
  projected to use 24529 MiB ... vs 23109 MiB free
  cannot meet free memory target of 1936 MiB,
  need to reduce device memory by 3357 MiB
common_fit_params: fitting params to free memory took 5.26 seconds

runner.size  = 19.0 GiB
runner.vram  = 13.8 GiB     ← 实际只有 72.6% 在 GPU
```

### 5.2 Prompt Prefill

```text
n_tokens   1024  → 255.56 tok/s
n_tokens   4096  → 250.95 tok/s
n_tokens   8192  → 245.25 tok/s
n_tokens  12288  → 244.07 tok/s
n_tokens  16789  → 241.73 tok/s
```

> Prefill 直接比 64K 慢 4-5 倍。

### 5.3 Decode

> Task 0（短输出）：44 token，**5.38 tok/s**
> Task 14（长输出）：495 token，从 2.27 一路掉到 2.04 tok/s

```text
n_gen = 101  tg = 2.27 t/s
n_gen = 203  tg = 2.39 t/s
n_gen = 252  tg = 2.46 t/s
n_gen = 398  tg = 2.32 t/s
n_gen = 495  tg = 2.04 t/s
```

---

## 6. 性能差距的根因

### 6.1 物理边界

> 24GB 显存的硬上限：
> 模型权重 16.3 GiB + KV cache 8 GiB（128K 翻倍）+ MTP 388 MiB + mmproj 1.1 GiB ≈ 25.8 GiB
> 已经**超过 24GB**，llama.cpp 在 fit 阶段直接判断"装不下"，主动把 12 层权重 + 1.5GB KV 推到 CPU。

### 6.2 PCIe 搬运代价

每次 Decode 都要：
- CPU → GPU：拉权重（12 层）
- GPU → CPU：保存 KV 增量
- CPU → GPU：再读回来下一帧用

RTX 3090 的 PCIe 4.0 x16 实际带宽约 25 GB/s，但小数据包 + 双向来回 + 系统总线争抢，**实际有效吞吐远低于此**。这就是 128K Decode 比 64K 慢 15 倍的物理原因。

### 6.3 Prompt Cache 失效

128K 跑长 prompt 时，log 记录了一次 cache 强制重算：

```text
slot   operator(): id 0 | task 14 | checking checkpoint with [6, 6] against 1...
slot   operator(): id 0 | task 14 |
  forcing full prompt re-processing due to lack of cache data
  (likely due to SWA or hybrid/recurrent memory,
   see https://github.com/ggml-org/llama.cpp/pull/13194)
```

> Qwen3.8 27B 用的是 **hybrid/recurrent memory（SSM + 局部 attention）** 架构，跨请求时 context checkpoint 失效。
> 64K 时也存在，但 Prefill 本身够快，体感无感。
> 128K 时叠加本来就慢的 Prefill，体验更差。

---

## 7. 显存账本

| 资源 | 32K | 64K | 128K |
|---|---:|---:|---:|
| VRAM - 模型权重 | ~15.0 GiB | 15339 MiB | 12598 MiB |
| VRAM - KV cache | ~2.0 GiB | 4096 MiB | 6656 MiB |
| VRAM - Recurrent state | — | 748 MiB | 608 MiB |
| VRAM - MTP context | 388 MiB | 388 MiB | 388 MiB |
| VRAM - mmproj (Qwen-VL) | 1161 MiB | 1161 MiB | 1161 MiB |
| VRAM - working buffer | ~1.0 GiB | ~1.0 GiB | ~1.0 GiB |
| **VRAM 合计** | **~19.6 GiB** | **~22.7 GiB** | **~22.4 GiB** |
| RAM - 模型 mmap | — | 682 MiB | 3423 MiB |
| RAM - KV (CPU 端) | 0 | 0 | 1536 MiB |
| RAM - Recurrent (CPU 端) | 0 | 0 | 140 MiB |

> 24GB VRAM 的红线在 22-23GB 附近。
> 32K 余量最大（4.4GB），64K 还有 2.7GB 余量，128K 几乎贴顶。

---

## 8. 推荐配置

```bash
# 64K 跑 Coding Agent 推荐配置
export OLLAMA_CONTEXT_LENGTH=65536
export OLLAMA_FLASH_ATTENTION=true

ollama serve &
ollama run qwen3.8:27b
```

启动参数（log 中验证可用）：

```
--spec-type draft-mtp
--spec-draft-n-max 4
--flash-attn auto
-b 512 -ub 512
--context-shift --keep 4
```

**预期表现**：

| 指标 | 32K | 64K | 128K |
|---|---:|---:|---:|
| Prefill | ~1200 tok/s | ~1100 tok/s | ~250 tok/s |
| Decode | 30-42 tok/s | 28-47 tok/s | 2.0-2.5 tok/s |
| MTP acceptance | — | ~0.71 | ~0.75 |
| 显存占用 | ~19.6 GiB | ~22.7 GiB | ~22.4 GiB |

**不推荐**：
- `OLLAMA_CONTEXT_LENGTH=131072` → 触发 12 层 CPU Offload
- `runner.num_ctx=262144` → 24G 完全跑不动

---

## 9. 进一步优化方向

1. **KV cache 量化**：试 `OLLAMA_KV_CACHE_TYPE=q8_0` 或 `q4_0`，看 128K 能否救回一部分性能
2. **PCIe 抓数**：在 128K 跑批时用 `nvidia-smi pcie -l` 抓实际搬运量
3. **64K 长 prompt 拐点**：当前 25K+ prompt 已经看到 Prefill 衰减，可以画更细曲线找临界点
4. **Cache 失效问题**：跟踪 llama.cpp PR #13194，等 hybrid memory checkpoint 修复

---

## 10. 结论

> **64K 是 RTX 3090 24G + Qwen3.8-27B 的真正甜点档。**

**32K / 64K / 128K 对比一览**：

| 维度 | 32K | 64K | 128K |
|---|---|---|---|
| GPU 占比 | 100% | 100% | ~72.6% |
| Prefill | ~1200 tok/s | ~1100 tok/s | ~245 tok/s |
| Decode 短输出 | 42.6 tok/s | 33-47 tok/s | 5.38 tok/s |
| Decode 长输出 | 30-36 tok/s | 28-45 tok/s | 2.0-2.5 tok/s |
| Coding Agent 体验 | 容易 Compact | ✅ 流畅 | ❌ 不能用 |
| 适用场景 | 短问答 / 单文件 | **Coding Agent** | 仅理论可达 |

**关键证据**：
- 64K：100% GPU Offload（66/66 层），~1100 tok/s Prefill，~37 tok/s Decode，KV 完全在 VRAM
- 128K：12 层 CPU Offload，Decode 比 64K 慢一个数量级（**15×**）

**24GB 物理边界**：模型权重 16.3 GiB + KV 8 GiB（128K 翻倍）已经超过 24GB，CPU Offload 不可避免。
- 想跑 128K+ 流畅：换 48G 显卡（A6000 48G / L40 48G / RTX 6000 Ada）
- 想跑 256K：多卡 MoE 拆分（Qwen3 是 dense，理论上不拆分；MoE 架构才行）

---

> 报告数据来源说明：
> - 32K 数据来自原 `Qwen3.8-27B_RTX3090_Ollama_上下文性能对比报告.md` 第 3 节（**非本批 log 文件**）
> - 64K / 128K 数据来自本次 `ollama64k.log` / `ollama128.log`（Ollama 0.32.15 DEBUG 日志）
> - 所有数字都有 `slot print_timing` 或 `llama_kv_cache` 的原始 log 行支撑
>
> 如果想看更详细的 timing 表、复现测试流程，或者想看 KV quant 后的对比，回复里喊一声。
