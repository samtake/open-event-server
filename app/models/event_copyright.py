#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
事件版权模型 - Open Event Server 事件版权管理模块

此文件定义了事件版权模型类，用于表示事件的版权信息。

作者: FOSSASIA
"""

from sqlalchemy.orm import backref

from app.models import db
from app.models.base import SoftDeletionModel


class EventCopyright(SoftDeletionModel):
    """
    事件版权模型类
    
    此类代表事件的版权信息，包括版权持有者、许可证等。
    """

    __tablename__ = 'event_copyrights'  # 数据库表名

    # 字段定义
    id = db.Column(db.Integer, primary_key=True)  # 版权ID
    holder = db.Column(db.String)  # 版权持有者
    holder_url = db.Column(db.String)  # 版权持有者URL
    licence = db.Column(db.String, nullable=False)  # 许可证
    licence_url = db.Column(db.String)  # 许可证URL
    year = db.Column(db.Integer)  # 年份
    logo = db.Column(db.String)  # 徽标

    # 事件关联
    event_id = db.Column(db.Integer, db.ForeignKey('events.id', ondelete='CASCADE'))  # 事件ID
    event = db.relationship('Event', backref=backref('copyright', uselist=False))  # 事件关联

    def __repr__(self):
        """
        字符串表示
        
        返回:
            str: 版权对象的字符串表示
        """
        return '<Copyright %r>' % self.holder
