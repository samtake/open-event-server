#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
事件模型 - Open Event Server 事件管理模块

此文件定义了事件模型类，包含事件的完整信息和相关功能。

作者: FOSSASIA
"""

import re
from argparse import Namespace
from datetime import datetime

import flask_login as login
import pytz
from flask import current_app
from flask_babel import _
from sqlalchemy import event
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from sqlalchemy.sql.expression import and_, or_

from app.api.helpers.db import get_new_identifier
from app.models import db
from app.models.base import SoftDeletionModel
from app.models.email_notification import EmailNotification
from app.models.event_topic import EventTopic
from app.models.feedback import Feedback
from app.models.helpers.versioning import clean_html, clean_up_string
from app.models.order import Order
from app.models.role import Role
from app.models.search import sync
from app.models.session import Session
from app.models.speaker import Speaker
from app.models.ticket import Ticket
from app.models.ticket_fee import get_fee, get_maximum_fee
from app.models.ticket_holder import TicketHolder
from app.settings import get_settings


def get_new_event_identifier(length=8):
    """
    生成新的事件标识符
    
    参数:
        length (int): 标识符长度，默认为8
        
    返回:
        str: 新的事件标识符
    """
    return get_new_identifier(Event, length=length)


class Event(SoftDeletionModel):
    """
    事件模型类
    
    此类代表系统中的事件，包含事件的完整信息，如基本信息、时间、地点、
    票务、支付选项等。
    """

    class State:
        """事件状态枚举"""
        PUBLISHED = 'published'  # 已发布
        DRAFT = 'draft'          # 草稿

    class Privacy:
        """事件隐私设置枚举"""
        PUBLIC = 'public'    # 公开
        PRIVATE = 'private'  # 私有

    __tablename__ = 'events'  # 数据库表名
    __versioned__ = {'exclude': ['schedule_published_on', 'created_at']}  # 版本控制排除字段
    
    # 基本信息
    id = db.Column(db.Integer, primary_key=True)  # 事件ID
    identifier = db.Column(
        db.String, default=get_new_event_identifier, nullable=False, unique=True
    )  # 事件唯一标识符
    name = db.Column(db.String, nullable=False)  # 事件名称
    external_event_url = db.Column(db.String)  # 外部事件URL
    logo_url = db.Column(db.String)  # Logo URL
    
    # 时间信息
    starts_at = db.Column(db.DateTime(timezone=True), nullable=False)  # 开始时间
    ends_at = db.Column(db.DateTime(timezone=True), nullable=False)    # 结束时间
    timezone = db.Column(db.String, nullable=False, default="UTC")    # 时区
    
    # 地点信息
    online = db.Column(db.Boolean, nullable=False, default=False, server_default='False')  # 是否在线活动
    latitude = db.Column(db.Float)    # 纬度
    longitude = db.Column(db.Float)   # 经度
    location_name = db.Column(db.String)  # 地点名称
    searchable_location_name = db.Column(db.String)  # 可搜索地点名称
    
    # 直播设置
    public_stream_link = db.Column(db.String)  # 公共直播链接
    stream_loop = db.Column(db.Boolean, default=False)  # 是否循环播放
    stream_autoplay = db.Column(db.Boolean, default=False)  # 是否自动播放
    
    # 事件状态
    is_featured = db.Column(db.Boolean, default=False, nullable=False)  # 是否精选
    is_promoted = db.Column(db.Boolean, default=False, nullable=False)  # 是否推广
    is_demoted = db.Column(db.Boolean, default=False, nullable=False)  # 是否降级
    
    # 功能开关
    is_chat_enabled = db.Column(db.Boolean, default=False, nullable=False)  # 是否启用聊天
    is_videoroom_enabled = db.Column(db.Boolean, default=False, nullable=False)  # 是否启用视频室
    is_document_enabled = db.Column(db.Boolean, default=False, nullable=False)  # 是否启用文档
    document_links = db.Column(JSONB)  # 文档链接
    chat_room_id = db.Column(db.String)  # 聊天室ID
    
    # 描述信息
    description = db.Column(db.Text)  # 事件描述
    after_order_message = db.Column(db.Text)  # 订单后消息
    
    # 图片信息
    original_image_url = db.Column(db.String)  # 原始图片URL
    thumbnail_image_url = db.Column(db.String)  # 缩略图URL
    large_image_url = db.Column(db.String)   # 大图URL
    icon_image_url = db.Column(db.String)    # 图标URL
    show_remaining_tickets = db.Column(db.Boolean, default=False, nullable=False)  # 是否显示剩余票
    
    # 所有者信息
    owner_name = db.Column(db.String)  # 所有者名称
    owner_description = db.Column(db.String)  # 所有者描述
    has_owner_info = db.Column(db.Boolean)  # 是否有所有者信息
    
    # 地图设置
    is_map_shown = db.Column(db.Boolean)  # 是否显示地图
    is_oneclick_signup_enabled = db.Column(db.Boolean)  # 是否启用一键注册
    
    # 功能开关
    is_sessions_speakers_enabled = db.Column(db.Boolean, default=False)  # 是否启用会话和演讲者
    is_cfs_enabled = db.Column(
        db.Boolean, default=False, nullable=False, server_default='False'
    )  # 是否启用征集演讲
    
    # 关联关系
    track = db.relationship('Track', backref="event")  # 轨道关联
    microlocation = db.relationship('Microlocation', backref="event")  # 微地点关联
    session = db.relationship('Session', backref="event")  # 会话关联
    speaker = db.relationship('Speaker', backref="event")  # 演讲者关联
    sponsor = db.relationship('Sponsor', backref="event")  # 赞助商关联
    exhibitors = db.relationship('Exhibitor', backref="event")  # 参展商关联
    tickets = db.relationship('Ticket', backref="event_")  # 票券关联
    tags = db.relationship('TicketTag', backref='events')  # 标签关联
    roles = db.relationship("UsersEventsRoles", backref="event")  # 角色关联
    role_invites = db.relationship('RoleInvite', back_populates='event')  # 角色邀请关联
    custom_form = db.relationship('CustomForms', backref="event")  # 自定义表单关联
    faqs = db.relationship('Faq', backref="event")  # 常见问题关联
    feedbacks = db.relationship('Feedback', backref="event")  # 反馈关联
    attendees = db.relationship('TicketHolder', backref="event")  # 参会者关联
    
    # 状态和设置
    privacy = db.Column(db.String, default="public")  # 隐私设置
    state = db.Column(db.String, default="draft")      # 事件状态
    
    # 分类关联
    event_type_id = db.Column(
        db.Integer, db.ForeignKey('event_types.id', ondelete='CASCADE')
    )  # 事件类型ID
    event_topic_id = db.Column(
        db.Integer, db.ForeignKey('event_topics.id', ondelete='CASCADE')
    )  # 事件主题ID
    event_sub_topic_id = db.Column(
        db.Integer, db.ForeignKey('event_sub_topics.id', ondelete='CASCADE')
    )  # 事件子主题ID
    
    # 组关联
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id', ondelete='SET NULL'))  # 组ID
    
    # 公告状态
    is_announced = db.Column(
        db.Boolean, default=False, nullable=False, server_default='False'
    )  # 是否已公告
    
    # URL信息
    ticket_url = db.Column(db.String)  # 票券URL
    
    # 约束
    db.UniqueConstraint('track.name')  # 轨道名称唯一约束
    
    # 行为准则
    code_of_conduct = db.Column(db.String)  # 行为准则
    
    # 日程发布
    schedule_published_on = db.Column(db.DateTime(timezone=True))  # 日程发布时间
    
    # 票务设置
    is_ticketing_enabled = db.Column(db.Boolean, default=False)  # 是否启用票务
    is_donation_enabled = db.Column(db.Boolean, default=False)     # 是否启用捐赠
    is_ticket_form_enabled = db.Column(db.Boolean, default=True, nullable=False)  # 是否启用票券表单
    is_badges_enabled = db.Column(db.Boolean, default=False)  # 是否启用徽章
    
    # 支付设置
    payment_country = db.Column(db.String)  # 支付国家
    payment_currency = db.Column(db.String)  # 支付货币
    paypal_email = db.Column(db.String)     # PayPal邮箱
    
    # 税务设置
    is_tax_enabled = db.Column(db.Boolean, default=False)  # 是否启用税务
    is_billing_info_mandatory = db.Column(db.Boolean, default=False, nullable=False)  # 账单信息是否必填
    
    # 支付方式
    can_pay_by_paypal = db.Column(
        db.Boolean, default=False, nullable=False, server_default='False'
    )  # 是否支持PayPal支付
    can_pay_by_stripe = db.Column(
        db.Boolean, default=False, nullable=False, server_default='False'
    )  # 是否支持Stripe支付
    can_pay_by_cheque = db.Column(
        db.Boolean, default=False, nullable=False, server_default='False'
    )  # 是否支持支票支付
    can_pay_by_bank = db.Column(
        db.Boolean, default=False, nullable=False, server_default='False'
    )  # 是否支持银行转账
    can_pay_by_invoice = db.Column(
        db.Boolean, default=False, nullable=False, server_default='False'
    )  # 是否支持发票支付
    can_pay_onsite = db.Column(
        db.Boolean, default=False, nullable=False, server_default='False'
    )  # 是否支持现场支付
    can_pay_by_omise = db.Column(
        db.Boolean, default=False, nullable=False, server_default='False'
    )  # 是否支持Omise支付
    can_pay_by_alipay = db.Column(
        db.Boolean, default=False, nullable=False, server_default='False'
    )  # 是否支持支付宝支付
    can_pay_by_paytm = db.Column(
        db.Boolean, default=False, nullable=False, server_default='False'
    )  # 是否支持Paytm支付
    
    # 支付详情
    cheque_details = db.Column(db.String)  # 支票详情
    bank_details = db.Column(db.String)    # 银行详情
    onsite_details = db.Column(db.String)  # 现场支付详情
    invoice_details = db.Column(db.String)  # 发票详情
    
    # 时间戳
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())  # 创建时间
    
    # URL信息
    pentabarf_url = db.Column(db.String)  # Pentabarf URL
    ical_url = db.Column(db.String)       # iCal URL
    xcal_url = db.Column(db.String)       # xCal URL
    
    # 赞助商
    is_sponsors_enabled = db.Column(db.Boolean, default=False)  # 是否启用赞助商
    
    # 退款政策
    refund_policy = db.Column(db.String)  # 退款政策
    
    # Stripe集成
    is_stripe_linked = db.Column(db.Boolean, default=False)  # 是否已连接Stripe
    
    # 销售统计
    completed_order_sales = db.Column(db.Integer)  # 已完成订单销售额
    placed_order_sales = db.Column(db.Integer)    # 已下单销售额
    pending_order_sales = db.Column(db.Integer)   # 待处理销售额
    completed_order_tickets = db.Column(db.Integer)  # 已完成订单票数
    placed_order_tickets = db.Column(db.Integer)     # 已下单票数
    pending_order_tickets = db.Column(db.Integer)    # 待处理票数
    
    # 折扣码
    discount_code_id = db.Column(
        db.Integer, db.ForeignKey('discount_codes.id', ondelete='CASCADE')
    )  # 折扣码ID
    discount_code = db.relationship(
        'DiscountCode', backref='events', foreign_keys=[discount_code_id]
    )  # 折扣码关联
    
    # 分类关联
    event_type = db.relationship(
        'EventType', backref='event', foreign_keys=[event_type_id]
    )  # 事件类型关联
    event_topic = db.relationship(
        'EventTopic', backref='event', foreign_keys=[event_topic_id]
    )  # 事件主题关联
    event_sub_topic = db.relationship(
        'EventSubTopic', backref='event', foreign_keys=[event_sub_topic_id]
    )  # 事件子主题关联
    
    # 组关联
    group = db.relationship('Group', backref='events', foreign_keys=[group_id])  # 组关联
    
    # 用户角色关联
    owner = db.relationship(
        'User',
        viewonly=True,
        secondary='join(UsersEventsRoles, Role,'
        ' and_(Role.id == UsersEventsRoles.role_id, Role.name == "owner"))',
        primaryjoin='UsersEventsRoles.event_id == Event.id',
        secondaryjoin='User.id == UsersEventsRoles.user_id',
        backref='owner_events',
        sync_backref=False,
        uselist=False,
    )  # 所有者关联
    
    organizers = db.relationship(
        'User',
        viewonly=True,
        secondary='join(UsersEventsRoles, Role,'
        ' and_(Role.id == UsersEventsRoles.role_id, Role.name == "organizer"))',
        primaryjoin='UsersEventsRoles.event_id == Event.id',
        secondaryjoin='User.id == UsersEventsRoles.user_id',
        backref='organizer_events',
        sync_backref=False,
    )  # 组织者关联
    
    coorganizers = db.relationship(
        'User',
        viewonly=True,
        secondary='join(UsersEventsRoles, Role,'
        ' and_(Role.id == UsersEventsRoles.role_id, Role.name == "coorganizer"))',
        primaryjoin='UsersEventsRoles.event_id == Event.id',
        secondaryjoin='User.id == UsersEventsRoles.user_id',
        backref='coorganizer_events',
        sync_backref=False,
    )  # 共同组织者关联
    
    track_organizers = db.relationship(
        'User',
        viewonly=True,
        secondary='join(UsersEventsRoles, Role,'
        ' and_(Role.id == UsersEventsRoles.role_id,'
        ' Role.name == "track_organizer"))',
        primaryjoin='UsersEventsRoles.event_id == Event.id',
        secondaryjoin='User.id == UsersEventsRoles.user_id',
        backref='track_organizer_events',
        sync_backref=False,
    )  # 轨道组织者关联
    
    registrars = db.relationship(
        'User',
        viewonly=True,
        secondary='join(UsersEventsRoles, Role,'
        ' and_(Role.id == UsersEventsRoles.role_id, Role.name == "registrar"))',
        primaryjoin='UsersEventsRoles.event_id == Event.id',
        secondaryjoin='User.id == UsersEventsRoles.user_id',
        backref='registrar_events',
        sync_backref=False,
    )  # 注册员关联
    
    moderators = db.relationship(
        'User',
        viewonly=True,
        secondary='join(UsersEventsRoles, Role,'
        ' and_(Role.id == UsersEventsRoles.role_id, Role.name == "moderator"))',
        primaryjoin='UsersEventsRoles.event_id == Event.id',
        secondaryjoin='User.id == UsersEventsRoles.user_id',
        backref='moderator_events',
        sync_backref=False,
    )  # 主持人关联
    
    # 所有工作人员
    users = db.relationship(
        'User',
        viewonly=True,
        secondary='join(UsersEventsRoles, Role,'
        ' and_(Role.id == UsersEventsRoles.role_id))',
        primaryjoin='UsersEventsRoles.event_id == Event.id',
        secondaryjoin='User.id == UsersEventsRoles.user_id',
        backref='events',
        sync_backref=False,
    )  # 所有用户关联

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        original_image_url = kwargs.get('original_image_url')
        self.original_image_url = (
            self.set_default_event_image(kwargs.get('event_topic_id'))
            if original_image_url is None
            else original_image_url
        )
        # TODO(Areeb): Test for cleaning up of these on __init__
        self.description = clean_up_string(kwargs.get('description'))
        self.owner_description = clean_up_string(kwargs.get('owner_description'))
        self.code_of_conduct = clean_up_string(kwargs.get('code_of_conduct'))
        self.after_order_message = clean_up_string(kwargs.get('after_order_message'))

    def __repr__(self):
        return '<Event %r>' % self.name

    def __setattr__(self, name, value):
        allow_link = name == 'description' or 'owner_description' or 'after_order_message'
        if (
            name == 'owner_description'
            or name == 'description'
            or name == 'code_of_conduct'
            or name == 'after_order_message'
        ):
            super().__setattr__(
                name, clean_html(clean_up_string(value), allow_link=allow_link)
            )
        else:
            super().__setattr__(name, value)

    @classmethod
    def set_default_event_image(cls, event_topic_id):
        """
        设置默认事件图片
        
        根据事件主题ID获取对应的系统默认图片URL。
        
        参数:
            event_topic_id (int): 事件主题ID
            
        返回:
            str or None: 系统默认图片URL，如果没有找到则返回None
        """
        if event_topic_id is None:
            return None
        event_topic = EventTopic.query.filter_by(id=event_topic_id).first()
        return event_topic.system_image_url

    @property
    def fee(self):
        """
        获取事件手续费率
        
        返回该事件的手续费率（百分比，0-100）。
        
        返回:
            float: 手续费率百分比
        """
        return get_fee(self.payment_country, self.payment_currency)

    @property
    def maximum_fee(self):
        """
        获取事件最大手续费
        
        返回该事件的最大手续费金额。
        
        返回:
            float: 最大手续费金额
        """
        return get_maximum_fee(self.payment_country, self.payment_currency)

    def notification_settings(self, user_id):
        """
        获取用户的通知设置
        
        查询指定用户对该事件的通知设置。
        
        参数:
            user_id (int): 用户ID，如果为None则使用当前登录用户
            
        返回:
            EmailNotification or None: 通知设置对象，如果不存在则返回None
        """
        try:
            return (
                EmailNotification.query.filter_by(
                    user_id=(login.current_user.id if not user_id else int(user_id))
                )
                .filter_by(event_id=self.id)
                .first()
            )
        except:
            return None

    def get_average_rating(self):
        """
        获取事件的平均评分
        
        计算该事件的所有反馈的平均评分。
        
        返回:
            float or None: 平均评分（保留两位小数），如果没有评分则返回None
        """
        avg = (
            db.session.query(func.avg(Feedback.rating))
            .filter_by(event_id=self.id)
            .scalar()
        )
        if avg is not None:
            avg = round(avg, 2)
        return avg

    def is_payment_enabled(self):
        """
        检查事件是否启用了支付功能
        
        检查事件是否配置了至少一种支付方式。
        
        返回:
            bool: 是否启用了支付功能
        """
        return (
            self.can_pay_by_paypal
            or self.can_pay_by_stripe
            or self.can_pay_by_omise
            or self.can_pay_by_alipay
            or self.can_pay_by_cheque
            or self.can_pay_by_bank
            or self.can_pay_onsite
            or self.can_pay_by_paytm
            or self.can_pay_by_invoice
        )

    @property
    def average_rating(self):
        """
        事件的平均评分属性
        
        返回该事件的平均评分。
        
        返回:
            float or None: 平均评分
        """
        return self.get_average_rating()

    def get_owner(self):
        """
        获取事件所有者
        
        返回事件的所有者用户对象。
        
        返回:
            User or None: 事件所有者，如果没有找到则返回None
        """
        for role in self.roles:
            if role.role.name == Role.OWNER:
                return role.user
        return None

    def as_dict(self):
        """
        将事件对象转换为字典
        
        返回包含事件所有字段的字典表示。
        
        返回:
            dict: 事件字段字典
        """
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    @property
    def tickets_sold_object(self):
        """
        获取已售出门票查询对象
        
        返回一个查询对象，用于查询该事件的已完成订单中的参会者。
        
        返回:
            Query: 查询对象
        """
        obj = (
            db.session.query(Order.event_id)
            .filter_by(event_id=self.id, status='completed')
            .join(TicketHolder)
        )
        return obj

    def calc_tickets_sold_count(self):
        """
        计算已售出门票总数
        
        返回该事件所有已完成订单中的参会者总数。
        
        返回:
            int: 已售出门票总数
        """
        return self.tickets_sold_object.count()

    def calc_tickets_sold_prev_month(self):
        """
        计算上月售出门票数
        
        返回该事件在上个月售出的门票数量。
        
        返回:
            int: 上月售出门票数
        """
        previous_month = datetime.now().month - 1
        return self.tickets_sold_object.filter_by(completed_at=previous_month).count()

    def calc_total_tickets_count(self):
        """
        计算总可用门票数
        
        返回该事件所有票券类型的总可用门票数量。
        
        返回:
            int: 总可用门票数
        """
        total_available = (
            db.session.query(func.sum(Ticket.quantity))
            .filter_by(event_id=self.id)
            .scalar()
        )
        if total_available is None:
            total_available = 0
        return total_available

    def get_orders_query(self, start=None, end=None):
        """
        获取订单查询对象
        
        返回一个查询对象，用于查询该事件在指定时间范围内的已完成订单。
        
        参数:
            start (datetime, optional): 开始时间
            end (datetime, optional): 结束时间
            
        返回:
            Query: 订单查询对象
        """
        query = Order.query.filter_by(event_id=self.id, status='completed')
        if start:
            query = query.filter(Order.completed_at > start)
        if end:
            query = query.filter(Order.completed_at < end)
        return query

    def calc_revenue(self, start=None, end=None):
        """
        计算事件收入
        
        计算该事件在指定时间范围内所有已完成订单的总收入。
        
        参数:
            start (datetime, optional): 开始时间
            end (datetime, optional): 结束时间
            
        返回:
            float: 总收入金额
        """
    @property
    def chat_room_name(self):
        """
        获取聊天室名称
        
        根据事件名称和标识符生成聊天室名称。
        
        返回:
            str: 聊天室名称
        """
        return re.sub('[^0-9a-zA-Z!]', '-', self.name) + '-' + self.identifier

    @property
    def tickets_available(self):
        """
        可用门票数属性
        
        返回该事件的总可用门票数。
        
        返回:
            int: 可用门票数
        """
        return self.calc_total_tickets_count()

    @property
    def tickets_sold(self):
        """
        已售出门票数属性
        
        返回该事件的已售出门票总数。
        
        返回:
            int: 已售出门票数
        """
        return self.calc_tickets_sold_count()

    @property
    def revenue(self):
        """
        收入属性
        
        返回该事件的总收入。
        
        返回:
            float: 总收入
        """
        return self.calc_revenue()

    @property
    def has_sessions(self):
        """
        是否有会话属性
        
        检查该事件是否有关联的会话。
        
        返回:
            bool: 是否有会话
        """
        return Session.query.filter_by(event_id=self.id).count() > 0

    @property
    def has_speakers(self):
        """
        是否有演讲者属性
        
        检查该事件是否有关联的演讲者。
        
        返回:
            bool: 是否有演讲者
        """
        return Speaker.query.filter_by(event_id=self.id).count() > 0

    @property
    def order_statistics(self):
        """
        订单统计属性
        
        返回该事件的订单统计信息。
        
        返回:
            Namespace: 订单统计信息
        """
        return Namespace(id=self.id)

    @property
    def general_statistics(self):
        """
        通用统计属性
        
        返回该事件的通用统计信息。
        
        返回:
            Namespace: 通用统计信息
        """
        return Namespace(id=self.id)

    @property
    def site_link(self):
        """
        事件站点链接属性
        
        返回该事件的前端展示页面链接。
        
        返回:
            str: 事件站点链接
        """
        frontend_url = get_settings()['frontend_url']
        return f"{frontend_url}/e/{self.identifier}"

    @property
    def organizer_site_link(self):
        """
        组织者站点链接属性
        
        返回该事件的管理页面链接。
        
        返回:
            str: 组织者站点链接
        """
        frontend_url = get_settings()['frontend_url']
        return f"{frontend_url}/events/{self.identifier}"

    @property
    def starts_at_tz(self):
        """
        开始时间（时区转换）属性
        
        返回该事件在指定时区的开始时间。
        
        返回:
            datetime: 开始时间（已转换时区）
        """
        return self.starts_at.astimezone(pytz.timezone(self.timezone))

    @property
    def ends_at_tz(self):
        """
        结束时间（时区转换）属性
        
        返回该事件在指定时区的结束时间。
        
        返回:
            datetime: 结束时间（已转换时区）
        """
        return self.ends_at.astimezone(pytz.timezone(self.timezone))

    @property
    def normalized_location(self):
        """
        标准化位置属性
        
        返回该事件的标准化位置信息。
        
        返回:
            str: 位置信息
        """
        if self.location_name:
            return self.location_name
        elif self.online:
            return self.site_link
        return _('Location Not Announced')

    @property
    def event_location_status(self):
        """
        事件位置状态属性
        
        返回该事件的位置状态信息。
        
        返回:
            str: 位置状态信息
        """
        if self.online:
            return _(
                'Online (Please login to the platform to access the video room on the event page)'
            )
        elif self.location_name:
            return self.location_name
        else:
            return _('Location Not Announced')

    @property
    def has_coordinates(self):
        """
        是否有坐标属性
        
        检查该事件是否有经纬度坐标。
        
        返回:
            bool: 是否有坐标
        """
        return self.latitude and self.longitude

    @property
    def safe_video_stream(self):
        """
        安全视频流属性
        
        在应用访问控制后，有条件地返回视频流。
        
        返回:
            VideoStream or None: 视频流对象，如果没有权限则返回None
        """
        stream = self.video_stream
        if stream and stream.user_can_access:
            return stream
        return None

    @property
    def notify_staff(self):
        """
        通知工作人员属性
        
        返回接收事件通知的工作人员列表。
        
        返回:
            list: 工作人员用户列表
        """
        return self.organizers + [self.owner]

    @property
    def tickets_placed_or_completed_count(self):
        """
        已下单或已完成票数属性
        
        返回该事件已下单或已完成的门票数量。
        
        返回:
            int: 已下单或已完成票数
        """
        obj = (
            db.session.query(Order.event_id)
            .filter(
                and_(
                    Order.event_id == self.id,
                    or_(Order.status == 'completed', Order.status == 'placed'),
                )
            )
            .join(TicketHolder)
        )
        return obj.count()


@event.listens_for(Event, 'after_update')
@event.listens_for(Event, 'after_insert')
def receive_init(mapper, connection, target):
    """
    事件更新或插入后监听器
    
    监听事件的更新和插入事件，用于同步到Elasticsearch索引。
    
    参数:
        mapper: SQLAlchemy映射器
        connection: 数据库连接
        target: 事件实例
    """
    if current_app.config['ENABLE_ELASTICSEARCH']:
        if target.state == 'published' and target.deleted_at is None:
            sync.mark_event(sync.REDIS_EVENT_INDEX, target.id)
        elif target.deleted_at:
            sync.mark_event(sync.REDIS_EVENT_DELETE, target.id)


@event.listens_for(Event, 'after_delete')
def receive_after_delete(mapper, connection, target):
    """
    事件删除后监听器
    
    监听事件的删除事件，用于从Elasticsearch索引中移除。
    
    参数:
        mapper: SQLAlchemy映射器
        connection: 数据库连接
        target: 事件实例
    """
    if current_app.config['ENABLE_ELASTICSEARCH']:
        sync.mark_event(sync.REDIS_EVENT_DELETE, target.id)
