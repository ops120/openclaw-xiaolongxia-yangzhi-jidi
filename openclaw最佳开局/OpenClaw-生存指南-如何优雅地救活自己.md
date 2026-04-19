# OpenClaw 生存指南：如何优雅地救活自己

## 背景

当 OpenClaw 安装过多 skill 或修改配置后，容易出现以下症状：
- 进程无响应
- 内存持续增长
- 消息堆积无法处理
- 无法通过外部渠道（如飞书）重启

此时需要一台"急救车"——一个保持最小化配置的实例，专门用于在关键时刻远程恢复主节点。

## 方案设计

### 角色分工

| 实例 | 角色 | 说明 |
|------|------|------|
| openclaw | 主站 | 承担主要业务，安装了各种 skill 和配置 |
| openclaw-rescue | 急救站 | 最小化配置，无额外 skill，专门用于紧急恢复 |

### 设计原则

1. **最小化安装** - 急救站不安装任何额外 skill，保持最简状态
2. **IM 驱动** - 急救站通过飞书接收指令，执行救援操作（比 SSH 更快捷）
3. **独立运行** - 急救站与主站完全隔离，主站卡死不影响急救站
4. **持续可用** - 急救站需要稳定运行，确保随时可连

## 急救站最简安装方案

### 服务器信息

- **IP**: 192.168.110.133
- **SSH**: `ssh -i .ssh/openclaw root@192.168.110.133`

### 安装步骤

#### 1. 创建急救站 profile

```bash
# 初始化急救站 profile
openclaw --profile openclaw-rescue init
```

#### 2. 配置急救站最小化 openclaw.json

```json
{
  "meta": {
    "lastTouchedVersion": "2026.2.26"
  },
  "models": {
    "mode": "merge",
    "providers": {
      "minimax": {
        "baseUrl": "https://api.minimaxi.com/anthropic",
        "apiKey": "your-api-key",
        "api": "anthropic-messages",
        "models": [
          {
            "id": "MiniMax-M2.7-highspeed",
            "name": "MiniMax-M2.7-highspeed",
            "contextWindow": 200000,
            "maxTokens": 32000
          }
        ]
      }
    }
  },
  "agents": {
    "defaults": {
      "model": {
        "primary": "minimax/MiniMax-M2.7-highspeed"
      }
    }
  },
  "channels": {
    "feishu": {
      "enabled": true,
      "appId": "cli_a96e3f9c79b8dbca",
      "appSecret": "your-secret",
      "connectionMode": "websocket",
      "domain": "feishu"
    }
  },
  "gateway": {
    "mode": "local",
    "controlUi": {
      "allowedOrigins": ["http://localhost:*"]
    }
  }
}
```

#### 3. 创建 systemd 服务

创建 `/root/.config/systemd/user/openclaw-rescue.service`:

```ini
[Unit]
Description=OpenClaw Rescue Station
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/openclaw --profile openclaw-rescue gateway
Restart=always
RestartSec=5
Environment=OPENCLAW_STATE_DIR=/root/.openclaw-rescue

[Install]
WantedBy=default.target
```

#### 4. 启用并启动

```bash
systemctl --user daemon-reload
systemctl --user enable openclaw-rescue
systemctl --user start openclaw-rescue
```

#### 5. 验证

```bash
# 检查状态
systemctl --user status openclaw-rescue

# 检查端口（急救站使用不同端口避免冲突）
netstat -tlnp | grep openclaw

# 查看日志
journalctl --user -u openclaw-rescue -f
```

### 急救站配置要点

| 配置项 | 值 | 说明 |
|--------|-----|------|
| maxConcurrent | 4（默认） | 保持默认配置 |
| skill | 无 | **绝对不要安装任何 skill** |
| 飞书 appId | 专用 | 使用独立飞书应用 |
| gateway 端口 | 18790 | 与主站 18789 区分 |

## 通过飞书远程救援主站

急救站的核心功能：通过飞书向急救站发指令，远程控制主站。

