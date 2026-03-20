#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
常见问题类型模型 - Open Event Server 常见问题类型管理模块

此文件定义了常见问题类型模型类，用于管理事件常见问题的分类。

作者: FOSSASIA
"""

from app.models import db


class FaqType(db.Model):
    """
    常见问题类型模型类
    
    此类代表事件常见问题的分类，如注册、支付、活动等。
    """
    
    __tablename__ = 'faq_types'  # 数据库表名
    
    # 基本信息
    id = db.Column(db.Integer, primary_key=True)  # 类型ID
    name = db.Column(db.String, nullable=False)  # 类型名称
    
    # 关联关系
    event_id = db.Column(db.Integer, db.ForeignKey('events.id', ondelete='CASCADE'))  # 事件ID
    event = db.relationship("Event", backref="faq_types", foreign_keys=[event_id])  # 事件关联
    faqs = db.relationship('Faq', backref="faq_type")  # 常见问题关联

    def __repr__(self):
        """
        字符串表示
        
        返回:
            str: 常见问题类型对象的字符串表示
        """
        return '<FAQType %r>' % self.name