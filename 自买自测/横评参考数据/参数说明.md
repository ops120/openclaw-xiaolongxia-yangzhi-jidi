# Qwen3.8-27B + Ollama 0.32.15 参数速查表

> 本表汇总两份硬件报告（`..._RTX3090-24G_...md` / `..._RTX5070-32G_...md`）中所有关键参数。
> 数据来源：4 份 ollama DEBUG log + 4 张 nvidia-smi 截图 + `新建文本文档.txt`。
> 所有数字均能溯源到原始 log / 截图。

---

## 1. 模型参数（4 份 log 共有）

| 参数 | 值 | 来源 |
|---|---|---|
| 模型名称 | Qwen3.8 27B 0814 | `general.name` |
| 架构 | qwen35 | `general.architecture` |
| 参数量 | 27.32 B | `print_info: model params` |
| 训练上下文长度 | 262144（256K）| `qwen35.context_length` |
| Transformer 层数 | 64 | `print_info: n_layer` |
| 总层数（含 MTP）| 65 | `print_info: n_layer_all` |
| Attention 头数 | 24 | `print_info: n_head` |
| KV 头数 | 4（GQA）| `print_info: n_head_kv` |
| Embedding 长度 | 5120 | `qwen35.embedding_length` |
| FFN 长度 | 17408 | `qwen35.feed_forward_length` |
| 头维度 | 256 | `qwen35.attention.key_length` |
| RoPE 基础 | 10000000 | `qwen35.rope.freq_base` |
| RMSNorm epsilon | 1.0e-06 | `qwen35.attention.layer_norm_rms_epsilon` |
| SSM 状态大小 | 128 | `qwen35.ssm.state_size` |
| SSM 内核 | 4 | `qwen35.ssm.conv_kernel` |
| Full attention interval | 4（每 4 层一次）| `qwen35.full_attention_interval` |
| EOS token ID | 248046 | `tokenizer.ggml.eos_token_id` |
| PAD token ID | 248044 | `tokenizer.ggml.padding_token_id` |
| BOS token ID | 248044 | `tokenizer.ggml.bos_token_id` |
| add_bos_token | false | `tokenizer.ggml.add_bos_token` |
| 词表大小 | 248320 | `tokenizer.ggml.tokens` |

> 架构是 **hybrid/recurrent memory（SSM + 局部 attention）**，不是纯 transformer。PR #13194 提到的 SWA cache 失效问题跟这个架构相关。

---

## 2. 量化参数（4 份 log 共有）

| 参数 | 值 | 来源 |
|---|---|---|
| GGUF 版本 | V3（latest）| `version GGUF V3 (latest)` |
| 量化版本 | 2 | `general.quantization_version` |
| 文件类型 | 15（Q4_K_M）| `general.file_type` |
| f32 tensor 数 | 360 | `llama_model_loader: - type  f32` |
| q4_K tensor 数 | 439 | `llama_model_loader: - type q4_K` |
| q6_K tensor 数 | 67 | `llama_model_loader: - type q6_K` |
| 加载层数（64K/128K/192K）| 66/66 GPU | `load_tensors: offloaded 66/66 layers to GPU` |
| 加载层数（128K 触发 offload）| 54/66 GPU | `load_tensors: offloaded 54/66 layers to GPU` |
| ollama tag 默认 | `qwen3.8:27b`（hash `22130167c4c2`）| ollama 官方 + `ollama ps` |
| ollama tag 纯 Q4_K_M | `qwen3.8:27b-q4_K_M`（hash `25b843619e94`）| ollama 官方 |
| 多模态支持 | Qwen-VL mmproj（1161 MiB）| `load_model: [mtmd] estimated worst-case memory usage of mmproj is 1161.02 MiB` |

> 默认 `qwen3.8:27b` 跟 `qwen3.8:27b-mtp-q4_K_M` 共享 hash `22130167c4c2`，**默认就是 MTP + Q4_K_M**。

---

## 3. 启动参数（4 份 log 共有 `cmd=`）

