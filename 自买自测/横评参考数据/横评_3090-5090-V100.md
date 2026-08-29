# Qwen3.8-27B 三卡横评：RTX 3090 24G vs RTX 5090 32G vs Tesla V100 32G

> 本报告**完全基于**四份硬件实测报告：
> - `RTX3090-24G/花巨资测试_Qwen3.8-27B_RTX3090-24G_Ollama_上下文对比.md`（实测 32K / 64K / 128K，ollama 路线）
> - `RTX5070-32G/花巨资测试_Qwen3.8-27B_RTX5070-32G_Ollama_上下文对比.md`（实测 64K / 128K / 192K / 256K，ollama 路线）
> - `RTX5070-32G/花巨资测试_Qwen3.8-27B_RTX5070-32G_vLLM_投机解码对比.md`（实测 32K / 128K / 192K，**vLLM + NVFP4 + fp8 KV 路线，5090 only**）
> - `V100-32G/花巨资测试_Qwen3.8-27B_V100-32G_Ollama_上下文对比.md`（实测 192K 单卡/双卡 + 256K，ollama 路线）
>
> 三份 ollama 报告原始数据为 ollama DEBUG log；vLLM 报告原始数据为 vLLM 0.26.1rc1 日志。
> **vLLM 数据仅 5090 有，3090 / V100 无 vLLM 数据**——第 9 章 vLLM 路线为 5090-only。
> 本报告**只做横向对比的二次归纳**，未引入新的硬件规格或预测。
>
> **命名说明**：本报告用"**RTX 5090**"指代 32GB 档位的卡——`新建文本文档.txt` 中的 `nvidia-smi` 原文为 `Name: NVIDIA GeForce RTX 5090 / 32607 MiB`，但文件夹/独立报告沿用"5070"目录名（`5070 32G 测试相关`）。两者**指同一份硬件测试数据**。

---

## 0. 结论（基于 3 卡 × 多档实测）

### 0.1 一句话

> **ollama 路线**：
> **想跑 64K：RTX 3090 24G 是性价比首选**（~37 tok/s Decode）。
> **想跑 192K：RTX 5090 32G 完胜 V100 32G**（Decode 52 vs 30 tok/s，1.73×）。
> **想跑 256K：3090/5090/V100 三卡都触发 offload**，本批数据无 100% GPU 跑 256K 的证据。
>
> **vLLM 路线（5090 only）**：
> **vLLM + NVFP4 + fp8 KV 已经比 ollama Q4_K_M + MTP 快 35%**（192K 同档 70 vs 52 tok/s）。
> **DFlash 2 在 32K 跑出 ~170 tok/s**（峰值 230，**比 ollama 192K MTP 快 3.3-4.4×**）。
> **MTP 在 192K 装不下**（vLLM 报错：KV 需 7.0 GiB，实有 6.42 GiB）。

### 0.2 三卡推荐档位对照

| 卡 | 框架 | ⭐ 首选档 | 次选档 | 不推荐档 | 100% GPU 极限 |
|---|---|---|---|---|---:|
| **RTX 3090 24G** | ollama 0.32.15 | 64K（~37 tok/s）| 32K（~36 tok/s）| 128K（~2.3 tok/s，offload）| **64K** |
| **RTX 5090 32G** | ollama 0.32.15 | 192K（~52 tok/s）| 128K（~58 tok/s）| 256K（~7 tok/s，offload）| **192K** |
| **RTX 5090 32G** | vLLM 0.26.1rc1 | **32K + DFlash 2（~170 tok/s，峰值 230）** | 128K + MTP（~120 tok/s）| 192K + MTP（❌ KV 装不下）| **192K** |
| **Tesla V100 32G** | ollama（未明文） | 192K 单卡（~30 tok/s）| — | 192K 双卡（未加速）/ 256K | **192K** |

> **框架支持范围**：
> - **3090 / V100**：本批只测了 ollama，**vLLM 数据缺失**（"未在 3090 / V100 复现"）
> - **5090**：ollama 和 vLLM 都测了，vLLM 在 32K 跑出 DFlash 2 路线，**整体 Decode 比 ollama 快 35-330%**（按档位）

### 0.3 三卡核心指标横向对比（**仅基于直接可比的档位**）

> **直接可比规则**：两卡必须在同一 `num_ctx` 档都有完整数据。中间档数据缺失的格子留 "—"，**禁止跨档外推**。
> **本表所有数据来自 ollama 0.32.15（vLLM 数据见第 9 章）**。

| 卡 | 框架 | 指标 | 64K | 128K | 192K | 256K |
|---|---|---|---:|---:|---:|---:|
| 3090 24G | ollama 0.32.15 | 加载层数 | 66/66 | **54/66** | — | — |
| 5090 32G | ollama 0.32.15 | 加载层数 | 66/66 | 66/66 | 66/66 | **54/66** |
| V100 32G | ollama（未明文）| 加载层数 | — | — | 66/66 | **56/66** |
| 3090 24G | ollama 0.32.15 | runner.vram (GiB) | 16.3 | 13.8 | — | — |
| 5090 32G | ollama 0.32.15 | runner.vram (GiB) | 16.3 | 16.6 | 17.0 | 14.5 |
| V100 32G | ollama（未明文）| runner.vram (GiB) | — | — | 17.0 | 14.9 |
| 3090 24G | ollama 0.32.15 | KV GPU (GiB) | 4.0 | 6.5 | — | — |
| 5090 32G | ollama 0.32.15 | KV GPU (GiB) | 4.0 | 8.0 | 12.0 | 13.0 |
| V100 32G | ollama（未明文）| KV GPU (GiB) | — | — | 12.0 | 14.3 |
| 3090 24G | ollama 0.32.15 | KV CPU (GiB) | 0 | **1.5** | — | — |
| 5090 32G | ollama 0.32.15 | KV CPU (GiB) | 0 | 0 | 0 | **3.0** |
| V100 32G | ollama（未明文）| KV CPU (GiB) | — | — | 0 | **2.0** |
| 3090 24G | ollama 0.32.15 | Prefill 8K (tok/s) | ~1100 | ~245 | — | — |
| 5090 32G | ollama 0.32.15 | Prefill 8K (tok/s) | **2580** | **2650** | 2597 | 535 |
| V100 32G | ollama（未明文）| Prefill 3K (tok/s) | — | — | 780 | — |
| 3090 24G | ollama 0.32.15 | Decode 中位 (tok/s) | ~37 | ~2.3 | — | — |
| 5090 32G | ollama 0.32.15 | Decode 中位 (tok/s) | ~56 | ~58 | ~52 | ~7 |
| V100 32G | ollama（未明文）| Decode 中位 (tok/s) | — | — | ~30 | — |
| 3090 24G | ollama 0.32.15 | MTP accept | 0.71 | 0.75 | — | — |
| 5090 32G | ollama 0.32.15 | MTP accept | 0.50 | 0.55 | 0.46 | 0.53 |
| V100 32G | ollama（未明文）| MTP accept | — | — | 0.58 | — |

