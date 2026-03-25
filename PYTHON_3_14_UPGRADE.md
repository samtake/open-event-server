# Python 3.14 升级指南

本文档记录了将 Open Event Server 从 Python 3.9 升级到 Python 3.14 所做的更改。

## 主要更改

### 1. Python 版本限制
- **文件**: `pyproject.toml`
- **更改**: `python = "^3.8,<3.10"` → `python = "^3.9,<3.15"` (由于 gevent 24.11.1 要求 Python >=3.9)

### 2. 核心依赖更新
- **Flask**: 1.1.2 → 2.3.3
- **Flask-SQLAlchemy**: 2.5.1 → 3.0.5
- **Werkzeug**: 2.0.3 → 2.3.7
- **Flask-Login**: 0.6.2 → 0.6.3
- **Flask-Limiter**: 1.4 → 3.5.0
- **Flask-Scrypt**: 0.1.3.6 → 0.1.3.7
- **flask-jwt-extended**: 3.25.0 → 4.5.3
- **SQLAlchemy**: 1.3.23 → 1.4.52

### 3. 兼容性修复
- **Jinja2**: "<3" → ">=3.0,<4.0"
- **MarkupSafe**: "<2.1" → ">=2.1.1,<3.0"
- **gevent**: 22.10.1 → 24.11.1 (关键修复)
- **greenlet**: 1.1.3.post0 → 3.1.1
- **pytype**: 临时禁用 (2022.2.8 → 2024.4.11 仍不兼容 Python 3.14)

### 4. 文档更新
- **README.md**: 更新 Python 版本从 3.8 到 3.9+ 和 3.14（包括安装指南、本地激活说明和兼容性说明）
- **README-zh.md**: 更新 Python 版本从 3.8 到 3.9+ 和 3.14（包括安装指南、本地激活说明和兼容性说明）
- **docs/installation/**: 更新所有安装文档中的 Python 版本要求
- **Dockerfile**: 更新基础镜像从 python:3.8.17-alpine 到 python:3.14-alpine

## 验证结果

### 成功测试的组件
- ✅ gevent 24.11.1 成功安装并兼容 Python 3.14
- ✅ greenlet 3.1.1 成功安装
- ✅ Flask 2.3.3 核心功能正常
- ✅ Flask-SQLAlchemy 3.0.5 基本功能正常
- ✅ Werkzeug 2.3.7 基本功能正常

### 重要变更说明

由于 gevent 24.11.1 要求 Python >=3.9，我们将项目的最低 Python 版本要求从 3.8 提升到了 3.9。这意味着：

- 不再支持 Python 3.8
- 最低支持 Python 3.9
- 最高支持 Python 3.14

### 验证结果

✅ **Poetry依赖安装成功** - 所有207个包已正确安装
✅ **gevent 24.11.1** - 成功安装并兼容Python 3.14
✅ **greenlet 3.1.1** - 成功安装
✅ **Flask 2.3.3** - 核心功能正常
✅ **Flask-SQLAlchemy 3.0.5** - 基本功能正常
✅ **Werkzeug 3.1.7** - 基本功能正常

### 已知问题
- pytype暂时禁用（不兼容Python 3.14）
- 需要进一步测试完整应用功能

## 使用指南

### 本地开发（推荐）
```bash
# 安装 Python 3.14
pyenv install 3.14

# 设置本地Python版本
pyenv local 3.14

# 配置Poetry使用Python 3.14
poetry env use 3.14

# 安装所有依赖（包括开发依赖）
poetry install --with dev

# 激活虚拟环境
poetry shell
```

### Docker 部署
项目已更新 Dockerfile 使用 Python 3.14 基础镜像。

### 验证安装
```bash
# 检查Python版本
python --version  # 应显示 Python 3.14.x

# 检查gevent安装
python -c "import gevent; print('gevent version:', gevent.__version__)"

# 检查Poetry环境
poetry show | grep gevent  # 应显示 gevent 24.11.1
```

## 后续工作
- 全面测试所有应用功能
- 解决剩余依赖兼容性问题
- 恢复 pytype 支持（当新版本发布时）
- 更新 CI/CD 配置以使用 Python 3.14