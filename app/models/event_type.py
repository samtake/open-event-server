#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
事件类型模型 - Open Event Server 事件类型管理模块

此文件定义了事件类型模型类，用于表示事件的类型。

作者: FOSSASIA
"""

from app.api.helpers.db import get_new_slug
from app.models import db
from app.models.base import SoftDeletionModel


class EventType(SoftDeletionModel):
    """
    事件类型模型类
    
    此类代表事件的类型，如会议、研讨会、工作坊等。
    """
    
    __tablename__ = 'event_types'  # 数据库表名

    # 字段定义
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # 类型ID
    name = db.Column(db.String, nullable=False)  # 类型名称
    slug = db.Column(db.String, unique=True, nullable=False)  # 唯一标识符
    events = db.relationship('Event', backref='event-type')  # 事件关联

    def __init__(self, **kwargs):
        """
        初始化事件类型
        
        参数:
            **kwargs: 关键字参数
        """
        super().__init__(**kwargs)
        # 自动生成唯一的slug
        self.slug = get_new_slug(EventType, self.name)

    def __repr__(self):
        """
        字符串表示
        
        返回:
            str: 事件类型对象的字符串表示
        """
        return '<EventType %r>' % self.name
