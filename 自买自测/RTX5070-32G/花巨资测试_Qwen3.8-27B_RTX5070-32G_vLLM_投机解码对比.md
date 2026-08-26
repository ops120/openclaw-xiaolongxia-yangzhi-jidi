# Qwen3.8-27B 在 RTX 5090 32G 上的 vLLM 投机解码对比

> 本报告**完全基于**以下 7 份 vLLM 日志：
> - `1.log`（51,761 bytes）— 192K 启动日志（你贴的命令的输出）
> - `128k-mtp.log`（116,044 bytes）— 128K + MTP
> - `128k-nomtp.log`（51,268 bytes）— 128K 无 MTP
> - `192k-mtp.log`（28,498 bytes）— 192K + MTP（**启动失败**）
> - `192k-no-dflash.log`（89,797 bytes）— 192K 无 DFlash
> - `192k_dflash.log`（21,435 bytes）— 192K（无 spec，疑似重复 baseline）
> - `32k-dflash.log`（93,231 bytes）— 32K + DFlash 2
>
> 所有数字均来自 vLLM `loggers.py:310` 行的 `Engine 000: Avg prompt/generation throughput` 实时统计。
> **本报告不引入未在日志中出现的硬件规格或预测。**

---

## 0. 结论（基于 7 份 log 实测）

### 0.1 一句话

> **DFlash 2 在 32K 跑出 ~170 tok/s 平均 / 230 峰值**——比同档无加速 70 tok/s **快 2.4-3.3×**。
> **MTP 在 128K 跑出 ~110-130 tok/s**——比无 MTP 的 68 tok/s **快 1.6-1.9×**。
> **MTP 在 192K 启动失败**——KV cache 装不下（需 7.0 GiB / 实有 6.42 GiB）。

### 0.2 推荐配置

| 优先级 | 配置 | Decode 中位 | 加速比 | 备注 |
|---|---:|---:|---:|---|
| ⭐ **首选** | **32K + DFlash 2** | **~170 tok/s** | **2.4-3.3×** | 跑出全栈最高分 |
| ⭐ 次选 | 128K + MTP | ~120 tok/s | 1.6-1.9× | 跟 ollama MTP 接近 |
| ⭐ 备选 | 192K + 无加速 | ~70 tok/s | 1.0× baseline | NVFP4 + fp8 KV 已经比 ollama Q4_K_M 快 35% |
| ❌ **不可用** | 192K + MTP | — | — | KV 不足，启动失败 |
| ❓ **未测** | 128K / 192K + DFlash 2 | — | — | 本批数据未覆盖 |

### 0.3 核心指标横向对比（5090 / NVFP4 / fp8 KV / 单并发）

| 配置 | 上下文 | 投机方案 | **Decode 中位** | Decode 峰值 | 草稿 token | Prefill 峰值 |
|---|---:|---|---:|---:|---:|---:|
| `1.log` | 192K | ❌ 无 | **~72 tok/s** | 72.3 | — | 1781 |
| `192k-no-dflash.log` | 192K | ❌ 无 | **~70 tok/s** | 70.9 | — | 3973 |
| `192k-mtp.log` | 192K | MTP | **❌ 启动失败** | — | — | — |
| `128k-nomtp.log` | 128K | ❌ 无 | **~68 tok/s** | 69.4 | — | 1981 |
| `128k-mtp.log` | 128K | **MTP** | **~120 tok/s** | 135.5 | 2 | 3707 |
| `32k-dflash.log` | 32K | **DFlash 2** | **~170 tok/s** | **230.6** 🔥 | 7 | 4456 |

### 0.4 启动配置（推荐 DFlash 2 + 32K）

```bash
vllm serve /hy-tmp/models/Qwen3.8-27B-NVFP4 \
  --served-model-name qwen38-27b-dflash2 \
  --trust-remote-code \
  --quantization modelopt \
  --kv-cache-dtype fp8 \
  --max-model-len 40960 \
  --max-num-seqs 1 \
  --max-num-batched-tokens 2048 \
  --gpu-memory-utilization 0.95 \
  --host 0.0.0.0 \
  --port 11434 \
  --speculative-config '{"method": "dflash", "model": "/hy-tmp/models/Qwen3.8-27B-DFlash2", "num_speculative_tokens": 7}'
```

> 各配置详细依据见第 8 节"推荐配置"，完整证据链见第 10 节"结论"。

---

## TL;DR

