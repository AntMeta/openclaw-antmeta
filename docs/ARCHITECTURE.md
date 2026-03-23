# AntMeta 架构设计

## 整体架构

AntMeta 采用分层架构设计，确保安全、可扩展、易维护。

```
┌─────────────────────────────────────────────────────────────┐
│                     Presentation Layer                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ CLI (typer) │  │ Web UI      │  │ Python API          │  │
│  │ (rich)      │  │ (planned)   │  │                     │  │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘  │
└─────────┼────────────────┼────────────────────┼─────────────┘
          │                │                    │
          └────────────────┼────────────────────┘
                           │
┌──────────────────────────┼──────────────────────────────────┐
│                     Core Layer                               │
│  ┌───────────────────────┴──────────────────────────────┐   │
│  │                   Orchestrator                        │   │
│  │  - 团队生命周期管理                                    │   │
│  │  - 成员协调与通信                                      │   │
│  │  - 任务编排与监控                                      │   │
│  └───────────────────────┬──────────────────────────────┘   │
│                          │                                   │
│  ┌───────────────────────┼──────────────────────────────┐   │
│  │         TeamManager   │   RoleLoader                  │   │
│  │  - 团队状态持久化      │   - 角色定义加载              │   │
│  │  - 任务依赖解析        │   - Agency 集成               │   │
│  └───────────────────────┴──────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
          │
          │ sessions_spawn
          ▼
┌─────────────────────────────────────────────────────────────┐
│                   Execution Layer                            │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐        │
│  │ Agent 1 │  │ Agent 2 │  │ Agent 3 │  │ Agent N │        │
│  │ (隔离)  │  │ (隔离)  │  │ (隔离)  │  │ (隔离)  │        │
│  │ 子会话  │  │ 子会话  │  │ 子会话  │  │ 子会话  │        │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘        │
│       │            │            │            │              │
│       └────────────┴────────────┴────────────┘              │
│                         │                                    │
│                    OpenClaw Gateway                         │
└─────────────────────────────────────────────────────────────┘
```

## 核心组件

### 1. Orchestrator (编排器)

**职责**: 团队创建、成员管理、任务编排

```python
class Orchestrator:
    def create_team(name, description) -> Team
    def add_member(team, role, name, task) -> TeamMember
    def send_message(team, member, message) -> bool
    def orchestrate_parallel(team) -> List[Result]
    def orchestrate_sequential(team, order) -> List[Result]
```

**关键设计**:
- 不直接执行代码，只协调子会话
- 通过 `sessions_spawn` 创建隔离环境
- 消息传递使用 `sessions_send`

### 2. TeamManager (团队管理器)

**职责**: 团队状态持久化、任务依赖管理

**存储结构**:
```
~/.antmeta/
└── teams/
    └── {team_name}/
        ├── team.json          # 团队配置和状态
        ├── workspace/         # 共享工作区
        └── logs/              # 操作日志
```

**依赖解析**:
```python
# 任务 A 依赖任务 B
task_a = Task(
    id="task-a",
    depends_on=["task-b"],
    status=TaskStatus.BLOCKED
)

# 当 task-b 完成时，自动解锁 task-a
def update_task_status(task_id, status):
    if status == COMPLETED:
        unblock_dependent_tasks(task_id)
```

### 3. RoleLoader (角色加载器)

**职责**: 加载和解析角色定义

**加载优先级**:
1. 内置 YAML 角色 (`roles/*.yaml`)
2. Agency 角色 (`~/.openclaw/agency-agents/*/SOUL.md`)

**角色结构**:
```yaml
role:
  name: string          # 角色标识
  display_name: string  # 显示名称
  emoji: string         # 图标
  soul_md: string       # 个性定义 (SOUL.md)
  agents_md: string     # 工作流程 (AGENTS.md)
  security:             # 安全策略
    allowed_tools: []
    sandbox: bool
    ...
```

## 安全架构

### 隔离模型

```
┌─────────────────────────────────┐
│         Main Session            │
│  - 完全权限                     │
│  - 可创建/销毁子会话            │
└─────────────┬───────────────────┘
              │ sessions_spawn
              ▼
┌─────────────────────────────────┐
│        Sub-agent Session        │
│  - 受限权限 (由 Role 定义)       │
│  - 独立环境变量                  │
│  - 独立工作目录                  │
│  - 超时自动终止                  │
└─────────────────────────────────┘
```