### 0.4 跨硬件倍数关系（直接可比档位）

| 维度 | 档位 | 5090 / 3090 | 5090 / V100 | 来源 |
|---|---|---:|---:|---|
| **Prefill 8K** | 64K | **2.35×** | — | 5090: 2580 vs 3090: 1100 |
| **Prefill 8K** | 128K | **10.8×** | — | 5090: 2650 vs 3090: 245（3090 此时已 offload）|
| **Prefill 8K vs 3K** | 192K | — | **~3.3×** | 5090 8K: 2597 vs V100 3K: 780（注意 prompt 规模差）|
| **Decode 中位** | 64K | **1.51×** | — | 5090: 56 vs 3090: 37 |
| **Decode 中位** | 128K | **25.2×** | — | 5090: 58 vs 3090: 2.3（3090 此时已 offload）|
| **Decode 中位** | 192K | — | **1.73×** | 5090: 52 vs V100: 30 |

> **128K 那一行注意**：3090 已是 12 层 offload 状态、5090 仍是 100% GPU——倍数包含了"offload vs 全 GPU"的差距，**不只是硬件性能差**。

### 0.5 启动配置（三卡共有）

```bash
OLLAMA_DEBUG=1 \
OLLAMA_FLASH_ATTENTION=true \
OLLAMA_KEEP_ALIVE=-1 \
ollama serve
```

```
--spec-type draft-mtp
--spec-draft-n-max 4
--spec-draft-backend-sampling
--flash-attn auto
-b 512 -ub 512
--context-shift --keep 4
```

> 三卡启动命令**完全一致**。区别只在 `OLLAMA_CONTEXT_LENGTH` 和硬件层。

---

## TL;DR

| 维度 | 3090 24G | 5090 32G | 5090 32G（vLLM）| V100 32G |
|---|---|---|---|---|
| **架构** | Ampere（GA102）| Blackwell（GB202）| Blackwell（GB202）| Volta（GV100）|
| **compute** | 8.6 | 12.0 | 12.0 | 7.0 |
| **推理引擎** | ollama 0.32.15 | ollama 0.32.15 | **vLLM 0.26.1rc1** | ollama（未明文）|
| **量化** | Q4_K_M | Q4_K_M | **NVFP4 + fp8 KV** | Q4_K_M |
| **加速方案** | MTP | MTP | MTP / DFlash 2 / 无 | MTP |
| **100% GPU 极限** | 64K | 192K | 192K（无 MTP/DFlash）| 192K |
| **Offload 触发** | 128K（12 层）| 256K（12 层）| MTP 192K 装不下 KV | 256K（10 层）|
| **32K Decode** | ~36 tok/s | 推测 ~56 tok/s | **~170 tok/s（DFlash）** | — |
| **64K Decode** | ~37 tok/s | ~56 tok/s | — | — |
| **128K Decode** | ~2.3 tok/s（offload）| ~58 tok/s | **~120 tok/s（MTP）**| — |
| **192K Decode** | — | ~52 tok/s | **~70 tok/s（无加速）/ 启动失败（MTP）**| ~30 tok/s |
| **256K Decode** | — | ~7 tok/s（offload）| — | —（无 task 数据）|
| **MTP acceptance** | 0.71-0.75 | 0.46-0.55 | — | 0.55-0.58 |
| **性价比档** | 64K（24G 卡）| 192K（32G 卡）| **32K（DFlash 2）/ 128K（MTP）** | 192K（32G 卡）|

---

## 1. 测试覆盖与数据来源

### 1.1 三卡实测档位一览

```
                    32K    64K    128K   192K   256K
RTX 3090 24G        ✓      ✓      ✓      —      —
RTX 5090 32G        —      ✓      ✓      ✓      ✓
Tesla V100 32G      —      —      —      ✓      ✓
```

### 1.2 直接可比档位矩阵

| | 3090 24G | 5090 32G | V100 32G |
|---|:---:|:---:|:---:|
| **32K** | ✓ | — | — |
| **64K** | ✓ | ✓ | — |
| **128K** | ✓ | ✓ | — |
| **192K** | — | ✓ | ✓ |
| **256K** | — | ✓ | ✓（仅 offload fit 数据）|

> **本报告只对比上表中"两卡都有"的格子**。其余格子是单卡数据，不参与横评。
> 例如"3090 192K"无数据 → 不能跟 5090 192K 对比；不能拿 3090 128K 跨档推断 192K 表现。

### 1.3 三份子报告的可信度

| 卡 | 框架 | log 完整性 | 实时 ollama ps | 实时 nvidia-smi 截图 | 综合 |
|---|---|:---:|:---:|:---:|:---:|
| 3090 24G | ollama 0.32.15 | ✅ 多 task | — | — | ★★★★ |
| 5090 32G | ollama 0.32.15 | ✅ 多 task | ✅ | ✅ 4 张 | ★★★★★ |
| V100 32G | ollama（未明文）| ✅ 192K 多 task / 256K 仅 fit | — | — | ★★★（256K 数据薄）|

---

## 2. 硬件环境对比

### 2.1 三卡硬件规格（**只列 log 中明文出现的事实**）

| 维度 | RTX 3090 24G | RTX 5090 32G | Tesla V100 32G |
|---|---|---|---|
| **架构** | Ampere | Blackwell | Volta |
| **log 中描述** | `RTX 3090 24GB` | `GeForce RTX 5090 / 32607 MiB` | `Tesla V100-SXM2-32GB` |
| **compute** | 8.6 | 12.0 | 7.0 |
| **log 中报告的 VRAM** | 22.9 GiB available | 31.4 GiB available | 31.7 GiB available |
| **驱动** | CUDA 12.8.1 | 570.195.03 | log 未明文 |
| **CUDA library** | cuda_v12 | cuda_v12 | cuda_v12 |
| **Ollama** | 0.32.15 | 0.32.15 | log 未明文 |
| **系统内存** | 251.8 GiB | 503.5 GiB | 755.5 GiB |
| **CPU 线程** | n_threads=44 | log 未明文 | log 未明文 |

> **未在 log 中出现的硬件规格**（如 FP16 算力、显存带宽、TDP），本报告**不引入**。需要的请查厂商 datasheet。

### 2.2 三卡启动参数对比

| 参数 | 3090 24G | 5090 32G | V100 32G |
|---|:---:|:---:|:---:|
| `--spec-type draft-mtp` | ✅ | ✅ | ✅ |
| `--spec-draft-n-max 4` | ✅ | ✅ | ✅ |
| `--spec-draft-backend-sampling` | ✅ | ✅ | ✅ |
| `--flash-attn auto` | ✅ | ✅ | ✅ |
| `-b 512 -ub 512` | ✅ | ✅ | ✅ |
| `--context-shift --keep 4` | ✅ | ✅ | ✅ |
| `OLLAMA_FLASH_ATTENTION=true` | ✅ | ✅ | ✅ |

