#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
会话类型模型 - Open Event Server 会话类型管理模块

此文件定义了会话类型模型类，用于表示会议中的会话类型。

作者: FOSSASIA
"""

from app.models import db
from app.models.base import SoftDeletionModel


class SessionType(SoftDeletionModel):
    """
    会话类型模型类
    
    此类代表会议中的会话类型，如主题演讲、工作坊、小组讨论等。
    """
    
    __tablename__ = "session_types"  # 数据库表名
    
    # 字段定义
    id = db.Column(db.Integer, primary_key=True)  # 会话类型ID
    name = db.Column(db.String, nullable=False)  # 会话类型名称
    length = db.Column(db.String, nullable=False)  # 会话时长
    position = db.Column(db.Integer, default=0, nullable=False)  # 排序位置
    event_id = db.Column(db.Integer, db.ForeignKey('events.id', ondelete='CASCADE'))  # 事件ID
    event = db.relationship("Event", backref="session_type", foreign_keys=[event_id])  # 事件关联
    sessions = db.relationship('Session', backref="session_type")  # 会话关联

    def __repr__(self):
        """
        字符串表示
        
        返回:
            str: 会话类型对象的字符串表示
        """
        return '<SessionType %r>' % self.name
