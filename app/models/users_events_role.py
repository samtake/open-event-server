#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户事件角色模型 - Open Event Server 用户事件角色管理模块

此文件定义了用户事件角色模型类，用于表示用户在事件中的角色。

作者: FOSSASIA
"""

from app.models import db


class UsersEventsRoles(db.Model):
    """
    用户事件角色模型类
    
    此类表示用户在特定事件中的角色，建立用户、事件和角色之间的关联。
    """
    
    __tablename__ = 'users_events_roles'  # 数据库表名
    __table_args__ = (
        # 用户、事件、角色组合唯一约束
        db.UniqueConstraint(
            'user_id', 'event_id', 'role_id', name='uq_uer_user_event_role'
        ),
    )

    # 字段定义
    id = db.Column(db.Integer, primary_key=True)  # 关联ID

    # 事件关联
    event_id = db.Column(
        db.Integer, db.ForeignKey('events.id', ondelete='CASCADE'), nullable=False
    )  # 事件ID

    # 用户关联
    user_id = db.Column(
        db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False
    )  # 用户ID
    user = db.relationship("User")  # 用户关系

    # 角色关联
    role_id = db.Column(
        db.Integer, db.ForeignKey('roles.id', ondelete='CASCADE'), nullable=False
    )  # 角色ID
    role = db.relationship("Role")  # 角色关系

    def __repr__(self):
        """
        字符串表示
        
        返回:
            str: 用户事件角色对象的字符串表示
        """
        return f'<UER {self.user!r}:{self.event_id!r}:{self.role!r}>'