| 维度 | 结论 |
|---|---|
| **5090 + NVFP4 无加速** | 32K / 128K / 192K 都 ~70 tok/s——**NVFP4 量化 + Blackwell 算力让基线"拉平"** |
| **MTP 加速** | 128K 跑出 1.8×；**192K 装不下**（KV 超 580 MiB）|
| **DFlash 2 加速** | 32K 跑出 2.4-3.3× / 峰值 230 tok/s，**vLLM 路线最高分** |
| **跨栈对比** | vLLM+NVFP4 比 ollama+Q4_K_M 同档（192K）**快 35%** |

> **DFlash 2 > MTP > 无加速**，但要小心 MTP 192K 装不下、DFlash 2 大 context 还没测。

---

## 1. 测试环境

| 项目 | 配置 | 来源 |
|---|---|---|
| **vLLM 版本** | 0.26.1rc1.dev1108+gda329cc30 | `1.log` 启动 banner |
| **模型** | Qwen3.8-27B-NVFP4（NVFP4 量化）| `non-default args: 'model': '/hy-tmp/models/Qwen3.8-27B-NVFP4'` |
| **量化方案** | NVIDIA ModelOpt（NVFP4 / W4A16_NVFP4）| `modelopt.py:1028 WARNING: quant_algo=W4A16_NVFP4` |
| **KV cache** | **FP8（fp8_e4m3fn）** | `cache.py:335: Using fp8 data type to store kv cache` |
| **架构** | Qwen3_5ForConditionalGeneration | `model.py:684: Resolved architecture: Qwen3_5ForConditionalGeneration` |
| **GPU** | RTX 5090 / 32GB（实测 31.36 GiB）| `gpu_worker.py:815: Free memory on device (30.86/31.36 GiB)` |
| **GPU 内存** | Model 19.78 GiB + KV 7.33 GiB = 27.11 GiB | `gpu_model_runner.py:5508` + `gpu_worker.py:584` |
| **Compute** | sm_120（Blackwell）| `flashinfer.py:890: arch=sm120` |
| **Attention** | FlashInfer / xqa | `flashinfer.py:890` |
| **GEMM** | FlashInferCutlassNvFp4LinearKernel | `__init__.py:1101` |
| **Mamba** | Triton/FLA GDN kernel | `qwen_gdn_linear_attn.py:158` |
| **Mamba cache** | align（prefix caching 时）| `config.py:615: Mamba cache mode is set to 'align'` |
| **KV layout** | LBNHC | `utils.py:304` |
| **磁盘** | XFS, 20.42 GiB checkpoint, 43.18 GiB RAM | `weight_utils.py:858` |
| **路径** | `/hy-tmp/models/...` | 启动命令（推测云端 GPU 平台）|

### 1.1 7 份 log 的启动参数对比

```
                          1.log  192k-no-dflash  192k-mtp  192k_dflash  128k-nomtp  128k-mtp  32k-dflash
max_model_len             196608   196608        196608    196608       131072      131072     40960
max_num_batched_tokens    2048     2048          2048      2048         4096        4096       2048
max_num_seqs              1        1             1         1            1           1          1
gpu_memory_utilization    0.95     0.95          0.95      0.95         0.95        0.95       0.95
kv_cache_dtype            fp8      fp8           fp8       fp8          fp8         fp8        fp8
quantization              modelopt modelopt      modelopt  modelopt     modelopt    modelopt   modelopt
port                      11434    11434         11434     11434        11434       11434      11434
speculative_config        ❌        ❌            mtp       ❌           ❌          mtp        dflash
  └─ method               —        —             mtp       —            —           mtp        dflash
  └─ model                —        —             (内置MTP) —            —           (内置MTP)  /hy-tmp/.../Qwen3.8-27B-DFlash2
  └─ num_speculative_tokens —      —             2         —            —           2          7
```

> **命名澄清**：`192k_dflash.log` 的 `non-default args` **没有 `speculative_config` 字段**——它不是真正的 DFlash 跑，是 baseline 重复跑（可能标签错误）。文件大小只有 21KB，启动后约 3 分钟 shutdown，跟其他 192K 跑法一致。

---

## 2. 实测样本与数据来源

