"""
角色加载器 - 从 Agency 导入角色定义
"""

import yaml
from pathlib import Path
from typing import List, Optional

from antmeta.core import Role


class RoleLoader:
    """角色加载器"""
    
    def __init__(self, roles_dir: Optional[Path] = None):
        # 优先使用项目内置角色，然后查找 Agency 角色
        self.roles_dir = roles_dir or Path(__file__).parent.parent.parent / "roles"
        self.agency_dir = Path.home() / ".openclaw" / "agency-agents"
    
    def list_available_roles(self) -> List[str]:
        """列出所有可用角色"""
        roles = set()
        
        # 从内置角色目录加载
        if self.roles_dir.exists():
            for f in self.roles_dir.glob("*.yaml"):
                roles.add(f.stem)
        
        # 从 Agency 目录加载
        if self.agency_dir.exists():
            for d in self.agency_dir.iterdir():
                if d.is_dir():
                    roles.add(d.name)
        
        return sorted(list(roles))
    
    def load_role(self, role_name: str) -> Optional[Role]:
        """加载指定角色"""
        # 1. 优先从内置 YAML 加载
        yaml_file = self.roles_dir / f"{role_name}.yaml"
        if yaml_file.exists():
            return self._load_from_yaml(yaml_file)
        
        # 2. 从 Agency 目录加载
        agency_dir = self.agency_dir / role_name
        if agency_dir.exists():
            return Role.from_agency_files(agency_dir)
        
        return None
    
    def _load_from_yaml(self, yaml_file: Path) -> Role:
        """从 YAML 文件加载角色"""
        with open(yaml_file, "r") as f:
            data = yaml.safe_load(f)
        
        role_data = data.get("role", {})
        
        return Role(
            name=role_data.get("name", yaml_file.stem),
            display_name=role_data.get("display_name", yaml_file.stem),
            emoji=role_data.get("emoji", "🐜"),
            soul_md=role_data.get("soul_md", ""),
            agents_md=role_data.get("agents_md", ""),
            # 可以扩展支持 YAML 中定义安全策略
        )
    
    def import_all_agency_roles(self) -> int:
        """导入所有 Agency 角色到本地 YAML"""
        if not self.agency_dir.exists():
            return 0
        
        count = 0
        for agent_dir in self.agency_dir.iterdir():
            if not agent_dir.is_dir():
                continue
            
            role = Role.from_agency_files(agent_dir)
            yaml_file = self.roles_dir / f"{role.name}.yaml"
            
            if not yaml_file.exists():  # 不覆盖已有角色
                self._save_role_to_yaml(role, yaml_file)
                count += 1
        
        return count
    
    def _save_role_to_yaml(self, role: Role, yaml_file: Path) -> None:
        """保存角色到 YAML 文件"""
        data = {
            "role": {
                "name": role.name,
                "display_name": role.display_name,
                "emoji": role.emoji,
                "soul_md": role.soul_md,
                "agents_md": role.agents_md,
            }
        }
        
        yaml_file.parent.mkdir(parents=True, exist_ok=True)
        with open(yaml_file, "w") as f:
            yaml.dump(data, f, allow_unicode=True, sort_keys=False)