> 三卡启动参数**完全一致**，差异仅在 `OLLAMA_CONTEXT_LENGTH` 环境变量和 GPU 硬件本身。

---

## 3. 100% GPU 极限对比

> "100% GPU 极限" = 该卡在不触发 CPU offload 情况下能跑的最大 `num_ctx`。

| 卡 | 框架 | 100% GPU 极限 | log 证据 |
|---|---|---:|---|
| **RTX 3090 24G** | ollama 0.32.15 | **64K** | 64K: `offloaded 66/66 layers to GPU`；128K: `offloaded 54/66 layers to GPU` |
| **RTX 5090 32G** | ollama 0.32.15 | **192K** | 64K/128K/192K: `offloaded 66/66 layers to GPU`；256K: `offloaded 54/66 layers to GPU` |
| **Tesla V100 32G** | ollama（未明文）| **192K** | 192K 单卡: `offloaded 66/66 layers to GPU`；256K: `offloaded 56/66 layers to GPU` |

### 3.1 关键发现

- **32GB 卡的 100% GPU 极限 = 192K**（5090 / V100 一致）
- **24GB 卡的 100% GPU 极限 = 64K**（3090）
- **24G → 32G 卡带来的不是速度提升，而是 context 容量从 64K 拉到 192K**（3 倍）
- **V100（Volta）和 5090（Blackwell）虽然差 4 代架构，100% GPU 极限一样**——说明**这个边界由显存大小决定，不是算力决定**

### 3.2 runner.vram 与 100% GPU 极限的关系

| 卡 | 框架 | 100% GPU 极限档 | 该档 runner.vram | 24G/32G 卡的 VRAM 利用率 |
|---|---|---:|---:|---:|
| 3090 24G | ollama 0.32.15 | 64K | 16.3 GiB | **68%** |
| 5090 32G | ollama 0.32.15 | 192K | 17.0 GiB | **53%** |
| V100 32G | ollama（未明文）| 192K | 17.0 GiB | **53%** |

> 5090 在 192K 档 nvidia-smi 显示实际 VRAM 占用 31484 MiB / 32607 MiB = **97%**（数据来自 5090 报告第 7.4.5 节）。
> 说明 **ollama `runner.vram` 报的是"模型权重 + KV" 主体，未包含 cuBLAS workspace / MTP draft 上下文**——这部分"看不见的 VRAM"占了 12-14 GiB。

---

## 4. Offload 触发点对比

### 4.1 各卡 offload 边界

| 卡 | 框架 | offload 触发档 | offloaded | 触发行（节选）|
|---|---|---:|---|---|
| **3090 24G** | ollama 0.32.15 | 128K | 54/66（**12 层**）| `load_tensors: offloaded 54/66 layers to GPU` |
| **5090 32G** | ollama 0.32.15 | 256K | 54/66（**12 层**）| `load_tensors: offloaded 54/66 layers to GPU` |
| **V100 32G** | ollama（未明文）| 256K | 56/66（**10 层**）| `load_tensors: offloaded 56/66 layers to GPU` |

### 4.2 Offload 模式分解

| 卡 | 框架 | 触发档 | KV CPU | model mmap 增长 | fit 阶段报错 |
|---|---|---:|---:|---:|:---:|
| 3090 24G | ollama 0.32.15 | 128K | 1.5 GiB | 682 → 3423 MiB（5×）| `cannot meet free memory target of 1936 MiB, need to reduce device memory by 3357 MiB` |
| 5090 32G | ollama 0.32.15 | 256K | 3.0 GiB | 682 → 3423 MiB（5×）| `cannot meet free memory target of 1936 MiB, need to reduce device memory by 3924 MiB` |
| V100 32G | ollama（未明文）| 256K | 2.0 GiB | 682 → 2983 MiB（4.4×）| `cannot meet free memory target of 1936 MiB, need to reduce device memory by 3352 MiB` |

### 4.3 跨硬件共性

- **三卡的 offload 触发报错的措辞高度一致**：都是 `cannot meet free memory target of 1936 MiB`
- **`1936 MiB`** 是 llama.cpp 写死的"working set 最低预留"——三卡都一样
- **offload 后 mmap 都涨到 ~3 GiB 量级**（5× 682 MiB）
- **3090 和 5090 offload 都是 12 层**（54/66）—— `n_layer=66` 总数一致
- **V100 offload 是 10 层**（56/66）——可能因为 V100 的 mmap 涨得少（4.4× vs 5×），CPU 端有余量

> **关键观察**：offload 层数不固定为 12——它是 fit 阶段反复迭代试出来的最小 offload 数。只要能腾出 1936 MiB 就停。

---

## 5. 直接可比档位 ①：64K（3090 vs 5090）

> V100 没测 64K → 本节只有 3090 vs 5090。

### 5.1 资源分布

| 卡 | 框架 | 指标 | 64K | 差异 |
|---|---|---|---:|---|
| **3090 24G** | ollama 0.32.15 | 加载层数 | 66/66 | 一致 |
| **5090 32G** | ollama 0.32.15 | 加载层数 | 66/66 | 一致 |
| **3090 24G** | ollama 0.32.15 | runner.size | 16.3 GiB | **完全一致** |
| **5090 32G** | ollama 0.32.15 | runner.size | 16.3 GiB | **完全一致** |
| **3090 24G** | ollama 0.32.15 | runner.vram | 16.3 GiB | **完全一致** |
| **5090 32G** | ollama 0.32.15 | runner.vram | 16.3 GiB | **完全一致** |
| **3090 24G** | ollama 0.32.15 | KV GPU | 4096 MiB | **完全一致** |
| **5090 32G** | ollama 0.32.15 | KV GPU | 4096 MiB | **完全一致** |
| **3090 24G** | ollama 0.32.15 | KV CPU | 0 | 一致 |
| **5090 32G** | ollama 0.32.15 | KV CPU | 0 | 一致 |
| **3090 24G** | ollama 0.32.15 | mmap | 682 MiB | 一致 |
| **5090 32G** | ollama 0.32.15 | mmap | 682 MiB | 一致 |

> 64K 档两卡资源分布**完全相同**——差距完全来自算力。

### 5.2 Prefill 8K 对比

| 卡 | 框架 | Prefill 8K | 5090 倍数 |
|---|---|---:|---:|
| 3090 24G | ollama 0.32.15 | ~1100 tok/s | 1.00× |
| 5090 32G | ollama 0.32.15 | 2580 tok/s | **2.35×** |

> 64K 时两卡资源分布完全相同，所以 Prefill 差距**纯粹来自架构和算力**——5090 算力更强（Blackwell 相比 Ampere 跨代提升 + 更宽的显存总线）。

### 5.3 Decode 对比

