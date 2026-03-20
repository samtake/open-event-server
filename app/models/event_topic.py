#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
事件主题模型 - Open Event Server 事件主题管理模块

此文件定义了事件主题模型类，用于表示事件的分类主题。

作者: FOSSASIA
"""

from app.api.helpers.db import get_new_slug
from app.models import db
from app.models.base import SoftDeletionModel


class EventTopic(SoftDeletionModel):
    """
    事件主题模型类
    
    此类代表事件的分类主题，如技术、商业、教育等。
    """
    
    __tablename__ = 'event_topics'  # 数据库表名

    # 字段定义
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # 主题ID
    name = db.Column(db.String, nullable=True)  # 主题名称
    system_image_url = db.Column(db.String)  # 系统图片URL
    slug = db.Column(db.String, unique=True, nullable=False)  # 唯一标识符
    events = db.relationship('Event', backref='event_topics')  # 事件关联
    event_sub_topics = db.relationship('EventSubTopic', backref='event-topic')  # 子主题关联

    def __init__(self, **kwargs):
        """
        初始化事件主题
        
        参数:
            **kwargs: 关键字参数
        """
        super().__init__(**kwargs)
        # 自动生成唯一的slug
        self.slug = get_new_slug(EventTopic, self.name)

    def __repr__(self):
        """
        字符串表示
        
        返回:
            str: 事件主题对象的字符串表示
        """
        return '<EventTopic %r>' % self.name
