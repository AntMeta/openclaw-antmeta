"""
编排器 - 核心协调逻辑
"""

import html
import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from antmeta.core import (
    Team, TeamMember, Task, Role, 
    TaskStatus, MemberStatus, SecurityProfile
)
from antmeta.core.team import TeamManager


class Orchestrator:
    """
    蚁元编排器
    
    协调多 Agent 团队的安全执行
    """
    
    # 安全常量
    MAX_SOUL_MD_LENGTH = 10000
    MAX_AGENTS_MD_LENGTH = 10000
    MAX_TASK_LENGTH = 5000
    MAX_MESSAGE_LENGTH = 5000
    
    def __init__(self, data_dir: Optional[Path] = None):
        self.team_manager = TeamManager(data_dir)
        self.active_sessions: Dict[str, Any] = {}  # 存储活跃的子会话
    
    def create_team(
        self, 
        name: str, 
        description: str = "",
        leader: str = "default"
    ) -> Team:
        """
        创建新团队
        
        Args:
            name: 团队名称
            description: 团队描述
            leader: 团队负责人
            
        Returns:
            创建的团队对象
        """
        team = self.team_manager.create_team(name, description, leader)
        
        # 记录审计日志
        self._log_audit_event(name, "team_created", f"Team '{name}' created by {leader}")
        
        return team
    
    def add_member(
        self,
        team_name: str,
        role: Role,
        member_name: str,
        task: str,
        security_override: Optional[Dict] = None
    ) -> TeamMember:
        """
        添加团队成员（启动隔离子会话）
        
        这是蚁元的核心安全机制：
        - 每个成员在独立的 sessions_spawn 中运行
        - 完全隔离的上下文和权限
        - 可配置的安全策略
        
        Args:
            team_name: 团队名称
            role: 角色定义
            member_name: 成员实例名称
            task: 分配的任务描述
            security_override: 安全策略覆盖
            
        Returns:
            创建的团队成员
        """
        # 加载团队
        team = self.team_manager.load_team(team_name)
        if not team:
            raise ValueError(f"Team '{team_name}' not found")
        
        # 合并安全策略
        security = role.security
        if security_override:
            for key, value in security_override.items():
                setattr(security, key, value)
        
        # 创建工作目录（安全权限）
        member_workspace = team.workspace_dir / member_name
        member_workspace.mkdir(exist_ok=True)
        # 设置目录权限为仅所有者可读写执行
        os.chmod(member_workspace, 0o700)
        
        # 准备子会话环境
        env = self._prepare_session_env(team, role, member_name, task, security)
        
        # 构建任务提示（注入角色定义）- 已清理防止注入
        prompt = self._build_task_prompt(role, task, team.name)
        
        # 启动隔离子会话
        # 注意：这里模拟 sessions_spawn 调用
        # 实际实现需要集成 OpenClaw 的 sessions_spawn
        session_key = f"{team_name}-{member_name}-{uuid.uuid4().hex[:8]}"
        
        # 在实际实现中，这里应该调用：
        # result = sessions_spawn(
        #     task=prompt,
        #     runtime="subagent",
        #     mode="session",
        #     label=session_key,
        #     timeout_seconds=security.max_execution_time,
        #     env=env,
        #     sandbox="require" if security.sandbox else "optional"
        # )
        
        # 创建成员记录
        member = TeamMember(
            role=role,
            name=member_name,
            session_key=session_key,
            status=MemberStatus.WORKING,
            current_task=task,
        )
        
        # 更新团队
        team.members.append(member)
        self.team_manager.save_team(team)
        
        # 记录到活跃会话
        self.active_sessions[session_key] = {
            "team": team_name,
            "member": member_name,
            "task": task,
            "workspace": str(member_workspace),
        }
        
        # 记录审计日志
        self._log_audit_event(
            team_name, 
            "member_added", 
            f"Member '{member_name}' with role '{role.name}' added"
        )
        
        return member
    
    def send_message(
        self,
        team_name: str,
        to_member: str,
        message: str,
        message_type: str = "task"
    ) -> bool:
        """
        向团队成员发送消息
        
        使用 OpenClaw 的 sessions_send 机制
        """
        team = self.team_manager.load_team(team_name)
        if not team:
            return False
        
        member = team.get_member(to_member)
        if not member or not member.session_key:
            return False
        
        # 清理消息防止注入
        safe_message = self._sanitize_message(message)
        
        # 实际实现中调用 sessions_send
        # sessions_send(
        #     session_key=member.session_key,
        #     message=f"[{message_type}] {safe_message}"
        # )
        
        # 记录到团队日志
        self._log_message(team_name, to_member, safe_message, message_type)
        return True
    
    def broadcast(
        self,
        team_name: str,
        message: str,
        message_type: str = "announcement"
    ) -> int:
        """向团队所有成员广播消息"""
        team = self.team_manager.load_team(team_name)
        if not team:
            return 0
        
        # 清理消息
        safe_message = self._sanitize_message(message)
        
        count = 0
        for member in team.members:
            if member.session_key and member.status == MemberStatus.WORKING:
                if self.send_message(team_name, member.name, safe_message, message_type):
                    count += 1
        
        return count
    
    def get_member_status(
        self,
        team_name: str,
        member_name: str
    ) -> Optional[Dict[str, Any]]:
        """获取成员当前状态"""
        team = self.team_manager.load_team(team_name)
        if not team:
            return None
        
        member = team.get_member(member_name)
        if not member:
            return None
        
        # 在实际实现中，这里应该查询子会话状态
        # history = sessions_history(
        #     session_key=member.session_key,
        #     limit=50
        # )
        
        return {
            "member": member_name,
            "role": member.role.name,
            "status": member.status.value,
            "task": member.current_task,
            "joined_at": member.joined_at,
            # "recent_history": history,
        }
    
    def orchestrate_parallel(self, team_name: str) -> List[Dict[str, Any]]:
        """
        并行编排 - 所有成员同时工作
        
        这是蚁元的主要工作模式：
        所有子会话已在各自的隔离环境中并行运行
        这里只是监控和收集结果
        """
        team = self.team_manager.load_team(team_name)
        if not team:
            return []
        
        results = []
        for member in team.members:
            status = self.get_member_status(team_name, member.name)
            if status:
                results.append(status)
        
        # 记录审计日志
        self._log_audit_event(team_name, "parallel_orchestration", f"Collected {len(results)} member statuses")
        
        return results
    
    def orchestrate_sequential(
        self,
        team_name: str,
        order: List[str]
    ) -> List[Dict[str, Any]]:
        """
        顺序编排 - 按指定顺序执行
        
        等待前一个成员完成后再启动下一个
        """
        results = []
        for member_name in order:
            # 等待成员完成
            # 实际实现中需要轮询或事件通知
            status = self.get_member_status(team_name, member_name)
            if status:
                results.append(status)
        
        # 记录审计日志
        self._log_audit_event(team_name, "sequential_orchestration", f"Executed {len(results)} members in sequence")
        
        return results
    
    def _sanitize_message(self, message: str) -> str:
        """
        清理消息内容，防止注入攻击
        
        Args:
            message: 原始消息
            
        Returns:
            清理后的安全消息
        """
        if not message:
            return ""
        
        # 截断超长消息
        if len(message) > self.MAX_MESSAGE_LENGTH:
            message = message[:self.MAX_MESSAGE_LENGTH - 3] + "..."
        
        # HTML 转义防止注入
        return html.escape(message)
    
    def _prepare_session_env(
        self,
        team: Team,
        role: Role,
        member_name: str,
        task: str,
        security: SecurityProfile
    ) -> Dict[str, str]:
        """准备子会话环境变量"""
        # 清理角色定义防止注入
        safe_soul = html.escape(role.soul_md[:self.MAX_SOUL_MD_LENGTH])
        safe_agents = html.escape(role.agents_md[:self.MAX_AGENTS_MD_LENGTH])
        
        env = {
            # 团队信息
            "ANTMETA_TEAM": html.escape(team.name),
            "ANTMETA_MEMBER": html.escape(member_name),
            "ANTMETA_ROLE": html.escape(role.name),
            "ANTMETA_TASK": html.escape(task[:self.MAX_TASK_LENGTH]),
            "ANTMETA_WORKSPACE": str(team.workspace_dir / member_name),
            
            # 角色定义（已清理）
            "ANTMETA_ROLE_SOUL": safe_soul,
            "ANTMETA_ROLE_AGENTS": safe_agents,
            
            # 安全策略
            **security.to_env_dict(),
        }
        
        # 添加原始环境变量（需要保留的）
        for key in ["HOME", "USER", "PATH", "PYTHONPATH"]:
            if key in os.environ:
                env[key] = os.environ[key]
        
        return env
    
    def _build_task_prompt(
        self,
        role: Role,
        task: str,
        team_name: str
    ) -> str:
        """构建注入角色定义的任务提示（已清理防止注入）"""
        # 清理所有输入
        safe_soul = html.escape(role.soul_md[:self.MAX_SOUL_MD_LENGTH])
        safe_agents = html.escape(role.agents_md[:self.MAX_AGENTS_MD_LENGTH])
        safe_task = html.escape(task[:self.MAX_TASK_LENGTH])
        safe_team = html.escape(team_name)
        
        return f"""# 蚁元 / AntMeta - 团队任务

你现在是团队 "{safe_team}" 的一员，扮演以下角色：

## 🎭 角色身份 / Role Identity

{safe_soul}

## 📋 工作流程 / Workflow

{safe_agents}

## 🎯 当前任务 / Current Task

{safe_task}

## 💬 协调指令 / Coordination Protocol

作为蚁元团队成员，你需要：

1. **检查任务**: 使用环境变量或上下文了解当前状态
2. **报告进度**: 完成后向团队负责人报告结果
3. **协作沟通**: 如需要与其他成员协作，通过消息系统
4. **安全执行**: 严格遵守安全策略，只在授权范围内操作

## 🚀 开始执行

现在请开始执行你的任务。记住：
- 你是团队的一部分，简单但协作产生复杂能力
- 安全优先，权限明确
- 结果导向，及时汇报

开始工作！
"""
    
    def _log_message(
        self,
        team_name: str,
        to_member: str,
        message: str,
        message_type: str
    ) -> None:
        """记录消息到团队日志（安全权限）"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "to": to_member,
            "type": message_type,
            "message": message[:500],  # 截断长消息
        }
        
        log_file = self.team_manager.data_dir / team_name / "logs" / "messages.jsonl"
        log_file.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        
        with open(log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
        
        # 设置日志文件权限为仅所有者可读写
        os.chmod(log_file, 0o600)
    
    def _log_audit_event(
        self,
        team_name: str,
        event_type: str,
        description: str
    ) -> None:
        """
        记录审计日志
        
        Args:
            team_name: 团队名称
            event_type: 事件类型
            description: 事件描述
        """
        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "team": team_name,
            "event_type": event_type,
            "description": description,
        }
        
        audit_file = self.team_manager.data_dir / team_name / "logs" / "audit.jsonl"
        audit_file.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        
        with open(audit_file, "a") as f:
            f.write(json.dumps(audit_entry) + "\n")
        
        # 设置审计日志文件权限
        os.chmod(audit_file, 0o600)
