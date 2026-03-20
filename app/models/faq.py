#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
常见问题模型 - Open Event Server 常见问题管理模块

此文件定义了常见问题模型类，用于管理事件的常见问题解答。

作者: FOSSASIA
"""

from app.models import db
from app.models.base import SoftDeletionModel


class Faq(SoftDeletionModel):
    """
    常见问题模型类
    
    此类代表事件的常见问题解答，包含问题和答案。
    """
    
    __tablename__ = 'faqs'  # 数据库表名
    
    # 基本信息
    id = db.Column(db.Integer, primary_key=True)  # 问题ID
    question = db.Column(db.String, nullable=False)  # 问题
    answer = db.Column(db.String, nullable=False)  # 答案
    
    # 关联关系
    event_id = db.Column(db.Integer, db.ForeignKey('events.id', ondelete='CASCADE'))  # 事件ID
    faq_type_id = db.Column(db.Integer, db.ForeignKey('faq_types.id', ondelete='CASCADE'))  # 问题类型ID

    def __repr__(self):
        """
        字符串表示
        
        返回:
            str: 常见问题对象的字符串表示
        """
        return '<FAQ %r>' % self.question