### 权限控制

**工具白名单模式**:
```python
# 只允许显式授权的工具
allowed_tools = ["read", "web_search"]

# 任何不在白名单中的工具调用都会被拒绝
```

**沙箱策略**:
- `sandbox=true`: 强制沙箱，限制文件系统访问
- `sandbox=false`: 警告模式（不推荐用于生产）

**网络策略**:
- `allow`: 允许所有网络访问
- `deny`: 完全禁止网络
- `whitelist`: 仅允许特定域名

## 数据流

### 创建团队

```
用户调用 create_team()
        │
        ▼
┌───────────────┐
│ TeamManager   │
│ - 创建目录    │
│ - 初始化状态  │
└───────┬───────┘
        │
        ▼
~/.antmeta/teams/{name}/team.json
```

### 添加成员

```
用户调用 add_member(role, name, task)
        │
        ▼
┌───────────────┐
│ Orchestrator  │
│ - 加载 Role   │
│ - 准备环境    │
│ - 构建 Prompt │
└───────┬───────┘
        │
        ▼ sessions_spawn
┌───────────────┐
│  子会话       │
│ - 隔离环境    │
│ - 角色 Prompt │
│ - 安全策略    │
└───────────────┘
```

### 消息传递

```
Leader (Main Session)
        │
        │ sessions_send(session_key, message)
        ▼
┌───────────────┐
│  消息队列     │
│  (JSONL)      │
└───────┬───────┘
        │
        ▼ sessions_poll
Worker (Sub-session)
```

## 扩展点

### 1. 自定义角色

创建 `roles/my-role.yaml`:
```yaml
role:
  name: my-role
  soul_md: |
    ## Identity
    I am a custom agent...
```

### 2. 自定义编排策略

继承 `Orchestrator`:
```python
class MyOrchestrator(Orchestrator):
    def orchestrate_custom(self, team):
        # 自定义协调逻辑
        pass
```

### 3. 自定义后端

除了 OpenClaw `sessions_spawn`，未来可支持：
- Docker 容器
- Kubernetes Pod
- 远程服务器

## 性能考量

### 资源使用

| 指标 | 单个 Agent | 10 Agents | 50 Agents |
|------|-----------|-----------|-----------|
| 内存 | ~100MB | ~1GB | ~5GB |
| CPU | 低 | 中等 | 高 |
| 存储 | ~10MB | ~100MB | ~500MB |

### 优化建议

1. **合理控制并发数**: 根据机器配置设置最大并行数
2. **及时清理**: 使用 `cleanup()` 释放已完成的工作区
3. **共享依赖**: 使用虚拟环境或容器镜像缓存

## 故障处理

### 子会话崩溃

```python
try:
    result = orchestrate_parallel(team)
except SessionCrashedError as e:
    # 自动重启或通知用户
    restart_member(team, e.member_name)
```

### 任务超时

```python
# 在 Role 中配置超时
security.max_execution_time = 300  # 5分钟

# 超时后自动终止
```

### 依赖死锁

```python
# 检测循环依赖
def detect_cycle(tasks):
    # 拓扑排序检测
    ...
```

## 与其他系统的关系

### OpenClaw

AntMeta 是 OpenClaw 的上层抽象：
- 使用 `sessions_spawn` 创建子会话
- 使用 `sessions_send` 进行通信
- 遵守 OpenClaw 的安全模型

### Agency

AntMeta 复用 Agency 的角色定义：
- 导入 SOUL.md 作为 `soul_md`
- 导入 AGENTS.md 作为 `agents_md`
- 添加额外的安全策略配置

### OpenViking 记忆架构

计划中的集成：
```python
# 团队执行结果自动记录到 L2-Detailed
def log_to_openviking(team, results):
    daily_log = f"memory/L2-detailed/{today}.md"
    append_team_execution(team, results, to=daily_log)
```

## 演进路线

### v0.1 (当前)
- 核心 Team/Member 管理
- 基础 CLI
- Agency 角色导入

### v0.2 (计划)
- Web UI 监控面板
- 工作流模板系统
- 任务依赖可视化

### v0.3 (计划)
- OpenViking 自动同步
- 性能监控
- 团队协作优化

### v1.0 (计划)
- 生产级稳定性
- 完整的审计日志
- 企业级安全特性
