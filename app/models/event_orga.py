#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
事件组织模型 - Open Event Server 事件组织管理模块

此文件定义了事件组织模型类，用于表示事件组织的基本信息。

作者: FOSSASIA
"""

from sqlalchemy.sql import func

from app.models import db
from app.models.base import SoftDeletionModel


class EventOrgaModel(SoftDeletionModel):
    """
    事件组织模型类
    
    此类代表事件组织的基本信息，包括名称、开始时间和支付货币等。
    """
    
    __tablename__ = 'events_orga'  # 数据库表名

    # 基本信息
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # 组织ID
    name = db.Column(db.String, nullable=False)  # 组织名称
    starts_at = db.Column(db.DateTime(timezone=True), default=func.now())  # 开始时间
    payment_currency = db.Column(db.String, nullable=False)  # 支付货币

    def __repr__(self):
        """
        字符串表示
        
        返回:
            str: 事件组织对象的字符串表示
        """
        return '<EventOrgaModel %r>' % self.name