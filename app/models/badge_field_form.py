#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
徽章字段表单模型 - Open Event Server 徽章字段管理模块

此文件定义了徽章字段表单模型类，用于管理徽章的字段配置。
徽章字段表单定义了徽章上显示的各种字段的样式和布局。

作者: FOSSASIA
"""

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import ARRAY

from app.models import db


class BadgeFieldForms(db.Model):
    """
    徽章字段表单模型类
    
    此类代表徽章字段表单，用于定义徽章上显示的各种字段的样式和布局。
    包括字体、颜色、对齐方式等属性。
    """
    
    __tablename__ = 'badge_field_forms'  # 数据库表名

    # 基本信息
    id = db.Column(db.Integer, primary_key=True)  # 字段ID
    badge_form_id = db.Column(
        db.Integer, db.ForeignKey('badge_forms.id', ondelete='CASCADE')
    )  # 徽章表单ID
    
    # 字段标识和内容
    badge_id = db.Column(db.String, nullable=False)  # 徽章ID
    field_identifier = db.Column(db.String, nullable=True)  # 字段标识符
    custom_field = db.Column(db.String, nullable=True)  # 自定义字段
    
    # 文本内容
    sample_text = db.Column(db.String, nullable=True)  # 示例文本
    
    # 字体样式
    font_size = db.Column(db.Integer, nullable=True)  # 字体大小
    font_name = db.Column(db.String, nullable=True)  # 字体名称
    font_weight = db.Column(ARRAY(db.JSON), nullable=True)  # 字体粗细
    font_color = db.Column(db.String, nullable=True)  # 字体颜色
    
    # 文本样式
    text_rotation = db.Column(db.Integer, nullable=True)  # 文本旋转角度
    text_alignment = db.Column(db.String, nullable=True)  # 文本对齐方式
    text_type = db.Column(db.String, nullable=True)  # 文本类型
    
    # 状态信息
    is_deleted = db.Column(db.Boolean, nullable=True)  # 是否已删除
    is_field_expanded = db.Column(db.Boolean, nullable=True)  # 字段是否展开
    
    # 边距设置
    margin_top = db.Column(db.Integer, nullable=True)  # 上边距
    margin_bottom = db.Column(db.Integer, nullable=True)  # 下边距
    margin_left = db.Column(db.Integer, nullable=True)  # 左边距
    margin_right = db.Column(db.Integer, nullable=True)  # 右边距
    
    # QR码设置
    qr_custom_field = db.Column(ARRAY(String), nullable=True)  # QR码自定义字段

    # 关联关系
    badge_form = db.relationship(
        'BadgeForms', backref='badge_field_forms_', foreign_keys=[badge_form_id]
    )  # 徽章表单关联

    def __repr__(self):
        """
        字符串表示
        
        返回:
            str: 徽章字段表单对象的字符串表示
        """
        return f'<BadgeFieldForms {self.id}>'

    def convert_to_dict(self):
        """
        将对象数据转换为字典
        
        返回:
            dict: 包含所有字段信息的字典
        """
        return {
            'id': self.id,
            'field_identifier': self.field_identifier,
            'custom_field': self.custom_field,
            'sample_text': self.sample_text,
            'badge_id': self.badge_id,
            'font_size': self.font_size,
            'font_name': self.font_name,
            'font_weight': self.font_weight,
            'font_color': self.font_color,
            'text_rotation': self.text_rotation,
            'text_alignment': self.text_alignment,
            'text_type': self.text_type,
            'is_deleted': self.is_deleted,
            'margin_top': self.margin_top,
            'margin_bottom': self.margin_bottom,
            'margin_left': self.margin_left,
            'margin_right': self.margin_right,
            'qr_custom_field': self.qr_custom_field,
            'is_field_expanded': self.is_field_expanded,
        }

    def get_badge_field(self):
        """
        获取徽章字段（支持API #8982）
        
        返回:
            dict: 包含徽章字段基本信息的字典
        """
        return {
            'id': self.id,
            'field_identifier': self.field_identifier,
            'custom_field': self.custom_field,
        }

    @staticmethod
    def get_badge_field_form_if_exist(badge_field_id, badge_id):
        """
        检查自定义表单翻译是否存在
        
        参数:
            badge_field_id (int): 徽章字段ID
            badge_id (str): 徽章ID
            
        返回:
            BadgeFieldForms: 徽章字段表单对象，如果不存在则返回None
        """
        try:
            badgeFieldForm = (
                BadgeFieldForms.query.filter_by(badge_id=badge_id)
                .filter_by(id=badge_field_id)
                .first()
            )
            return badgeFieldForm
        except ModuleNotFoundError:
            return None