"""
示例：全栈 Web 应用开发团队

本示例演示如何使用蚁元创建一个全栈开发团队
"""

from antmeta.orchestrator import Orchestrator
from antmeta.role_loader import RoleLoader


def main():
    """创建并运行一个全栈开发团队"""
    
    # 初始化组件
    orchestrator = Orchestrator()
    role_loader = RoleLoader()
    
    # 1. 创建团队
    print("🐜 创建团队: webapp-project")
    team = orchestrator.create_team(
        name="webapp-project",
        description="构建一个全栈待办事项应用",
        leader="user"
    )
    print(f"   工作目录: {team.workspace_dir}")
    
    # 2. 加载角色
    print("\n📋 加载角色定义...")
    
    frontend_role = role_loader.load_role("frontend-developer")
    backend_role = role_loader.load_role("backend-architect")  # 从 Agency
    security_role = role_loader.load_role("security-engineer")  # 从 Agency
    
    # 3. 添加团队成员
    print("\n👥 添加团队成员:")
    
    # 前端开发者
    print("   - Alice (Frontend Developer)")
    orchestrator.add_member(
        team_name="webapp-project",
        role=frontend_role,
        member_name="alice",
        task="构建 React 前端界面，包括登录、待办列表、添加/编辑任务功能",
        security_override={"max_execution_time": 1800}
    )
    
    # 后端架构师
    print("   - Bob (Backend Architect)")
    orchestrator.add_member(
        team_name="webapp-project",
        role=backend_role,
        member_name="bob",
        task="设计 RESTful API，实现用户认证、数据持久化、API 文档",
        security_override={"max_execution_time": 1800}
    )
    
    # 安全工程师
    print("   - Carol (Security Engineer)")
    orchestrator.add_member(
        team_name="webapp-project",
        role=security_role,
        member_name="carol",
        task="审查认证流程安全性，检查 SQL 注入和 XSS 漏洞，评估 API 安全",
        security_override={"allowed_tools": ["read", "web_search"]}  # 严格限制
    )
    
    # 4. 启动并行执行
    print("\n🚀 启动并行开发...")
    print("   所有成员已在各自的隔离环境中开始工作")
    
    # 在实际场景中，这里应该监控进度
    # 为演示目的，仅显示当前状态
    print("\n📊 团队状态:")
    
    import time
    time.sleep(2)  # 模拟等待
    
    for member_name in ["alice", "bob", "carol"]:
        status = orchestrator.get_member_status("webapp-project", member_name)
        if status:
            print(f"   - {member_name}: {status['status']} ({status['role']})")
    
    # 5. 模拟协调
    print("\n💬 团队协调:")
    print("   - Bob 完成 API 设计，通知 Alice")
    orchestrator.send_message(
        team_name="webapp-project",
        to_member="alice",
        message="API 设计完成，端点: /api/auth/*, /api/todos/*",
        message_type="info"
    )
    
    print("   - Alice 收到通知，开始对接")
    print("   - Carol 定期审查代码安全")
    
    # 6. 收集结果
    print("\n📈 收集结果...")
    results = orchestrator.orchestrate_parallel("webapp-project")
    
    print(f"\n✅ 团队执行完成！共 {len(results)} 个成员参与")
    
    # 7. 清理（可选）
    print("\n🧹 清理资源...")
    # orchestrator.team_manager.delete_team("webapp-project", force=True)
    
    print("\n🎉 示例完成！")
    print(f"   查看工作目录: {team.workspace_dir}")


if __name__ == "__main__":
    main()
