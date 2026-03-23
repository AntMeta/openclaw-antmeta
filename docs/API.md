# AntMeta API 参考

## Orchestrator

主控制器，用于管理团队和成员。

### 初始化

```python
from antmeta.orchestrator import Orchestrator

orch = Orchestrator(data_dir="~/.antmeta")
```

**参数**:
- `data_dir`: 数据存储目录，默认 `~/.antmeta`

### create_team

创建新团队。

```python
team = orch.create_team(
    name="my-team",
    description="My project team",
    leader="user"
)
```

**参数**:
| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `name` | str | ✅ | 团队名称（唯一） |
| `description` | str | ❌ | 团队描述 |
| `leader` | str | ❌ | 负责人标识 |

**返回**: `Team` 对象

**异常**:
- `FileExistsError`: 团队已存在

---

### add_member

向团队添加成员。

```python
member = orch.add_member(
    team_name="my-team",
    role=frontend_role,
    member_name="alice",
    task="Build login page",
    security_override={
        "max_execution_time": 1800
    }
)
```

**参数**:
| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `team_name` | str | ✅ | 团队名称 |
| `role` | Role | ✅ | 角色定义 |
| `member_name` | str | ✅ | 成员实例名 |
| `task` | str | ✅ | 任务描述 |
| `security_override` | dict | ❌ | 安全策略覆盖 |

**返回**: `TeamMember` 对象

---

### send_message

向成员发送消息。

```python
orch.send_message(
    team_name="my-team",
    to_member="alice",
    message="API is ready",
    message_type="info"
)
```

**参数**:
| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `team_name` | str | ✅ | 团队名称 |
| `to_member` | str | ✅ | 目标成员 |
| `message` | str | ✅ | 消息内容 |
| `message_type` | str | ❌ | 消息类型 |

**返回**: `bool` 是否成功

---

### broadcast

向所有成员广播消息。

```python
count = orch.broadcast(
    team_name="my-team",
    message="Standup in 5 min",
    message_type="announcement"
)
```

**返回**: `int` 成功发送的成员数

---

### get_member_status

获取成员状态。

```python
status = orch.get_member_status("my-team", "alice")
# {
#     "member": "alice",
#     "role": "frontend-developer",
#     "status": "working",
#     "task": "Build login page",
#     ...
# }
```

---

### orchestrate_parallel

并行执行所有成员任务。

```python
results = orch.orchestrate_parallel("my-team")
```

**返回**: `List[Dict]` 每个成员的状态

---

## RoleLoader

角色加载器。

### list_available_roles

列出所有可用角色。

```python
loader = RoleLoader()
roles = loader.list_available_roles()
# ['backend-architect', 'frontend-developer', ...]
```

---

### load_role

加载指定角色。

```python
role = loader.load_role("frontend-developer")
```

**返回**: `Role` 对象或 `None`

---

### import_all_agency_roles

导入所有 Agency 角色。

```python
count = loader.import_all_agency_roles()
print(f"Imported {count} roles")
```

---

## 数据模型

### Role

```python
@dataclass
class Role:
    name: str                    # 角色标识
    display_name: str            # 显示名称
    emoji: str                   # 图标
    soul_md: str                 # 个性定义
    agents_md: str               # 工作流程
    security: SecurityProfile    # 安全策略
```

### SecurityProfile

```python
@dataclass
class SecurityProfile:
    allowed_tools: List[str]     # 允许的工具
    forbidden_tools: List[str]   # 禁止的工具
    sandbox: bool                # 是否强制沙箱
    network_policy: str          # 网络策略
    max_execution_time: int      # 最大执行时间（秒）
    max_memory_mb: int           # 最大内存（MB）
    max_cpu_percent: int         # 最大CPU使用率
```

### Team

```python
@dataclass
class Team:
    name: str                    # 团队名称
    description: str             # 描述
    leader: str                  # 负责人
    members: List[TeamMember]    # 成员列表
    tasks: List[Task]            # 任务列表
    workspace_dir: Path          # 工作目录
```

### TeamMember

```python
@dataclass
class TeamMember:
    role: Role                   # 角色
    name: str                    # 成员名
    session_key: str             # 子会话标识
    status: MemberStatus         # 状态
    current_task: str            # 当前任务
```

### Task

```python
@dataclass
class Task:
    id: str                      # 任务ID
    title: str                   # 标题
    description: str             # 描述
    owner: str                   # 负责人
    status: TaskStatus           # 状态
    priority: str                # 优先级
    depends_on: List[str]        # 依赖任务
```

---

## 枚举类型

### TaskStatus

```python
class TaskStatus(Enum):
    PENDING = "pending"           # 待处理
    IN_PROGRESS = "in_progress"   # 进行中
    BLOCKED = "blocked"           # 被阻塞
    COMPLETED = "completed"       # 已完成
    FAILED = "failed"             # 失败
```

### MemberStatus

```python
class MemberStatus(Enum):
    IDLE = "idle"                 # 空闲
    WORKING = "working"           # 工作中
    COMPLETED = "completed"       # 已完成
    ERROR = "error"               # 错误
```

---

## CLI 命令

### 全局选项

```bash
antmeta [OPTIONS] COMMAND [ARGS]

Options:
  --help  Show help message
```

### 命令列表

| 命令 | 说明 |
|------|------|
| `version` | 显示版本 |
| `list-roles` | 列出角色 |
| `create-team` | 创建团队 |
| `list-teams` | 列出团队 |
| `add-member` | 添加成员 |
| `status` | 查看状态 |
| `import-agency` | 导入角色 |

### 示例

```bash
# 创建团队
antmeta create-team webapp \
  --description "Full-stack web app"

# 添加成员
antmeta add-member webapp \
  frontend-developer alice \
  "Build React UI"

# 查看状态
antmeta status webapp
```
