# 贡献指南

感谢您对蚁元 / AntMeta 的兴趣！

## 开发环境设置

```bash
# 克隆仓库
git clone https://github.com/AntMeta/openclaw-antmeta.git
cd openclaw-antmeta

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装开发依赖
pip install -e ".[dev]"
```

## 代码规范

### 格式化

使用 black 格式化代码：

```bash
black src/ tests/
```

### 类型检查

```bash
mypy src/
```

### 代码检查

```bash
ruff check src/
```

### 测试

```bash
pytest tests/ -v
```

## 提交规范

使用 [Conventional Commits](https://www.conventionalcommits.org/) 格式：

```
feat: 添加新功能
fix: 修复 bug
docs: 更新文档
style: 代码格式调整
refactor: 重构代码
test: 添加测试
chore: 构建/工具调整
```

## 拉取请求流程

1. Fork 仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'feat: Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 报告问题

请使用 GitHub Issues 报告问题，包含：
- 问题描述
- 复现步骤
- 期望行为
- 实际行为
- 环境信息（Python 版本、操作系统）

## 许可证

通过贡献代码，您同意将您的贡献在 MIT 许可证下发布。
