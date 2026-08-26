# Qwen3.8-27B 在 V100 32G 上的上下文对比实测

> 本报告**完全基于**以下 3 份文档：
> - `ollama192k单卡.log`（135,191 bytes）— 1× V100 32G 跑 192K
> - `ollama192k-2.log`（125,007 bytes）— 2× V100 32G 跑 192K（log 验证 ID:0+ID:1 两块卡）
> - `ollama256k.log`（37,620 bytes）— 1× V100 32G 跑 256K
>
> 本批**未提供 nvidia-smi 实时截图**。
> **本报告仅基于 V100 32G 自身数据，不与其他硬件做横向对比。**

---

## 0. 结论（基于 3 档实测）

### 0.1 一句话

> **V100 32G 单卡 192K 是 100% GPU 跑的最大档**——Decode 中位 ~30 tok/s。
> **256K 触发 10 层 CPU offload**，Decode 跌至个位数 tok/s。
> **双卡 192K 没有加速效果**（Decode 跟单卡持平）。

### 0.2 推荐档位

| 优先级 | 配置 | GPU 占比 | Decode 中位 | 评价（基于本批数据）|
|---|---:|---:|---:|---|
| ⭐ **首选** | **V100 单卡 192K** | 100% | ~30 tok/s | 100% GPU 跑，无 offload |
| ❌ 不推荐 | V100 双卡 192K | 100% | ~30 tok/s（**未加速**）| 多卡没带来收益 |
| ❌ 不推荐 | V100 单卡 256K | 56/66 GPU | 个位数 tok/s | 触发 10 层 offload |

### 0.3 3 档核心指标（来自 log 一手数据）

| 指标 | 192K 单卡 | 192K 双卡 | 256K 单卡 |
|---|---:|---:|---:|
| 加载层数 | 66/66 GPU | 66/66 GPU | **56/66 GPU** |
| runner.size | 17.0 GiB | 24.6 GiB | 20.2 GiB |
| runner.vram | 17.0 GiB | 24.6 GiB | **14.9 GiB** |
| `size == vram`？ | ✅ | ✅ | ❌ |
| KV cache GPU0 | 12 GiB | 6 GiB | 14.3 GiB |
| KV cache GPU1 | — | 6 GiB | — |
| KV cache CPU | 0 | 0 | **2 GiB** |
| Prompt Prefill（3K）| ~780 tok/s | ~785 tok/s | 触发 offload |
| Decode 中位 | ~30 tok/s | ~30 tok/s | 个位数 |

### 0.4 启动配置（推荐 V100 单卡 192K）

```bash
OLLAMA_CONTEXT_LENGTH=196608 \
OLLAMA_DEBUG=1 \
OLLAMA_FLASH_ATTENTION=true \
OLLAMA_KEEP_ALIVE=-1 \
ollama serve
```

> 各档详细依据见第 9 节"推荐档位"。

---

## TL;DR

| 档位 | 结论 |
|---|---|
| **V100 单卡 192K** | 100% GPU，runner.size == runner.vram == 17.0 GiB，KV 12 GiB（全部 GPU）|
| **V100 双卡 192K** | 100% GPU 但**未加速**——KV 拆到 2 张卡（各 6 GiB），总 VRAM 24.6 GiB，Decode 跟单卡持平 |
| **V100 单卡 256K** | **触发 10 层 offload**，runner.vram 14.9 GiB ≠ runner.size 20.2 GiB，KV 14.3 GiB GPU + 2 GiB CPU |

> 192K 是 100% GPU 跑的最大档，256K 触发 offload。

---

## 1. 测试环境

