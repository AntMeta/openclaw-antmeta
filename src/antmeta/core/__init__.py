"""
核心数据模型定义
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from pathlib import Path


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"


class MemberStatus(Enum):
    """成员状态"""
    IDLE = "idle"
    WORKING = "working"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class SecurityProfile:
    """安全配置档案"""
    allowed_tools: List[str] = field(default_factory=lambda: ["read", "web_search"])
    forbidden_tools: List[str] = field(default_factory=list)
    sandbox: bool = True
    network_policy: str = "allow"  # allow | deny | whitelist
    max_execution_time: int = 300  # 秒
    max_memory_mb: int = 512
    max_cpu_percent: int = 50
    
    def to_env_dict(self) -> Dict[str, str]:
        """转换为环境变量字典"""
        return {
            "ANTMETA_ALLOWED_TOOLS": ",".join(self.allowed_tools),
            "ANTMETA_FORBIDDEN_TOOLS": ",".join(self.forbidden_tools),
            "ANTMETA_SANDBOX": "true" if self.sandbox else "false",
            "ANTMETA_NETWORK_POLICY": self.network_policy,
            "ANTMETA_MAX_EXECUTION_TIME": str(self.max_execution_time),
            "ANTMETA_MAX_MEMORY_MB": str(self.max_memory_mb),
            "ANTMETA_MAX_CPU_PERCENT": str(self.max_cpu_percent),
        }


@dataclass
class Role:
    """角色定义"""
    name: str
    display_name: str
    emoji: str = "🐜"
    soul_md: str = ""  # 个性定义
    agents_md: str = ""  # 工作流程定义
    security: SecurityProfile = field(default_factory=SecurityProfile)
    
    @classmethod
    def from_agency_files(cls, role_dir: Path) -> "Role":
        """从 Agency 文件导入角色"""
        soul_file = role_dir / "SOUL.md"
        agents_file = role_dir / "AGENTS.md"
        
        soul_md = soul_file.read_text() if soul_file.exists() else ""
        agents_md = agents_file.read_text() if agents_file.exists() else ""
        
        # 根据角色名称设置默认安全策略
        security = cls._get_default_security(role_dir.name)
        
        return cls(
            name=role_dir.name,
            display_name=role_dir.name.replace("-", " ").title(),
            soul_md=soul_md,
            agents_md=agents_md,
            security=security,
        )
    
    @staticmethod
    def _get_default_security(role_name: str) -> SecurityProfile:
        """根据角色类型获取默认安全策略"""
        # 安全审查角色 - 最严格
        if "security" in role_name or "audit" in role_name:
            return SecurityProfile(
                allowed_tools=["read", "web_search"],
                sandbox=True,
                network_policy="allow",
                max_execution_time=600,
            )
        
        # 代码编写角色 - 适度权限
        elif any(x in role_name for x in ["developer", "engineer", "architect"]):
            return SecurityProfile(
                allowed_tools=["read", "write", "web_search", "browser"],
                sandbox=True,
                network_policy="allow",
                max_execution_time=1800,
            )
        
        # 外部连接角色 - 需要网络
        elif any(x in role_name for x in ["marketing", "research", "analyst"]):
            return SecurityProfile(
                allowed_tools=["read", "write", "web_search", "browser", "exec"],
                sandbox=True,
                network_policy="allow",
                max_execution_time=1200,
            )
        
        # 默认安全策略
        return SecurityProfile()


@dataclass
class Task:
    """任务定义"""
    id: str
    title: str
    description: str = ""
    owner: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    priority: str = "medium"  # low | medium | high | critical
    depends_on: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None
    result: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "owner": self.owner,
            "status": self.status.value,
            "priority": self.priority,
            "depends_on": self.depends_on,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "result": self.result,
        }


@dataclass
class TeamMember:
    """团队成员"""
    role: Role
    name: str
    session_key: Optional[str] = None
    status: MemberStatus = MemberStatus.IDLE
    current_task: Optional[str] = None
    joined_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role.name,
            "name": self.name,
            "session_key": self.session_key,
            "status": self.status.value,
            "current_task": self.current_task,
            "joined_at": self.joined_at,
        }


@dataclass
class Team:
    """团队定义"""
    name: str
    description: str
    leader: str
    members: List[TeamMember] = field(default_factory=list)
    tasks: List[Task] = field(default_factory=list)
    workspace_dir: Path = field(default_factory=lambda: Path.home() / ".antmeta" / "teams" / "default")
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "leader": self.leader,
            "members": [m.to_dict() for m in self.members],
            "tasks": [t.to_dict() for t in self.tasks],
            "workspace_dir": str(self.workspace_dir),
            "created_at": self.created_at,
        }
    
    def get_member(self, name: str) -> Optional[TeamMember]:
        """获取指定名称的成员"""
        for member in self.members:
            if member.name == name:
                return member
        return None
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """获取指定 ID 的任务"""
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None