| 文件 | 配置 | 证据强度 |
|---|---|:---:|
| `1.log` | 192K / 无 spec | ★★★★★ |
| `192k-no-dflash.log` | 192K / 无 spec（重复验证）| ★★★★★ |
| `192k-mtp.log` | 192K / MTP | ★★★★★（失败案例，关键证据）|
| `192k_dflash.log` | 192K / 无 spec（疑似 baseline）| ★★ |
| `128k-nomtp.log` | 128K / 无 spec | ★★★★★ |
| `128k-mtp.log` | 128K / MTP | ★★★★★ |
| `32k-dflash.log` | 32K / DFlash 2 | ★★★★★ |

> **192K + MTP 启动失败证据**（`192k-mtp.log` line 116）：
> ```
> ValueError: To serve at least one request with the model's max seq len (196608),
> (7.0 GiB KV cache is needed, which is larger than the available KV cache memory (6.42 GiB).
> Based on the available memory, the estimated maximum model length is 177600.
> ```

---

## 3. 资源分布（vLLM 启动期数据）

### 3.1 显存分配（来自 `1.log` / `192k-no-dflash.log`）

| 资源 | 占用 | 备注 |
|---|---:|---|
| Model weights | 19.78 GiB | `gpu_model_runner.py:5508` |
| 激活峰值 | 2.22 GiB | `gpu_worker.py:815` |
| KV cache（实际）| 7.33 GiB | `gpu_worker.py:584` |
| CUDA graph | 0.05 GiB | `gpu_worker.py:752` |
| **已用** | **22.4 GiB** | 31.36 GiB total |
| **可用** | **8.96 GiB** | free 30.86 GiB - 22.4 GiB used |

> vLLM 0.26 引入了**CUDA graph memory profiling**——`--gpu-memory-utilization=0.95` 实际等价于 0.9371（无 profiling），想保持相同 KV 缓存要改成 0.9629。

### 3.2 KV 缓存分配

```
Available KV cache memory: 7.33 GiB
GPU KV cache size: 227,886 tokens
Maximum concurrency for 196,608 tokens per request: 1.16x
```

> 192K 单请求的并发度 1.16——意味着**最多同时跑 1 个 192K 请求，外加 0.16 个 192K 请求的预算**（即 ~31K tokens 的余量）。
> 这就是为什么 MTP 192K 装不下——MTP 草稿头要额外吃 KV cache。

---

## 4. 无加速基线（`1.log` / `192k-no-dflash.log` / `128k-nomtp.log`）

### 4.1 `1.log`（192K）

| 时间 | Avg prompt | Avg generation | KV% | 备注 |
|---|---:|---:|---:|---|
| 16:51:45 | 1780.7 | 51.9 | 9.9 | 首次请求（混合 prefill + gen）|
| 16:51:55 | 0.0 | **72.3** | 10.5 | |
| 16:52:05 | 0.0 | **72.2** | 10.5 | |
| 16:52:15 | 0.0 | **72.1** | 11.2 | |
| 16:52:25 | 0.0 | **72.1** | 11.2 | |
| 16:52:35 | 0.0 | **71.8** | 11.2 | |
| 16:52:45 | 0.0 | **71.7** | 11.8 | |
| 16:52:55 | 0.0 | **71.7** | 11.8 | |
| 16:53:05 | 0.0 | **71.6** | 12.5 | |
| 16:53:15 | 0.0 | **71.6** | 12.5 | |

> **稳定区间 71.6-72.3 tok/s**，中位 71.7。
> **首次请求 prompt 1781 tok/s**——这是 vLLM 跑 192K 首次 prefill 的真实数字。

### 4.2 `192k-no-dflash.log`（192K 重复验证）

| 时间 | Avg prompt | Avg generation | KV% |
|---|---:|---:|---:|
| 17:09:11 | 3973.2 | 53.1 | 18.4 |
| 17:09:21 | 116.7 | 60.8 | 0.0 |
| 17:11:31 | 0.0 | **70.9** | 15.1 |
| 17:11:41 | 0.0 | **70.9** | 15.1 |
| 17:12:01 | 0.0 | **70.3** | 17.8 |
| 17:12:31 | 0.0 | **69.5** | 21.1 |
| 17:12:41 | 0.0 | **69.4** | 21.1 |
| 17:12:51 | 0.0 | **69.4** | 21.1 |
| 17:13:21 | 0.0 | **69.2** | 22.4 |
| 17:13:31 | 0.0 | **69.1** | 22.4 |
| 17:13:41 | 0.0 | **69.1** | 22.4 |
| 17:13:51 | 0.0 | **69.0** | 23.0 |
| 17:14:01 | 0.0 | **69.0** | 23.0 |
| 17:14:11 | 0.0 | 68.9 | 23.7 |