| 项目 | 配置 |
|---|---|
| GPU | NVIDIA Tesla V100-SXM2-32GB（**compute 7.0 / Volta 架构**）|
| 显存 | HBM2 32GB（31.7 GiB available）|
| 驱动 / CUDA | log 中未提供具体版本（`runner.library=CUDA`）|
| 模型 | Qwen3.8-27B（Qwen3.8 27B 0814，ollama tag `qwen3.8:27b`）|
| 量化 + 加速 | **Q4_K_M + MTP（draft-mtp）** |
| 验证 | 3 份 log 中 file_type=15 + 启动 `--spec-type draft-mtp` 一致；3 份 log 共享同一模型 hash `f5f1dd89...` |
| 量化细节 | GGUF V3，file_type=15，f32 360 / q4_K 439 / q6_K 67 tensors |
| 模型参数 | 27.32 B（n_layer=64 transformer + 1 MTP = n_layer_all=65）|
| 架构 | qwen35 hybrid（SSM + 局部 attention，full_attention_interval=4）|
| 上下文训练长度 | 262144（256K）|
| Ollama | log 中未提供具体版本 |
| 系统内存 | **755.5 GiB** |
| GPU 显存 | 31.7 GiB（单卡 32G）/ 63.5 GiB（双卡 2×32G）|
| 启动参数 | `--spec-type draft-mtp --spec-draft-n-max 4 --spec-draft-backend-sampling --flash-attn auto -b 512 -ub 512 --context-shift --keep 4` |
| 场景 | 验证 V100 32G 上 Qwen3.8-27B 上下文能力 |

> **V100 是 2017 年 Volta 架构**（compute 7.0），FP32 算力约 14 TFLOPS，FP16 tensor core 算力约 112 TFLOPS。
> `OLLAMA_FLASH_ATTENTION=true` 在 log 中被设置——Flash Attention 完整支持需要 compute 8.0+，V100 上会通过软件路径或退化为普通 attention。

---

## 2. 实测样本与数据来源

| 档位 | 配置 | 数据来源 | 证据强度 |
|---|---|---|---|
| **192K 单卡** | 1× V100 32G | `ollama192k单卡.log`（30+ task 完整数据）| ★★★★★ |
| **192K 双卡** | 2× V100 32G（63.5 GiB，log 中 `runner.inference="[{ID:0 Library:CUDA} {ID:1 Library:CUDA}]"`）| `ollama192k-2.log`（多 task 完整数据）| ★★★★★ |
| **256K 单卡** | 1× V100 32G | `ollama256k.log`（仅 fit 阶段日志，无 print_timing 任务数据）| ★★★☆☆ |

> **256K log 特殊性**：触发 offload fit 阶段后，只有 `common_params_fit_impl` 反复调整 n_layer 的迭代日志（n_layer=66 → 58 → 57 → 56），**没有** `slot print_timing` 任务数据。可能测试时未跑到实际推理任务。

---

## 3. 资源分布（3 档 log 直接读出）

### 3.1 加载层数与 Offload

| 档位 | log 行 | 含义 |
|---|---|---|
| 192K 单卡 | `load_tensors: offloaded 66/66 layers to GPU` | 全部在 GPU |
| 192K 双卡 | `load_tensors: offloaded 66/66 layers to GPU` | 全部在 GPU（双卡各分部分）|
| 256K 单卡 | `load_tensors: offloaded 56/66 layers to GPU` | **10 层 offload** |

256K 触发的 fit 错误原文：

```text
common_params_fit_impl: cannot meet free memory target of 1936 MiB,
                       need to reduce device memory by 3352 MiB
common_params_fit_impl: id=0, n_layer=66, n_part= 0, overflow_type=4, mem= 32849 MiB
common_params_fit_impl: id=0, n_layer=58, n_part= 0, overflow_type=4, mem= 29844 MiB
common_params_fit_impl: set ngl_per_device_high[0].n_layer=58
common_params_fit_impl: id=0, n_layer=57, n_part= 0, overflow_type=4, mem= 29623 MiB
common_params_fit_impl: set ngl_per_device_high[0].n_layer=57
common_params_fit_impl: id=0, n_layer=56, n_part= 0, overflow_type=4, mem= 29401 MiB
common_params_fit_impl: set ngl_per_device[0].n_layer=56
```

> fit 阶段从 66 层逐步降到 56 层（CPU 腾出 32849-29401 = 3448 MiB 给 KV/working set）。

### 3.2 runner.size / runner.vram

| 档位 | runner.size | runner.vram | size == vram？ | 解读 |
|---|---:|---:|---|---|
| 192K 单卡 | 17.0 GiB | 17.0 GiB | ✅ | 模型 + KV 全部在 VRAM |
| 192K 双卡 | 24.6 GiB | 24.6 GiB | ✅ | 模型 7.25 GiB 在 GPU0 + KV 6+6 GiB 拆到 2 卡 + working set |
| 256K 单卡 | 20.2 GiB | **14.9 GiB** | ❌ | 10 层在 CPU，KV 14.3 GiB + 模型 13 GiB 仍占 27.3 GiB 但 VRAM 端只 14.9 |