| 参数 | 值 | 作用 |
|---|---|---|
| `OLLAMA_CONTEXT_LENGTH` | 32768 / 65536 / 131072 / 196608 / 262144 | num_ctx 限制 |
| `OLLAMA_FLASH_ATTENTION` | true（5070 显式 true，3090 隐式 auto）| Flash Attention |
| `OLLAMA_KEEP_ALIVE` | -1（5070） / 5m0s（3090 默认）| 模型驻留时间 |
| `OLLAMA_DEBUG` | 1 / DEBUG | 输出 DEBUG 日志 |
| `OLLAMA_MAX_QUEUE` | 512 | 请求队列长度 |
| `OLLAMA_NUM_PARALLEL` | 1 | 并发数 |
| `OLLAMA_MAX_LOADED_MODELS` | 0（无限制）| 同时加载模型数 |
| `OLLAMA_LOAD_TIMEOUT` | 5m0s | 加载超时 |
| `OLLAMA_SCHED_SPREAD` | false | 不分散到多卡 |
| `OLLAMA_VULKAN` | true | 启用 Vulkan 后端 |
| `OLLAMA_HOST` | http://127.0.0.1:11434 | 监听地址 |

> 4 份 log 启动命令完全一致（除了 num_ctx）。

### 3.1 llama-server 启动参数（`--` 开头）

| 参数 | 值 | 作用 |
|---|---|---|
| `--model` | sha256-f5f1dd8920d417aac2718b0bda3403da274301efdd6760b4f0f4b864ff2ad57d | 模型 blob |
| `--port` | 动态 | 监听端口 |
| `--host` | 127.0.0.1 | 监听地址 |
| `--no-webui` | true | 禁用 web UI |
| `--offline` | true | 离线模式 |
| `-c` | 与 OLLAMA_CONTEXT_LENGTH 一致 | num_ctx |
| `-np` | 1 | 并发数 |
| `--log-verbosity` | 4 | 日志详细度 |
| `--no-log-prefix` | true | 无前缀 |
| `--no-log-timestamps` | true | 无时间戳 |
| `--no-jinja` | true | 不用 jinja 模板 |
| `--chat-template` | chatml | chat 模板 |
| `--mmproj` | sha256-ac3714bfdddeca31351f2752bf1a63f266f4df87c0b68c895e44945ca704448e | 多模态 |
| `--spec-type` | **draft-mtp** | MTP speculative decoding |
| `--spec-draft-n-max` | **4** | draft 长度 |
| `--spec-draft-backend-sampling` | true | draft 用 backend 采样 |
| `--flash-attn` | auto | Flash Attention 自动判断 |
| `-b` | 512 | 物理 batch |
| `-ub` | 512 | 逻辑 batch |
| `--context-shift` | true | 启用 context shifting |
| `--keep` | 4 | 保留 token 数 |

---

## 4. 推理参数（context 阶段）

| 参数 | 64K | 128K | 192K | 256K |
|---|---:|---:|---:|---:|
| `n_ctx` | 65536 | 131072 | 196608 | 262144 |
| `n_seq_max` | 1 | 1 | 1 | 1 |
| `n_batch` | 512 | 512 | 512 | 512 |
| `n_ubatch` | 512 | 512 | 512 | 512 |
| `flash_attn` | auto | auto | auto | auto |
| `kv_unified` | false | false | false | false |
| `freq_base` | 10000000.0 | 10000000.0 | 10000000.0 | 10000000.0 |
| `freq_scale` | 1 | 1 | 1 | 1 |
| `n_rs_seq` | 4（主）/ 0（MTP draft）| 4 / 0 | 4 / 0 | 4 / 0 |
| `n_outputs_max` | 5（主）/ 1（MTP draft）| 5 / 1 | 5 / 1 | 5 / 1 |
| `n_ctx_train` | 262144 | 262144 | 262144 | 262144 |
| KV shifting | 128K 起不支持 | 不支持 | 不支持 | 不支持 |

> KV cache shifting 在 128K+ 触发："`KV cache shifting is not supported for this context, disabling KV cache shifting`"

---

## 5. KV cache 与 Recurrent 内存