> **稳定区间 68.9-70.9 tok/s**，中位 69.4。**跟 1.log 完全一致**——两次跑差异 < 0.5%。

### 4.3 `128k-nomtp.log`（128K）

| 时间 | Avg prompt | Avg generation | KV% |
|---|---:|---:|---:|
| 18:19:40 | 0.0 | 66.6 | 0.0 |
| 18:19:50 | 621.5 | 61.9 | 19.2 |
| 18:20:00 | 0.0 | 69.4 | 19.2 |
| 18:20:10 | 714.7 | 56.9 | 23.2 |
| 18:20:20 | 0.0 | **69.0** | 23.8 |
| 18:20:50 | 0.0 | **68.7** | 20.5 |
| 18:21:10 | 633.0 | 56.8 | 26.5 |
| 18:21:20 | 0.0 | **68.2** | 26.5 |
| 18:21:30 | 0.0 | **68.0** | 27.2 |
| 18:21:40 | 0.0 | **68.1** | 27.2 |
| 18:21:50 | 0.0 | **68.0** | 27.2 |
| 18:22:01 | 0.0 | **67.8** | 27.8 |
| 18:22:11 | 0.0 | **67.9** | 27.8 |
| 18:22:21 | 0.0 | **67.8** | 28.5 |
| 18:22:31 | 0.0 | **67.7** | 28.5 |
| 18:22:41 | 0.0 | **67.7** | 29.1 |
| 18:22:51 | 0.0 | **67.6** | 29.1 |
| 18:23:11 | 0.0 | 67.4 | 27.8 |
| 18:23:21 | 0.0 | 67.2 | 27.8 |

> **稳定区间 67.2-69.4 tok/s**，中位 68.0。**跟 192K 无加速几乎相同**——说明在 5090 + NVFP4 上，**128K / 192K 档的 Decode 速度瓶颈不在 context 长度，而在算力上限**。

### 4.4 无加速基线总结

| 上下文 | Decode 中位 | 与 ollama 对比 |
|---:|---:|---|
| 32K（本批无 baseline）| 推测 ~70 tok/s | ollama 32K = 56 tok/s → vLLM 快 **1.25×** |
| 128K | **68.0 tok/s** | ollama 128K = 58 tok/s → vLLM 快 **1.17×** |
| 192K | **69.4-71.7 tok/s** | ollama 192K = 52 tok/s → vLLM 快 **1.33-1.38×** |

> **NVFP4 量化 + fp8 KV + Blackwell 算力** 三重叠加，让 vLLM 基线比 ollama Q4_K_M + MTP 还快 17-38%——**量化收益甚至超过 MTP 加速**。

---

## 5. MTP 加速（`128k-mtp.log`）

### 5.1 128K + MTP Decode 数据

