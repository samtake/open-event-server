#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
事件访问码模型 - Open Event Server 访问码管理模块

此文件定义了事件访问码模型类，用于管理事件的访问代码。
访问码可以用于限制对事件或特定票的访问。

作者: FOSSASIA
"""

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.sql import func

from app.api.helpers.db import get_count
from app.models import db
from app.models.base import SoftDeletionModel
from app.models.order import Order
from app.models.ticket_holder import TicketHolder


@dataclass(init=False, unsafe_hash=True)
class AccessCode(SoftDeletionModel):
    """
    访问码模型类
    
    此类代表事件的访问码，可用于限制对事件或特定票的访问。
    访问码可以设置有效期、使用次数限制等属性。
    """
    
    __tablename__ = "access_codes"  # 数据库表名

    # 基本信息
    id: int = db.Column(db.Integer, primary_key=True)  # 访问码ID
    code: str = db.Column(db.String)  # 访问码字符串
    access_url: str = db.Column(db.String)  # 访问URL
    is_active: bool = db.Column(db.Boolean)  # 是否激活
    
    # 数量限制
    tickets_number: int = db.Column(
        db.Integer
    )  # 票数限制（事件级别访问时，表示最大使用次数）
    min_quantity: int = db.Column(db.Integer)  # 最小数量
    max_quantity: int = db.Column(
        db.Integer
    )  # 最大数量（事件级别访问时，表示有效月份数）
    
    # 有效期
    valid_from: datetime = db.Column(db.DateTime(timezone=True), nullable=True)  # 有效期开始时间
    valid_till: datetime = db.Column(db.DateTime(timezone=True), nullable=True)  # 有效期结束时间
    
    # 关联关系
    ticket_id: int = db.Column(
        db.Integer, db.ForeignKey('tickets.id', ondelete='CASCADE')
    )  # 票ID
    event_id: int = db.Column(db.Integer, db.ForeignKey('events.id', ondelete='CASCADE'))  # 事件ID
    created_at: datetime = db.Column(db.DateTime(timezone=True), default=func.now())  # 创建时间
    marketer_id: int = db.Column(
        db.Integer, db.ForeignKey('users.id', ondelete='CASCADE')
    )  # 营销人员ID

    # 关系定义
    marketer = db.relationship('User', backref='access_codes_')  # 营销人员关联
    ticket = db.relationship('Ticket', backref='access_code', foreign_keys=[ticket_id])  # 票关联
    event = db.relationship('Event', backref='access_codes', foreign_keys=[event_id])  # 事件关联

    @staticmethod
    def get_service_name():
        """
        获取服务名称
        
        返回:
            str: 服务名称 'access_code'
        """
        return 'access_code'

    @property
    def valid_expire_time(self):
        """
        获取有效过期时间
        
        返回:
            datetime: 有效过期时间（如果设置了valid_till则返回valid_till，否则返回事件结束时间）
        """
        return self.valid_till or self.event.ends_at

    def get_confirmed_attendees_query(self):
        """
        获取使用访问码完成订单的参与者列表
        
        返回:
            Query: 参与者查询对象
        """
        return (
            TicketHolder.query.filter_by(deleted_at=None)
            .filter_by(is_access_code_applied=True)
            .join(Order)
            .filter_by(access_code_id=self.id)
            .filter(Order.status.in_(['completed', 'placed', 'pending', 'initializing']))
        )

    @property
    def confirmed_attendees_count(self) -> int:
        """
        获取确认的参与者数量
        
        返回:
            int: 确认的参与者数量
        """
        return get_count(self.get_confirmed_attendees_query())