| 参数 | 64K | 128K | 192K | 256K |
|---|---:|---:|---:|---:|
| KV total size | 4096 MiB | 8192 MiB | 12288 MiB | 16384 MiB |
| KV on GPU | 4096 MiB | 6656 MiB | 12288 MiB | **13312 MiB** |
| KV on CPU | 0 | **1536 MiB** | 0 | **3072 MiB** |
| K (f16) | 2048 MiB | 4096 MiB | 6144 MiB | 8192 MiB |
| V (f16) | 2048 MiB | 4096 MiB | 6144 MiB | 8192 MiB |
| KV cells | 65536 | 131072 | 196608 | 262144 |
| KV layers | 16 | 16 | 16 | 16 |
| n_embd_head_k | 256 | 256 | 256 | 256 |
| Recurrent state total | 748.12 MiB | 748.12 MiB | 748.12 MiB | 748.12 MiB |
| Recurrent on GPU | 748.12 MiB | 607.85 MiB | 748.12 MiB | 607.85 MiB |
| Recurrent on CPU | 0 | 140.27 MiB | 0 | 140.27 MiB |
| R (f32) | 28.12 MiB | 28.12 MiB | 28.12 MiB | 28.12 MiB |
| S (f32) | 720.00 MiB | 720.00 MiB | 720.00 MiB | 720.00 MiB |
| MTP context | 388 MiB | 388 MiB | 388 MiB | 388 MiB |

---

## 6. 硬件参数（来自 nvidia-smi 截图，5070 32G）

| 参数 | 64K | 128K | 192K | 256K |
|---|---|---|---|---|
| 截图时间 | 14:30:15 | 14:12:44 | 14:20:53 | 13:59:50 |
| 状态 | idle | active | active | idle |
| GPU | RTX 5090 | RTX 5090 | RTX 5090 | RTX 5090 |
| Driver | 570.195.03 | 570.195.03 | 570.195.03 | 570.195.03 |
| CUDA | 12.8 | 12.8 | 12.8 | 12.8 |
| VRAM total | 32607 MiB | 32607 MiB | 32607 MiB | 32607 MiB |
| **进程占 VRAM** | **22486 MiB** | **27004 MiB** | **31484 MiB** | **31052 MiB** |
| **32G 占比** | **69%** | **83%** | **97%** | **95%** |
| GPU-Util | 0% | 71% | 63% | 0% |
| 功耗 | 5W | 459W | 472W | 86W |
| 温度 | 40°C | 47°C | 59°C | 35°C |
| PID | 16322 | 9698 | 13651 | 7466 |

> **进程占 VRAM ≠ runner.vram**（详见两份报告第 7.4.7 节），差值 5-15 GiB，**随 context 线性增长**。

---

## 7. 3090 24G 硬件参数（来自 4 份 log 的 `sched.go:613/620`）

| 参数 | 值 | 来源 |
|---|---|---|
| GPU | NVIDIA GeForce RTX 3090 | 4 份 log 共有 |
| compute capability | 8.6 | `verifying if device is supported` |
| VRAM available | 22.9 GiB | `gpu memory` |
| VRAM free | 23.3 GiB | `gpu memory` |
| 系统 RAM total | 251.8 GiB | `system memory` |
| 系统 RAM free | 211-213 GiB | `system memory` |
| CPU 线程 | 44 + 44 batch = 88 逻辑核 | `n_threads` |
| 指令集 | SSE3 / SSSE3 / AVX / AVX2 / F16C / FMA / BMI2 | `system_info` |
| llama.cpp | 1 (9d77fa172) with GNU 13.3.1 | `common_param` |
| CUDA | 12.8.1 | 启动命令 |
| lib | cuda_v12 / cuda_v13 / vulkan | `libDirs` |

---

## 8. 5070 32G 硬件参数（来自 4 份 log + 4 张 nvidia-smi）

| 参数 | 值 | 来源 |
|---|---|---|
| GPU | NVIDIA GeForce RTX 5090 | 4 张 nvidia-smi |
| VRAM total | 31.4 GiB | `total_vram` |
| VRAM available | 30.4 GiB | `gpu memory` |
| VRAM free | 30.9 GiB | `gpu memory` |
| 系统 RAM total | 503.5 GiB | `system memory` |
| 系统 RAM free | 397-402 GiB | `system memory` |
| TDP 上限 | 600W | nvidia-smi |
| idle 功耗 | 5W（64K）/ 86W（256K）| nvidia-smi |

> 5070 32G 系统 RAM 接近 3090 24G 机器的 2 倍。

---

## 9. 性能参数（4 档实测）

### 9.1 Prefill（tokens / second）