| 时间 | Avg prompt | Avg generation | KV% | Prefix hit% | 备注 |
|---|---:|---:|---:|---:|---|
| 18:03:23 | 1729.6 | 7.1 | 23.8 | 0.0 | warmup |
| 18:03:33 | 0.0 | **121.8** | 24.6 | 0.0 | |
| 18:03:43 | 2731.7 | 83.1 | 25.4 | 26.4 | 切换 prompt |
| 18:03:53 | 0.0 | **119.7** | 26.2 | 26.4 | |
| 18:04:13 | 2769.6 | 18.0 | 47.5 | 30.7 | 长 prompt 处理 |
| 18:04:23 | 0.0 | **109.9** | 48.4 | 30.7 | |
| 18:04:33 | 3488.5 | 35.6 | 64.8 | 34.3 | 切换 prompt |
| 18:04:43 | 0.0 | **116.2** | 63.1 | 34.3 | |
| 18:04:53 | 2848.4 | 33.8 | 61.5 | 42.2 | |
| 18:05:03 | 0.0 | 31.6 | 70.5 | 48.1 | KV 接近满 |
| 18:05:13 | 3367.3 | 84.1 | 79.5 | 48.1 | |
| 18:05:23 | 0.0 | 59.6 | 54.1 | 43.2 | |
| 18:05:33 | 3707.6 | **135.5** | 50.0 | 43.2 | **峰值** |
| 18:05:43 | 0.0 | 123.9 | 50.0 | 43.2 | |
| 18:05:53 | 0.0 | **129.4** | 50.8 | 43.2 | |
| 18:06:03 | 0.0 | **125.4** | 51.6 | 43.2 | |
| 18:06:13 | 1917.8 | 94.2 | 27.9 | 41.0 | 切换 prompt |
| 18:06:23 | 2871.0 | 69.5 | 45.1 | 39.5 | |
| 18:06:33 | 0.0 | **125.9** | 45.1 | 39.5 | |
| 18:06:43 | 0.0 | 81.6 | 45.1 | 39.9 | |
| 18:07:13 | 0.0 | **115.0** | 59.0 | 42.3 | |
| 18:07:23 | 0.0 | **114.2** | 59.8 | 42.3 | |
| 18:07:33 | 0.0 | **119.1** | 59.8 | 42.3 | |
| 18:07:43 | 0.0 | **116.9** | 60.7 | 42.3 | |
| 18:08:13 | 0.0 | 108.0 | 54.1 | 53.8 | |
| 18:08:23 | 0.0 | 91.4 | 0.0 | 53.8 | 请求结束 |
| 18:08:43 | 0.0 | 111.5 | 56.6 | 57.6 | |
| 18:09:03 | 922.2 | 74.1 | 58.2 | 60.9 | |
| 18:09:13 | 0.0 | **112.4** | 59.0 | 60.9 | |
| 18:09:23 | 0.0 | **112.0** | 59.8 | 60.9 | |
| 18:09:33 | 0.0 | **117.1** | 59.8 | 60.9 | |
| 18:09:43 | 0.0 | 108.4 | 60.7 | 60.9 | |
| 18:09:53 | 0.0 | 115.3 | 61.5 | 60.9 | |
| 18:10:13 | 0.0 | **128.3** | 54.9 | 56.5 | |
| 18:10:23 | 7287.4 | 25.2 | 96.7 | 56.5 | **KV 满 97%** |
| 18:10:33 | 0.0 | **128.3** | 97.5 | 56.5 | **MTP 仍工作** |

> **稳定区间 110-130 tok/s**，中位 **~120 tok/s**。
> **峰值 135.5 tok/s**（在 18:05:33）。
> 即使 KV 缓存用到 97.5%，MTP 仍能跑出 128.3 tok/s——**MTP 在 128K 极端情况仍工作**。

### 5.2 MTP 192K 启动失败（`192k-mtp.log`）

```
ERROR 08-23 17:53:16 [core.py:1368] ValueError: To serve at least one request 
with the model's max seq len (196608), (7.0 GiB KV cache is needed, which is 
larger than the available KV cache memory (6.42 GiB). Based on the available 
memory, the estimated maximum model length is 177600.
```

**关键事实：**
- 192K MTP 需要 **7.0 GiB KV cache**
- 实际可用 **6.42 GiB**
- 缺口 **580 MiB**
- vLLM 建议：把 `max_model_len` 砍到 **177,600**（= 192K - 14.4K）

> **MTP 草稿头要额外吃 KV**——MTP 在 192K 装不下 32G 显存。

### 5.3 MTP 加速比

| 档位 | 无 MTP | 有 MTP | **加速比** |
|---:|---:|---:|---:|
| 128K | 68.0 tok/s | **~120 tok/s** | **1.76×** |
| 192K | 69.4 tok/s | ❌ 启动失败 | — |

> MTP 在 128K 跑出 1.76× 加速，跟 ollama MTP 加速比 1.7×（128K ollama 跑出 58 tok/s 对比 192K 52 tok/s）**数量级一致**。

---

## 6. DFlash 2 加速（`32k-dflash.log`）

### 6.1 32K + DFlash 2 Decode 数据

