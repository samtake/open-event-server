#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
事件子主题模型 - Open Event Server 事件子主题管理模块

此文件定义了事件子主题模型类，用于表示事件的子分类主题。

作者: FOSSASIA
"""

from sqlalchemy.schema import UniqueConstraint

from app.api.helpers.db import get_new_slug
from app.models import db


class EventSubTopic(db.Model):
    """
    事件子主题模型类
    
    此类代表事件的子分类主题，如技术主题下的前端开发、后端开发等。
    """
    
    __tablename__ = 'event_sub_topics'  # 数据库表名
    __table_args__ = (
        # 唯一约束
        UniqueConstraint('slug', 'event_topic_id', name='slug_event_topic_id'),
    )

    # 字段定义
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # 子主题ID
    name = db.Column(db.String, nullable=False)  # 子主题名称
    slug = db.Column(db.String, nullable=False)  # 唯一标识符
    events = db.relationship('Event', backref='event-sub-topic')  # 事件关联
    event_topic = db.relationship('EventTopic', backref='event-sub-topics')  # 主题关联
    event_topic_id = db.Column(
        db.Integer, db.ForeignKey('event_topics.id', ondelete='CASCADE')
    )  # 主题ID

    def __init__(self, **kwargs):
        """
        初始化事件子主题
        
        参数:
            **kwargs: 关键字参数
        """
        super().__init__(**kwargs)
        # 自动生成唯一的slug
        self.slug = get_new_slug(EventSubTopic, self.name)

    def __repr__(self):
        """
        字符串表示
        
        返回:
            str: 事件子主题对象的字符串表示
        """
        return '<EventSubTopic %r>' % self.name
