#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
演讲征集模型 - Open Event Server 演讲征集管理模块

此文件定义了演讲征集模型类，用于表示事件的演讲征集信息。

作者: FOSSASIA
"""

from sqlalchemy.orm import backref

from app.models import db
from app.models.base import SoftDeletionModel


class SpeakersCall(SoftDeletionModel):
    """
    演讲征集模型类
    
    此类代表事件的演讲征集信息，包括征集公告、时间等。
    """
    
    __tablename__ = 'speakers_calls'  # 数据库表名
    
    # 字段定义
    id = db.Column(db.Integer, primary_key=True)  # 征集ID
    announcement = db.Column(db.Text, nullable=True)  # 征集公告
    starts_at = db.Column(db.DateTime(timezone=True), nullable=False)  # 开始时间
    soft_ends_at = db.Column(db.DateTime(timezone=True), nullable=True)  # 软截止时间
    ends_at = db.Column(db.DateTime(timezone=True), nullable=False)  # 截止时间
    hash = db.Column(db.String, nullable=True)  # 哈希值
    privacy = db.Column(db.String, nullable=False, default='public')  # 隐私设置
    event_id = db.Column(db.Integer, db.ForeignKey('events.id', ondelete='CASCADE'))  # 事件ID
    event = db.relationship("Event", backref=backref("speakers_call", uselist=False))  # 事件关联

    def __repr__(self):
        """
        字符串表示
        
        返回:
            str: 演讲征集对象的字符串表示
        """
        return '<speakers_call %r>' % self.announcement