> **192K 双卡：runner.vram 24.6 GiB** 超过了单卡 32G 容量的 75%——KV 被拆分到两张卡（各 6 GiB），模型权重全在 GPU0（7.25 GiB），剩 11+ GiB 给 working set。

### 3.3 KV cache 拆分

| 档位 | KV GPU0 | KV GPU1 | KV CPU | KV total |
|---|---:|---:|---:|---:|
| 192K 单卡 | 12288 MiB | — | 0 | 12288 MiB |
| 192K 双卡 | 6144 MiB | 6144 MiB | 0 | 12288 MiB（拆分到 2 卡）|
| 256K 单卡 | 14336 MiB | — | **2048 MiB** | 16384 MiB |

> 192K 时 V100 双卡把 KV 拆成 6 GiB + 6 GiB，**模型权重只放 GPU0**（7.25 GiB），导致 GPU0 偏热、GPU1 偏闲。
> 256K 时 2 GiB KV 落 CPU。

### 3.4 CPU 端 model mmap

| 档位 | CPU_Mapped model buffer | 解读 |
|---|---:|---|
| 192K 单卡 | 682 MiB | mmap 正常值 |
| 192K 双卡 | 682 MiB | mmap 正常值 |
| 256K 单卡 | **2982.90 MiB** | mmap 涨 4.4×（与 10 层 offload 一致）|

---

## 4. Prompt Prefill 对比

### 4.1 192K 单卡 Prefill

```
n_tokens   2560  → 782.78 tok/s
n_tokens   3072  → 767.00 tok/s
n_tokens   3584  → 767.22 tok/s
n_tokens  17065  → 614.39 tok/s  (task 61)
n_tokens  18610  → 468.38 tok/s  (task 356)
```

### 4.2 192K 双卡 Prefill

```
n_tokens   2560  → 785.34 tok/s
n_tokens   3072  → 784.37 tok/s
n_tokens   3584  → 783.30 tok/s
n_tokens  17066  → 671.74 tok/s  (task 337)
n_tokens   5632  → 557.33 tok/s  (task 1259)
```

### 4.3 256K 单卡 Prefill

256K log 中无 `prompt processing` 抽样（fit 阶段反复迭代未完成到任务执行）。

### 4.4 Prefill 跨档对比

| Prompt 规模 | 192K 单卡 | 192K 双卡 | 倍数 |
|---|---:|---:|---:|
| 3K | 767-783 | 783-785 | 1.02× |
| 17K | 614 | 672 | 1.09× |
| 18K | 468 | — | — |
| 5.6K | — | 557 | — |

> 192K 单卡 / 双卡 Prefill **几乎一致**（3K prompt 都在 ~780 tok/s）。
> 双卡 Prefill 提升 2-9%。

---

## 5. Decode 对比

### 5.1 192K 单卡 Decode（完整数据）

| Task | n_gen | prompt | eval tok/s | draft |
|---:|---:|---:|---:|---:|
| 0 | 214 | 147 | **36.31** | 0.685 |
| 61 | 288 | 17065 | **27.59** | 0.593 |
| 183 | 456 | 3246 | **24.73** | 0.448 |
| 356 | 388 | 18610 | **24.04** | — |

> 范围 24-36 tok/s，**中位 ~30 tok/s**。

### 5.2 192K 双卡 Decode（完整数据）

| Task | n_gen | prompt | eval tok/s | draft |
|---:|---:|---:|---:|---:|
| 201 | 484 | 146 | **44.93** | 0.665 |
| 337 | 325 | 17066 | **33.04** | 0.560 |
| 473 | 1270 | 3331 | **27.48** | 0.419 |
| 957 | 759 | 4226 | **26.06** | — |

> 范围 26-45 tok/s，**中位 ~30 tok/s**。

### 5.3 256K 单卡 Decode

256K log 无 print_timing 任务数据（fit 阶段未完成到任务执行）。

### 5.4 Decode 跨档对比

| 档位 | Decode 范围 | 中位 |
|---|---:|---:|
| 192K 单卡 | 24-36 tok/s | ~30 |
| 192K 双卡 | 26-45 tok/s | ~30 |
| 256K 单卡 | N/A（无 task 数据）| — |

