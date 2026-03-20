#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
事件地点模型 - Open Event Server 事件地点管理模块

此文件定义了事件地点模型类，用于表示事件的地理位置。

作者: FOSSASIA
"""

from app.api.helpers.db import get_new_slug
from app.models import db


class EventLocation(db.Model):
    """
    事件地点模型类
    
    此类代表事件的地理位置，如城市、国家等。
    """
    
    __tablename__ = 'event_locations'  # 数据库表名

    # 字段定义
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # 地点ID
    name = db.Column(db.String, nullable=False)  # 地点名称
    slug = db.Column(db.String, unique=True, nullable=False)  # 唯一标识符

    def __init__(self, **kwargs):
        """
        初始化事件地点
        
        参数:
            **kwargs: 关键字参数
        """
        super().__init__(**kwargs)
        # 自动生成唯一的slug
        self.slug = get_new_slug(EventLocation, self.name)

    def __repr__(self):
        """
        字符串表示
        
        返回:
            str: 事件地点对象的字符串表示
        """
        return '<EventLocation %r>' % self.slug