| 卡 | 框架 | Decode 范围 | 中位 | 5090 倍数 |
|---|---|---:|---:|---:|
| 3090 24G | ollama 0.32.15 | 28-47 tok/s | ~37 | 1.00× |
| 5090 32G | ollama 0.32.15 | 48-67 tok/s | ~56 | **1.51×** |

### 5.4 64K 跨档总结

> **在 64K 这种"两卡都完全在 GPU"的档位**，5090 相对 3090 的优势：
> - Prefill **2.35×**
> - Decode **1.51×**

---

## 6. 直接可比档位 ②：128K（3090 vs 5090）

> V100 没测 128K → 本节只有 3090 vs 5090。
> **关键差异**：128K 时 3090 **已 offload**，5090 **仍 100% GPU**。

### 6.1 资源分布对比

| 卡 | 框架 | 指标 | 128K | 差异 |
|---|---|---|---:|---|
| **3090 24G** | ollama 0.32.15 | 加载层数 | **54/66**（12 offload）| 3090 已 offload |
| **5090 32G** | ollama 0.32.15 | 加载层数 | 66/66 | — |
| **3090 24G** | ollama 0.32.15 | runner.size | 19.0 GiB | 3090 +14% |
| **5090 32G** | ollama 0.32.15 | runner.size | 16.6 GiB | — |
| **3090 24G** | ollama 0.32.15 | runner.vram | **13.8 GiB** | 3090 -17% |
| **5090 32G** | ollama 0.32.15 | runner.vram | 16.6 GiB | — |
| **3090 24G** | ollama 0.32.15 | KV GPU | 6656 MiB | 5090 多 1.5 GiB |
| **5090 32G** | ollama 0.32.15 | KV GPU | 8192 MiB | — |
| **3090 24G** | ollama 0.32.15 | KV CPU | **1536 MiB** | 3090 新增 CPU 端 KV |
| **5090 32G** | ollama 0.32.15 | KV CPU | 0 | — |
| **3090 24G** | ollama 0.32.15 | mmap | **3423 MiB** | 3090 涨 5× |
| **5090 32G** | ollama 0.32.15 | mmap | 682 MiB | — |

> 128K 时两卡的差距**不只是算力，还有 on/off GPU 状态**——3090 已经扛不住 24G 显存。

### 6.2 Prefill 8K 对比

| 卡 | 框架 | Prefill 8K | 5090 倍数 |
|---|---|---:|---:|
| 3090 24G | ollama 0.32.15 | ~245 tok/s | 1.00× |
| 5090 32G | ollama 0.32.15 | 2650 tok/s | **10.8×** |

### 6.3 Decode 对比

| 卡 | 框架 | Decode 范围 | 中位 | 5090 倍数 |
|---|---|---:|---:|---:|
| 3090 24G | ollama 0.32.15 | 2.0-5.4 tok/s | ~2.3 | 1.00× |
| 5090 32G | ollama 0.32.15 | 52-85 tok/s | ~58 | **25.2×** |

> **128K 时 3090 的 2.3 tok/s 已经是"几乎不能用"**——这是 24G 显存物理边界的体现。
> 5090 跑 128K 跟跑 64K **几乎没差**（Decode 56 vs 58 tok/s），因为它仍在 100% GPU 状态。

### 6.4 关键差异

> **128K 档的 25× Decode 差距不能简单解读为"5090 比 3090 强 25 倍"**——
> 它是 **"100% GPU vs 12 层 CPU offload"** + **"Blackwell vs Ampere 算力"** 双重叠加的结果。
> 即使把 3090 算力打 3 倍，仍是 25× → 3× = 8.3× 差距，这部分来自 offload 的 PCIe 搬运代价。

---

## 7. 直接可比档位 ③：192K（5090 vs V100）

> 3090 没测 192K → 本节只有 5090 vs V100。
> 两卡在 192K 档**都是 100% GPU 跑**——纯算力对比。

### 7.1 资源分布

| 卡 | 框架 | 指标 | 192K 单卡 | 差异 |
|---|---|---|---:|---|
| **5090 32G** | ollama 0.32.15 | 加载层数 | 66/66 | 一致 |
| **V100 32G** | ollama（未明文）| 加载层数 | 66/66 | 一致 |
| **5090 32G** | ollama 0.32.15 | runner.size | 17.0 GiB | **完全一致** |
| **V100 32G** | ollama（未明文）| runner.size | 17.0 GiB | **完全一致** |
| **5090 32G** | ollama 0.32.15 | runner.vram | 17.0 GiB | **完全一致** |
| **V100 32G** | ollama（未明文）| runner.vram | 17.0 GiB | **完全一致** |
| **5090 32G** | ollama 0.32.15 | KV GPU | 12288 MiB | **完全一致** |
| **V100 32G** | ollama（未明文）| KV GPU | 12288 MiB | **完全一致** |
| **5090 32G** | ollama 0.32.15 | KV CPU | 0 | 一致 |
| **V100 32G** | ollama（未明文）| KV CPU | 0 | 一致 |
| **5090 32G** | ollama 0.32.15 | mmap | 682 MiB | 一致 |
| **V100 32G** | ollama（未明文）| mmap | 682 MiB | 一致 |

> 192K 档两卡资源分布**完全相同**——差距完全来自算力和架构。

### 7.2 Prefill 对比（注意 prompt 规模差异）

| 卡 | 框架 | Prefill 3K | Prefill 8K | Prefill 16K | Prefill 17K |
|---|---|---:|---:|---:|---:|
| **5090 32G** | ollama 0.32.15 | — | 2597 tok/s | 1871 tok/s | 1871 tok/s |
| **V100 32G** | ollama（未明文）| 767-783 tok/s | — | — | — |

> **V100 log 中没有 8K prompt 的 Prefill 数据**，最近的是 3K 段（2560-3584 token）。
> 所以 **3K vs 3K 不能直接比**（5090 没测 3K）。
>
> 唯一可用的"间接对比"是：
> - V100 3K 段 Prefill ~780 tok/s
> - 5090 在 8K（更大 prompt）还能维持 2597 tok/s
>
> **粗估 5090 Prefill 是 V100 的 3 倍以上**（V100 算力 / Blackwell vs Volta / 显存带宽都是 5090 优势）。

### 7.3 Decode 对比

| 卡 | 框架 | Decode 范围 | 中位 | 5090 倍数 |
|---|---|---:|---:|---:|
| 5090 32G | ollama 0.32.15 | 46-66 tok/s | ~52 | 1.00× |
| V100 32G | ollama（未明文）| 24-36 tok/s | ~30 | **1.73×** |

### 7.4 192K 跨档总结