| 档位 | 4K-8K prompt | 16K prompt | 28K-32K prompt | 78K-92K prompt |
|---|---:|---:|---:|---:|
| 32K（原报告）| — | — | — | — |
| 64K | 1227-1257 | 1199 | 1043 (28K) | — |
| 128K | 250 | 244 | — | — |
| 192K | 2597 | 1871 | — | 1779 (92K) |
| 256K | 517-535 | 511 | — | — |

### 9.2 Decode（tokens / second，log 中位）

| 档位 | 短输出 | 长输出 |
|---|---:|---:|
| 32K（原报告）| 42.6 | 30-36 |
| 64K | 33-47 | 28-45 |
| 128K | 5.38 | 2.0-2.5 |
| 192K | 60-66 | 46-66 |
| 256K | 9.78 | 5.48 |

### 9.3 MTP / Draft Acceptance

| 档位 | 样本数 | 平均 | 范围 | mean draft len |
|---|---:|---:|---|---:|
| 64K | 30+ | 0.50 | 0.36-0.77 | 2.7-4.8 |
| 128K | 1+ | 0.75 | 0.75 | 4.0 |
| 192K | 10+ | 0.46 | 0.34-0.60 | 2.4-3.4 |
| 256K | 2 | 0.53 | 0.44-0.62 | 2.8-3.5 |

---

## 10. 资源分布（4 档实测对比）

| 维度 | 64K | 128K | 192K | 256K |
|---|---:|---:|---:|---:|
| 加载层数 | 66/66 | 54/66 | 66/66 | 54/66 |
| CPU Mapped model | 682 MiB | 3423 MiB | 682 MiB | 3423 MiB |
| CUDA0 model buffer | 15339 MiB | 12598 MiB | 15339 MiB | 12598 MiB |
| **runner.size** | **16.3 GiB** | **19.0 GiB** | **17.0 GiB** | **21.2 GiB** |
| **runner.vram** | **16.3 GiB** | **13.8 GiB** | **17.0 GiB** | **14.5 GiB** |
| `size == vram`? | ✅ | ❌ | ✅ | ❌ |
| 进程 PROCESSOR | 100% GPU | 27%/73% CPU/GPU | 100% GPU | 32%/68% CPU/GPU |
| fit 阶段报错 | 无 | cannot meet target | 无 | cannot meet target |
| fit 耗时 | < 1s | 5.26s | < 1s | 5.26s |

---

## 11. 关键哈希 / PID 对照

| 档位 | runner.pid | ollama tag hash |
|---|---:|---|
| 64K (3090) | — | `22130167c4c2` |
| 128K (3090) | — | `22130167c4c2` |
| 64K (5070) | 16322 | `22130167c4c2` |
| 128K (5070) | 9698 | `22130167c4c2` |
| 192K (5070) | 13651 | `22130167c4c2` |
| 256K (5070) | 7466 | `22130167c4c2` |

> 6 份 log 全部使用同一个 model hash `22130167c4c2`，确认是同一个 ollama 镜像。
> 3090 的 PID 没出现在 log 中（log 里 runner.pid 字段缺失，因为 3090 log 是 DEBUG 但某些行未捕获），但 5070 截图 PID 跟 log 完美对应。

---

## 12. 推荐配置（综合两份报告）

| 硬件 | 推荐档位 | OLLAMA_CONTEXT_LENGTH | runner.vram | Decode |
|---|---|---:|---:|---:|
| RTX 3090 24G | 64K | 65536 | 16.3 GiB | ~37 tok/s |
| RTX 5070/5090 32G | 192K | 196608 | 17.0 GiB | ~52 tok/s |

通用启动模板：

```bash
export OLLAMA_CONTEXT_LENGTH=<上表推荐值>
export OLLAMA_FLASH_ATTENTION=true
export OLLAMA_KEEP_ALIVE=-1
export OLLAMA_DEBUG=1

ollama serve
```

启动参数（4 份 log 共有）：

```
--spec-type draft-mtp
--spec-draft-n-max 4
--spec-draft-backend-sampling
--flash-attn auto
-b 512 -ub 512
--context-shift --keep 4
```

---

> 速查表完成。所有参数都能溯源到 4 份 log + 4 张 nvidia-smi 截图 + `新建文本文档.txt`。
> 任何字段对不上时请以原始 log 为准，本表仅作快速查阅。
