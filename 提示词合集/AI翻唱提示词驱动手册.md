# AI 翻唱（AI Cover）

![platform-windows](https://img.shields.io/badge/platform-Windows-blue)
![python-3.10](https://img.shields.io/badge/python-3.10-blue)
![license-note](https://img.shields.io/badge/license-仅供学习研究-lightgrey)
![method-zero-shot](https://img.shields.io/badge/method-零样本免训练-green)

> 只换人声、原曲伴奏 100% 不变的全自动翻唱流水线。
> 全程**零样本、免训练**：只需一段 3~30 秒的目标音色参考音频，即可把任意歌曲的人声换成目标音色。

技术栈：**[Demucs](https://github.com/facebookresearch/demucs)**（人声分离）+ **[Seed-VC](https://github.com/Plachtaa/seed-vc)**（零样本歌声转换）+ **FFmpeg**（合成）。

环境要求：Windows + PowerShell · Python 3.10 · Git · FFmpeg · NVIDIA 显卡（可选，无 GPU 也能跑只是慢）。

---

## ⚡ 快速开始：一条提示词装好全部环境

> **新手不用读 3~6 章**，复制下面这段发给 AI（如 Claude、ChatGPT 的终端助手），
> 它会读本手册、按顺序装好 Demucs + Seed-VC + torch cu121，并验证 GPU。全程零手动操作。

```
我要在本机搭一套 AI 翻唱环境。请先读《AI翻唱提示词驱动手册.md》第 3~6 章，
然后按顺序执行环境安装：检查/安装基础软件（§3.2）→ 建目录（§3.3）→ 设置存储约束
（§3.4）→ 安装 Demucs（§5.1）→ 安装 Seed-VC（§6.1，含 torch cu121 国内方案）→
验证 GPU。每步都要确认成功再继续，报错就停下并告诉我怎么解决。
本机显卡信息：<nvidia-smi 输出粘贴到这里，无显卡就写"纯 CPU">
```

装完后，翻唱直接用这些提示词（完整提示词库见下节《提示词使用》）：

```
用 懒羊羊 配这个 "<素材文件路径>.mp4"      # 用参考音色翻唱一首歌
先处理成干声：<素材文件路径>                # 把素材提成参考干声
声音大小要一样，合成的声音有点小            # 音量对齐原曲
```

---

## 💬 提示词使用（完整提示词库）

以下为日常可复用的指令模板，交给 AI 后它会按本手册自动执行对应步骤。
每条都附**真实示例**（沿用项目里已跑通的案例：参考音频 `reference\懒羊羊_干声.wav`、`reference\ngw.wav`）。

> 💡 **参考名 ↔ 文件映射**：提示词里的"懒羊羊"指 `reference\懒羊羊_干声.wav`，"ngw"指 `reference\ngw.wav`。
> 换用你自己的参考音频时，把提示词里的名字换成 `reference\` 目录下对应的文件名即可。

**从零安装环境（新手必看）**

不用手动逐条执行 §3~§6，把下面这段直接发给 AI 即可，它会照着本手册一步步装好并验证：

> 模板：
> ```
> 我要在本机搭一套 AI 翻唱环境。请先读《AI翻唱提示词驱动手册.md》第 3~6 章，
> 然后按顺序执行环境安装：检查/安装基础软件（§3.2）→ 建目录（§3.3）→ 设置存储约束
> （§3.4）→ 安装 Demucs（§5.1）→ 安装 Seed-VC（§6.1，含 torch cu121 国内方案）→
> 验证 GPU。每步都要确认成功再继续，报错就停下并告诉我怎么解决。
> 本机显卡信息：<nvidia-smi 输出粘贴到这里，无显卡就写"纯 CPU">
> ```
>
> 真实示例：
> ```
> 我要在本机搭一套 AI 翻唱环境。请先读《AI翻唱提示词驱动手册.md》第 3~6 章，
> 然后按顺序执行环境安装：检查/安装基础软件（§3.2）→ 建目录（§3.3）→ 设置存储约束
> （§3.4）→ 安装 Demucs（§5.1）→ 安装 Seed-VC（§6.1，含 torch cu121 国内方案）→ 验证 GPU。
> 每步都要确认成功再继续，报错就停下并告诉我怎么解决。
> 本机显卡信息：NVIDIA P104-100, 8GB, driver 551.81, CUDA 12.4
> ```
>
> AI 会执行：
> 1. 检查 Python 3.10 / Git / FFmpeg，缺失就装；
> 2. 建 `input/ reference/ output/separated、output/converted、output/final、tools/ models/` 目录；
> 3. 设置 `PIP_CACHE_DIR`、`HF_HOME`、`HF_ENDPOINT` 指向项目目录；
> 4. 建 `.venv-demucs` 装 Demucs，`py -3.10` 建 `.venv-seedvc` 装 Seed-VC 全套依赖；
> 5. 有显卡就换 cu121 torch（download.pytorch.org 慢就走 §6.1 的 wheel 方案），锁 numpy 1.26.4；
> 6. 最后跑 `import torch; print(torch.cuda.is_available())` 验证，应为 `True`。
>
> 装完后建议跑一遍附录 B 的最小闭环（10 秒片段 + 10 秒参考干声）确认整条链路可用。

**翻唱（用参考音色配一首歌/视频）**

> 模板：`用 <参考名> 配这个 "<视频/音频文件路径>"`
>
> 真实示例：
> ```
> 用 懒羊羊 配这个 "G:\ai_project\AI翻唱\input\20260810_抖音视频.mp4"
> 用 ngw 翻唱 逆流成河
> ```
> AI 会执行：mp4 抽音频（§4.3）→ Demucs 分离 → 复制带歌名干声（§5.4）→ Seed-VC 转换 → FFmpeg 合成 → 音量对齐验证。成品存到 `output\final\歌名_翻唱_参考名.mp3`。

**把素材处理成参考干声**

> 模板：`先处理成干声：<素材文件路径>`
>
> 真实示例：
> ```
> 先处理成干声："G:\ai_project\AI翻唱\reference\20250516_#懒羊羊_#翻唱_#模仿__这个打几分！.mp4"
> ```
> AI 会执行：抽音频 → Demucs 分离 → 把干净 `vocals.wav` 存到 `reference\`（本例得到 `reference\懒羊羊_干声.wav`），之后可直接当参考用。

**音量对齐**

> 模板：`声音大小要一样，合成的声音有点小`
>
> 真实示例：
> ```
> 声音大小要一样，合成的声音有点小
> ```
> AI 会执行 volumedetect 对比原曲，调整 §7.1 的人声/整轨增益系数（如 ×2.5 / ×4.0）重跑合成，直到成品与原曲 mean_volume 相差 ±1 dB 内。

**音色调优**

> 模板：`<成品> 音色不像 / 咬字发糊 / 有金属声`
>
> 真实示例：
> ```
> 逆流成河_翻唱_懒羊羊.mp3 音色不像，帮我调到更像
> ```
> AI 会按 §6.6 的参数值（不像→`--inference-cfg-rate` 升到 0.8~0.9，发糊→降到 0.5~0.6）、结合 §8.2 的调优顺序，重跑转换。

**并发多开（同时翻唱多首）**

> 模板：`用 <参考1> 配 A.mp4，用 <参考2> 配 B.mp4，两首都做`
>
> 真实示例：
> ```
> 用 懒羊羊 配 抖音视频.mp4，用 ngw 配 逆流成河.mp4，两首都做
> ```
> 显存足够时 AI 可并行跑多首；输出文件名带歌名（§5.4），不会互相覆盖。

**文档维护**

> 模板：`同步修正所有文档` / `按 GitHub 标准复核 <文档名>`
>
> 真实示例：
> ```
> 同步修正所有文档
> 按 GitHub 标准复核 AI翻唱提示词驱动手册.md
> ```
> AI 会把你本次实测的坑（新参数、新命令、踩坑结论）写回 `AI翻唱操作文档.md` 或 `AI翻唱提示词驱动手册.md`。

---

## 项目简介

- **目标**：把一首歌的人声换成目标音色，原曲伴奏（编曲、乐器、和声伴奏）100% 不变。
- **核心原则（必须遵守）**：先人声分离 → 只对分离出的干声做音色转换 → 再与原始伴奏合成。
  任何情况下都不要把整首歌直接丢给转换模型（否则伴奏会被染色，违背曲不变）。
- **完全免训练**：所有环节用的都是预训练模型 + 零样本推理。

---

## 目录

- [⚡ 快速开始](#-快速开始一条提示词装好全部环境)
- [💬 提示词使用](#-提示词使用完整提示词库)
- [项目简介](#项目简介)
- [总体流程](#1-总体流程)
- [目录与文件约定](#2-目录与文件约定)
- [环境准备](#3-环境准备一次性)
- [素材准备](#4-素材准备)
- [步骤一：人声分离（Demucs）](#5-步骤一人声分离demucs)
- [步骤二：歌声换音色（Seed-VC）](#6-步骤二歌声换音色seed-vc)
- [步骤三：合成（FFmpeg）](#7-步骤三合成ffmpeg)
- [质量检查与调优](#8-质量检查与调优)
- [台词换音色](#9-台词换音色可选场景)
- [常见问题](#10-常见问题排查表)
- [合规与版权](#11-合规与版权提醒)
- [附录 A：UVR5 备选](#附录-auvr5-备选人声分离质量不够时)
- [附录 B：最小闭环验证](#附录-b一条龙快速验证最小闭环)
- [附录 C：实测参考数据](#附录-c实测参考数据2026-08-8gb-显存-cuda-显卡)

---

## 1. 总体流程

```
原曲音频
   │  ① 人声分离（Demucs）
   ├─► vocals.wav（干声）─────────► ② 歌声换音色（Seed-VC，零样本 SVC）
   │                                        │
   └─► no_vocals.wav（伴奏，原封不动）     ▼
                                    converted_vocals.wav
                                          │  ③ 合成（FFmpeg）
                                          ▼
                                    final\成品.mp3（人声已换、伴奏未动）
```

| 环节 | 工具 | 说明 |
|---|---|---|
| ① 人声分离 | Demucs（htdemucs_ft 模型） | 命令行操作，质量高，免费开源 |
| ② 换音色 | Seed-VC（SVC 模型） | 零样本歌声转换，参考音频 3~30 秒，免训练 |
| ③ 合成 | FFmpeg | 人声 + 原伴奏混音导出 |

---

## 2. 目录与文件约定

在项目目录下建立固定结构（下文用 `<项目目录>` 指代，例如 `D:\ai_songs`）：

```
<项目目录>\
├─ input\                  # 原曲（要翻唱的歌）
├─ reference\              # 目标音色参考音频（3~30 秒干净人声）
├─ output\
│  ├─ separated\           # Demucs 分离结果
│  ├─ converted\           # Seed-VC 转换结果
│  └─ final\               # 最终成品
├─ tools\
│  └─ seed-vc\             # Seed-VC 源码仓库（git clone 得到）
└─ 本手册.md
```

文件命名规范（重要，靠文件名定位文件）：
- 原曲：`input\歌名_原唱.mp3`（或 wav/flac/mp4）
- 参考音频：`reference\目标歌手_参考.wav`
- 变量写法：下文命令中 `<歌名>`、`<参考名>` 指上述文件名去掉扩展名的部分。
- 路径含中文没有问题，命令中**所有路径必须加英文双引号**。
- **非中文 Windows 系统**：ffmpeg 用 ANSI 代码页取参，中文路径可能乱码，建议先 `chcp 65001` 或改用英文路径（Demucs/Seed-VC 走 Python 无此问题）。
- 若原曲/参考是 **mp4 视频**：先按 §4.3 抽取音频，再走后续流程。

---

## 3. 环境准备（一次性）

### 3.1 硬件与耗时预期
- **有 NVIDIA 显卡**（建议显存 ≥ 6GB，支持 CUDA）：分离/转换都走 GPU，速度快。
  - 实测（8GB 显存显卡）：Demucs 分离 20~30 秒音频约 1~2 秒；Seed-VC 40 steps 约 20~60 秒。
- **无显卡（纯 CPU）**：能跑但慢。
  - 预期：Demucs 4 分钟歌 2~5 分钟；Seed-VC 40 steps 一首 30~60 分钟。
  - CPU 机器建议：`--diffusion-steps` 用 20~30，长歌按 §8.3 切片并行。
- 时间紧张时先拿 10~30 秒片段调好参数（steps=20~30），再对整首执行。

### 3.2 检查/安装基础软件
1. **Python 3.10**（Seed-VC 明确要求 3.10，用 `py -3.10 --version` 检查；没有则从 python.org 装 3.10.x，勾选 Add to PATH）。
2. **Git**：`git --version` 检查，没有则 `winget install --id Git.Git -e`。
3. **FFmpeg**：`ffmpeg -version` 检查，没有则：
   ```powershell
   winget install --id Gyan.FFmpeg -e
   ffmpeg -version   # 安装后重开终端验证
   ```
4. **NVIDIA 驱动/CUDA 检查**（有显卡时）：`nvidia-smi`，记录 CUDA 版本（如 12.x）。

### 3.3 建目录
```powershell
cd <项目目录>
New-Item -ItemType Directory -Force -Path input, reference, output\separated, output\converted, output\final, tools
```

### 3.4 存储约束（重要）
**所有 pip 缓存、模型权重建议放在项目目录内，避免占用系统盘。** 具体做法：
1. **pip 缓存**重定向到项目目录（临时设置，重开终端需重设；要永久可用 `setx`）：
   ```powershell
   $env:PIP_CACHE_DIR='<项目目录>\.pip-cache'
   $env:PIP_NO_CACHE_DIR='0'
   # 永久：setx PIP_CACHE_DIR "<项目目录>\.pip-cache"
   ```
2. **HuggingFace 模型缓存**重定向到项目目录：
   ```powershell
   New-Item -ItemType Directory -Force -Path "<项目目录>\models"
   $env:HF_HOME='<项目目录>\models\huggingface'
   # 永久：setx HF_HOME "<项目目录>\models\huggingface"
   # 国内网络顺带设镜像：
   $env:HF_ENDPOINT='https://hf-mirror.com'
   setx HF_ENDPOINT "https://hf-mirror.com"
   ```
3. **虚拟环境**建在项目根下：`.venv-demucs\`、`.venv-seedvc\`。
4. 自检：`echo $env:PIP_CACHE_DIR`、`echo $env:HF_HOME` 都指向项目目录即可。

---

## 4. 素材准备

### 4.1 原曲
- 拷贝原曲到 `input\`，尽量用无损或高质量音频（wav/flac 最佳，mp3 320k 也可）。
- 原曲采样率建议 44.1kHz（Demucs 输出固定 44.1kHz）。

### 4.2 目标音色参考音频（决定成败，务必认真准备）
- **时长**：3~30 秒，推荐 10~30 秒；越长越像。
- **内容**：目标歌手**唱歌的干净干声**（不是带伴奏的成品歌）。理想来源：
  - 目标歌手同一首歌/同调性的 live 干声；
  - 官方伴奏版、消音版的纯人声；
  - 目标歌手清唱片段。
- **质量要求**：无背景音乐、无混响叠加、人声清晰、无爆音。如果手头只有带伴奏的成品歌，先用 Demucs 分离出干声再当参考（命令同 §5）。
- **采样率**：建议 44.1kHz。16kHz 的也能用，但音色还原度略低（实测 16kHz 参考可用但不如 44.1kHz 干净干声）。

### 4.3 mp4 视频 → 音频（原曲或参考是视频时先做这步）
```powershell
cd <项目目录>
ffmpeg -y -i "input\<文件名>.mp4" -vn -acodec pcm_s16le -ar 44100 -ac 2 "input\<歌名>_原唱.wav"
# 参考视频同理，输出到 reference\ 或先抽到 input\ 再走 Demucs 提干声
```

---

## 5. 步骤一：人声分离（Demucs）

### 5.1 安装 Demucs（一次性）
```powershell
cd <项目目录>

# 创建独立虚拟环境
py -3.10 -m venv .venv-demucs

# 安装 demucs（国内网络可加镜像：-i https://mirrors.aliyun.com/pypi/simple/ ）
.venv-demucs\Scripts\python -m pip install -U pip
.venv-demucs\Scripts\python -m pip install demucs -i https://mirrors.aliyun.com/pypi/simple/

# 有 NVIDIA 显卡时，把 CPU 版 torch 换成 cu121 版（方法见 §6.1 的「torch cu121 安装」，
# demucs 与 seedvc 两个环境装同一套 cu121 torch）。
# 装完强制 numpy<2（torch 2.4.0 编译于 numpy 1.x，numpy 2.x 会导入报错）：
.venv-demucs\Scripts\python -m pip install "numpy==1.26.4" -i https://mirrors.aliyun.com/pypi/simple/
```

### 5.2 执行分离
```powershell
cd <项目目录>
# 有显卡加 -d cuda；无显卡去掉该参数
.venv-demucs\Scripts\python -m demucs --two-stems=vocals -n htdemucs_ft -d cuda "input\<歌名>_原唱.wav" -o output\separated
```
参数说明：
- `--two-stems=vocals`：只分「人声 / 其余」，确保伴奏完整保留。
- `-n htdemucs_ft`：官方最强模型（首次运行自动下载模型，需联网）。
- `-d cuda`：GPU 推理。无 GPU 机器去掉即可。

### 5.3 验证结果（必须检查）
```powershell
Get-ChildItem output\separated\htdemucs_ft\<歌名>_原唱 | Select-Object Name, Length
ffprobe -v error -show_entries format=duration -of csv=p=0 output\separated\htdemucs_ft\<歌名>_原唱\vocals.wav
```
预期：`vocals.wav`（干声）+ `no_vocals.wav`（伴奏），时长与原曲一致。

### 5.4 规避同名覆盖（重要，实测踩坑）
Seed-VC 以 `--source` 的文件名生成输出。所有歌的分离结果都叫 `vocals.wav`，直接转换会导致不同歌的输出互相覆盖（上一首的结果被下一首顶掉）。
**分离后立即把干声复制成带歌名的文件**，后续转换、合成都用带歌名的名字：
```powershell
Copy-Item "output\separated\htdemucs_ft\<歌名>_原唱\vocals.wav" "output\separated\htdemucs_ft\<歌名>_原唱\<歌名>_vocals.wav"
```
这样 Seed-VC 输出即为 `vc_<歌名>_vocals_<参考名>_1.0_40_0.7.wav`，天然带歌名、跨歌不冲突。

### 5.5 失败处理
- 模型下载失败/卡住：先执行 `$env:HF_ENDPOINT='https://hf-mirror.com'` 再重跑。
- 分离后人声还带明显伴奏：改用四轨模式 `demucs -n htdemucs_ft`（会输出 `vocals/drums/bass/other` 四轨，**伴奏需把 drums+bass+other 合成回去**：`ffmpeg -i drums.wav -i bass.wav -i other.wav -filter_complex "[0:a][1:a][2:a]amix=inputs=3[m]" -map "[m]" no_vocals.wav`），或直接改用 UVR5（GUI，见附录 A），后者更省事。

---

## 6. 步骤二：歌声换音色（Seed-VC）

### 6.1 安装（一次性）
```powershell
cd <项目目录>

# 克隆仓库
git clone https://github.com/Plachtaa/seed-vc.git tools\seed-vc

# 创建 Python 3.10 虚拟环境
py -3.10 -m venv .venv-seedvc

# 装 torch：有显卡按你的 CUDA 版本选 cu118/cu121；无显卡选 cpu。
.venv-seedvc\Scripts\python -m pip install -U pip
# CUDA 12.x（推荐）：cu121
.venv-seedvc\Scripts\python -m pip install torch==2.4.0 torchvision==0.19.0 torchaudio==2.4.0 --index-url https://download.pytorch.org/whl/cu121
# CUDA 11.8：把上面 URL 末尾 cu121 改成 cu118
# 纯 CPU：把上面 URL 末尾 cu121 改成 cpu（torch==2.4.0 有 cpu 官方轮子）
```
> ⚠️ 上游 `Plachtaa/seed-vc` 仓库已归档（read-only），clone 后仍可直接使用（本文档全部命令经实测跑通）。
> 若需长期维护，可关注社区 fork 或替代方案。
> torch==2.4.0 同时有 cu118 / cu121 / cpu 三种官方轮子，没有 cu124（要 cu124 须升 torch>=2.5）。`nvidia-smi` 的 CUDA 版本 >= 11.8 即可用 cu121。

#### torch cu121 国内安装（download.pytorch.org 慢时的替代方案，实测通过）
阿里云 `pytorch-wheels` 镜像（`https://mirrors.aliyun.com/pytorch-wheels/cu121/`）**不是标准 PEP503 索引，pip 直接 `--index-url` 会报 "No matching distribution"**。正确做法是手动下载 3 个 wheel 再本地安装（2 个环境共用一份 wheel）：
```powershell
cd <项目目录>
New-Item -ItemType Directory -Force -Path .pip-cache\wheels-cu121
curl.exe -L -o .pip-cache\wheels-cu121\torch-2.4.0+cu121-cp310-cp310-win_amd64.whl "https://mirrors.aliyun.com/pytorch-wheels/cu121/torch-2.4.0%2Bcu121-cp310-cp310-win_amd64.whl"
curl.exe -L -o .pip-cache\wheels-cu121\torchvision-0.19.0+cu121-cp310-cp310-win_amd64.whl "https://mirrors.aliyun.com/pytorch-wheels/cu121/torchvision-0.19.0%2Bcu121-cp310-cp310-win_amd64.whl"
curl.exe -L -o .pip-cache\wheels-cu121\torchaudio-2.4.0+cu121-cp310-cp310-win_amd64.whl "https://mirrors.aliyun.com/pytorch-wheels/cu121/torchaudio-2.4.0%2Bcu121-cp310-cp310-win_amd64.whl"
# 安装（--find-links 优先用本地 wheel；依赖从阿里云 pypi 源拉取）
.venv-demucs\Scripts\python -m pip install --find-links .pip-cache\wheels-cu121 -i https://mirrors.aliyun.com/pypi/simple/ torch==2.4.0+cu121 torchvision==0.19.0+cu121 torchaudio==2.4.0+cu121
.venv-seedvc\Scripts\python -m pip install --find-links .pip-cache\wheels-cu121 -i https://mirrors.aliyun.com/pypi/simple/ torch==2.4.0+cu121 torchvision==0.19.0+cu121 torchaudio==2.4.0+cu121
# torch 2.4.0 需 numpy<2，两个环境统一锁到 1.26.4：
.venv-demucs\Scripts\python -m pip install "numpy==1.26.4" -i https://mirrors.aliyun.com/pypi/simple/
.venv-seedvc\Scripts\python -m pip install "numpy==1.26.4" -i https://mirrors.aliyun.com/pypi/simple/
```
> 提示：torch 主包 wheel 约 2.3GB，下载需几分钟；断点续传用 `curl -L -C -`。

安装其余依赖：
```powershell
.venv-seedvc\Scripts\python -m pip install -r tools\seed-vc\requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
```

验证 GPU（有显卡时）：
```powershell
.venv-demucs\Scripts\python -c "import torch; print(torch.__version__, torch.cuda.is_available())"
.venv-seedvc\Scripts\python -c "import torch; print(torch.__version__, torch.cuda.is_available())"
# 输出应为 2.4.0+cu121 True
```

### 6.2 执行歌声转换
```powershell
cd <项目目录>\tools\seed-vc
$env:HF_ENDPOINT='https://hf-mirror.com'   # 国内网络建议设置

<项目目录>\.venv-seedvc\Scripts\python inference.py `
  --source "<项目目录>\output\separated\htdemucs_ft\<歌名>_原唱\<歌名>_vocals.wav" `
  --target "<项目目录>\reference\<参考名>.wav" `
  --output "<项目目录>\output\converted" `
  --diffusion-steps 40 `
  --length-adjust 1.0 `
  --inference-cfg-rate 0.7 `
  --f0-condition True `
  --fp16 True
```
> ⚠️ 纯 CPU 机器请去掉 `--fp16 True`（CPU 推理不支持半精度，会报错）。

参数说明（翻唱场景推荐值）：
| 参数 | 值 | 说明 |
|---|---|---|
| `--f0-condition True` | **必须** | 歌声转换专用：保留原曲旋律音高（False 是语音变声，会丢失歌唱音高） |
| `--diffusion-steps` | 30~50 | 质量档；40 均衡，50 更稳，10 以内只用于快速试听 |
| `--inference-cfg-rate` | 0.5~0.9 | 音色相似度/稳定度权衡；像但糊就降，不像就升 |
| `--length-adjust` | 1.0 | 时长系数；输出与源不等长时微调（如 0.99/1.01） |
| `--semi-tone-shift` | 0 | 原唱与目标歌手音域差异大时可整体移调（如 -2 / +2） |
| `--fp16 True` | True | 半精度推理，省显存（默认） |

### 6.3 模型自动下载
- 首次运行自动从 HuggingFace 下载 SVC 模型与音高模型（`rmvpe.pt`），保存到 `tools\seed-vc\checkpoints\`。
- 下载失败就设置 `$env:HF_ENDPOINT='https://hf-mirror.com'` 后重跑。

### 6.4 输出文件
转换结果在 `--output` 目录，文件名为 `vc_<源文件名>_<参考文件名>_<length-adjust>_<diffusion-steps>_<cfg-rate>.wav`，
例如干声命名为 `<歌名>_vocals.wav` 时输出 `vc_<歌名>_vocals_目标歌手_1.0_40_0.7.wav`（44.1kHz）。
> 因输出名基于源文件名，带歌名命名的干声输出天然避免跨歌覆盖。

### 6.5 验证
- 文件存在、时长约等于干声时长（允许 ±3% 内微差）。
- 试听人声：音色接近参考、旋律与原曲一致、无明显破音/金属声。

### 6.6 失败处理
- **显存不足（CUDA out of memory）**：`--diffusion-steps` 降到 20~30；确认 `--fp16 True`；或切片（§8.3）。
- **模型下载失败**：设 `HF_ENDPOINT` 镜像后重试。
- **输出很像参考但糊/咬字不清**：`--inference-cfg-rate` 降到 0.5~0.6。
- **输出不像参考**：换更长更干净的参考干声；`--inference-cfg-rate` 升到 0.8~0.9。
- **整体音高不对/跑调感**：检查是否忘了 `--f0-condition True`。

---

## 7. 步骤三：合成（FFmpeg）

### 7.1 执行合成
```powershell
cd <项目目录>

# 实测参数：Seed-VC 输出音量明显偏低（平均比原干声低约 11~12 dB），
# 合成时需 人声×2.5 + 整轨×4.0 才能与原曲响度基本一致。
ffmpeg -y `
  -i output\converted\vc_<歌名>_vocals_<参考名>_1.0_40_0.7.wav `
  -i output\separated\htdemucs_ft\<歌名>_原唱\no_vocals.wav `
  -filter_complex "[0:a]volume=2.5[v];[1:a]volume=1.0[m];[v][m]amix=inputs=2:duration=longest:dropout_transition=0,volume=4.0,alimiter=limit=1.0" `
  -ac 2 -b:a 320k `
  output\final\<歌名>_翻唱_<参考名>.mp3
```
说明：
- `volume=2.5`：人声补偿（Seed-VC 输出偏小，2.5 倍后与原干声响度相当）。
- `volume=1.0`：伴奏保持原音量。
- `volume=4.0`（amix 之后）：整轨总增益，对齐原曲响度；不同歌曲按下方验证微调。
- `alimiter=limit=1.0` 防削波，峰值压到 0 dB 以内。
- 输出 mp3（320k）。要 wav 就改 `-c:a pcm_s16le output.wav`。

音量验证（对齐原曲，推荐每次合成后跑一遍）：
```powershell
ffmpeg -i output\final\<歌名>_翻唱_<参考名>.mp3 -af volumedetect -f null NUL 2>&1 | Select-String "mean_volume|max_volume"
ffmpeg -i input\<歌名>_原唱.wav   -af volumedetect -f null NUL 2>&1 | Select-String "mean_volume|max_volume"
# 两者 mean_volume 差在 ±1 dB 内即视为音量一致；差大了就整体调 volume=4.0 附近的数值重跑。
```

### 7.2 验证成品
- 时长 ≈ 原曲时长。
- 试听整曲：伴奏部分应与原曲完全一致；人声为新音色、旋律节奏与原曲吻合。

---

## 8. 质量检查与调优

### 8.1 检查清单（每首成品过一遍）
1. 伴奏是否原封未动？（对照原曲，无染色/糊化）
2. 人声相似度是否可接受？
3. 咬字、气口、尾音是否自然？有无金属声、爆音？
4. 人声与伴奏音量是否平衡？成品响度是否与原曲接近？
5. 有无整段跑调或音高漂移？

### 8.2 常用调优顺序（按性价比）
1. **换更好的参考音频**（最有效）：目标歌手同一首歌的高质量干声、10~30 秒。
2. `--diffusion-steps` 40 → 50。
3. `--inference-cfg-rate` 微调 ±0.1。
4. 检查分离质量：`vocals.wav` 里若残留伴奏，换更干净的分轨。
5. `--semi-tone-shift` 解决明显音域不适配。

### 8.3 长歌/长素材切片策略（可选）
显存充足（≥8GB）时常规不需要切片，直接整首跑即可。只在以下情况切片：
- 整首跑出现 `CUDA out of memory`；
- 干声超过 8 分钟、希望单步重跑更可控。

切片方法（每 45 秒一段，从项目根目录执行）：
```powershell
ffmpeg -y -i "output\separated\htdemucs_ft\<歌名>_原唱\vocals.wav" -f segment -segment_time 45 -c copy "output\converted\seg_%03d.wav"
```
逐段跑 Seed-VC（`--source` 指向每个切片），然后拼接（**从项目根目录执行**，`concat.txt` 放项目根，路径要写全 `output\converted\...`）：
```powershell
# concat.txt 每行：file 'output\converted\vc_seg_001_...wav'
# （把每个切片经 Seed-VC 转换后的输出按顺序写进 concat.txt）
ffmpeg -y -f concat -safe 0 -i concat.txt -c copy "output\converted\vocals_converted_full.wav"
```
注意：切片建议带 1~2 秒重叠并交叉淡化，避免接缝处音色跳变；普通场景直接整首跑更省事。

### 8.4 常见副产物问题
- **和声（backing vocal）丢失/变薄**：Demucs 常把和声留在伴奏轨或丢掉。可接受就无视；不可接受需用 UVR5 多轨模式或手动补和声（超出本手册范围）。
- **齿音/气声变重**：降低 `--inference-cfg-rate`；或参考音频避开气声过多的片段。

---

## 9. 台词换音色（可选场景）

### 路线 A：已有台词录音 → 直接变声（保留原表演节奏）
用 Seed-VC 的**语音**模型（不是歌声模型）：
```powershell
cd <项目目录>\tools\seed-vc
<项目目录>\.venv-seedvc\Scripts\python inference.py `
  --source "<项目目录>\input\台词原文.wav" `
  --target "<项目目录>\reference\<参考名>.wav" `
  --output "<项目目录>\output\converted" `
  --diffusion-steps 25 `
  --inference-cfg-rate 0.7 `
  --f0-condition False `
  --fp16 True
```
要点：`--f0-condition False`（语音场景），此时自动使用 22.05kHz 语音模型；纯 CPU 机器同样去掉 `--fp16 True`。

### 路线 B：文本 → 目标音色台词（重新合成，适合短剧/多语种配音）
用 **GPT-SoVITS V4**（MIT 协议，5 秒参考即可零样本合成，支持中/英/日/韩/粤）：
1. 最省事：下载 Windows 集成包（HuggingFace `lj1995/GPT-SoVITS-windows-package` 的 7z），解压后双击 `_go-webui.bat`。
2. 浏览器打开 WebUI（默认 `http://127.0.0.1:9874`），进入「1-在线推理」标签页：上传 ≥5 秒参考音频（及文字）、输入台词文本、点击合成。
3. 备选开源（免训练、质量高）：`IndexTTS-2`、`CosyVoice`（阿里）等。安装命令以各自 GitHub 官方 README 为准（名称可能变动，请以仓库为准）。

---

## 10. 常见问题排查表

| 现象 | 原因 | 处理 |
|---|---|---|
| 模型下载失败/卡住 | 网络无法访问 HuggingFace | 先执行 `$env:HF_ENDPOINT='https://hf-mirror.com'` 再重跑 |
| `CUDA out of memory` | 显存撞顶 | 降 `--diffusion-steps` 到 20~30、确认 `--fp16 True`、再不行按 §8.3 切片 |
| `torch.cuda.is_available()` 为 False | PyTorch 与驱动不匹配 | 查 `nvidia-smi` 的 CUDA 版本，重装对应 cu 版本 torch |
| 导入 torch 报 numpy 错 | numpy 2.x 与 torch 2.4 不兼容 | `pip install "numpy==1.26.4"` |
| pip 报 "No matching distribution" | 国内镜像索引格式限制 | 改用官方源，或按 §6.1 手动下载 wheel 安装 |
| 输出有金属声/破音 | steps 太低或 cfg 太高 | steps 提到 40+，cfg 降到 0.5~0.6 |
| 输出时长明显不对 | 模型输出长度漂移 | 调 `--length-adjust`（±0.01 步进） |
| 整首歌转完人声像说话 | 忘了 `--f0-condition True` | 歌声场景必须为 True |
| 伴奏被染色 | 直接把整首歌喂给了转换模型 | 必须先分离，只转 `vocals.wav` |
| 分离后人声残留伴奏 | Demucs 极限 | 换 UVR5 或四轨分离（伴奏需混回，见 §5.5） |
| 成品整体音量偏小 | Seed-VC 输出偏低 | 合成时人声 ×2.5、整轨 ×4.0（见 §7.1），再按 volumedetect 微调 |
| 转换结果被上一首覆盖 | 所有歌干声都叫 `vocals.wav`，输出同名 | 分离后把干声复制成 `<歌名>_vocals.wav` 再转换（见 §5.4） |
| PowerShell 提示禁止执行脚本 | 执行策略限制 | 先执行 `Set-ExecutionPolicy -Scope Process Bypass` |
| `py -3.10` 找不到 | 未装 Python 3.10 或未加入 PATH | 装 python.org 3.10.x；或用 `C:\Users\<用户>\AppData\Local\Programs\Python\Python310\python.exe` 全路径 |

---

## 11. 合规与版权提醒

> ⚠️ 本手册及其中所有素材/成品**仅供学习研究**，请勿用于商业用途、冒名、诈骗、诽谤等。

- 克隆/模仿**真实歌手、演员的声音**需要其本人授权；请勿用于冒名、诈骗、诽谤等用途。
- 生成内容发布到 B 站/YouTube/TikTok 等平台时，注意各平台的「AI 生成内容标识」政策。
- 翻唱作品涉及原曲词曲版权，公开传播请遵守相关法规与平台规则。
- 各开源项目许可证不同（Seed-VC 为 GPL-3.0，GPT-SoVITS 为 MIT 等），商用前逐一核对。

---

## 附录 A：UVR5 备选（人声分离质量不够时）
- 下载 UVR5（Ultimate Vocal Remover）GUI 版（GitHub `Anjok07/ultimatevocalremovergui`），选择 **MDX-Net / Kim_Vocal_2** 模型分离人声与伴奏。
- 输出后同样得到 `vocals.wav` 与 `no_vocals.wav`，后续流程不变。

## 附录 B：一条龙快速验证（最小闭环）
拿到一台装好的机器后，用 10 秒原曲片段 + 10 秒参考干声快速跑通全流程：
1. Demucs 分离 → 2. Seed-VC 转换（steps=20）→ 3. FFmpeg 合成。
验证输出可听、流程无报错，再处理正式曲目（steps=40+、优化参考音频）。

## 附录 C：实测参考数据（2026-08，8GB 显存 CUDA 显卡）
- 全流程一首 20~30 秒短视频（含环境就绪后）：Demucs 1~2 秒 + Seed-VC 20~60 秒 + 合成 <1 秒。
- Seed-VC 输出响度比原干声低约 11~12 dB，合成必须补偿（§7.1）。
- 16kHz 参考音频可用，但 44.1kHz 干净干声还原度更高。
