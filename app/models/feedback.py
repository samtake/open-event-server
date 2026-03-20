#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
反馈模型 - Open Event Server 反馈管理模块

此文件定义了反馈模型类，用于管理用户对会话的反馈。

作者: FOSSASIA
"""

from app.models import db
from app.models.base import SoftDeletionModel


class Feedback(SoftDeletionModel):
    """
    反馈模型类
    
    此类代表用户对会话的反馈，包含评分和评论。
    """
    
    __tablename__ = 'feedback'  # 数据库表名
    __table_args__ = (
        db.UniqueConstraint('session_id', 'user_id', name='session_user_uc'),  # 唯一约束
    )

    # 基本信息
    id = db.Column(db.Integer, primary_key=True)  # 反馈ID
    rating = db.Column(db.Float, nullable=False)  # 评分
    comment = db.Column(db.String, nullable=True)  # 评论
    
    # 关联关系
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'))  # 用户ID
    event_id = db.Column(db.Integer, db.ForeignKey('events.id', ondelete='CASCADE'))  # 事件ID
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.id', ondelete='CASCADE'))  # 会话ID

    def __init__(self, **kwargs):
        """
        初始化反馈
        
        参数:
            **kwargs: 关键字参数
        """
        super().__init__(**kwargs)
        # TODO(Areeb): 测试评分的四舍五入
        rating = float(kwargs.get('rating'))
        self.rating = round(rating * 2, 0) / 2  # 四舍五入到最近的0.5

    def __repr__(self):
        """
        字符串表示
        
        返回:
            str: 反馈对象的字符串表示
        """
        return '<Feedback %r>' % self.rating