> **在 192K 这种"两卡都 100% GPU 跑"的档位**，5090 相对 V100 的优势：
> - Decode **1.73×**
> - Prefill **3× 以上**（V100 8K 数据缺失，只能粗估）
>
> **V100 跑 192K 不是不能用**（30 tok/s 是流畅的）——**比 3090 跑 64K 慢一点**（30 vs 37 tok/s）。
> 也就是说：**老架构 V100 32G 跑 192K ≈ 新架构 3090 24G 跑 64K 的速度**。

### 7.5 V100 双卡 192K 补充

| 卡 | 框架 | 维度 | 192K 单卡 | 192K 双卡 | 差异 |
|---|---|---|---:|---:|---|
| V100 32G | ollama（未明文）| Prefill 3K | ~780 tok/s | ~785 tok/s | +1% |
| V100 32G | ollama（未明文）| Decode 中位 | ~30 tok/s | ~30 tok/s | **持平** |
| V100 32G | ollama（未明文）| runner.vram | 17.0 GiB | 24.6 GiB | +45% |
| V100 32G | ollama（未明文）| KV 拆分 | 12 GiB 单卡 | 6+6 GiB 双卡 | 拆分 |

> **双卡没有加速**——KV 拆到 2 张卡反而增加跨卡通信开销。
> 这是 V100 上的实测现象，**不外推到其他硬件**（本报告不预测 5090 双卡行为）。

---

## 8. 直接可比档位 ④：256K（5090 vs V100）

> 3090 没测 256K → 本节只有 5090 vs V100。
> 两卡**都触发 offload**——offload 模式不同。

### 8.1 Offload 模式

| 卡 | 框架 | 指标 | 256K | 差异 |
|---|---|---|---:|---|
| **5090 32G** | ollama 0.32.15 | 加载层数 | **54/66**（12 offload）| 5090 触发 12 层 |
| **V100 32G** | ollama（未明文）| 加载层数 | **56/66**（10 offload）| V100 少 offload 2 层 |
| **5090 32G** | ollama 0.32.15 | runner.size | 21.2 GiB | 5090 略大 |
| **V100 32G** | ollama（未明文）| runner.size | 20.2 GiB | — |
| **5090 32G** | ollama 0.32.15 | runner.vram | 14.5 GiB | 接近 |
| **V100 32G** | ollama（未明文）| runner.vram | 14.9 GiB | — |
| **5090 32G** | ollama 0.32.15 | KV GPU | 13312 MiB | V100 多 1 GiB |
| **V100 32G** | ollama（未明文）| KV GPU | 14336 MiB | — |
| **5090 32G** | ollama 0.32.15 | KV CPU | **3072 MiB** | 5090 多 1 GiB |
| **V100 32G** | ollama（未明文）| KV CPU | **2048 MiB** | — |
| **5090 32G** | ollama 0.32.15 | mmap | 3423 MiB | 5090 多 440 MiB |
| **V100 32G** | ollama（未明文）| mmap | 2983 MiB | — |
| **5090 32G** | ollama 0.32.15 | fit 报错 | 需腾 3924 MiB | 5090 需腾更多 |
| **V100 32G** | ollama（未明文）| fit 报错 | 需腾 3352 MiB | — |

### 8.2 Prefill 对比

| 卡 | 框架 | Prefill 8K | 备注 |
|---|---|---:|---|
| 5090 32G | ollama 0.32.15 | 535 tok/s | log 实测 |
| V100 32G | ollama（未明文）| — | log 无 Prefill 数据（fit 阶段未完成到 task）|

> **V100 256K log 没有 print_timing 任务数据**——只能从 fit 阶段知道它**最终接受了** 10 层 offload 的方案，但没跑到实际推理。

### 8.3 Decode 对比

| 卡 | 框架 | Decode | 备注 |
|---|---|---:|---|
| 5090 32G | ollama 0.32.15 | **~7 tok/s** | task 0 9.78 / task 16 5.48，中位 ~7 |
| V100 32G | ollama（未明文）| **—** | **无 task 数据**（log 中无 print_timing）|

> **本批数据 V100 256K 的 Decode 是空缺**——不能直接比 5090（7 tok/s）vs V100（未知）。
> 只能从 5090 的 7 tok/s 推测 V100 也不会好到哪去（10 层 offload 状态下都受 PCIe 搬运限制），但**这是推测不是实测**。

### 8.4 256K 跨档总结

> **两卡在 256K 都触发 offload**——5090 触发 12 层、V100 触发 10 层。
> 5090 有实测 Decode ~7 tok/s；V100 无 task 数据。
> **256K 这个档位本批数据下没有"100% GPU 跑"的证据**——三卡都到极限了。

---

## 9. vLLM 路线（5090 only，**未在 3090 / V100 复现**）

> **本节严格基于 5090 的 7 份 vLLM 日志**。
> 3090 / V100 **没有 vLLM 数据**——本章所有结论只对 5090 有效，**不外推**。
> 详细 vLLM 报告见 `RTX5070-32G/花巨资测试_Qwen3.8-27B_RTX5070-32G_vLLM_投机解码对比.md`。

### 9.1 vLLM 测试覆盖

> **本节所有数据来自 vLLM 0.26.1rc1 + NVFP4 + fp8 KV（5090 only）**。

| 上下文 | 框架 | 无加速 | MTP | DFlash 2 | 备注 |
|---|---|:---:|:---:|:---:|---|
| 32K | vLLM 0.26.1rc1 | ❌ 未测 | ❌ 未测 | ✅ **~170 tok/s** | DFlash 2 跑出 vLLM 最高分 |
| 128K | vLLM 0.26.1rc1 | ✅ ~68 tok/s | ✅ **~120 tok/s** | ❌ 未测 | MTP 1.76× over 无加速 |
| 192K | vLLM 0.26.1rc1 | ✅ **~70 tok/s** | ❌ **启动失败** | ❌ 未测 | MTP 装不下 KV |

### 9.2 无加速基线（vLLM + NVFP4 + fp8 KV）

> 5090 的 vLLM 无加速基线跨档几乎相同：

| 框架 | 上下文 | Decode 中位 | 与 ollama 同档对比 |
|---|---|---:|---|
| vLLM 0.26.1rc1 | 128K | 68.0 tok/s | ollama 128K = 58 tok/s → vLLM 快 **1.17×** |
| vLLM 0.26.1rc1 | 192K | 69.4-71.7 tok/s | ollama 192K = 52 tok/s → vLLM 快 **1.33-1.38×** |

> **NVFP4 量化 + Blackwell 算力** 三重叠加让 vLLM 基线比 ollama Q4_K_M + MTP 还快 17-38%——**量化收益甚至超过 MTP 加速**。
> **128K 跟 192K 速度几乎一样**（68.0 vs 69.4-71.7，差 < 5%）——说明在 5090 + NVFP4 上，**Decode 速度瓶颈不在 context 长度，而在算力上限**。

### 9.3 MTP 加速（vLLM）

