#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工厂基类 - Open Event Server 测试工厂基础

此文件定义了所有测试工厂的基类。

作者: FOSSASIA
"""

import factory
from objproxies import CallbackProxy

from app.models import db


class BaseFactory(factory.alchemy.SQLAlchemyModelFactory):
    """
    基础工厂类
    
    所有测试工厂的基类，提供数据库会话。
    """
    
    class Meta:
        """工厂元数据"""
        abstract = True  # 抽象工厂，不能直接实例化
        sqlalchemy_session = CallbackProxy(lambda: db.session)  # 数据库会话
