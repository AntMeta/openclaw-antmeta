"""
团队管理核心逻辑
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from antmeta.core import Team, TeamMember, Task, Role, TaskStatus, MemberStatus


class TeamManager:
    """团队管理器"""
    
    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = Path(data_dir or Path.home() / ".antmeta" / "teams")
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def create_team(self, name: str, description: str = "", leader: str = "default") -> Team:
        """创建新团队"""
        # 创建团队目录
        team_dir = self.data_dir / name
        team_dir.mkdir(exist_ok=False)
        
        # 创建工作空间
        workspace = team_dir / "workspace"
        workspace.mkdir()
        
        # 创建日志目录
        logs = team_dir / "logs"
        logs.mkdir()
        
        # 创建团队
        team = Team(
            name=name,
            description=description,
            leader=leader,
            workspace_dir=workspace,
        )
        
        # 保存团队配置
        self._save_team(team)
        
        return team
    
    def load_team(self, name: str) -> Optional[Team]:
        """加载团队"""
        team_file = self.data_dir / name / "team.json"
        if not team_file.exists():
            return None
        
        with open(team_file, "r") as f:
            data = json.load(f)
        
        # 重建团队成员
        members = []
        for m_data in data.get("members", []):
            # 简化版本，实际需要加载完整的 Role
            member = TeamMember(
                role=Role(name=m_data["role"], display_name=m_data["role"]),
                name=m_data["name"],
                session_key=m_data.get("session_key"),
                status=MemberStatus(m_data["status"]),
                current_task=m_data.get("current_task"),
                joined_at=m_data.get("joined_at", datetime.now().isoformat()),
            )
            members.append(member)
        
        # 重建任务
        tasks = []
        for t_data in data.get("tasks", []):
            task = Task(
                id=t_data["id"],
                title=t_data["title"],
                description=t_data.get("description", ""),
                owner=t_data.get("owner"),
                status=TaskStatus(t_data["status"]),
                priority=t_data.get("priority", "medium"),
                depends_on=t_data.get("depends_on", []),
                created_at=t_data.get("created_at", datetime.now().isoformat()),
                completed_at=t_data.get("completed_at"),
                result=t_data.get("result"),
            )
            tasks.append(task)
        
        return Team(
            name=data["name"],
            description=data.get("description", ""),
            leader=data.get("leader", "default"),
            members=members,
            tasks=tasks,
            workspace_dir=Path(data.get("workspace_dir", str(self.data_dir / name))),
            created_at=data.get("created_at", datetime.now().isoformat()),
        )
    
    def save_team(self, team: Team) -> None:
        """保存团队状态"""
        self._save_team(team)
    
    def _save_team(self, team: Team) -> None:
        """内部保存方法"""
        team_file = self.data_dir / team.name / "team.json"
        with open(team_file, "w") as f:
            json.dump(team.to_dict(), f, indent=2, default=str)
    
    def list_teams(self) -> List[str]:
        """列出所有团队"""
        teams = []
        for item in self.data_dir.iterdir():
            if item.is_dir() and (item / "team.json").exists():
                teams.append(item.name)
        return teams
    
    def delete_team(self, name: str, force: bool = False) -> bool:
        """删除团队"""
        team_dir = self.data_dir / name
        if not team_dir.exists():
            return False
        
        if not force:
            # 可以添加确认逻辑
            pass
        
        import shutil
        shutil.rmtree(team_dir)
        return True
    
    def add_task(self, team_name: str, task: Task) -> bool:
        """为团队添加任务"""
        team = self.load_team(team_name)
        if not team:
            return False
        
        team.tasks.append(task)
        self.save_team(team)
        return True
    
    def update_task_status(
        self, 
        team_name: str, 
        task_id: str, 
        status: TaskStatus,
        result: Optional[str] = None
    ) -> bool:
        """更新任务状态"""
        team = self.load_team(team_name)
        if not team:
            return False
        
        task = team.get_task(task_id)
        if not task:
            return False
        
        task.status = status
        if status == TaskStatus.COMPLETED:
            task.completed_at = datetime.now().isoformat()
            task.result = result
            
            # 解锁依赖于此任务的其他任务
            self._unblock_dependent_tasks(team, task_id)
        
        self.save_team(team)
        return True
    
    def _unblock_dependent_tasks(self, team: Team, completed_task_id: str) -> None:
        """解锁依赖于已完成任务的被阻塞任务"""
        for task in team.tasks:
            if task.status == TaskStatus.BLOCKED:
                if completed_task_id in task.depends_on:
                    # 检查所有依赖是否都已完成
                    all_completed = all(
                        team.get_task(dep_id) and 
                        team.get_task(dep_id).status == TaskStatus.COMPLETED
                        for dep_id in task.depends_on
                    )
                    if all_completed:
                        task.status = TaskStatus.PENDING
