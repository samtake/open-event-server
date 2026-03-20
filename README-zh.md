# Open Event Server（中文版）

![Open Event Server](/docs/images/open-event-server.png)

[![GitHub release](https://img.shields.io/github/release/fossasia/open-event-server.svg)](https://github.com/fossasia/open-event-server/releases/latest)
[![Build Status](https://travis-ci.org/fossasia/open-event-server.svg?branch=development)](https://travis-ci.org/fossasia/open-event-server)
[![CircleCI Build Staus Badge](https://img.shields.io/circleci/build/github/fossasia/open-event-server?label=CircleCI%20Build)](https://www.circleci.com/gh/fossasia/open-event-server)
[![Codacy Badge](https://app.codacy.com/project/badge/Grade/f5036c0e23b44270ad24397e338b8412)](https://www.codacy.com/gh/fossasia/open-event-server/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=fossasia/open-event-server&amp;utm_campaign=Badge_Grade)
[![Codecov branch](https://codecov.io/gh/fossasia/open-event-server/branch/development/graph/badge.svg?style=flat-square)](https://codecov.io/gh/fossasia/open-event-server)
[![Gitter](https://img.shields.io/badge/chat-on%20gitter-ff006f.svg?style=flat-square)](https://gitter.im/fossasia/open-event-server)
[![Reviewed by Hound](https://img.shields.io/badge/Reviewed_by-Hound-8E64B0.svg)](https://houndci.com)
[![Mailing List](https://img.shields.io/badge/Mailing%20List-FOSSASIA-blue.svg)](https://groups.google.com/forum/#!forum/open-event)
[![Twitter Follow](https://img.shields.io/twitter/follow/eventyay.svg?style=social&label=Follow&maxAge=2592000?style=flat-square)](https://twitter.com/eventyay)

> **Open Event Server 使组织者能够管理从音乐会到会议和聚会的各种活动。**

它为多个议程和场地的活动提供功能。活动管理员可以为演讲者创建邀请表单，并在*拖放*界面中构建日程。活动信息存储在**数据库**中。该系统提供**API 端点**用于**获取**数据，以及**修改**和**更新**数据。组织者可以以一种标准的压缩文件格式导入和导出活动数据，该格式包含 **JSON** 数据以及诸如 **图片和音频** 等二进制媒体文件。

**Open Event Server** 提供一个良好记录的 [JSON:API 规范](http://jsonapi.org/) 兼容的 `REST API`，外部服务（例如 Open Event App 生成器和前端）可以使用该 API 访问和操作数据。

**API 文档：**
- 每个项目安装都附带 **API 文档**（例如测试安装：[https://open-event-api.herokuapp.com](https://open-event-api.herokuapp.com)）。
- **API 文档** 的托管版本位于仓库的 `gh-pages` 分支，地址为 [http://dev.eventyay.com/api/v1](http://dev.eventyay.com/api/v1)

## 交流方式

* 请加入我们的 **[邮件列表](https://groups.google.com/forum/#!forum/open-event)** 讨论有关项目的问题。
> https://groups.google.com/forum/#!forum/open-event

* 我们在 **[Gitter](https://gitter.im/fossasia/open-event-server)** 上有聊天频道。
> [gitter.im/fossasia/open-event-server](https://gitter.im/fossasia/open-event-server)

## 演示版本

演示版本会自动从我们的仓库部署：
* 从 `master` 分支部署 - **[open-event-api.herokuapp.com](https://open-event-api.herokuapp.com/)**
* 从 `development` 分支部署 - **[open-event-api-dev.herokuapp.com](https://open-event-api-dev.herokuapp.com/)**

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

注意：open-event-server **目前支持 Python 3.8**。

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

## 开发

### 初始设置

#### Python 和 Poetry 安装

我们使用 Python 3.8。如果你的操作系统默认不提供 Python 3.8，最好使用 [`pyenv`](https://github.com/pyenv/pyenv/) 安装。

对于 Mac 用户，请参考 [这里](https://opensource.com/article/19/5/python-3-default-mac) 了解更多信息。
```bash
$ brew install pyenv
$ pyenv init # 按照指示将运行命令添加到你的环境中
```
编辑环境文件后，重新加载 shell 并导航到此仓库，然后安装 `3.8.17` 以便在本地使用：
```bash
$ pyenv install 3.8.17
$ cd ...your../open-event-server/
$ pyenv local 3.8.17
```
现在在 open-event-server 中使用时，Python 版本应会自动切换。

我们还希望 [poetry](https://python-poetry.org/) 可用。

#### 依赖包设置

切换到 `open-event-server` 目录并执行以下命令：

激活本地 Python 3.8.17
```bash
$ pyenv local 3.8.17
```

使用 poetry 安装依赖
```bash
$ poetry install --with dev
```

激活 pre-commit 钩子
```bash
$ poetry run pre-commit install
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

## 日志记录

某些信息会被记录并存储在数据库中，以供将来参考、解决冲突或维护系统概况。阅读有关[日志记录的更多内容](/docs/general/logs.md)。

## 国际化 (i18n)

[![Translation status](https://hosted.weblate.org/widgets/open-event/-/multi-blue.svg)](https://hosted.weblate.org/engage/open-event)

Open Event 使用 Weblate（一种旨在简化开发人员和翻译人员翻译工作的网络工具）进行翻译。

如果你希望为 Open Event 贡献翻译，请[在该服务器注册](https://hosted.weblate.org/accounts/register/)。

激活帐户后，请前往[翻译部分](https://hosted.weblate.org/projects/open-event/)。

## 贡献、错误报告、功能请求

这是一个开源项目，我们欢迎贡献者报告错误并提交功能请求，也欢迎提交 pull request。请在此处报告问题：https://github.com/fossasia/open-event-server/issues。建议你先阅读[开发者手册](https://github.com/fossasia/open-event/tree/master/docs/dev-handbook)，以便对生态系统有基本了解。

## 分支策略

我们有以下分支：
 * **development**
	 所有开发工作都在此分支进行。如果你要贡献代码，请将 pull request 提交到 _development_。
	 所有 PR 必须通过 Travis 的构建检查和单元测试检查（https://open-event-api-dev.herokuapp.com - 运行在 development 分支）。

 * **master**
   此分支包含已发布的代码。在 development 分支积累了重要功能/错误修复后，我们会进行版本更新并发布。（https://api.eventyay.com - 运行在 `master` 分支。托管在 Google Cloud Platform (Google Container Engine + Kubernetes)）。
 * **gh-pages**
   此分支包含文档网站 http://dev.eventyay.com。每次 development 分支提交时，都会通过脚本和 Travis 自动构建该站点。它包含 Readme 和 /docs 文件夹的 md 文件，还包括 javadocs。

## 发布策略

当前的临时发布策略（由于活动频繁且存在许多错误）是每周一和周五发布 alpha 版本（因为我们发现周末活动更多）。因此，在 master 分支发布新版本之前，任何错误修复都不会反映在 eventyay.com 上。

## 贡献最佳实践

**提交**
* 编写清晰、有意义的 git 提交信息（请阅读 http://chris.beams.io/posts/git-commit/）
* 确保你的 PR 描述包含 GitHub 的特殊关键字引用，当 PR 合并时会自动关闭相关 issue。（更多信息见 https://github.com/blog/1506-closing-issues-via-pull-requests ）
* 当你对 PR 做了非常小的更改（例如修复失败的 travis 构建、一些样式更正或审查者要求的小更改）时，请务必将提交压缩（squash）为一个提交，这样不会为很小的修复生成大量提交。（了解如何 squash： https://davidwalsh.name/squash-commits-git ）

**功能请求和错误报告**
* 在你向[问题跟踪器](https://github.com/fossasia/open-event-server/issues)提交功能请求或错误报告时，请务必添加重现步骤。尤其是当该错误比较奇怪/罕见时。

**加入开发**
* 在开始开发之前，请在本地设置系统并完整浏览应用程序。点击你能找到的任何链接/按钮，看看它会指向哪里。探索。 （不用担心...不会对应用程序或你造成影响：wink: 你唯一会得到的是对各个部分更熟悉，并可能找到改进的好主意。）
* 在你的机器上测试该应用并探索管理区域。Heroku 上的测试部署不会让你访问管理部分，在那里你可以开启/关闭模块，例如票务，并为服务添加密钥，例如 S3 上的存储。
* 如果你想处理某个 issue，请在该 issue 下留言。如果它已经分配给了某人，但没有迹象表明有人在做，你可以随时留言，以便如果之前的受让人完全放弃该 issue，可以将它分配给你。

## 许可证

本项目目前根据 **[GNU 通用公共许可证 v3](LICENSE)** 许可。

> 若要以不同许可证获取软件，请联系 [FOSSASIA](http://blog.fossasia.org/contact/)。
