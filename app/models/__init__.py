#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模型初始化模块 - Open Event Server 数据库模型初始化

此模块负责初始化SQLAlchemy数据库实例和版本控制。
设置数据库ORM基础配置，包括版本控制和测试会话代理。

作者: FOSSASIA
"""

import sys

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy_continuum import make_versioned
from sqlalchemy_continuum.plugins import FlaskPlugin

# 启用模型版本控制，支持数据历史记录
make_versioned(plugins=[FlaskPlugin()], options={'strategy': 'subquery'})

# 创建SQLAlchemy数据库实例
db = SQLAlchemy()

# 如果在测试环境中运行，设置会话代理
# 将会话指向嵌套事务，在每个测试后回滚
if 'pytest' in sys.modules:
    from objproxies import CallbackProxy

    db._session = db.session
    db.session = CallbackProxy(lambda: db._session)