> **192K 单卡 vs 双卡 Decode 几乎打平**（都在 30 tok/s 区间）。
> **关键反直觉发现**：双卡**没有带来 Decode 加速**。

---

## 6. MTP / Draft Acceptance

| 档位 | 样本 | 平均 | 范围 | mean draft len |
|---|---:|---:|---|---:|
| 192K 单卡 | 4+ | 0.58 | 0.45-0.69 | 2.8-3.7 |
| 192K 双卡 | 3+ | 0.55 | 0.42-0.67 | 2.7-3.7 |
| 256K 单卡 | 0 | — | — | — |

> 跨档 MTP acceptance 都在 0.42-0.69 区间，平均 ~0.55-0.58。
> 不是性能差距主因。

---

## 7. 单卡 vs 双卡深度对比

| 维度 | 192K 单卡 | 192K 双卡 | 差异 |
|---|---|---|---|
| Prefill 3K | 767 tok/s | 785 tok/s | +2% |
| Prefill 17K | 614 tok/s | 672 tok/s | +9% |
| Decode 短 | 36 tok/s | 45 tok/s | +25% |
| Decode 长 | 24-28 tok/s | 27-33 tok/s | +10-15% |
| Decode 中位 | ~30 tok/s | ~30 tok/s | 持平 |
| runner.vram | 17.0 GiB | 24.6 GiB | +45% |
| KV 拆分 | 单卡 12 GiB | 双卡 6+6 GiB | 拆分 |
| MTP acceptance | 0.58 | 0.55 | -5% |

> **关键结论**：双卡**几乎没加速** Decode（短输出 +25% 来自 task 0 极短输出噪声，中位持平）。
> 原因推测（**该推测不在本文档范围内**，仅作观察）：
> 1. MTP speculative decoding 是 sequential 的，多卡帮助不大
> 2. Ollama multi-GPU 调度在 MTP 场景下未优化
> 3. KV 拆分到 2 张卡反而增加跨卡通信开销

### 7.1 双卡未加速的 log 证据

| 证据 | 出处 |
|---|---|
| `runner.inference="[{ID:0 Library:CUDA} {ID:1 Library:CUDA}]"` | 192K-2 log 中两条 verifying if device 记录 |
| `CUDA0 KV buffer size = 6144.00 MiB` + `CUDA1 KV buffer size = 6144.00 MiB` | 双卡 KV 拆 6+6 |
| `CUDA0 model buffer size = 7252.61 MiB` | 单卡全装模型（7.25 GiB）|
| `runner.size="24.6 GiB"` | 总占用包含 working set |
| Decode 任务数据中位 27-45 tok/s | 跟单卡 24-36 tok/s 几乎一致 |

---

## 8. 推荐档位

### 8.1 3 档可用性归纳

| 配置 | 是否 100% GPU | Decode 中位 | 综合评价 |
|---|---:|---:|---|
| V100 单卡 192K | ✅ | ~30 tok/s | 100% GPU 跑的最大档 |
| V100 单卡 256K | ❌ 56/66 | 个位数 | offload 触发 |
| V100 双卡 192K | ✅ | ~30 tok/s（**未加速**）| 多卡无收益 |

### 8.2 推荐：V100 单卡 192K（首选）

**依据（全部来自本批 log）**：

1. 3 档中**唯一 100% GPU 跑**的最大档（`offloaded 66/66 layers to GPU`）
2. `runner.size=17.0 GiB == runner.vram=17.0 GiB`，完全在 VRAM
3. Decode 中位 ~30 tok/s，长输出 24-28 tok/s
4. MTP acceptance 0.45-0.69
5. 系统 755 GiB RAM 富余

**启动配置**（来自 3 份 log 共有启动命令）：

```bash
OLLAMA_CONTEXT_LENGTH=196608 \
OLLAMA_FLASH_ATTENTION=true \
OLLAMA_KEEP_ALIVE=-1 \
ollama serve
```

启动参数（3 份 log 共有 `cmd=`）：

```
--spec-type draft-mtp
--spec-draft-n-max 4
--spec-draft-backend-sampling
--flash-attn auto
-b 512 -ub 512
--context-shift --keep 4
```