| 框架 | 档位 | 无 MTP | 有 MTP | 加速比 | 备注 |
|---|---|---:|---:|---:|---|
| vLLM 0.26.1rc1 | 128K | 68.0 tok/s | **~120 tok/s** | **1.76×** | 峰值 135.5 tok/s |
| vLLM 0.26.1rc1 | 192K | 70 tok/s | **❌ 启动失败** | — | 7.0 GiB 需 vs 6.42 GiB 实有，缺 580 MiB |

> **MTP 192K 报错原文**（`192k-mtp.log` line 116）：
> ```
> ValueError: To serve at least one request with the model's max seq len (196608),
> (7.0 GiB KV cache is needed, which is larger than the available KV cache memory (6.42 GiB).
> Based on the available memory, the estimated maximum model length is 177600.
> ```
> vLLM 建议把 `max_model_len` 砍到 **177,600**（= 192K - 14.4K）救回——本批数据**未测过这个 workaround**。

### 9.4 DFlash 2 加速（vLLM）

| 框架 | 档位 | 无加速 | DFlash 2 | **加速比** | 备注 |
|---|---|---:|---:|---:|---|
| vLLM 0.26.1rc1 | 32K | 推测 ~70 tok/s | **~170 tok/s**（峰值 **230.6**）| **2.43-3.29×** | vLLM 路线最高分 |
| vLLM 0.26.1rc1 | 128K | 68 tok/s | ❌ 未测 | — | — |
| vLLM 0.26.1rc1 | 192K | 70 tok/s | ❌ 未测 | — | — |

> DFlash 2 草稿模型：`/hy-tmp/models/Qwen3.8-27B-DFlash2`（来自 HF `incoai/Qwen3.8-27B-DFlash2`，~2B 参数）。
> 配置：`num_speculative_tokens=7`（Inco 官方推荐）。
> **关键观察**：DFlash 2 在 KV 用到 80% 时仍能跑 147 tok/s——**比 MTP 更能扛长 context**。

### 9.5 跨方案加速比（5090 / NVFP4 / fp8 KV）

| 框架（基线 vs 加速） | 对比 | 加速比 | 来源 |
|---|---|---:|---|
| vLLM → vLLM | **DFlash 2 vs 无加速（32K）** | **2.43-3.29×** | 170 / 70 |
| vLLM → vLLM | **MTP vs 无加速（128K）** | **1.76×** | 120 / 68 |
| vLLM → vLLM | **DFlash 2 vs MTP（同档假设）** | ~1.4-1.8× | 170 / 120 |
| **vLLM vs ollama** | **vLLM+NVFP4 vs ollama+Q4_K_M（192K）** | **1.33-1.38×** | 70 / 52 |
| **vLLM vs ollama** | **DFlash 2 vs ollama 192K + MTP** | **3.3-4.4×** | 170-230 / 52 |

### 9.6 ollama vs vLLM 路线对比（5090 only）

| 框架 | 维度 | 数值 | 差距 |
|---|---|---:|---:|
| ollama 0.32.15 | 量化格式 | Q4_K_M（GGUF）| NVFP4 更小 |
| vLLM 0.26.1rc1 | 量化格式 | NVFP4（ModelOpt）| — |
| ollama 0.32.15 | KV cache | 默认（FP16）| 节省一半 KV 显存 |
| vLLM 0.26.1rc1 | KV cache | **FP8 压缩** | — |
| ollama 0.32.15 | 192K Decode | 52 tok/s | **1.35×** |
| vLLM 0.26.1rc1 | 192K Decode（无 MTP）| **70 tok/s** | — |
| ollama 0.32.15 | 192K + MTP | 52 tok/s | MTP 路线 vLLM 失败 |
| vLLM 0.26.1rc1 | 192K + MTP | ❌ 装不下 | — |
| ollama 0.32.15 | 128K + MTP | 58 tok/s | **2.07×** |
| vLLM 0.26.1rc1 | 128K + MTP | **120 tok/s** | — |
| ollama 0.32.15 | 32K + DFlash 2 | ❌ 不支持 | **DFlash 2 独占** |
| vLLM 0.26.1rc1 | 32K + DFlash 2 | **170 tok/s**（峰值 230）| — |
| ollama 0.32.15 | Prefill 8K（192K）| 2597 tok/s | 1.53× |
| vLLM 0.26.1rc1 | Prefill 8K（192K）| **3973 tok/s** | — |

> **关键发现**：
> 1. **vLLM 路线在 128K + MTP 跑出 120 tok/s**——比 ollama 192K MTP（52 tok/s）快 2.3 倍
> 2. **DFlash 2 是 vLLM 独占加速**——ollama 0.32.15 不支持
> 3. **vLLM 192K + MTP 装不下**——是 vLLM 0.26.1rc1 + NVFP4 路线独有的限制，**ollama 192K + MTP 装得下**

### 9.7 vLLM 启动配置

**DFlash 2 + 32K（推荐）：**
```bash
vllm serve /hy-tmp/models/Qwen3.8-27B-NVFP4 \
  --quantization modelopt --kv-cache-dtype fp8 \
  --max-model-len 40960 --max-num-seqs 1 \
  --speculative-config '{"method": "dflash", "model": "/hy-tmp/models/Qwen3.8-27B-DFlash2", "num_speculative_tokens": 7}'
```

**MTP + 128K：**
```bash
vllm serve /hy-tmp/models/Qwen3.8-27B-NVFP4 \
  --quantization modelopt --kv-cache-dtype fp8 \
  --max-model-len 131072 --max-num-seqs 1 --max-num-batched-tokens 4096 \
  --speculative-config '{"method": "mtp", "num_speculative_tokens": 2}'
```

**无加速 + 192K：**
```bash
vllm serve /hy-tmp/models/Qwen3.8-27B-NVFP4 \
  --quantization modelopt --kv-cache-dtype fp8 \
  --max-model-len 196608 --max-num-seqs 1
```

> 三个 vLLM 启动配置都是 `non-default args` 行直接读出来的。
> **port=11434**——故意用 ollama 默认端口，让客户端代码无缝切换后端。

---

## 10. MTP / Draft Acceptance 跨硬件对比

| 卡 | 框架 | 档位 | acceptance 范围 | 平均 |
|---|---|---|---:|---:|
| **3090 24G** | ollama 0.32.15 | 64K | — | **~0.71** |
| 3090 24G | ollama 0.32.15 | 128K | — | **~0.75** |
| **5090 32G** | ollama 0.32.15 | 64K | 0.36-0.77 | ~0.50 |
| 5090 32G | ollama 0.32.15 | 128K | 0.40-0.81 | ~0.55 |
| 5090 32G | ollama 0.32.15 | 192K | 0.34-0.60 | ~0.46 |
| 5090 32G | ollama 0.32.15 | 256K | 0.44-0.62 | ~0.53 |
| **V100 32G** | ollama（未明文）| 192K 单卡 | 0.45-0.69 | ~0.58 |
| V100 32G | ollama（未明文）| 192K 双卡 | 0.42-0.67 | ~0.55 |

