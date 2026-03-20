#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
导出任务模型 - Open Event Server 导出任务管理模块

此文件定义了导出任务模型类，用于管理事件数据的导出任务。
导出任务用于将事件数据导出为各种格式。

作者: FOSSASIA
"""

from sqlalchemy.orm import backref
from sqlalchemy.sql import func

from app.models import db


class ExportJob(db.Model):
    """
    导出任务模型类
    
    此类代表事件的导出任务，用于将事件数据导出为各种格式。
    每个导出任务记录包含任务类型、开始时间、用户邮箱等信息。
    """
    
    __tablename__ = 'export_jobs'  # 数据库表名
    
    # 基本信息
    id = db.Column(db.Integer, primary_key=True)  # 任务ID
    task = db.Column(db.String, nullable=False)  # 任务类型
    starts_at = db.Column(db.DateTime(timezone=True), default=func.now())  # 开始时间
    
    # 用户信息
    user_email = db.Column(db.String)  # 用户邮箱
    # 不链接到User表，因为当用户被删除时，这个记录会丢失
    
    # 事件关联
    event_id = db.Column(db.Integer, db.ForeignKey('events.id', ondelete='CASCADE'))  # 事件ID
    event = db.relationship('Event', backref=backref('export_jobs'))  # 事件关联
    attendee_id = db.Column(db.Integer, nullable=True)  # 参与者ID

    def __repr__(self):
        """
        字符串表示
        
        返回:
            str: 导出任务对象的字符串表示
        """
        return '<ExportJob %d for event %d>' % (self.id, self.event.id)