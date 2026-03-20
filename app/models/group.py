#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分组模型 - Open Event Server 分组管理模块

此文件定义了分组模型类，用于管理用户创建的分组。
分组允许用户将相关的事件组织在一起。

作者: FOSSASIA
"""

from datetime import datetime

from flask_jwt_extended import current_user
from sqlalchemy import func
from sqlalchemy_utils import aggregated

from app.models import db
from app.models.base import SoftDeletionModel
from app.models.user_follow_group import UserFollowGroup
from app.settings import get_settings


class Group(SoftDeletionModel):
    """
    分组模型类
    
    此类代表用户创建的分组，用于将相关的事件组织在一起。
    分组包含名称、描述、社交链接等信息。
    """
    
    __tablename__ = 'groups'  # 数据库表名

    # 基本信息
    id = db.Column(db.Integer, primary_key=True)  # 分组ID
    name = db.Column(db.String, nullable=False)  # 分组名称
    user_id = db.Column(
        db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False
    )  # 用户ID
    
    # 媒体信息
    social_links = db.Column(db.JSON)  # 社交链接
    logo_url = db.Column(db.String)  # 徽标URL
    banner_url = db.Column(db.String)  # 横幅URL
    thumbnail_image_url = db.Column(db.String)  # 缩略图URL
    
    # 状态信息
    is_promoted = db.Column(db.Boolean, default=False, nullable=False)  # 是否推广
    about = db.Column(db.Text)  # 描述
    
    # 时间信息
    created_at: datetime = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)  # 创建时间
    modified_at: datetime = db.Column(
        db.DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )  # 修改时间

    # 聚合字段
    @aggregated(
        'followers', db.Column(db.Integer, default=0, server_default='0', nullable=False)
    )
    def follower_count(self):
        """
        获取关注者数量
        
        返回:
            int: 关注者数量
        """
        return func.count('1')

    # 关联关系
    user = db.relationship('User', backref='groups')  # 用户关联
    roles = db.relationship("UsersGroupsRoles", backref="group")  # 角色关联

    @property
    def follower(self):
        """
        获取当前用户的关注状态
        
        返回:
            UserFollowGroup: 当前用户的关注对象，如果不存在则返回None
        """
        if not current_user:
            return None
        return UserFollowGroup.query.filter_by(user=current_user, group=self).first()

    @property
    def view_page_link(self):
        """
        获取分组页面链接
        
        返回:
            str: 分组页面的URL
        """
        frontend_url = get_settings()['frontend_url']
        return f"{frontend_url}/g/{self.id}"