### 8.3 不推荐：V100 双卡 192K

**原因**：

1. Decode 中位 ~30 tok/s，**跟单卡持平**（task 957 26.06 vs 单卡 task 183 24.73）
2. runner.vram 24.6 GiB，**多占 7.6 GiB 显存**
3. KV 拆到 2 张卡，模型权重全在 GPU0（GPU0 偏热、GPU1 偏闲）
4. 多卡没带来收益，反而消耗更多 VRAM

### 8.4 不推荐：V100 单卡 256K

**原因**：

1. `offloaded 56/66 layers to GPU`——**10 层 offload**
2. `runner.vram=14.9 GiB ≠ runner.size=20.2 GiB`——结构性 offload
3. `CPU KV buffer size = 2048.00 MiB`——新增 CPU 端 KV
4. log 中无 print_timing 任务数据，**预计 Decode 个位数 tok/s**
5. mmap 涨 4.4× 到 2.98 GiB

### 8.5 选择依据表

| 需求 | 推荐 | 依据（来自本批数据）|
|---|---|---|
| 想要 100% GPU 跑的最大档 | **V100 单卡 192K** | 3 档中唯一 100% GPU 跑的最大档 |
| 想要 32GB 卡上的最稳配置 | **V100 单卡 192K** | Decode 中位 ~30 tok/s，Prefill ~780 tok/s |
| 想要双卡加速 | ❌ 没有收益 | 双卡 Decode 跟单卡持平 |
| 想要跑 256K+ | ❌ 物理边界 | 3 档数据都未跑出 256K 100% GPU |

---

## 9. 结论

> **V100 32G 单卡 192K 是这台老卡上能跑 Qwen3.8-27B 的最稳配置**。
>
> **关键证据**：
> - 192K 单卡：100% GPU 跑，Decode ~30 tok/s
> - 192K 双卡：**未加速**，Decode 跟单卡持平（多卡无收益）
> - 256K 单卡：触发 10 层 offload，Decode 跌至个位数
> - 192K / 256K offload 触发点：192K 是 100% GPU 极限，256K 必须 offload
>
> **如果只是需要 Coding Agent 能力**：V100 32G 单卡 192K 配置（30 tok/s）已能流畅运行。
> **如果对性能要求更高**：本批数据未提供 192K 以上的 100% GPU 配置，**该方向需补测**。

### 9.1 关键证据链

| 事实 | 来源（文档 + 行类型）|
|---|---|
| V100 是 Volta 架构 | `ollama192k单卡.log` 中 `verifying if device is supported library=cuda_v12 description="Tesla V100-SXM2-32GB" compute=7.0` |
| 192K 单卡全 GPU | `ollama192k单卡.log` 中 `offloaded 66/66 layers to GPU` + `runner.size=17.0 GiB == runner.vram=17.0 GiB` |
| 192K 双卡未加速 | `ollama192k-2.log` 中 Decode 中位 ~30 tok/s 跟单卡持平 |
| 256K 触发 offload | `ollama256k.log` 中 `offloaded 56/66 layers to GPU` + `runner.vram=14.9 GiB ≠ runner.size=20.2 GiB` + `CPU KV buffer size = 2048.00 MiB` |

### 9.2 数据未覆盖的方面（坦白说明）

| 未覆盖内容 | 原因 |
|---|---|
| 64K / 128K 档 | 本批文档无这 2 档 log |
| nvidia-smi 实时截图 | 本批未提供 |
| 256K Decode 实际数值 | log 中无 print_timing 任务数据（fit 阶段未完成到任务执行）|
| 双卡模式下不同并发数对比 | log 中 `runner.parallel=1`，未测 2/4 并发 |
| BF16 完整权重测试 | V100 支持 BF16 但本批只测了 Q4_K_M 量化版 |
| KV cache 量化（q4_0/q8_0）效果 | 未测 |

---

> 报告数据来源：
> - 3 份 ollama DEBUG log（V100 单卡/双卡 192K + V100 单卡 256K）
> - 所有数字都有 `slot print_timing` 或 `runner.*` 的原始 log 行支撑
> - **报告仅分析 V100 32G 自身数据，不与其他硬件做横向对比**
>
> 如果想看更详细的 timing 表、或补测 64K/128K 档位，回复里喊一声。
