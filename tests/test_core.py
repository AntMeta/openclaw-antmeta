"""
AntMeta 测试套件
"""

import pytest
from pathlib import Path
import tempfile
import shutil

from antmeta.core import (
    Team, TeamMember, Task, Role, 
    TaskStatus, MemberStatus, SecurityProfile
)
from antmeta.core.team import TeamManager


class TestSecurityProfile:
    """安全策略测试"""
    
    def test_default_security(self):
        """测试默认安全策略"""
        security = SecurityProfile()
        assert "read" in security.allowed_tools
        assert security.sandbox is True
        assert security.network_policy == "allow"
    
    def test_to_env_dict(self):
        """测试环境变量转换"""
        security = SecurityProfile(
            allowed_tools=["read", "write"],
            sandbox=False
        )
        env = security.to_env_dict()
        assert "ANTMETA_ALLOWED_TOOLS" in env
        assert env["ANTMETA_SANDBOX"] == "false"


class TestRole:
    """角色测试"""
    
    def test_role_creation(self):
        """测试角色创建"""
        role = Role(
            name="test-role",
            display_name="Test Role",
            soul_md="Test soul",
            agents_md="Test agents"
        )
        assert role.name == "test-role"
        assert role.emoji == "🐜"  # 默认图标
    
    def test_default_security_by_role_type(self):
        """测试根据角色类型分配默认安全策略"""
        # 安全审查角色
        security_role = Role._get_default_security("security-engineer")
        assert "write" not in security_role.allowed_tools
        
        # 开发者角色
        dev_role = Role._get_default_security("frontend-developer")
        assert "write" in dev_role.allowed_tools


class TestTeamManager:
    """团队管理器测试"""
    
    @pytest.fixture
    def temp_dir(self):
        """临时目录 fixture"""
        temp = tempfile.mkdtemp()
        yield Path(temp)
        shutil.rmtree(temp)
    
    def test_create_team(self, temp_dir):
        """测试创建团队"""
        manager = TeamManager(temp_dir)
        team = manager.create_team("test-team", "Test description")
        
        assert team.name == "test-team"
        assert team.description == "Test description"
        assert (temp_dir / "test-team" / "team.json").exists()
    
    def test_create_duplicate_team(self, temp_dir):
        """测试创建重复团队应失败"""
        manager = TeamManager(temp_dir)
        manager.create_team("test-team")
        
        with pytest.raises(FileExistsError):
            manager.create_team("test-team")
    
    def test_load_team(self, temp_dir):
        """测试加载团队"""
        manager = TeamManager(temp_dir)
        manager.create_team("test-team", "Test")
        
        loaded = manager.load_team("test-team")
        assert loaded is not None
        assert loaded.name == "test-team"
    
    def test_load_nonexistent_team(self, temp_dir):
        """测试加载不存在的团队"""
        manager = TeamManager(temp_dir)
        loaded = manager.load_team("nonexistent")
        assert loaded is None
    
    def test_list_teams(self, temp_dir):
        """测试列出团队"""
        manager = TeamManager(temp_dir)
        manager.create_team("team-a")
        manager.create_team("team-b")
        
        teams = manager.list_teams()
        assert "team-a" in teams
        assert "team-b" in teams
    
    def test_delete_team(self, temp_dir):
        """测试删除团队"""
        manager = TeamManager(temp_dir)
        manager.create_team("test-team")
        
        success = manager.delete_team("test-team", force=True)
        assert success is True
        assert not (temp_dir / "test-team").exists()
    
    def test_add_task(self, temp_dir):
        """测试添加任务"""
        manager = TeamManager(temp_dir)
        manager.create_team("test-team")
        
        task = Task(
            id="task-1",
            title="Test task",
            owner="alice"
        )
        
        success = manager.add_task("test-team", task)
        assert success is True
        
        team = manager.load_team("test-team")
        assert len(team.tasks) == 1
        assert team.tasks[0].title == "Test task"


class TestTaskDependencies:
    """任务依赖测试"""
    
    @pytest.fixture
    def manager(self):
        """带团队的 Manager fixture"""
        temp = tempfile.mkdtemp()
        manager = TeamManager(Path(temp))
        manager.create_team("dep-team")
        
        yield manager
        shutil.rmtree(temp)
    
    def test_task_dependency_blocking(self, manager):
        """测试任务依赖阻塞"""
        # 创建任务 A
        task_a = Task(id="task-a", title="Task A")
        manager.add_task("dep-team", task_a)
        
        # 创建任务 B，依赖任务 A
        task_b = Task(
            id="task-b",
            title="Task B",
            depends_on=["task-a"],
            status=TaskStatus.BLOCKED
        )
        manager.add_task("dep-team", task_b)
        
        # 完成任务 A
        manager.update_task_status("dep-team", "task-a", TaskStatus.COMPLETED)
        
        # 任务 B 应该被解锁
        team = manager.load_team("dep-team")
        task_b_updated = team.get_task("task-b")
        assert task_b_updated.status == TaskStatus.PENDING


class TestTeamMember:
    """团队成员测试"""
    
    def test_member_creation(self):
        """测试成员创建"""
        role = Role(name="test-role", display_name="Test")
        member = TeamMember(role=role, name="alice")
        
        assert member.name == "alice"
        assert member.status == MemberStatus.IDLE
        assert member.role.name == "test-role"
    
    def test_member_to_dict(self):
        """测试成员序列化"""
        role = Role(name="test-role", display_name="Test")
        member = TeamMember(
            role=role,
            name="alice",
            status=MemberStatus.WORKING,
            current_task="Test task"
        )
        
        data = member.to_dict()
        assert data["name"] == "alice"
        assert data["status"] == "working"
        assert data["current_task"] == "Test task"


class TestIntegration:
    """集成测试"""
    
    @pytest.fixture
    def setup(self):
        """完整测试环境"""
        temp = tempfile.mkdtemp()
        data_dir = Path(temp)
        
        manager = TeamManager(data_dir)
        team = manager.create_team("integration-team", "Test team")
        
        yield {
            "manager": manager,
            "team": team,
            "data_dir": data_dir
        }
        
        shutil.rmtree(temp)
    
    def test_full_workflow(self, setup):
        """测试完整工作流"""
        manager = setup["manager"]
        team_name = "integration-team"
        
        # 1. 创建任务
        task = Task(id="task-1", title="Implement feature", owner="alice")
        manager.add_task(team_name, task)
        
        # 2. 添加成员
        role = Role(name="developer", display_name="Developer")
        member = TeamMember(role=role, name="alice", current_task="task-1")
        team = manager.load_team(team_name)
        team.members.append(member)
        manager.save_team(team)
        
        # 3. 更新任务状态
        manager.update_task_status(team_name, "task-1", TaskStatus.COMPLETED, "Done!")
        
        # 4. 验证
        team = manager.load_team(team_name)
        assert team.get_task("task-1").status == TaskStatus.COMPLETED
        assert team.get_task("task-1").result == "Done!"
