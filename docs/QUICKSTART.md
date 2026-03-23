# 蚁元 / AntMeta - 使用指南

## 快速开始

### 安装

```bash
# 从源码安装
git clone https://github.com/AntMeta/openclaw-antmeta.git
cd openclaw-antmeta
pip install -e .
```

### 基础命令

```bash
# 查看版本
antmeta version

# 列出所有可用角色
antmeta list-roles

# 创建团队
antmeta create-team my-project --description "我的项目"

# 从 Agency 导入角色
antmeta import-agency

# 添加成员
antmeta add-member my-project frontend-developer alice "构建前端界面"

# 查看团队状态
antmeta status my-project
```

## Python API 使用

```python
from antmeta.orchestrator import Orchestrator
from antmeta.role_loader import RoleLoader

# 初始化
orchestrator = Orchestrator()
loader = RoleLoader()

# 创建团队
team = orchestrator.create_team(
    name="my-team",
    description="示例团队"
)

# 加载角色
role = loader.load_role("frontend-developer")

# 添加成员
member = orchestrator.add_member(
    team_name="my-team",
    role=role,
    member_name="worker-1",
    task="实现登录功能"
)

# 并行执行
results = orchestrator.orchestrate_parallel("my-team")
```

## 完整示例

查看 `examples/webapp_team.py` 了解如何构建全栈开发团队。

## 架构特点

- **进程隔离**: 基于 OpenClaw sessions_spawn
- **角色系统**: 支持 Agency 153+ 角色
- **安全策略**: 按角色配置权限
- **记忆集成**: 与 OpenViking 架构集成

## 许可证

MIT License
