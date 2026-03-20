#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PostgreSQL模块 - Open Event Server PostgreSQL会话管理

此模块提供PostgreSQL数据库会话创建功能。

作者: FOSSASIA
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import Config


def get_session_from_config():
    """
    使用应用配置创建PostgreSQL会话
    
    返回:
        Session: SQLAlchemy会话对象
    """
    # 使用配置中的数据库URI创建数据库引擎
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
    # 创建会话工厂
    maker = sessionmaker()
    # 将会话工厂绑定到引擎
    maker.configure(bind=engine)

    # 返回新的会话实例
    return maker()