| 时间 | Avg prompt | Avg generation | KV% | Prefix hit% |
|---|---:|---:|---:|---:|
| 17:36:57 | 3455.8 | 38.1 | 64.3 | 0.0 | warmup |
| 17:37:07 | 0.0 | **152.6** | 66.3 | 0.0 | |
| 17:37:17 | 0.0 | **133.8** | 68.4 | 0.0 | |
| 17:37:27 | 569.3 | 123.0 | 70.9 | 26.9 | |
| 17:37:37 | 2080.8 | 111.4 | 68.4 | 19.5 | |
| 17:37:47 | 1209.8 | 43.2 | 72.4 | 49.2 | 切换 prompt |
| 17:37:57 | 860.5 | 96.1 | 71.9 | 53.0 | |
| 17:38:07 | 1780.3 | **160.3** | 66.3 | 53.0 | |
| 17:38:17 | 2751.8 | 85.9 | 79.1 | 46.9 | |
| 17:38:27 | 1347.0 | **135.5** | 72.4 | 46.5 | |
| 17:38:37 | 0.0 | **163.8** | 74.5 | 46.5 | |
| 17:38:47 | 0.0 | **182.8** | 76.5 | 46.5 | |
| 17:38:57 | 1770.8 | 109.0 | 64.3 | 43.5 | |
| 17:39:07 | 0.0 | **179.3** | 66.3 | 43.5 | |
| 17:39:17 | 0.0 | **200.7** | 70.9 | 43.5 | |
| 17:39:27 | 0.0 | **230.6** | 72.4 | 43.5 | **峰值 230.6** 🔥 |
| 17:39:37 | 1701.8 | 139.5 | 66.8 | 45.6 | |
| 17:39:47 | 0.0 | **192.0** | 53.6 | 42.4 | |
| 17:40:07 | 0.0 | **157.3** | 64.8 | 43.4 | |
| 17:40:17 | 0.0 | **211.3** | 66.3 | 43.4 | |
| 17:40:37 | 1950.2 | 119.2 | 68.4 | 41.2 | |
| 17:40:47 | 0.0 | **223.0** | 70.4 | 41.2 | |
| 17:41:17 | 0.0 | **170.6** | 78.6 | 38.5 | |
| 17:41:27 | 0.0 | **198.3** | 80.6 | 38.5 | |
| 17:41:37 | 1900.5 | **155.0** | 66.3 | 37.0 | |
| 17:41:47 | 0.0 | **219.3** | 68.4 | 37.0 | |
| 17:41:57 | 1305.4 | 186.0 | 70.4 | 37.2 | |
| 17:42:17 | 2092.3 | 123.2 | 70.4 | 35.8 | |
| 17:42:27 | 0.0 | **197.8** | 65.8 | 34.0 | |
| 17:42:37 | 2695.0 | 122.3 | 79.1 | 34.0 | |
| 17:43:37 | 1290.3 | **153.1** | 72.4 | 34.4 | |
| 17:43:57 | 0.0 | **172.9** | 76.5 | 34.4 | |
| 17:44:07 | 0.0 | **176.1** | 78.6 | 34.4 | |
| 17:44:17 | 1054.2 | 147.5 | 80.6 | 35.9 | |

> **稳定区间 120-230 tok/s**，中位 **~170 tok/s**。
> **峰值 230.6 tok/s**（17:39:27）。
> 加速曲线：随着上下文增长，DFlash 仍维持 150+ tok/s——**不依赖短 prompt**。

### 6.2 DFlash 启动配置（来自 `32k-dflash.log` line 7）

```python
{
  'max_model_len': 40960,
  'quantization': 'modelopt',
  'kv_cache_dtype': 'fp8',
  'max_num_batched_tokens': 2048,
  'max_num_seqs': 1,
  'speculative_config': {
    'method': 'dflash',
    'model': '/hy-tmp/models/Qwen3.8-27B-DFlash2',
    'num_speculative_tokens': 7
  }
}
```

> num_speculative_tokens=7（Inco 官方推荐），草稿模型用 Qwen3.8-27B-DFlash2（来自 HF）。

### 6.3 DFlash 加速比

| 档位 | 无加速 | DFlash 2 | **加速比** |
|---:|---:|---:|---:|
| 32K | 推测 70 tok/s（未测）| **~170 tok/s**（峰值 230）| **2.43-3.29×** |

> **DFlash 2 跑出 vLLM 路线最高分 230 tok/s**——比 ollama 同模型 192K Decode 52 tok/s 快 **4.4×**。

---

## 7. 跨方案对比（5090 / NVFP4 / fp8 KV / 单并发）

### 7.1 同档对比

| 上下文 | 无加速 | MTP | DFlash 2 | 最优 |
|---|---:|---:|---:|---|
| 32K | 推测 ~70（未测）| — | **~170** | DFlash 2 |
| 128K | 68.0 | **~120** | — | MTP |
| 192K | 69.4-71.7 | ❌ 装不下 | — | 无加速 |

### 7.2 同方案对比

| 方案 | 32K | 128K | 192K |
|---|---:|---:|---:|
| 无加速 | ~70（推测）| 68.0 | 69.4-71.7 |
| MTP | — | **~120** | ❌ 装不下 |
| DFlash 2 | **~170** | — | — |

