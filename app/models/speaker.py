#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
演讲者模型 - Open Event Server 演讲者管理模块

此文件定义了演讲者模型类，用于表示会议中的演讲嘉宾。

作者: FOSSASIA
"""

from citext import CIText

from app.models import db
from app.models.base import SoftDeletionModel
from app.models.helpers.timestamp import Timestamp
from app.models.helpers.versioning import clean_html, clean_up_string


class Speaker(SoftDeletionModel, Timestamp):
    """
    演讲者模型类
    
    此类代表会议中的演讲嘉宾，包含个人信息、联系方式、简介等。
    """

    __tablename__ = 'speaker'  # 数据库表名
    __table_args__ = (
        db.UniqueConstraint(
            'event_id', 'email', 'deleted_at', name='uq_speaker_event_email'
        ),  # 事件ID和邮箱唯一约束
        db.Index('speaker_event_idx', 'event_id'),  # 事件ID索引
    )
    
    # 基本信息
    id = db.Column(db.Integer, primary_key=True)  # 演讲者ID
    name = db.Column(db.String, nullable=False)  # 姓名
    photo_url = db.Column(db.String)  # 照片URL
    thumbnail_image_url = db.Column(db.String)  # 缩略图URL
    small_image_url = db.Column(db.String)  # 小图URL
    icon_image_url = db.Column(db.String)  # 图标URL
    short_biography = db.Column(db.Text)  # 简短简介
    long_biography = db.Column(db.Text)  # 详细简介
    speaking_experience = db.Column(db.Text)  # 演讲经验
    email = db.Column(CIText)  # 邮箱（不区分大小写）
    mobile = db.Column(db.String)  # 手机号
    website = db.Column(db.String)  # 网站
    twitter = db.Column(db.String)  # Twitter
    facebook = db.Column(db.String)  # Facebook
    github = db.Column(db.String)  # GitHub
    mastodon = db.Column(db.String)  # Mastodon
    linkedin = db.Column(db.String)  # LinkedIn
    instagram = db.Column(db.String)  # Instagram
    organisation = db.Column(db.String)  # 组织
    is_featured = db.Column(db.Boolean, default=False)  # 是否精选
    is_email_overridden = db.Column(
        db.Boolean, default=False, nullable=False, server_default='False'
    )  # 邮箱是否被覆盖
    position = db.Column(db.String)  # 职位
    country = db.Column(db.String)  # 国家
    city = db.Column(db.String)  # 城市
    address = db.Column(db.String)  # 地址
    gender = db.Column(db.String)  # 性别
    order = db.Column(db.Integer, default=0, nullable=False)  # 排序
    heard_from = db.Column(db.String)  # 信息来源
    sponsorship_required = db.Column(db.Text)  # 赞助需求
    complex_field_values = db.Column(db.JSON)  # 复杂字段值
    speaker_positions = db.Column(db.JSON)  # 演讲者位置
    
    # 关联关系
    event_id = db.Column(db.Integer, db.ForeignKey('events.id', ondelete='CASCADE'))  # 事件ID
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'))  # 用户ID

    @staticmethod
    def get_service_name():
        """
        获取服务名称
        
        返回:
            str: 服务名称
        """
        return 'speaker'

    def __repr__(self):
        """
        字符串表示
        
        返回:
            str: 演讲者对象的字符串表示
        """
        return '<Speaker %r>' % self.name

    def __setattr__(self, name, value):
        """
        设置属性时的自定义处理
        
        对简介相关字段进行HTML清理。
        
        参数:
            name: 属性名称
            value: 属性值
        """
        if (
            name == 'short_biography'
            or name == 'long_biography'
            or name == 'speaking_experience'
            or name == 'sponsorship_required'
        ):
            super().__setattr__(name, clean_html(clean_up_string(value)))
        else:
            super().__setattr__(name, value)
