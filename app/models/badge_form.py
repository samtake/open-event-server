#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
徽章表单模型 - Open Event Server 徽章表单管理模块

此文件定义了徽章表单模型类，用于管理徽章的基本配置。
徽章表单定义了徽章的整体样式和外观。

作者: FOSSASIA
"""

from app.models import db


class BadgeForms(db.Model):
    """
    徽章表单模型类
    
    此类代表徽章表单，用于定义徽章的基本配置信息。
    包括徽章ID、尺寸、颜色、图像URL等属性。
    """
    
    __tablename__ = 'badge_forms'  # 数据库表名

    # 基本信息
    id = db.Column(db.Integer, primary_key=True)  # 徽章表单ID
    badge_id = db.Column(db.String, nullable=False)  # 徽章ID
    badge_size = db.Column(db.String, nullable=True)  # 徽章尺寸
    badge_color = db.Column(db.String, nullable=True)  # 徽章颜色
    badge_image_url = db.Column(db.String, nullable=True)  # 徽章图像URL
    badge_orientation = db.Column(db.String, nullable=True)  # 徽章方向
    
    # 事件关联
    event_id = db.Column(db.Integer, db.ForeignKey('events.id', ondelete='CASCADE'))  # 事件ID
    event = db.relationship('Event', backref='badge_forms_')  # 事件关联

    def __repr__(self):
        """
        字符串表示
        
        返回:
            str: 徽章表单对象的字符串表示
        """
        return f'<BadgeForm {self.id}>'