#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
邮件通知模型 - Open Event Server 邮件通知管理模块

此文件定义了邮件通知模型类，用于管理用户的邮件通知偏好设置。
邮件通知允许用户选择接收哪些类型的邮件通知。

作者: FOSSASIA
"""

from app.models import db
from app.models.base import SoftDeletionModel


class EmailNotification(SoftDeletionModel):
    """
    邮件通知模型类
    
    此类代表用户的邮件通知偏好设置，用于管理用户接收哪些类型的邮件通知。
    每个邮件通知记录包含用户ID、事件ID以及各种通知类型的开关状态。
    """
    
    __tablename__ = 'email_notifications'  # 数据库表名
    
    # 基本信息
    id = db.Column(db.Integer, primary_key=True)  # 通知ID
    
    # 通知类型
    next_event = db.Column(db.Boolean, default=False)  # 下一个事件通知
    new_paper = db.Column(db.Boolean, default=False)  # 新论文通知
    session_accept_reject = db.Column(db.Boolean, default=False)  # 会话接受/拒绝通知
    session_schedule = db.Column(db.Boolean, default=False)  # 会话安排通知
    after_ticket_purchase = db.Column(db.Boolean, default=True)  # 购票后通知
    
    # 关联关系
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'))  # 用户ID
    event_id = db.Column(db.Integer, db.ForeignKey('events.id', ondelete='CASCADE'))  # 事件ID
    event = db.relationship("Event")  # 事件关联
    user = db.relationship("User", backref="email_notifications")  # 用户关联

    def __str__(self):
        """
        字符串表示
        
        返回:
            str: 邮件通知对象的字符串表示
        """
        return '用户:' + str(self.user_id) + ' 事件: ' + str(self.event_id)