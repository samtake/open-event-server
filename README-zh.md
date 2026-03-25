
> **Open Event Server 使组织者能够管理从音乐会到会议和聚会的各种活动。**

它为多个议程和场地的活动提供功能。活动管理员可以为演讲者创建邀请表单，并在*拖放*界面中构建日程。活动信息存储在**数据库**中。该系统提供**API 端点**用于**获取**数据，以及**修改**和**更新**数据。组织者可以以一种标准的压缩文件格式导入和导出活动数据，该格式包含 **JSON** 数据以及诸如 **图片和音频** 等二进制媒体文件。

**Open Event Server** 提供一个良好记录的 [JSON:API 规范](http://jsonapi.org/) 兼容的 `REST API`，外部服务（例如 Open Event App 生成器和前端）可以使用该 API 访问和操作数据。

**API 文档：**
- 每个项目安装都附带 **API 文档**（例如测试安装：[https://open-event-api.herokuapp.com](https://open-event-api.herokuapp.com)）。
- **API 文档** 的托管版本位于仓库的 `gh-pages` 分支，地址为 [http://dev.eventyay.com/api/v1](http://dev.eventyay.com/api/v1)


## 开发

### 初始设置

#### Python 和 Poetry 安装

我们使用 Python 3.9+。如果你的操作系统默认不提供 Python 3.9+，最好使用 [`pyenv`](https://github.com/pyenv/pyenv/) 安装。

对于 Mac 用户，请参考 [这里](https://opensource.com/article/19/5/python-3-default-mac) 了解更多信息。
```bash
#安裝pyenv
brew install pyenv
# 按照指示将运行命令添加到你的环境中
pyenv init 
```
编辑环境文件后，重新加载 shell 并导航到此仓库，然后安装 `3.14` 以便在本地使用：
```bash
#安裝python版本
pyenv install 3.14 
#設置全局默认版本
pyenv global 3.14
#查看版本  
pyenv version 


cd ...your../open-event-server/
pyenv local 3.14
```
现在在 open-event-server 中使用时，Python 版本应会自动切换。

我们还希望 [poetry](https://python-poetry.org/) 可用。
```bash
brew install poetry
```

#### 依赖包设置

切换到 `open-event-server` 目录并执行以下命令：

激活本地 Python 3.14
```bash
pyenv local 3.14
```

使用 poetry 安装依赖
```bash
poetry install --with dev
```

激活 pre-commit 钩子
```bash
poetry run pre-commit install
```

这样每次 git 提交都会在提交之前由各种工具检查/格式化。

### 开发模式

要启用开发模式（Flask 开发配置），请将 `APP_CONFIG` 环境变量设置为 `config.DevelopmentConfig`。

```
export APP_CONFIG=config.DevelopmentConfig
```

### 模型更新与迁移

在修改模型时，请使用迁移。

```
 # 在模型更新后生成迁移
 python3 manage.py db migrate

 # 同步数据库
 python3 manage.py db upgrade

 # 回滚
 python3 manage.py db downgrade
```

在提交涉及模型的代码时，请同时更新迁移文件。

### API 文档

API 使用 [api blueprint](https://apiblueprint.org/) 进行文档编写。首先，使用以下命令生成描述/blueprint `.apib` 文件：

```bash
npx aglio --input docs/api/api_blueprint_source.apib --compile --output docs/api/api_blueprint.apib # 生成描述 .apib 文件
```

可以使用例如 [apiary gem](https://help.apiary.io/tools/apiary-cli/) 查看本地对描述的更改：

```bash
gem install apiaryio # 依赖
apiary preview --path docs/api/api_blueprint.apib # 在浏览器中打开生成文件
```

### 测试

克隆仓库并按照上述步骤设置服务器。确保已安装 [Poetry](https://python-poetry.org/docs) 并通过运行以下命令安装测试所需的所有依赖：

```
# 安装 Poetry
curl -sSL https://install.python-poetry.org | python -
source ~/.profile

# 安装 Python 依赖
poetry install

# 激活项目的虚拟环境
poetry shell
```

#### 运行单元测试

* 如果你安装了 docker 并希望更快地运行测试，请运行

```shell script
./scripts/test_db.sh
```

并在 `.env` 中为 `TEST_DATABASE` 设置适当的值

```shell script
TEST_DATABASE_URL=postgresql://test@localhost:5433/test
```

* 然后进入项目目录并运行以下命令：
```
pytest tests/
```

#### 运行机器人框架测试
* 确保已安装 FireFox
* 启动本地 flask 服务器实例。
* 进入项目目录并使用以下命令运行测试。

```
robot -v SERVER:{server_name} -v SUPERUSER_USERNAME:{super_user_email_here} -v SUPERUSER_PASSWORD:{super_user_password} tests/robot
```

将 `{}` 内的所有参数更改为你的本地服务器。最终命令类似：
```
robot -v SERVER:localhost:5000 -v SUPERUSER_USERNAME:test@opev.net -v SUPERUSER_PASSWORD:test_password tests/robot
```
* 测试完成后，会在根目录生成 `report.html` 和 `log.html` 报告。

### 预提交指南

Git 钩子脚本可帮助在提交代码审查前发现简单问题。

#### 安装 git 钩子脚本：
* 运行 pre-commit install 来设置 git 钩子脚本
```sh
$ pre-commit install
pre-commit installed at .git/hooks/pre-commit
```
* 现在 pre-commit 将在 git commit 时自动运行！

#### 有关配置，请 [点击这里](https://pre-commit.com/)



## 安装

Open Event Server 可以部署在多种平台上。下面提供了详细的特定平台安装说明。

1. [安装说明](/docs/installation/basic.md)
1. [Vagrant 安装](/docs/installation/vagrant.md)
1. [在 Google Compute Engine 上部署](/docs/installation/google.md)
1. [在 Google Container Engine (Kubernetes) 上部署](/docs/installation/gce-kubernetes.md)
1. [在 AWS EC2 上部署](/docs/installation/aws.md)
1. [在 Digital Ocean 上部署](/docs/installation/digital-ocean.md)
1. [使用 Docker 部署](/docs/installation/docker.md)
1. [在 Heroku 上部署](/docs/installation/heroku.md)

也提供一键 Heroku 部署：

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

## 技术栈

请熟悉项目的组成部分以便于贡献。

### 组件

* 数据库 - [PostgreSQL](https://www.postgresql.org)
* Web 框架 - [Flask](http://flask.pocoo.org)
* 应用服务器 - [uWSGI](https://github.com/unbit/uwsgi)
* Web 服务器 - [NGINX](https://www.nginx.com)

注意：open-event-server **目前支持 Python 3.9+**。

### 外部服务依赖

#### OAuth 社交认证

OAuth 用于从 Facebook 和 Google 帐号获取信息，使用户能够使用各自的凭据登录：
 1. Google - https://accounts.google.com/o/oauth2/auth
 2. Facebook - https://graph.facebook.com/oauth

#### Twitter

公共活动页面提供 Twitter feed 集成。

所需密钥可从 [https://dev.twitter.com/overview/documentation](https://dev.twitter.com/overview/documentation) 获取。

#### Instagram

可以扩展功能，并在活动服务中提供来自 Instagram 的图片。

所需密钥可从 [https://www.instagram.com/developer/authentication/](https://www.instagram.com/developer/authentication/) 获取。

#### Google 地图

Google 地图用于获取有关位置的信息（例如国家、城市、经纬度）。

所需密钥可从 [https://developers.google.com/maps/documentation/javascript/get-api-key](https://developers.google.com/maps/documentation/javascript/get-api-key) 获取。

#### 媒体存储 - 本地/Amazon S3/Google Cloud

媒体（例如音频、头像和徽标）可以存储在本地、Amazon S3 或 Google Storage 中。

1. [Amazon S3 设置说明](/docs/general/amazon-s3.md)
1. [Google Cloud 设置说明](https://cloud.google.com/storage/docs/migrating#defaultproj)

#### 电子邮件 - SMTP/Sendgrid

服务器可以通过 SMTP 或使用 Sendgrid API 发送电子邮件。

1. SMTP 可以在 `admin/settings` 中直接配置
2. 获取 [Sendgrid API 令牌](https://sendgrid.com/docs/User_Guide/Settings/api_keys.html)。

#### Heroku API

如果应用部署在 Heroku 上，我们使用 Heroku API 来获取最新版本并显示 Heroku 信息。

所需令牌可从 [https://devcenter.heroku.com/articles/authentication](https://devcenter.heroku.com/articles/authentication) 获取。

#### 支付网关

对于票务销售，该服务集成支付网关：
 1. Stripe - [获取密钥](https://support.stripe.com/questions/where-do-i-find-my-api-keys)
 2. Paypal - [获取凭据](https://developer.paypal.com/docs/classic/lifecycle/ug_sandbox/)

## 数据访问

#### 导入与导出

**导入：**

Open Event Server 支持多种格式作为有效的导入来源。

- 一个包含符合 API 结构的 JSON 和二进制媒体文件的 **zip 压缩包**。详情请参阅 [这里](/docs/general/import-export.md)。
- **Pentabarf XML** 格式也被支持作为有效的导入来源。（[示例文件](https://archive.fosdem.org/2016/schedule/xml)）。

**导出：**

活动数据和会话可以以多种格式导出。
- 一个包含符合 API 结构的 JSON 和二进制媒体文件的 **zip 压缩包**。详情请参阅 [这里](/docs/general/import-export.md)。
- **Pentabarf XML** 格式。（[示例文件](https://archive.fosdem.org/2016/schedule/xml)）。
- **iCal** 格式。（[示例文件](https://archive.fosdem.org/2016/schedule/ical)）。
- **xCal** 格式。（[示例文件](https://archive.fosdem.org/2016/schedule/xcal)）。

## 角色

系统有两类角色类型。

1. 系统角色与 Open Event 组织和应用程序的运营者相关。
2. 事件角色与系统的用户及其不同权限相关。

在此处了解更多 [here](/docs/general/roles.md)。

## 日志记录

某些信息会被记录并存储在数据库中，以供将来参考、解决冲突或维护系统概况。阅读有关[日志记录的更多内容](/docs/general/logs.md)。
