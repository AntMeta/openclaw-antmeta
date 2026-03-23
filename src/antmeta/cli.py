"""
命令行界面
"""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from antmeta import __version__
from antmeta.orchestrator import Orchestrator
from antmeta.role_loader import RoleLoader
from antmeta.core import Role, Task

app = typer.Typer(
    name="antmeta",
    help="蚁元 / AntMeta - 安全的 OpenClaw 多代理团队系统",
    add_completion=False,
)
console = Console()


@app.callback()
def main():
    """蚁元 - 像蚂蚁一样协作的多代理系统"""
    pass


@app.command()
def version():
    """显示版本信息"""
    console.print(Panel.fit(
        f"[bold cyan]蚁元 / AntMeta[/bold cyan]\n"
        f"版本: {__version__}\n"
        f"安全的 OpenClaw 多代理团队系统",
        title="🐜 AntMeta",
        border_style="green"
    ))


@app.command()
def list_roles():
    """列出所有可用角色"""
    loader = RoleLoader()
    roles = loader.list_available_roles()
    
    table = Table(title="可用角色 / Available Roles")
    table.add_column("序号", style="cyan", justify="right")
    table.add_column("角色名称", style="green")
    table.add_column("来源", style="yellow")
    
    agency_dir = Path.home() / ".openclaw" / "agency-agents"
    
    for i, role in enumerate(roles, 1):
        source = "内置" if (loader.roles_dir / f"{role}.yaml").exists() else "Agency"
        table.add_row(str(i), role, source)
    
    console.print(table)
    console.print(f"\n共 {len(roles)} 个角色可用")


@app.command()
def create_team(
    name: str = typer.Argument(..., help="团队名称"),
    description: str = typer.Option("", "--description", "-d", help="团队描述"),
):
    """创建新团队"""
    orchestrator = Orchestrator()
    
    try:
        team = orchestrator.create_team(name, description)
        console.print(f"[green]✅ 团队 '{name}' 创建成功！[/green]")
        console.print(f"   工作目录: {team.workspace_dir}")
    except FileExistsError:
        console.print(f"[red]❌ 团队 '{name}' 已存在[/red]")
        raise typer.Exit(1)


@app.command()
def list_teams():
    """列出所有团队"""
    orchestrator = Orchestrator()
    teams = orchestrator.team_manager.list_teams()
    
    if not teams:
        console.print("[yellow]暂无团队，使用 `antmeta create-team` 创建一个[/yellow]")
        return
    
    table = Table(title="团队列表 / Teams")
    table.add_column("名称", style="cyan")
    table.add_column("成员数", style="green", justify="right")
    table.add_column("任务数", style="blue", justify="right")
    
    for team_name in teams:
        team = orchestrator.team_manager.load_team(team_name)
        if team:
            table.add_row(
                team_name,
                str(len(team.members)),
                str(len(team.tasks))
            )
    
    console.print(table)


@app.command()
def add_member(
    team: str = typer.Argument(..., help="团队名称"),
    role: str = typer.Argument(..., help="角色名称"),
    name: str = typer.Argument(..., help="成员名称"),
    task: str = typer.Argument(..., help="任务描述"),
):
    """向团队添加成员"""
    orchestrator = Orchestrator()
    loader = RoleLoader()
    
    # 加载角色
    role_obj = loader.load_role(role)
    if not role_obj:
        console.print(f"[red]❌ 角色 '{role}' 不存在[/red]")
        console.print("使用 `antmeta list-roles` 查看可用角色")
        raise typer.Exit(1)
    
    try:
        member = orchestrator.add_member(team, role_obj, name, task)
        console.print(f"[green]✅ 成员 '{name}' 已添加到团队 '{team}'[/green]")
        console.print(f"   角色: {role}")
        console.print(f"   任务: {task}")
        console.print(f"   会话: {member.session_key}")
    except ValueError as e:
        console.print(f"[red]❌ {e}[/red]")
        raise typer.Exit(1)


@app.command()
def status(
    team: str = typer.Argument(..., help="团队名称"),
):
    """查看团队状态"""
    orchestrator = Orchestrator()
    team_obj = orchestrator.team_manager.load_team(team)
    
    if not team_obj:
        console.print(f"[red]❌ 团队 '{team}' 不存在[/red]")
        raise typer.Exit(1)
    
    # 团队信息
    console.print(Panel(
        f"[bold]{team_obj.name}[/bold]\n"
        f"{team_obj.description or '无描述'}\n"
        f"创建时间: {team_obj.created_at}",
        title="团队信息",
        border_style="blue"
    ))
    
    # 成员列表
    if team_obj.members:
        member_table = Table(title="团队成员")
        member_table.add_column("名称", style="cyan")
        member_table.add_column("角色", style="green")
        member_table.add_column("状态", style="yellow")
        member_table.add_column("当前任务", style="blue")
        
        for m in team_obj.members:
            member_table.add_row(
                m.name,
                m.role.name,
                m.status.value,
                m.current_task or "-"
            )
        console.print(member_table)
    else:
        console.print("[yellow]暂无成员[/yellow]")
    
    # 任务列表
    if team_obj.tasks:
        task_table = Table(title="团队任务")
        task_table.add_column("ID", style="cyan")
        task_table.add_column("标题", style="green")
        task_table.add_column("负责人", style="yellow")
        task_table.add_column("状态", style="blue")
        
        for t in team_obj.tasks:
            task_table.add_row(
                t.id,
                t.title,
                t.owner or "-",
                t.status.value
            )
        console.print(task_table)
    else:
        console.print("[yellow]暂无任务[/yellow]")


@app.command()
def import_agency(
    dry_run: bool = typer.Option(False, "--dry-run", help="仅预览，不实际导入"),
):
    """从 Agency 导入所有角色"""
    loader = RoleLoader()
    
    agency_dir = Path.home() / ".openclaw" / "agency-agents"
    if not agency_dir.exists():
        console.print(f"[yellow]⚠️ 未找到 Agency 目录: {agency_dir}[/yellow]")
        console.print("请先安装 Agency: git clone https://github.com/msitarzewski/agency-agents")
        raise typer.Exit(1)
    
    available = loader.list_available_roles()
    existing_yaml = list(loader.roles_dir.glob("*.yaml"))
    
    console.print(f"发现 {len(available)} 个可用角色")
    console.print(f"已有 {len(existing_yaml)} 个内置角色")
    
    if dry_run:
        console.print("[blue]--dry-run 模式，仅预览不导入[/blue]")
        return
    
    count = loader.import_all_agency_roles()
    console.print(f"[green]✅ 成功导入 {count} 个新角色[/green]")


def main_cli():
    """CLI 入口点"""
    app()


if __name__ == "__main__":
    main_cli()