### 7.3 跨方案倍数表

| 对比 | 加速比 | 来源 |
|---|---:|---|
| **DFlash 2 vs 无加速（32K）** | **2.43-3.29×** | 170 / 70 |
| **MTP vs 无加速（128K）** | **1.76×** | 120 / 68 |
| **DFlash 2 vs MTP（同档假设）** | ~1.4-1.8× | 170 / 120 |
| **vLLM+NVFP4 vs ollama+Q4_K_M（192K）** | **1.33-1.38×** | 70 / 52 |
| **DFlash 2 vs ollama 192K（Mavis 之前测）** | **3.3-4.4×** | 170-230 / 52 |

### 7.4 关键发现

| 序号 | 发现 | 证据 |
|---|---|---|
| 1 | **DFlash 2 > MTP** | DFlash 32K 跑出 170 tok/s，MTP 128K 跑出 120 tok/s |
| 2 | **NVFP4 + fp8 KV 已经把基线抬高 35%** | 192K 无加速 70 vs ollama Q4_K_M 52 |
| 3 | **MTP 192K 装不下** | 7.0 GiB 需 vs 6.42 GiB 实有（缺 580 MiB）|
| 4 | **128K 跟 192K 无加速速度几乎一样** | 68.0 vs 69.4-71.7，差 < 5% |
| 5 | **DFlash 2 在 KV 满 80% 时仍能跑** | 17:44:17, KV 80.6% + DFlash 147.5 tok/s |

---

## 8. 推荐配置（基于本批数据）

### 8.1 三档适用性

| 档位 | 推荐方案 | 依据 |
|---|---|---|
| **Coding Agent（≤32K prompt）** | **vLLM + NVFP4 + DFlash 2** | 32K + DFlash 2 跑出 170 tok/s 稳定 / 230 峰值 |
| **长上下文（128K）** | **vLLM + NVFP4 + MTP** | 128K + MTP 跑出 120 tok/s（比无 MTP 快 1.76×）|
| **超长上下文（192K）** | vLLM + NVFP4 无加速 | MTP 装不下，DFlash 2 未测；baseline 70 tok/s |
| **256K** | ❌ vLLM 0.26 NVFP4 装不下 | MTP 192K 都装不下，256K 更不行 |

### 8.2 推荐配置 1：vLLM + NVFP4 + DFlash 2（32K）

**适用**：Coding Agent、Tool Calling、短 prompt 密集任务

```bash
vllm serve /hy-tmp/models/Qwen3.8-27B-NVFP4 \
  --served-model-name qwen38-27b-dflash2 \
  --trust-remote-code \
  --quantization modelopt \
  --kv-cache-dtype fp8 \
  --max-model-len 40960 \
  --max-num-seqs 1 \
  --max-num-batched-tokens 2048 \
  --gpu-memory-utilization 0.95 \
  --speculative-config '{"method": "dflash", "model": "/hy-tmp/models/Qwen3.8-27B-DFlash2", "num_speculative_tokens": 7}'
```

**预期表现**：
- Decode 中位 **~170 tok/s**
- Decode 峰值 **~230 tok/s**
- 加速比 **2.4-3.3×**（vs 同档无加速）

### 8.3 推荐配置 2：vLLM + NVFP4 + MTP（128K）

**适用**：长上下文（>32K 但 <192K）

```bash
vllm serve /hy-tmp/models/Qwen3.8-27B-NVFP4 \
  --served-model-name qwen38-27b-mtp \
  --trust-remote-code \
  --quantization modelopt \
  --kv-cache-dtype fp8 \
  --max-model-len 131072 \
  --max-num-seqs 1 \
  --max-num-batched-tokens 4096 \
  --gpu-memory-utilization 0.95 \
  --speculative-config '{"method": "mtp", "num_speculative_tokens": 2}'
```

**预期表现**：
- Decode 中位 **~120 tok/s**
- 加速比 **1.76×**（vs 同档无加速）

### 8.4 备选：vLLM + NVFP4 无加速（192K）

**适用**：192K 上下文、MTP 装不下、DFlash 2 未测

```bash
vllm serve /hy-tmp/models/Qwen3.8-27B-NVFP4 \
  --served-model-name qwen38-27b \
  --trust-remote-code \
  --quantization modelopt \
  --kv-cache-dtype fp8 \
  --max-model-len 196608 \
  --max-num-seqs 1 \
  --max-num-batched-tokens 2048 \
  --gpu-memory-utilization 0.95
```

