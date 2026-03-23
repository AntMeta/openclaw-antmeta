"""
蚁元 / AntMeta - 安全的 OpenClaw 多代理团队系统
Safe Multi-Agent Team System for OpenClaw

核心理念:
- 蚁: 像蚂蚁一样简单、协作的 Agent 单元
- 元: 元级(Meta)协调，基础单元构建复杂系统
"""

__version__ = "0.1.0"
__author__ = "AntMeta Contributors"

from antmeta.core.team import Team
from antmeta.core.member import TeamMember
from antmeta.core.role import Role
from antmeta.orchestrator import Orchestrator

__all__ = [
    "Team",
    "TeamMember", 
    "Role",
    "Orchestrator",
]