### 工作流程

```
[手机飞书] → [急救站飞书] → [执行救援命令] → [主站恢复]
```

### 常用飞书指令

| 指令 | 说明 |
|------|------|
| `重启主站` | 重启 openclaw 主站 |
| `状态` | 查看主站运行状态 |
| `日志` | 查看主站最近日志 |
| `内存` | 查看主站内存使用 |
| `帮助` | 显示可用命令列表 |

### 配置飞书指令响应

急救站接收到特定消息后，自动执行对应命令：

```bash
# 示例：急救站收到 "重启主站" 后执行
systemctl --user restart openclaw
```

### 快速救援流程

1. **主站无响应** → 用手机飞书联系急救站
2. **发送** `重启主站`
3. **急救站** 自动执行 `systemctl --user restart openclaw`
4. **主站恢复** → 飞书收到恢复确认

## 急救站维护

### 保持急救站最小化

急救站 **永远不要**安装额外 skill，保持纯净：

```bash
# 检查急救站安装的 skill
openclaw --profile openclaw-rescue skills list

# 如果有，卸载
openclaw --profile openclaw-rescue skills uninstall <skill-name>
```

### 急救站定期检查

建议每周检查一次：

```bash
# 1. 检查急救站状态
systemctl --user status openclaw-rescue

# 2. 检查资源使用
free -h
df -h /

# 3. 检查主站状态
systemctl --user status openclaw

# 4. 测试远程重启功能
openclaw --profile openclaw gateway status
```

### 急救站配置备份

确保急救站的配置文件也有备份：

```bash
# 备份急救站配置
cp /root/.openclaw-rescue/openclaw.json /root/backup/openclaw-rescue.json.$(date +%Y%m%d)

# 备份 systemd 服务文件
cp /root/.config/systemd/user/openclaw-rescue.service /root/backup/
```

## 快速参考卡片

### 飞书远程救援（推荐）

| 场景 | 手机操作 |
|------|----------|
| 主站无响应 | 飞书联系急救站 → 发送 `重启主站` |
| 查看主站状态 | 发送 `状态` 到急救站 |
| 查看主站日志 | 发送 `日志` 到急救站 |

### 常用救援命令（SSH 方式）

| 操作 | 命令 |
|------|------|
| 通过急救站重启主站 | `systemctl --user restart openclaw` |
| 通过急救站查看主站状态 | `systemctl --user status openclaw` |
| 通过急救站查看主站日志 | `tail -f /tmp/openclaw/openclaw-$(date +%Y-%m-%d).log` |
| 强制杀死主站进程 | `pkill -f openclaw-gateway` |
| 查看主站内存占用 | `ps aux --sort=-%mem \| grep openclaw` |
| 检查 swap 状态 | `swapon --show` |

### profile 对照表

| 用途 | profile 名称 | 配置路径 | gateway 端口 |
|------|-------------|----------|--------------|
| 主站 | openclaw | /root/.openclaw | 18789 |
| 急救站 | openclaw-rescue | /root/.openclaw-rescue | 18790 |

## 预防措施总结

1. **修改配置前先备份**
   ```bash
   cp openclaw.json openclaw.json.backup.$(date +%s)
   ```

2. **安装 skill 前确认兼容性**
   - 先在测试实例验证
   - 确认 skill 不会修改核心配置

3. **保持急救站纯净**
   - 急救站不安装任何 skill
   - 急救站不做业务用途
   - 急救站飞书只用于救援，不做他用

4. **定期检查系统健康**
   - 内存使用率 < 80%
   - 磁盘空间 > 20%
   - swap 充足

5. **配置自动恢复**
   - systemd Restart=always
   - 看门狗脚本定期检测

6. **确保急救站飞书可联系**
   - 急救站飞书 ID 记录在手机
   - 定期测试急救站响应速度

## 更新记录

- **2026-04-19**: 初始版本，定义主站/急救站救援架构