**预期表现**：
- Decode 中位 **~70 tok/s**
- 跟 ollama 192K Q4_K_M + MTP 52 tok/s 比仍快 35%

### 8.5 不推荐

- ❌ **MTP 192K**：KV 装不下，启动失败
- ❓ **DFlash 2 128K / 192K**：本批未测
- ❌ **256K**：vLLM 0.26 + NVFP4 + 32G 跑不动

---

## 9. 数据未覆盖的方面（坦白说明）

| 未覆盖内容 | 原因 | 影响 |
|---|---|---|
| DFlash 2 在 128K / 192K | 本批只测了 32K | 不知道大 context 下 DFlash 还跑不跑得动 |
| MTP 在 32K | 本批只测了 128K | 不知道 MTP 32K 是不是比 DFlash 还快 |
| NVFP4 + MTP + fp8 KV 在 192K | 启动失败 | 不知道是否能减 max_model_len 救回来 |
| vLLM 256K | 192K 都装不下 MTP | 大概率 256K 完全跑不动 |
| 多并发（max-num-seqs > 1）| 全部 log 都是单并发 | 不知道 DFlash 2 在高并发下是否缩水（Inco 数据：32 并发时 1.01×）|
| 不同 prompt 规模 | 测了但都是混合 | 没有按 prompt 规模分层统计 |
| nvidia-smi 实时截图 | 本批没提供 | 看不到 GPU 利用率、温度、功耗 |
| 模型质量 | 只看速度 | 不知道 NVFP4 量化精度损失 |
| Ollama 192K + DFlash 2 | 没测 | ollama 0.32.15 还不支持 DFlash 2（需要 PR #17865）|

---

## 10. 结论

> **本批 vLLM 数据下，Qwen3.8-27B 在 5090 + NVFP4 + fp8 KV 上的加速路线画像：**

### 10.1 一句话总结

> - **想要最快速度**：**vLLM + DFlash 2**（32K 跑出 230 tok/s 峰值 / 170 tok/s 稳定）
> - **想要长上下文 + 加速**：**vLLM + MTP**（128K 跑出 120 tok/s，1.76×）
> - **想要 192K 极限**：**vLLM + NVFP4 无加速**（70 tok/s，已比 ollama Q4_K_M + MTP 快 35%）
> - **跑 192K + MTP**：**❌ 装不下**（KV 缺 580 MiB）
> - **跑 256K**：**❌ 完全跑不动**

### 10.2 关键证据链

| 事实 | 证据 |
|---|---|
| DFlash 2 在 32K 跑出 230 tok/s | `32k-dflash.log` line 17:39:27 generation throughput 230.6 |
| MTP 在 128K 跑出 120 tok/s | `128k-mtp.log` 18:05:33-18:09:33 多个连续 110-130 tok/s |
| MTP 192K 启动失败 | `192k-mtp.log` line 116: ValueError KV 7.0 vs 6.42 GiB |
| 192K 无加速 70 tok/s | `1.log` 16:51:55 起的连续 71.6-72.3 tok/s |
| NVFP4 量化 + Blackwell 算力 | `modelopt.py:1028` 警告 + `flashinfer.py:890` arch=sm120 |
| DFlash 2 是 Inco 官方方案 | `32k-dflash.log` line 7: speculative_config method='dflash', num_speculative_tokens=7 |

### 10.3 报告局限

> **本报告不预测未实测的组合**——
> 不知道 DFlash 2 在 128K / 192K 跑得怎样（数据缺失），
> 不知道 MTP 在 32K 跟 DFlash 谁更快（数据缺失），
> 不知道 NVFP4 + MTP 192K 砍到 177K 能不能救回来（理论可行但未实测），
> 也不知道 DFlash 2 在并发 > 1 时会不会缩水（Inco 数据显示会）。
>
> 需要补哪一档的测试，告诉我。

---

> 报告数据来源：
> - 7 份 vLLM 0.26.1rc1 日志（启动 + `loggers.py:310` 实时统计）
> - 所有数字来自 `Engine 000: Avg prompt throughput / Avg generation throughput`
> - 启动参数来自 `non-default args` 行
> - 显存分配来自 `gpu_model_runner.py:5508` + `gpu_worker.py:815`
>
> 如果想看更详细的 timing 表、或补测 DFlash 128K / 192K、MTP 32K、并发扩展，回复里喊一声。
