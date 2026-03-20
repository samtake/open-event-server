#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通知模型 - Open Event Server 通知管理模块

此文件定义了通知模型类，用于管理系统中的用户通知。
通知用于向用户发送各种事件相关的消息。

作者: FOSSASIA
"""

from sqlalchemy_utils import generic_relationship, generic_repr

from app.models import db
from app.models.helpers.timestamp import Timestamp


class NotificationType:
    """
    通知类型定义类
    
    此类定义了系统中所有可用的通知类型。
    """
    
    TICKET_PURCHASED = 'ticket_purchased'  # 购票通知
    TICKET_PURCHASED_ATTENDEE = 'ticket_purchased_attendee'  # 参与者购票通知
    TICKET_PURCHASED_ORGANIZER = 'ticket_purchased_organizer'  # 组织者购票通知
    TICKET_CANCELLED = 'ticket_cancelled'  # 取消票通知
    TICKET_CANCELLED_ORGANIZER = 'ticket_cancelled_organizer'  # 组织者取消票通知
    EVENT_ROLE = 'event_role'  # 事件角色通知
    NEW_SESSION = 'new_session'  # 新会话通知
    SESSION_STATE_CHANGE = 'session_state_change'  # 会话状态变更通知
    MONTHLY_PAYMENT = 'monthly_payment'  # 月度支付通知
    MONTHLY_PAYMENT_FOLLOWUP = 'monthly_payment'  # 月度支付跟进通知

    @staticmethod
    def entries():
        """
        获取所有通知类型
        
        返回:
            list: 所有通知类型列表
        """
        # 提取所有定义的值，过滤内部键
        return list(
            map(
                lambda entry: entry[1],
                filter(
                    lambda entry: not entry[0].startswith('__') and type(entry[1]) == str,
                    NotificationType.__dict__.items(),
                ),
            )
        )


@generic_repr
class NotificationActor(db.Model, Timestamp):
    """
    通知参与者模型类
    
    此类代表通知的参与者信息。
    """
    
    __tablename__ = 'notification_actors'  # 数据库表名

    # 基本信息
    id = db.Column(db.Integer, primary_key=True)  # 参与者ID
    
    # 用户关联
    actor_id = db.Column(
        db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False
    )  # 参与者ID
    actor = db.relationship(
        'User', backref='notification_actors', foreign_keys=[actor_id]
    )  # 参与者关联
    
    # 内容关联
    content_id = db.Column(
        db.Integer,
        db.ForeignKey('notification_content.id', ondelete='CASCADE'),
        nullable=False,
    )  # 内容ID
    content = db.relationship(
        'NotificationContent', backref='actors', foreign_keys=[content_id]
    )  # 内容关联


@generic_repr
class NotificationContent(db.Model, Timestamp):
    """
    通知内容模型类
    
    此类代表通知的具体内容信息。
    """
    
    __tablename__ = 'notification_content'  # 数据库表名

    # 基本信息
    id = db.Column(db.Integer, primary_key=True)  # 内容ID
    type = db.Column(db.String, nullable=False)  # 通知类型
    
    # 目标关联
    target_type = db.Column(db.Unicode(255))  # 目标类型
    target_id = db.Column(db.Integer)  # 目标ID
    target = generic_relationship(target_type, target_id)  # 目标关联
    
    # 操作状态
    target_action = db.Column(db.String)  # 目标操作


@generic_repr
class Notification(db.Model, Timestamp):
    """
    通知模型类
    
    用于存储用户通知。
    """
    
    __tablename__ = 'notifications'  # 数据库表名

    # 基本信息
    id = db.Column(db.Integer, primary_key=True)  # 通知ID
    
    # 用户关联
    user_id = db.Column(
        db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False
    )  # 用户ID
    user = db.relationship('User', backref='notifications', foreign_keys=[user_id])  # 用户关联
    
    # 阅读状态
    is_read = db.Column(db.Boolean, nullable=False, default=False, server_default='False')  # 是否已读
    
    # 内容关联
    content_id = db.Column(
        db.Integer,
        db.ForeignKey('notification_content.id', ondelete='CASCADE'),
        nullable=False,
    )  # 内容ID
    content = db.relationship(
        'NotificationContent', backref='content', foreign_keys=[content_id]
    )  # 内容关联