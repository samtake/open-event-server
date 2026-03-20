#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
订单模型 - Open Event Server 订单管理模块

此文件定义了订单模型类，用于表示用户的购票订单。

作者: FOSSASIA
"""

import time

from flask_jwt_extended import current_user
from sqlalchemy.sql import func

from app.api.helpers.db import get_new_identifier
from app.api.helpers.storage import UPLOAD_PATHS, generate_hash
from app.models import db
from app.models.ticket_holder import TicketHolder
from app.settings import get_settings


def get_new_id():
    """
    生成新的订单标识符
    
    返回:
        str: 新的订单标识符
    """
    return get_new_identifier(Order)


def get_updatable_fields():
    """
    获取可更新字段列表
    
    返回用户可以使用预付款表单修改的字段列表。
    
    返回:
        list: 可更新的字段名称列表
    """
    return [
        'country',           # 国家
        'address',           # 地址
        'city',              # 城市
        'state',             # 州/省
        'zipcode',           # 邮编
        'company',           # 公司
        'tax_business_info', # 税务信息
        'status',            # 状态
        'paid_via',          # 支付方式
        'order_notes',       # 订单备注
        'payment_mode',      # 支付模式
        'tickets_pdf_url',   # 票券PDF URL
        'is_billing_enabled', # 是否启用账单
    ]


class OrderTicket(db.Model):
    """
    订单票券关联模型
    
    表示订单和票券之间的多对多关系，包含数量和价格信息。
    """
    
    __tablename__ = 'orders_tickets'  # 数据库表名
    
    order_id = db.Column(
        db.Integer, db.ForeignKey('orders.id', ondelete='CASCADE'), primary_key=True
    )  # 订单ID
    ticket_id = db.Column(
        db.Integer, db.ForeignKey('tickets.id', ondelete='CASCADE'), primary_key=True
    )  # 票券ID
    quantity = db.Column(db.Integer)  # 数量
    price = db.Column(db.Float, default=0)  # 价格


class Order(db.Model):
    """
    订单模型类
    
    此类代表用户的购票订单，包含订单信息、支付信息、用户信息等。
    """
    
    __tablename__ = "orders"  # 数据库表名

    class Status:
        """订单状态枚举"""
        INITIALIZING = 'initializing'  # 初始化中
        PENDING = 'pending'            # 待处理
        COMPLETED = 'completed'        # 已完成
        CANCELLED = 'cancelled'          # 已取消
        EXPIRED = 'expired'              # 已过期

    # 基本信息
    id = db.Column(db.Integer, primary_key=True)  # 订单ID
    identifier = db.Column(db.String, unique=True, default=get_new_id)  # 订单标识符
    amount = db.Column(db.Float, nullable=False, default=0)  # 金额
    address = db.Column(db.String)  # 地址
    city = db.Column(db.String)  # 城市
    state = db.Column(db.String)  # 州/省
    country = db.Column(db.String)  # 国家
    zipcode = db.Column(db.String)  # 邮编
    company = db.Column(db.String)  # 公司
    tax_business_info = db.Column(db.String)  # 税务信息
    
    # 用户关联
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'))  # 用户ID
    event_id = db.Column(db.Integer, db.ForeignKey('events.id', ondelete='SET NULL'))  # 事件ID
    marketer_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'))  # 市场人员ID
    
    # 时间信息
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())  # 创建时间
    completed_at = db.Column(db.DateTime(timezone=True), nullable=True, default=None)  # 完成时间
    trashed_at = db.Column(db.DateTime(timezone=True), nullable=True, default=None)  # 删除时间
    
    # 支付信息
    transaction_id = db.Column(db.String)  # 交易ID
    paid_via = db.Column(db.String)  # 支付方式
    payment_mode = db.Column(db.String)  # 支付模式
    is_billing_enabled = db.Column(db.Boolean, nullable=False, default=False)  # 是否启用账单
    
    # 信用卡信息
    brand = db.Column(db.String)  # 品牌
    exp_month = db.Column(db.Integer)  # 到期月份
    exp_year = db.Column(db.Integer)  # 到期年份
    last4 = db.Column(db.String)  # 卡号后四位
    
    # 支付令牌
    stripe_token = db.Column(db.String)  # Stripe令牌
    stripe_payment_intent_id = db.Column(db.String)  # Stripe支付意图ID
    paypal_token = db.Column(db.String)  # PayPal令牌
    
    # 订单状态
    status = db.Column(db.String, default='initializing')  # 状态
    cancel_note = db.Column(db.String, nullable=True)  # 取消备注
    order_notes = db.Column(db.String)  # 订单备注
    tickets_pdf_url = db.Column(db.String)  # 票券PDF URL

    # 折扣码关联
    discount_code_id = db.Column(
        db.Integer,
        db.ForeignKey('discount_codes.id', ondelete='SET NULL'),
        nullable=True,
        default=None,
    )  # 折扣码ID
    discount_code = db.relationship('DiscountCode', backref='orders')  # 折扣码关联
    
    # 访问码关联
    access_code_id = db.Column(
        db.Integer,
        db.ForeignKey('access_codes.id', ondelete='SET NULL'),
        nullable=True,
        default=None,
    )  # 访问码ID
    access_code = db.relationship('AccessCode', backref='orders')  # 访问码关联

    # 关联关系
    event = db.relationship('Event', backref='orders')  # 事件关联
    user = db.relationship('User', backref='orders', foreign_keys=[user_id])  # 用户关联
    marketer = db.relationship(
        'User', backref='marketed_orders', foreign_keys=[marketer_id]
    )  # 市场人员关联
    tickets = db.relationship("Ticket", secondary='orders_tickets', backref='order')  # 票券关联
    order_tickets = db.relationship("OrderTicket", backref='order')  # 订单票券关联

    def __repr__(self):
        return '<Order %r>' % self.id

    def get_invoice_number(self):
        """
        获取发票号码
        
        根据订单创建时间和ID生成发票号码。
        
        返回:
            str: 发票号码
        """
        return (
            'O' + str(int(time.mktime(self.created_at.timetuple()))) + '-' + str(self.id)
        )

    @property
    def invoice_number(self):
        """
        发票号码属性
        
        返回:
            str: 发票号码
        """
        return self.get_invoice_number()

    @property
    def tickets_count(self):
        """
        票券数量属性
        
        返回:
            int: 订单中的票券总数
        """
        return sum(t.quantity for t in self.order_tickets)

    @property
    def is_free(self):
        """
        是否免费属性
        
        返回:
            bool: 如果订单是免费的则返回True，否则返回False
        """
        return self.payment_mode == 'free'

    def get_revenue(self):
        """
        获取收入
        
        计算订单的收入，扣除平台费用。
        
        返回:
            float: 订单收入
        """
        if self.amount:
            return self.amount - min(
                self.amount * (self.event.fee / 100.0), self.event.maximum_fee
            )
        return 0.0

    # Saves the order and generates and sends appropriate
    # documents and notifications
    def populate_and_save(self) -> None:
        """
        保存订单并生成相关文档和通知
        
        保存订单并生成相应的文档和通知。
        """
        from app.api.orders import save_order

        save_order(self)

    def is_attendee(self, user) -> bool:
        """
        检查用户是否为订单参与者
        
        参数:
            user: 用户对象
            
        返回:
            bool: 如果用户是订单参与者则返回True，否则返回False
        """
        return db.session.query(
            TicketHolder.query.filter_by(order_id=self.id, user=user).exists()
        ).scalar()

    @property
    def ticket_pdf_path(self) -> str:
        """
        票券PDF路径属性
        
        返回:
            str: 票券PDF文件路径
        """
        key = UPLOAD_PATHS['pdf']['tickets_all'].format(
            identifier=self.identifier, extra_identifier=self.identifier
        )
        return f'generated/tickets/{key}/{generate_hash(key)}/{self.identifier}.pdf'

    @property
    def invoice_pdf_path(self) -> str:
        """
        发票PDF路径属性
        
        返回:
            str: 发票PDF文件路径
        """
        key = UPLOAD_PATHS['pdf']['order'].format(identifier=self.identifier)
        return f'generated/invoices/{key}/{generate_hash(key)}/{self.identifier}.pdf'

    @property
    def filtered_ticket_holders(self):
        """
        过滤的票券持有者属性
        
        根据用户权限返回票券持有者列表。
        
        返回:
            list: 票券持有者列表
        """
        from app.api.helpers.permission_manager import has_access

        query_ = TicketHolder.query.filter_by(order_id=self.id, deleted_at=None)
        if (
            not has_access(
                'is_coorganizer',
                event_id=self.event_id,
            )
            and current_user.id != self.user_id
        ):
            query_ = query_.filter(TicketHolder.user == current_user)
        return query_.all()

    @property
    def safe_user(self):
        """
        安全用户属性
        
        根据用户权限返回用户对象或None。
        
        返回:
            User or None: 用户对象或None
        """
        from app.api.helpers.permission_manager import has_access

        if (
            not has_access(
                'is_coorganizer',
                event_id=self.event_id,
            )
            and current_user.id != self.user_id
        ):
            return None
        return self.user

    @property
    def site_view_link(self) -> str:
        """
        站点查看链接属性
        
        返回:
            str: 订单查看链接
        """
        frontend_url = get_settings()['frontend_url']
        return frontend_url + '/orders/' + self.identifier + '/view'
