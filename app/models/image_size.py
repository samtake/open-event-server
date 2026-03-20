#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片尺寸模型 - Open Event Server 图片尺寸管理模块

此文件定义了图片尺寸模型类，用于管理不同类型图片的尺寸和质量设置。

作者: FOSSASIA
"""

from app.models import db


class ImageSizes(db.Model):
    """
    图片尺寸模型类
    
    此类代表不同类型图片的尺寸和质量设置，如完整尺寸、缩略图、图标等。
    """
    
    __tablename__ = 'image_sizes'  # 数据库表名
    
    # 基本信息
    id = db.Column(db.Integer, primary_key=True)  # 尺寸ID
    type = db.Column(db.String)  # 图片类型
    
    # 完整尺寸设置
    full_width = db.Column(db.Integer)  # 完整宽度
    full_height = db.Column(db.Integer)  # 完整高度
    full_aspect = db.Column(db.Boolean, default=False)  # 完整比例
    full_quality = db.Column(db.Integer)  # 完整质量
    
    # 图标尺寸设置
    icon_width = db.Column(db.Integer)  # 图标宽度
    icon_height = db.Column(db.Integer)  # 图标高度
    icon_aspect = db.Column(db.Boolean, default=False)  # 图标比例
    icon_quality = db.Column(db.Integer)  # 图标质量
    
    # 缩略图尺寸设置
    thumbnail_width = db.Column(db.Integer)  # 缩略图宽度
    thumbnail_height = db.Column(db.Integer)  # 缩略图高度
    thumbnail_aspect = db.Column(db.Boolean, default=False)  # 缩略图比例
    thumbnail_quality = db.Column(db.Integer)  # 缩略图质量
    
    # 徽标尺寸设置
    logo_width = db.Column(db.Integer)  # 徽标宽度
    logo_height = db.Column(db.Integer)  # 徽标高度
    
    # 小尺寸设置
    small_size_width_height = db.Column(db.Integer)  # 小尺寸宽高
    small_size_quality = db.Column(db.Integer)  # 小尺寸质量
    
    # 缩略图尺寸设置
    thumbnail_size_width_height = db.Column(db.Integer)  # 缩略图尺寸宽高
    thumbnail_size_quality = db.Column(db.Integer)  # 缩略图尺寸质量
    
    # 图标尺寸设置
    icon_size_width_height = db.Column(db.Integer)  # 图标尺寸宽高
    icon_size_quality = db.Column(db.Integer)  # 图标尺寸质量

    def __repr__(self):
        """
        字符串表示
        
        返回:
            str: 图片尺寸对象的字符串表示
        """
        return '图片尺寸: ' + str(self.id)