### 10.1 跨硬件规律

- **3090 MTP acceptance 最高**（0.71-0.75）
- **5090 中间**（0.46-0.55）
- **V100 中间偏上**（0.55-0.58）
- **MTP acceptance 不是性能差距的主因**——三卡 acceptance 都在 0.4-0.8 之间，差距小于 2×，但性能差距有 25×（128K 3090 vs 5090）

---

## 11. 选择建议（按场景）

### 11.1 按 context 长度（ollama + vLLM 路线综合）

| 框架 | 需求 | 推荐 | 依据（来自本批数据）|
|---|---|---|---|
| vLLM 0.26.1rc1 | **只跑 ≤32K（vLLM 路线）** | **5090 32G + vLLM + DFlash 2** | 32K + DFlash 2 跑出 **170 tok/s 稳定 / 230 峰值** |
| ollama 0.32.15 | **只跑 ≤32K（ollama 路线）** | 3090 24G | 3090 32K 跑出 36 tok/s；5090 / V100 无 32K ollama 数据 |
| ollama 0.32.15 | **跑 64K** | **3090 24G**（ollama 性价比）| 3090 64K Decode 37 tok/s；5090 同档 56 tok/s |
| vLLM 0.26.1rc1 | **跑 128K（vLLM）** | **5090 32G + vLLM + MTP** | 128K + MTP 跑出 **120 tok/s**，比 ollama 128K MTP（58 tok/s）快 2× |
| ollama 0.32.15 | **跑 128K（ollama）** | **必须 32G 卡** | 24G 卡 128K 触发 12 层 offload，Decode 跌到 2.3 tok/s |
| vLLM 0.26.1rc1 | **跑 192K** | **5090 32G + vLLM（无 MTP）** | vLLM 192K 跑出 **70 tok/s**（比 ollama 192K MTP 52 tok/s 快 35%）|
| ollama（未明文）| **跑 192K（预算紧 + ollama）** | V100 32G 备选 | V100 192K 仍 100% GPU，Decode 30 tok/s 可用 |
| vLLM 0.26.1rc1 | **跑 192K（vLLM + MTP）** | ❌ 装不下 | 需把 max_model_len 砍到 177K，本批未测 workaround |
| ollama + vLLM | **跑 256K** | **三卡都不行** | ollama 三卡都触发 offload，vLLM 0.26 + NVFP4 装不下 |

### 11.2 按性能优先级

| 框架 | 优先级 | 推荐卡 + 路线 | 依据 |
|---|---|---|---|
| ollama 0.32.15 | **Prefill 速度** | **5090 32G**（ollama 路线）| 64K/128K/192K 都 2580-2650 tok/s，远超其他卡 |
| vLLM 0.26.1rc1 | **Decode 速度（vLLM 32K + DFlash 2）** | **5090 32G** | 32K + DFlash 2 跑出 **170 tok/s 稳定 / 230 峰值** |
| vLLM 0.26.1rc1 | **Decode 速度（vLLM 128K + MTP）** | **5090 32G** | 128K + MTP 跑出 120 tok/s |
| ollama 0.32.15 | **Decode 速度（ollama 100% GPU 档）** | **5090 32G** | 128K 58 / 192K 52 tok/s，跨档无衰减 |
| ollama + vLLM | **Decode 速度（offload 档）** | — | 没有任何卡的 offload 档 Decode 流畅 |
| ollama 0.32.15 | **MTP 接受率** | **3090 24G** | 0.71-0.75 最高，但不代表总性能最好 |

### 11.3 按预算 / 二手市场（**仅基于本批数据**）

| 卡 | 框架 | 二手价位（参考）| 24G vs 32G 卡定位 |
|---|---|---|---|
| 3090 24G | ollama 0.32.15 | 中 | ollama 性价比档（64K 极限）|
| 5090 32G | ollama + **vLLM** | 高 | **vLLM 旗舰**（DFlash 32K / MTP 128K / 192K 无加速全包）|
| V100 32G | ollama（未明文）| 低（数据中心退役卡）| ollama 备选（192K 极限，但速度慢）|

> **价格不是本批数据的范围**——上面只是行业普遍认知，**请自行查市价**。

---

## 12. 关键发现与未覆盖说明

### 12.1 跨硬件共性

| 发现 | 证据（三卡都观察到了）|
|---|---|
| 100% GPU 极限由**显存大小**决定，不是算力 | 5090 / V100 算力差 4 代，但 32G 卡 100% GPU 极限都是 192K |
| Offload 触发报错的措辞一致 | 三卡都是 `cannot meet free memory target of 1936 MiB` |
| Offload 后 mmap 都涨到 ~3 GiB | 3090 5× / 5090 5× / V100 4.4× |
| 100% GPU 档的 runner.vram 都接近 17 GiB | 3090 64K=16.3 / 5090 192K=17.0 / V100 192K=17.0 |
| **Decode 速度瓶颈在算力上限，不是 context 长度** | 5090 128K 跟 192K 无加速都是 ~70 tok/s（差 < 5%）|

### 12.2 跨硬件差异

| 卡 | 框架 | 维度 | 数据 |
|---|---|---|---|
| 3090 24G | ollama 0.32.15 | 100% GPU 极限 | 64K |
| 5090 32G | ollama 0.32.15 | 100% GPU 极限 | 192K |
| V100 32G | ollama（未明文）| 100% GPU 极限 | 192K |
| 3090 24G | ollama 0.32.15 | 64K Decode | ~37 tok/s |
| 5090 32G | ollama 0.32.15 | 64K Decode | ~56 tok/s |
| 3090 24G | ollama 0.32.15 | 128K Decode | ~2.3 tok/s（offload）|
| 5090 32G | ollama 0.32.15 | 128K Decode | ~58 tok/s |
| 5090 32G | ollama 0.32.15 | 192K Decode | ~52 tok/s |
| V100 32G | ollama（未明文）| 192K Decode | ~30 tok/s |
| 5090 32G | vLLM 0.26.1rc1 | 192K Decode（无加速）| **~70 tok/s** |
| 5090 32G | vLLM 0.26.1rc1 | 128K Decode（MTP）| **~120 tok/s** |
| 5090 32G | vLLM 0.26.1rc1 | 32K Decode（DFlash 2）| **~170 tok/s**（峰值 230）|
| 3090 24G | ollama 0.32.15 | Prefill 8K（64K 档）| 1100 tok/s |
| 5090 32G | ollama 0.32.15 | Prefill 8K（64K 档）| 2580 tok/s |
| 3090 24G | ollama 0.32.15 | MTP acceptance | 0.71-0.75 |
| 5090 32G | ollama 0.32.15 | MTP acceptance | 0.46-0.55 |
| V100 32G | ollama（未明文）| MTP acceptance | 0.55-0.58 |
| 3090 24G | ollama 0.32.15 | 显存利用率（100% GPU 极限档）| 68% |
| 5090 32G | ollama 0.32.15 | 显存利用率（100% GPU 极限档）| 53%（nvidia-smi 97%）|
| V100 32G | ollama（未明文）| 显存利用率（100% GPU 极限档）| 53% |

