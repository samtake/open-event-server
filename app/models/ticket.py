#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
票券模型 - Open Event Server 票券管理模块

此文件定义了票券模型类，用于表示活动中的各种类型的票券。

作者: FOSSASIA
"""

from sqlalchemy import or_

from app.api.helpers.errors import ConflictError
from app.models import db
from app.models.base import SoftDeletionModel
from app.models.order import Order, OrderTicket
from app.models.ticket_holder import TicketHolder

# 访问码和票券的多对多关联表
access_codes_tickets = db.Table(
    'access_codes_tickets',
    db.Column(
        'access_code_id', db.Integer, db.ForeignKey('access_codes.id', ondelete='CASCADE')
    ),
    db.Column('ticket_id', db.Integer, db.ForeignKey('tickets.id', ondelete='CASCADE')),
    db.PrimaryKeyConstraint('access_code_id', 'ticket_id'),
)

# 折扣码和票券的多对多关联表
discount_codes_tickets = db.Table(
    'discount_codes_tickets',
    db.Column(
        'discount_code_id',
        db.Integer,
        db.ForeignKey('discount_codes.id', ondelete='CASCADE'),
    ),
    db.Column('ticket_id', db.Integer, db.ForeignKey('tickets.id', ondelete='CASCADE')),
    db.PrimaryKeyConstraint('discount_code_id', 'ticket_id'),
)

# 票券标签和票券的多对多关联表
ticket_tags_table = db.Table(
    'ticket_tagging',
    db.Model.metadata,
    db.Column('ticket_id', db.Integer, db.ForeignKey('tickets.id', ondelete='CASCADE')),
    db.Column(
        'ticket_tag_id', db.Integer, db.ForeignKey('ticket_tag.id', ondelete='CASCADE')
    ),
)


class Ticket(SoftDeletionModel):
    """
    票券模型类
    
    此类代表活动中的票券，包含票券名称、描述、价格、数量、销售时间等信息。
    """
    
    __tablename__ = 'tickets'  # 数据库表名
    __table_args__ = (
        # 事件内票券名称唯一约束
        db.UniqueConstraint(
            'name', 'event_id', 'deleted_at', name='name_event_deleted_at_uc'
        ),
    )

    # 基本信息
    id = db.Column(db.Integer, primary_key=True)  # 票券ID
    name = db.Column(db.String, nullable=False)  # 票券名称
    description = db.Column(db.String)  # 票券描述
    is_description_visible = db.Column(db.Boolean)  # 描述是否可见
    type = db.Column(db.String, nullable=False)  # 票券类型
    quantity = db.Column(db.Integer, default=100)  # 票券数量
    position = db.Column(db.Integer, default=1)  # 排序位置
    price = db.Column(db.Float)  # 价格
    min_price = db.Column(db.Float, default=0, nullable=False)  # 最低价格
    max_price = db.Column(db.Float, default=0)  # 最高价格
    is_fee_absorbed = db.Column(db.Boolean, default=False)  # 是否吸收费用
    sales_starts_at = db.Column(db.DateTime(timezone=True), nullable=False)  # 销售开始时间
    sales_ends_at = db.Column(db.DateTime(timezone=True), nullable=False)  # 销售结束时间
    is_hidden = db.Column(db.Boolean, default=False)  # 是否隐藏

    # 订单限制
    min_order = db.Column(db.Integer, default=1)  # 最小订单数量
    max_order = db.Column(db.Integer, default=10)  # 最大订单数量
    is_checkin_restricted = db.Column(db.Boolean)  # 是否限制签到
    auto_checkin_enabled = db.Column(db.Boolean, default=False)  # 是否启用自动签到
    
    # 关联关系
    event_id = db.Column(db.Integer, db.ForeignKey('events.id', ondelete='CASCADE'))  # 事件ID
    event = db.relationship('Event', backref='tickets_')  # 事件关联

    tags = db.relationship('TicketTag', secondary=ticket_tags_table, backref='tickets')  # 标签关联
    order_ticket = db.relationship('OrderTicket', backref="ticket", passive_deletes=True)  # 订单票券关联

    access_codes = db.relationship(
        'AccessCode', secondary=access_codes_tickets, backref='tickets'
    )  # 访问码关联

    discount_codes = db.relationship(
        'DiscountCode', secondary=discount_codes_tickets, backref="tickets"
    )  # 折扣码关联
    form_id = db.Column(db.String)  # 表单ID
    badge_id = db.Column(db.String)  # 徽章ID

    def has_order_tickets(self):
        """
        检查票券是否有已下单的订单
        
        返回:
            bool: 如果有已下单的订单则返回True，否则返回False
        """
        from app.api.helpers.db import get_count

        # 获取与票券相关的订单ID
        orders = Order.id.in_(
            OrderTicket.query.with_entities(OrderTicket.order_id)
            .filter_by(ticket_id=self.id)
            .all()
        )
        # 统计非删除状态的订单数量
        count = get_count(Order.query.filter(orders).filter(Order.status != 'deleted'))
        # 如果有订单则返回True
        return bool(count > 0)

    def has_completed_order_tickets(self):
        """
        检查票券是否有已完成或已下单的订单
        
        返回:
            bool: 如果有已完成或已下单的订单则返回True，否则返回False
        """
        # 获取与票券相关的订单票券
        order_tickets = OrderTicket.query.filter_by(ticket_id=self.id)

        count = 0
        # 遍历订单票券，统计已完成或已下单的订单
        for order_ticket in order_tickets:
            order = Order.query.filter_by(id=order_ticket.order_id).first()
            if order.status == "completed" or order.status == "placed":
                count += 1

        return bool(count > 0)

    def tags_csv(self):
        """
        获取票券标签的CSV格式字符串
        
        返回:
            str: 以逗号分隔的标签名称字符串
        """
        tag_names = [tag.name for tag in self.tags]
        return ','.join(tag_names)

    @property
    def has_current_orders(self):
        """
        检查票券是否有当前订单
        
        返回:
            bool: 如果有当前订单则返回True，否则返回False
        """
        return db.session.query(
            Order.query.join(TicketHolder)
            .filter(
                TicketHolder.ticket_id == self.id,
                or_(
                    Order.status == 'completed',
                    Order.status == 'placed',
                    Order.status == 'pending',
                    Order.status == 'initializing',
                ),
            )
            .exists()
        ).scalar()

    @property
    def reserved_count(self):
        """
        获取已预订的票券数量
        
        返回:
            int: 已预订的票券数量
        """
        from app.api.attendees import get_sold_and_reserved_tickets_count

        return get_sold_and_reserved_tickets_count(self.id)

    @property
    def is_available(self):
        """
        检查票券是否可用
        
        返回:
            bool: 如果票券可用则返回True，否则返回False
        """
        return self.reserved_count < self.quantity

    def raise_if_unavailable(self):
        """
        如果票券不可用则抛出异常
        
        异常:
            ConflictError: 当票券不可用时抛出
        """
        if not self.is_available:
            raise ConflictError({'id': self.id}, f'Ticket "{self.name}" already sold out')

    def __repr__(self):
        return '<Ticket %r>' % self.name


class TicketTag(SoftDeletionModel):
    """
    票券标签模型类
    
    用于对票券进行分组和分类的标签。
    """

    __tablename__ = 'ticket_tag'  # 数据库表名
    __table_args__ = (db.UniqueConstraint('name', 'event_id', name='unique_ticket_tag'),)  # 事件内标签名称唯一约束

    id = db.Column(db.Integer, primary_key=True)  # 标签ID
    name = db.Column(db.String)  # 标签名称

    event_id = db.Column(db.Integer, db.ForeignKey('events.id', ondelete='CASCADE'))  # 事件ID
    event = db.relationship('Event', backref='ticket_tags')  # 事件关联

    def __repr__(self):
        return '<TicketTag %r>' % self.name
