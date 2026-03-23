# 蚁元 / AntMeta（目前存在问题，请待修复完成后使用）

<p align="center">
  <img src="https://img.shields.io/badge/python-3.10+-blue.svg" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="MIT License">
  <img src="https://img.shields.io/badge/OpenClaw-Compatible-orange.svg" alt="OpenClaw Compatible">
</p>

<p align="center">
  <b>安全的 OpenClaw 多代理团队系统</b><br>
  <i>Safe Multi-Agent Team System for OpenClaw, Claude Code, Codex</i>
</p>

---

## 🎯 核心理念

**"蚁元"寓意：**
- **蚁**: 像蚂蚁一样简单、协作的 Agent 单元
- **元**: 元级（Meta）协调，基础单元构建复杂系统

> 单个蚂蚁简单，蚁群却展现出惊人的集体智慧。  
> 每个代理就像一只蚂蚁，简单但协作产生复杂能力。

---

## ✨ 核心特性

| 特性 | 说明 |
|------|------|
| 🛡️ **进程隔离** | 基于 OpenClaw `sessions_spawn`，每个 Agent 完全隔离运行 |
| 🎭 **角色系统** | 继承 Agency 153+ 专业角色，开箱即用 |
| 🔒 **零代码风险** | 无自动代码执行，纯指令协调，安全可控 |
| 🧠 **记忆集成** | 与 OpenViking 四层记忆架构无缝集成 |
| 📊 **可视化监控** | CLI 面板 + Web UI 实时监控团队状态 |
| ⚡ **并行编排** | 支持并行、顺序、依赖等多种工作流 |

---

## 🚀 快速开始

### 安装

```bash
# 克隆仓库
git clone https://github.com/AntMeta/openclaw-antmeta.git
cd openclaw-antmeta

# 安装依赖
pip install -e ".[dev]"
```

### 基础命令

```bash
# 查看版本
antmeta version

# 列出所有可用角色
antmeta list-roles

# 创建团队
antmeta create-team my-project --description "我的项目"

# 从 Agency 导入角色（如果已安装）
antmeta import-agency

# 添加成员
antmeta add-member my-project frontend-developer alice "构建前端界面"

# 查看团队状态
antmeta status my-project
```

### Python API

```python
from antmeta.orchestrator import Orchestrator
from antmeta.role_loader import RoleLoader

# 初始化
orchestrator = Orchestrator()
loader = RoleLoader()

# 创建团队
team = orchestrator.create_team(name="my-team", description="示例团队")

# 加载角色并添加成员
role = loader.load_role("frontend-developer")
member = orchestrator.add_member(
    team_name="my-team",
    role=role,
    member_name="worker-1",
    task="实现登录功能"
)

# 并行执行
results = orchestrator.orchestrate_parallel("my-team")
```

---

## 🏗️ 架构设计

```
┌─────────────────────────────────────────┐
│           Main Session                  │
│         (Team Leader)                   │
│   - 团队创建/销毁                        │
│   - 任务分配                            │
│   - 结果汇总                            │
│   - 安全策略配置                         │
└──────────────┬──────────────────────────┘
               │ sessions_spawn (隔离子会话)
    ┌──────────┼──────────┐
    ▼          ▼          ▼
┌──────┐  ┌──────┐  ┌──────┐
│Agent │  │Agent │  │Agent │
│Role 1│  │Role 2│  │Role 3│
│隔离沙箱│  │隔离沙箱│  │隔离沙箱│
└──┬───┘  └──┬───┘  └──┬───┘
   │         │         │
   ▼         ▼         ▼
独立工作区  独立工作区  独立工作区
```

### 与 ClawTeam 对比

| 维度 | ClawTeam | AntMeta (蚁元) |
|------|----------|----------------|
| **隔离级别** | Git worktree | 进程/容器隔离 ✅ |
| **权限控制** | 默认全开 | 按角色精确配置 ✅ |
| **安全性** | 高风险 | 沙箱 + 工具白名单 ✅ |
| **资源开销** | 中等 | 按需 spawn ✅ |
| **可扩展性** | ~10-50 代理 | 理论上无上限 ✅ |

---

## 📁 项目结构

```
openclaw-antmeta/
├── src/antmeta/              # 核心源码
│   ├── core/                 # 数据模型
│   ├── orchestrator.py       # 编排器
│   ├── role_loader.py        # 角色加载
│   └── cli.py                # 命令行接口
├── roles/                    # 角色定义
├── examples/                 # 使用示例
├── tests/                    # 测试套件
└── docs/                     # 文档
```

---

## 🎭 角色系统

AntMeta 支持两种角色来源：

### 1. 内置 YAML 角色

```yaml
# roles/frontend-developer.yaml
role:
  name: frontend-developer
  display_name: Frontend Developer
  emoji: 🎨
  soul_md: |
    ## Identity
    I am a meticulous frontend developer...
  agents_md: |
    ## Workflow
    1. Analyze component structure
    2. Check for anti-patterns
    ...
  security:
    allowed_tools: ["read", "write", "web_search"]
    sandbox: true
```

### 2. Agency 角色导入

自动从 `~/.openclaw/agency-agents/` 导入 153+ 预定义角色。

---

## 🔒 安全策略

每个角色可配置独立的安全策略：

```python
security_override = {
    "allowed_tools": ["read", "web_search"],  # 仅允许只读工具
    "sandbox": True,                           # 强制沙箱
    "network_policy": "deny",                  # 禁止网络访问
    "max_execution_time": 300,                 # 5分钟超时
}
```

### 默认安全策略

| 角色类型 | 权限级别 | 说明 |
|---------|---------|------|
| Security Engineer | 🟢 严格 | 仅 `read`, `web_search` |
| Developer | 🟡 标准 | `read`, `write`, `web_search`, `browser` |
| Researcher | 🟡 标准 | 包含 `exec`，但网络受限 |

---

## 🧪 测试

```bash
# 运行测试
pytest tests/ -v

# 检查代码格式
black src/ --check

# 类型检查
mypy src/
```

---

## 🤝 集成

### OpenClaw

AntMeta 专为 OpenClaw 设计，无缝集成 `sessions_spawn`。

### Claude Code / Codex

```bash
# 启动兼容的 Agent
antmeta spawn --backend tmux claude --team my-team --agent-name worker
```

### Agency

自动识别并导入 Agency 的 153 个角色定义。

---

## 📚 文档

- [快速开始](docs/QUICKSTART.md)
- [架构设计](docs/ARCHITECTURE.md)
- [API 参考](docs/API.md)
- [角色定义指南](docs/ROLES.md)

---

## 🛣️ 路线图

- [x] 核心 Team/Member 管理
- [x] 基础 CLI 接口
- [x] Agency 角色导入
- [ ] Web UI 监控面板
- [ ] 工作流模板系统
- [ ] 与 OpenViking 记忆自动同步
- [ ] 性能监控与优化

---

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE)

---

<p align="center">
  <b>🐜 蚁元 - 简单个体，群体智慧</b><br>
  <i>Simple Agents, Collective Intelligence</i>
</p>