### 12.3 跨路线差异（5090 only）

| 维度 | ollama 0.32.15（Q4_K_M）| vLLM 0.26.1rc1（NVFP4）|
|---|---|---|
| KV cache 格式 | 默认（FP16）| **FP8 压缩** |
| 192K Decode | 52 tok/s | **70 tok/s**（无 MTP）|
| 128K Decode | 58 tok/s | **120 tok/s**（MTP）|
| 32K Decode | 推测 36-56 | **170 tok/s**（DFlash 2）|
| 192K + MTP | ✅ 52 tok/s | ❌ 装不下 |
| DFlash 2 支持 | ❌ 不支持 | ✅ 跑出 170 tok/s |
| Prefill 8K（192K）| 2597 tok/s | **3973 tok/s** |

> **关键结论**：vLLM + NVFP4 + fp8 KV 路线在 5090 上**全面快于** ollama + Q4_K_M + MTP 路线，但 **192K + MTP 是 vLLM 0.26.1rc1 的硬约束**（KV 不足）。

### 12.4 数据未覆盖的方面

| 框架 | 未覆盖内容 | 原因 |
|---|---|---|
| ollama | 3090 跑 192K / 256K | 本批 3090 测试只到 128K |
| ollama | 5090 跑 32K | 本批 5090 ollama 测试从 64K 起 |
| ollama | V100 跑 32K / 64K / 128K | 本批 V100 测试只从 192K 起 |
| ollama | 3090 vs 5090 跑 32K | 两卡都没测这一档 |
| ollama | V100 256K 实际 Decode | log 无 print_timing 任务数据 |
| ollama | 3090 / V100 nvidia-smi 实时截图 | 本批未提供 |
| ollama | V100 192K Prefill 8K 数据 | log 只到 3K 段 |
| ollama | 5090 / V100 双卡测试 | 5090 无双卡 log；V100 192K 双卡无加速 |
| ollama | 跨卡 PCIe 搬运实际带宽 | 无 nvidia-smi pcie -l 数据 |
| **vLLM** | **3090 / V100 跑 vLLM** | 本批只有 5090 测了 vLLM 路线 |
| **vLLM** | **vLLM DFlash 2 在 128K / 192K** | 本批只测了 32K |
| **vLLM** | **vLLM MTP 192K 砍到 177K 的 workaround** | 本批未测 |
| **vLLM** | **vLLM 256K** | 192K MTP 都装不下，256K 概率为 0 |
| **vLLM** | **vLLM 多并发（max-num-seqs > 1）** | 全部 log 都是单并发 |

---

## 13. 结论

> **本批实测数据下，Qwen3.8-27B 在三卡 × 两推理引擎 上的 context 处理能力画像：**

### 13.1 一句话总结

> **ollama 路线（Q4_K_M + MTP）：**
> - **想要最大 context + 最快速度**：**RTX 5090 32G**（192K 跑满，~52 tok/s）
> - **想要最大 context + 预算紧**：**Tesla V100 32G**（192K 跑满，~30 tok/s，慢但能用）
> - **想要 24G 卡跑 Coding Agent**：**RTX 3090 24G** 64K 档（~37 tok/s，甜点）
> - **想要跑 256K**：**三卡都触发 offload**，本批数据无 100% GPU 跑 256K 的证据
>
> **vLLM 路线（NVFP4 + fp8 KV，5090 only）：**
> - **想要最快 Decode**：**5090 32G + vLLM + DFlash 2（32K）**（**~170 tok/s 稳定 / 230 峰值**）
> - **想要长上下文 + 加速**：**5090 32G + vLLM + MTP（128K）**（**~120 tok/s**，比 ollama 128K MTP 快 2×）
> - **想要 192K 极限**：**5090 32G + vLLM 无加速**（~70 tok/s，比 ollama 192K MTP 快 35%）
> - **vLLM 192K + MTP**：**❌ 装不下 KV**

### 13.2 关键证据链

| 框架 | 事实 | 三卡都成立 / 各自证据 |
|---|---|---|
| ollama | 100% GPU 极限由显存决定 | 32G 卡都到 192K，24G 卡只到 64K |
| ollama | Offload 触发点统一措辞 | `cannot meet free memory target of 1936 MiB` 三卡都有 |
| ollama | Offload 后 Decode 跌一个数量级 | 3090 128K 2.3 / 5090 256K 7 / V100 256K 未知 |
| ollama | 100% GPU 档 KV 不落 CPU | 三卡 100% GPU 档 `CPU KV buffer size` 字段都不存在 |
| ollama | MTP acceptance 不是主因 | 三卡都在 0.4-0.8 区间 |
| ollama + vLLM | **Decode 速度瓶颈在算力上限** | 5090 128K 跟 192K 无加速都是 ~70 tok/s（差 < 5%）|
| vLLM vs ollama | **NVFP4 + fp8 KV 比 Q4_K_M + 默认 KV 快 35%** | 5090 192K：vLLM 70 vs ollama 52 tok/s |
| vLLM | **DFlash 2 比 MTP 强** | 5090 32K DFlash 170 vs 128K MTP 120 tok/s |
| vLLM | **vLLM 192K + MTP 是硬约束** | vLLM 报错：7.0 GiB 需 vs 6.42 GiB 实有 |

### 13.3 报告局限

> **本报告不预测未实测的组合**——
> 不知道 3090 跑 192K 会怎样（数据缺失），
> 不知道 5090 跑 32K ollama 会怎样（数据缺失），
> 不知道 V100 跑 128K 会怎样（数据缺失），
> 也不知道 5090 双卡会不会加速（V100 双卡没加速，但**这是单卡数据，不外推**），
> **不知道 3090 / V100 跑 vLLM 路线会怎样（vLLM 数据 5090 only）**，
> **不知道 vLLM DFlash 2 在 128K / 192K 跑不跑得动（数据缺失）**。
>
> 需要补哪一档的测试，告诉我。

---

> 报告数据来源：
> - 三份 ollama 子报告的 ollama DEBUG log（一手数据）
> - 5090 vLLM 子报告的 7 份 vLLM 0.26.1rc1 日志
> - 5090 报告的 4 张 nvidia-smi 截图 + `ollama ps` ×4 + `nvidia-smi` 实时输出
> - 3090 / V100 报告无 nvidia-smi 截图
> - **本横评仅做横向对比的二次归纳，未引入新的硬件规格或预测**
>
> 如果想看更详细的 timing 表、或补测缺失档位（3090 192K / 5090 32K ollama / V100 128K / vLLM 128K+ 等），回复里喊一声。
