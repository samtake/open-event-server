#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基础模型模块 - Open Event Server 基础模型定义

此模块定义了支持软删除的基础模型类，所有需要软删除功能的模型都应该继承此类。

作者: FOSSASIA
"""

from app.models import db


class SoftDeletionModel(db.Model):
    """
    软删除基础模型类
    
    支持软删除功能的基础模型，所有需要软删除功能的模型都应该继承此类。
    软删除不会真正从数据库中删除记录，而是设置deleted_at字段来标记删除状态。
    """

    __abstract__ = True  # 抽象基类，不会创建实际的数据库表

    # 软删除时间戳，当记录被软删除时设置此字段
    deleted_at = db.Column(db.DateTime(timezone=True))
