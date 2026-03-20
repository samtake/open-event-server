#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
折扣码模型 - Open Event Server 折扣码管理模块

此文件定义了折扣码模型类，用于管理事件的折扣代码。
折扣码可以用于为事件参与者提供折扣优惠。

作者: FOSSASIA
"""

from citext import CIText
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy.sql import func

from app.api.helpers.db import get_count
from app.api.helpers.ticketing import is_discount_available, validate_discount_code
from app.models import db
from app.models.base import SoftDeletionModel
from app.models.order import Order
from app.models.ticket import Ticket
from app.models.ticket_holder import TicketHolder


class DiscountCode(SoftDeletionModel):
    """
    折扣码模型类
    
    此类代表事件的折扣码，可用于为事件参与者提供折扣优惠。
    折扣码可以设置折扣金额或百分比、有效期、使用次数限制等属性。
    """
    
    __tablename__ = "discount_codes"  # 数据库表名
    __table_args__ = (
        UniqueConstraint('event_id', 'code', 'deleted_at', name='uq_event_discount_code'),
    )  # 唯一约束

    # 基本信息
    id = db.Column(db.Integer, primary_key=True)  # 折扣码ID
    code = db.Column(CIText, nullable=False)  # 折扣码
    discount_url = db.Column(db.String)  # 折扣URL
    value = db.Column(db.Float, nullable=False)  # 折扣值
    type = db.Column(db.String, nullable=False)  # 折扣类型
    is_active = db.Column(db.Boolean, default=True)  # 是否激活
    used_for = db.Column(db.String, nullable=False)  # 使用对象
    
    # 数量限制
    tickets_number = db.Column(db.Integer)  # 票数限制
    min_quantity = db.Column(db.Integer, default=1)  # 最小数量
    max_quantity = db.Column(db.Integer, default=100)  # 最大数量
    
    # 有效期
    valid_from = db.Column(db.DateTime(timezone=True), nullable=True)  # 有效期开始时间
    valid_till = db.Column(db.DateTime(timezone=True), nullable=True)  # 有效期结束时间
    
    # 关联关系
    event_id = db.Column(db.Integer, db.ForeignKey('events.id', ondelete='CASCADE'))  # 事件ID
    event = db.relationship('Event', backref='discount_codes', foreign_keys=[event_id])  # 事件关联
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())  # 创建时间
    marketer_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'))  # 营销人员ID
    marketer = db.relationship('User', backref='discount_codes_')  # 营销人员关联

    @staticmethod
    def get_service_name() -> str:
        """
        获取服务名称
        
        返回:
            str: 服务名称 'discount_code'
        """
        return 'discount_code'

    def __repr__(self) -> str:
        """
        字符串表示
        
        返回:
            str: 折扣码对象的字符串表示
        """
        return '<DiscountCode %r>' % self.id

    def get_confirmed_attendees_query(self):
        """
        获取使用折扣码完成订单的参与者列表
        
        返回:
            Query: 参与者查询对象
        """
        return (
            TicketHolder.query.filter_by(deleted_at=None)
            .filter_by(is_discount_applied=True)
            .join(Order)
            .filter_by(discount_code_id=self.id)
            .filter(Order.status.in_(['completed', 'placed', 'pending', 'initializing']))
        )

    @property
    def confirmed_attendees(self):
        """
        获取确认的参与者列表
        
        返回:
            list: 确认的参与者对象列表
        """
        return self.get_confirmed_attendees_query().all()

    @property
    def confirmed_attendees_count(self) -> int:
        """
        获取确认的参与者数量
        
        返回:
            int: 确认的参与者数量
        """
        return get_count(self.get_confirmed_attendees_query())

    @property
    def valid_expire_time(self):
        """
        获取有效过期时间
        
        返回:
            datetime: 有效过期时间（如果设置了valid_till则返回valid_till，否则返回事件结束时间）
        """
        return self.valid_till or self.event.ends_at

    def get_supported_tickets(self, ticket_ids=None):
        """
        获取支持的票种
        
        参数:
            ticket_ids (list): 票种ID列表，可选
            
        返回:
            Query: 票种查询对象
        """
        query = Ticket.query.with_parent(self).filter_by(deleted_at=None)
        if ticket_ids:
            query = query.filter(Ticket.id.in_(ticket_ids))
        return query

    def is_available(self, tickets=None, ticket_holders=None):
        """
        检查折扣码是否可用
        
        参数:
            tickets: 票种列表
            ticket_holders: 票持有者列表
            
        返回:
            bool: 折扣码是否可用
        """
        return is_discount_available(self, tickets=tickets, ticket_holders=ticket_holders)

    def validate(self, tickets=None, ticket_holders=None, event_id=None):
        """
        验证折扣码
        
        参数:
            tickets: 票种列表
            ticket_holders: 票持有者列表
            event_id: 事件ID
            
        返回:
            bool: 折扣码是否有效
        """
        return validate_discount_code(
            self, tickets=tickets, ticket_holders=ticket_holders, event_id=event_id
        )