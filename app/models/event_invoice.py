#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
事件发票模型 - Open Event Server 事件发票管理模块

此文件定义了事件发票模型类，用于表示事件的月度发票。

作者: FOSSASIA
"""

import logging
from datetime import datetime, timedelta

import pytz
from flask.templating import render_template
from sqlalchemy.sql import func

from app.api.helpers.files import create_save_pdf
from app.api.helpers.mail import send_email_for_monthly_fee_payment
from app.api.helpers.notification import notify_monthly_payment
from app.api.helpers.storage import UPLOAD_PATHS
from app.api.helpers.utilities import monthdelta, round_money
from app.models import db
from app.models.base import SoftDeletionModel
from app.models.order import Order
from app.models.setting import Setting
from app.models.ticket_fee import TicketFees
from app.settings import get_settings

logger = logging.getLogger(__name__)


class EventInvoice(SoftDeletionModel):
    """
    事件发票模型类
    
    此类代表事件的月度发票，用于向事件组织者收取平台费用。
    """
    
    # 发票到期天数
    DUE_DATE_DAYS = 30
    # 生成发票的最低金额
    MIN_AMOUNT = 2  # Minimum amount for which the invoice will be generated

    __tablename__ = 'event_invoices'  # 数据库表名

    # 基本信息
    id = db.Column(db.Integer, primary_key=True)  # 发票ID
    identifier = db.Column(db.String, unique=True, nullable=False)  # 发票标识符
    amount = db.Column(db.Float)  # 金额

    # 用户和事件关联
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'))  # 用户ID
    event_id = db.Column(db.Integer, db.ForeignKey('events.id', ondelete='SET NULL'))  # 事件ID

    # 时间信息
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())  # 创建时间
    issued_at = db.Column(db.DateTime(timezone=True), nullable=False)  # 签发时间

    # 支付字段
    completed_at = db.Column(db.DateTime(timezone=True), nullable=True, default=None)  # 完成时间
    transaction_id = db.Column(db.String)  # 交易ID
    paid_via = db.Column(db.String)  # 支付方式
    payment_mode = db.Column(db.String)  # 支付模式
    brand = db.Column(db.String)  # 品牌
    exp_month = db.Column(db.Integer)  # 到期月份
    exp_year = db.Column(db.Integer)  # 到期年份
    last4 = db.Column(db.String)  # 卡号后四位
    stripe_token = db.Column(db.String)  # Stripe令牌
    paypal_token = db.Column(db.String)  # PayPal令牌
    status = db.Column(db.String, default='due')  # 状态

    # PDF链接
    invoice_pdf_url = db.Column(db.String)  # 发票PDF URL

    # 关联关系
    event = db.relationship('Event', backref='invoices')  # 事件关联
    user = db.relationship('User', backref='event_invoices')  # 用户关联

    def __init__(self, **kwargs):
        """
        初始化事件发票
        
        参数:
            **kwargs: 关键字参数
        """
        super().__init__(**kwargs)

        if not self.issued_at:
            self.issued_at = datetime.now()

        if not self.identifier:
            self.identifier = self.get_new_id()

    def __repr__(self):
        """
        字符串表示
        
        返回:
            str: 事件发票对象的字符串表示
        """
        return '<EventInvoice {!r} {!r} {!r}>'.format(
            self.id,
            self.identifier,
            self.invoice_pdf_url,
        )

    def get_new_id(self) -> str:
        """
        获取新的发票标识符
        
        返回:
            str: 新的发票标识符
        """
        with db.session.no_autoflush:
            identifier = self.issued_at.strftime('%Y%mU-') + '%06d' % (
                EventInvoice.query.count() + 1
            )
            count = EventInvoice.query.filter_by(identifier=identifier).count()
            if count == 0:
                return identifier
            return self.get_new_id()

    @property
    def previous_month_date(self):
        """
        获取上个月的日期
        
        返回:
            datetime: 上个月的日期
        """
        return monthdelta(self.issued_at, -1)

    @property
    def due_at(self):
        """
        获取到期日期
        
        返回:
            datetime: 到期日期
        """
        return self.issued_at + timedelta(days=EventInvoice.DUE_DATE_DAYS)

    def populate(self):
        """
        填充发票信息
        
        设置发票的用户并生成PDF。
        
        返回:
            str: 发票PDF URL
        """
        assert self.event is not None

        with db.session.no_autoflush:
            self.user = self.event.owner
            return self.generate_pdf()

    def generate_pdf(self, force=False):
        """
        生成发票PDF
        
        根据事件的销售数据生成发票PDF。
        
        参数:
            force (bool): 是否强制生成，即使金额为0
            
        返回:
            str: 发票PDF URL
        """
        with db.session.no_autoflush:
            # 获取最新的发票日期
            latest_invoice_date = (
                EventInvoice.query.filter_by(event=self.event)
                .filter(EventInvoice.issued_at < self.issued_at)
                .with_entities(func.max(EventInvoice.issued_at))
                .scalar()
            )

            # 获取管理员信息
            admin_info = Setting.query.first()
            currency = self.event.payment_currency
            
            # 获取票务费用对象
            ticket_fee_object = (
                TicketFees.query.filter_by(country=self.event.payment_country).first()
                or TicketFees.query.filter_by(country='global').first()
            )
            if not ticket_fee_object:
                logger.error('Ticket Fee not found for event %s', self.event)
                return

            # 计算费用
            ticket_fee_percentage = ticket_fee_object.service_fee
            ticket_fee_maximum = ticket_fee_object.maximum_fee
            gross_revenue = self.event.calc_revenue(
                start=latest_invoice_date, end=self.issued_at
            )
            invoice_amount = gross_revenue * (ticket_fee_percentage / 100)
            if invoice_amount > ticket_fee_maximum:
                invoice_amount = ticket_fee_maximum
            self.amount = round_money(invoice_amount)
            
            # 检查金额是否满足生成条件
            if not force and self.amount == 0:
                logger.warning(
                    'Invoice amount of Event %s is 0, hence skipping generation',
                    self.event,
                )
                return
            if not force and self.amount < EventInvoice.MIN_AMOUNT:
                logger.warning(
                    'Invoice amount of Event %s is %f which is less than %f, hence skipping generation',
                    self.event,
                    self.amount,
                    EventInvoice.MIN_AMOUNT,
                )
                return
                
            # 计算净收入
            net_revenue = round_money(gross_revenue - invoice_amount)
            
            # 获取订单信息
            orders_query = self.event.get_orders_query(
                start=latest_invoice_date, end=self.issued_at
            )
            first_order_date = orders_query.with_entities(
                func.min(Order.completed_at)
            ).scalar()
            last_order_date = orders_query.with_entities(
                func.max(Order.completed_at)
            ).scalar()
            
            # 支付详情
            payment_details = {
                'tickets_sold': self.event.tickets_sold,
                'gross_revenue': round_money(gross_revenue),
                'net_revenue': round_money(net_revenue),
                'first_date': first_order_date or self.previous_month_date,
                'last_date': last_order_date or self.issued_at,
            }
            
            # 生成PDF
            self.invoice_pdf_url = create_save_pdf(
                render_template(
                    'pdf/event_invoice.html',
                    user=self.user,
                    admin_info=admin_info,
                    currency=currency,
                    event=self.event,
                    ticket_fee=ticket_fee_object,
                    payment_details=payment_details,
                    net_revenue=net_revenue,
                    invoice=self,
                ),
                UPLOAD_PATHS['pdf']['event_invoice'],
                dir_path='/static/uploads/pdf/event_invoices/',
                identifier=self.identifier,
                extra_identifiers={'event_identifier': self.event.identifier},
                new_renderer=True,
            )

        return self.invoice_pdf_url

    def send_notification(self, follow_up=False):
        """
        发送通知
        
        向用户发送发票通知邮件和系统通知。
        
        参数:
            follow_up (bool): 是否为跟进通知
        """
        # 格式化上个月的日期
        prev_month = self.previous_month_date.astimezone(
            pytz.timezone(self.event.timezone)
        ).strftime(
            "%b %Y"
        )  # Displayed as Aug 2016
        
        # 获取应用设置
        app_name = get_settings()['app_name']
        frontend_url = get_settings()['frontend_url']
        link = f'{frontend_url}/event-invoice/{self.identifier}/review'
        currency = self.event.payment_currency
        amount = f"{currency} {self.amount:.2f}"
        
        # 发送邮件
        send_email_for_monthly_fee_payment(
            self.user,
            self.event.name,
            prev_month,
            amount,
            app_name,
            link,
            follow_up=follow_up,
        )
        
        # 发送系统通知
        if isinstance(follow_up, bool):
            notify_monthly_payment(self, follow_up)
