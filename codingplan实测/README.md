# Coding Plan 服务横向评测

> **声明**: 以下所有数据均为实测数据，评测时间：2026年4月

## 评测概览

| 厂商 | Plan等级 | 价格(元/月) | 体感速度 | Codex支持 | 官方链接 |
|------|----------|-------------|----------|-----------|----------|
| 百度千帆 | Coding Plan Lite | 40 | 慢 | 仅80版本 | [订阅](https://console.bce.baidu.com/qianfan/resource/subscribe) |
| 小米 MiMo | lite | 39 | 快 | 仅80版本 | [定价](https://platform.xiaomimimo.com/#/token-plan) |
| MiniMax | Starter | 29 | 中 | 0.57.0 | [定价](https://platform.xiaomimimo.com/#/token-plan) |

---

## 详细对比

### 1. 百度千帆 (Baidu)

| 项目 | 详情 |
|------|------|
| **Plan等级** | Coding Plan Lite |
| **价格** | 40元/月 |
| **请求限制** | 最多约 1,200次/每5小时<br>每周最多约 9,000次<br>每月最多约 18,000次 |
| **RPM** | 20 |
| **RPS** | 无数据 |
| **TPS** | 无数据 |
| **支持模型** | GLM-5、MiniMax-M2.5、DeepSeek-V3.2 等 |
| **体感速度** | 慢 |
| **Codex支持** | 仅支持 80版本 |

---

### 2. 小米 MiMo (Xiaomi)

| 项目 | 详情 |
|------|------|
| **Plan等级** | lite |
| **价格** | 39元/月 |
| **服务额度** | 60,000,000 Credits（用完即止） |
| **RPM** | 无限制 |
| **RPS** | 无限制 |
| **TPS** | 无限制 |
| **支持模型** | MiMo-V2-Pro（全新旗舰）、MiMo-V2-Omni（全模态基座）、MiMo-V2-TTS（语音合成，限时免费） |
| **体感速度** | 快 |
| **Codex支持** | 仅支持 80版本 |
| **兼容工具** | OpenClaw、Claude Code、OpenCode、KiloCode 等国内外主流编程工具 |

---

### 3. MiniMax

| 项目 | 详情 |
|------|------|
| **Plan等级** | Starter |
| **价格** | 29元/月 |
| **请求限制** | 600次模型调用 / 5小时 |
| **RPM** | 无限制 |
| **RPS** | 无限制 |
| **TPS** | 正常约 50，低峰时段 100 |
| **支持模型** | MiniMax M2.7 / M2.5 |
| **体感速度** | 中 |
| **Codex支持** | 0.57.0 |
| **附加功能** | 约支持1个 OpenClaw agent<br>支持图像理解、联网搜索 MCP |
| **每周额度** | 为「每5小时额度」的 10 倍 |

---

## 关键指标对比

| 指标 | 百度千帆 | 小米 MiMo | MiniMax |
|------|----------|-----------|---------|
| **价格** | 40元/月 | 39元/月 | 29元/月 ⭐ |
| **RPM限制** | 20 | 无限制 ⭐ | 无限制 ⭐ |
| **RPS限制** | 无数据 | 无限制 ⭐ | 无限制 ⭐ |
| **TPS** | 无数据 | 无限制 ⭐ | 50-100 |
| **体感速度** | 慢 | 快 ⭐ | 中 |
| **Codex版本** | 80版本 | 80版本 | 0.57.0 ⭐ |

---

## 选择建议

| 需求场景 | 推荐方案 |
|----------|----------|
| **追求性价比** | MiniMax Starter (29元/月) |
| **追求速度** | 小米 MiMo lite (39元/月) |
| **需要最新Codex** | MiniMax Starter (支持 0.57.0) |
| **高并发需求** | 小米 MiMo 或 MiniMax（均无RPM/RPS限制） |
| **稳定低频使用** | 百度千帆（有明确月度限额） |

---

## 术语说明

- **RPM**: Requests Per Minute，每分钟请求数
- **RPS**: Requests Per Second，每秒请求数
- **TPS**: Tokens Per Second，每秒生成的Token数
- **Codex**: OpenAI 的代码生成模型版本
- **MCP**: Model Context Protocol，模型上下文协议
