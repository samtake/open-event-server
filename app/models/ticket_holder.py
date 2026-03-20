#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
票券持有者模型 - Open Event Server 票券持有者管理模块

此文件定义了票券持有者模型类，用于表示购票的参与者信息。

作者: FOSSASIA
"""

import base64
import binascii
import os
from dataclasses import dataclass
from datetime import datetime
from io import BytesIO

import qrcode
from citext import CIText

from app.api.helpers.storage import UPLOAD_PATHS, generate_hash
from app.models import db
from app.models.base import SoftDeletionModel


def get_new_id():
    """
    为票券持有者生成新的ID
    
    返回:
        str: 新的票券持有者ID
    """
    return str(binascii.b2a_hex(os.urandom(3)), 'utf-8')


@dataclass(init=False, unsafe_hash=True)
class TicketHolder(SoftDeletionModel):
    """
    票券持有者模型类
    
    此类代表购票的参与者，包含个人信息、联系方式、签到状态等。
    """
    
    __tablename__ = "ticket_holders"  # 数据库表名

    # 基本信息
    id: int = db.Column(db.Integer, primary_key=True)  # 票券持有者ID
    firstname: str = db.Column(db.String)  # 名字
    lastname: str = db.Column(db.String)  # 姓氏
    email: str = db.Column(CIText)  # 邮箱（不区分大小写）
    address: str = db.Column(db.String)  # 地址
    city: str = db.Column(db.String)  # 城市
    state: str = db.Column(db.String)  # 州/省
    country: str = db.Column(db.String)  # 国家
    job_title: str = db.Column(db.String)  # 职位
    phone: str = db.Column(db.String)  # 电话
    tax_business_info: str = db.Column(db.String)  # 税务信息
    
    # 地址信息
    billing_address: str = db.Column(db.String)  # 账单地址
    home_address: str = db.Column(db.String)  # 家庭地址
    shipping_address: str = db.Column(db.String)  # 邮寄地址
    company: str = db.Column(db.String)  # 公司
    work_address: str = db.Column(db.String)  # 工作地址
    work_phone: str = db.Column(db.String)  # 工作电话
    
    # 社交媒体
    website: str = db.Column(db.String)  # 网站
    blog: str = db.Column(db.String)  # 博客
    twitter: str = db.Column(db.String)  # Twitter
    facebook: str = db.Column(db.String)  # Facebook
    instagram: str = db.Column(db.String)  # Instagram
    linkedin: str = db.Column(db.String)  # LinkedIn
    github: str = db.Column(db.String)  # GitHub
    
    # 个人信息
    gender: str = db.Column(db.String)  # 性别
    accept_video_recording: bool = db.Column(db.Boolean)  # 是否接受视频录制
    accept_share_details: bool = db.Column(db.Boolean)  # 是否接受分享信息
    accept_receive_emails: bool = db.Column(db.Boolean)  # 是否接受接收邮件
    age_group: str = db.Column(db.String)  # 年龄组
    home_wiki: str = db.Column(db.String)  # 家庭维基
    wiki_scholarship: str = db.Column(db.String)  # 维基奖学金
    
    # 时间信息
    birth_date: datetime = db.Column(db.DateTime(timezone=True))  # 出生日期
    pdf_url: str = db.Column(db.String)  # PDF URL
    
    # 关联关系
    ticket_id: int = db.Column(
        db.Integer, db.ForeignKey('tickets.id', ondelete='CASCADE'), nullable=False
    )  # 票券ID
    order_id: int = db.Column(db.Integer, db.ForeignKey('orders.id', ondelete='CASCADE'))  # 订单ID
    
    # 签到状态
    is_checked_in: bool = db.Column(db.Boolean, default=False)  # 是否已签到
    is_checked_out: bool = db.Column(db.Boolean, default=False)  # 是否已签出
    is_registered: bool = db.Column(db.Boolean, default=False)  # 是否已注册
    device_name_checkin: str = db.Column(db.String)  # 签到设备名称
    checkin_times: str = db.Column(db.String)  # 签到时间
    checkout_times: str = db.Column(db.String)  # 签出时间
    register_times: str = db.Column(db.String)  # 注册时间
    attendee_notes: str = db.Column(db.String)  # 参与者备注
    
    # 事件关联
    event_id: int = db.Column(
        db.Integer, db.ForeignKey('events.id', ondelete='CASCADE'), nullable=False
    )  # 事件ID
    
    # 时间戳
    created_at: datetime = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)  # 创建时间
    modified_at: datetime = db.Column(
        db.DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )  # 修改时间
    
    # 复杂字段
    complex_field_values: str = db.Column(db.JSON)  # 复杂字段值
    
    # 同意选项
    is_consent_of_refund_policy: bool = db.Column(db.Boolean, default=False)  # 是否同意退款政策
    native_language: str = db.Column(db.JSON)  # 母语
    fluent_language: str = db.Column(db.JSON)  # 流利语言
    
    # 用户关联
    user = db.relationship(
        'User',
        foreign_keys=[email],
        primaryjoin='User.email == TicketHolder.email',
        viewonly=True,
        backref='attendees',
        sync_backref=False,
    )  # 用户关联
    
    # 订单关联
    order = db.relationship('Order', backref='ticket_holders')  # 订单关联
    ticket = db.relationship('Ticket', backref='ticket_holders')  # 票券关联
    
    # 同意表单字段
    is_consent_form_field: bool = db.Column(db.Boolean, default=False)  # 是否同意表单字段
    is_consent_form_field_photo: bool = db.Column(db.Boolean, default=False)  # 是否同意表单照片字段
    is_consent_form_field_email: bool = db.Column(db.Boolean, default=False)  # 是否同意表单邮箱字段
    
    # 徽章信息
    is_badge_printed: bool = db.Column(db.Boolean, default=False)  # 是否已打印徽章
    badge_printed_at: datetime = db.Column(db.DateTime(timezone=True))  # 徽章打印时间
    
    # 折扣和访问码
    is_discount_applied: bool = db.Column(db.Boolean, default=False)  # 是否已应用折扣
    is_access_code_applied: bool = db.Column(db.Boolean, default=False)  # 是否已应用访问码
    
    # 标签关联
    tag_id: int = db.Column(db.Integer, db.ForeignKey('tags.id', ondelete='CASCADE'))  # 标签ID
    tag = db.relationship('Tag', backref='ticket_holders')  # 标签关联
    
    # 标识符
    identifier = db.Column(db.String, default=get_new_id)  # 唯一标识符

    @property
    def name(self):
        """
        获取完整姓名
        
        返回:
            str: 参与者的完整姓名
        """
        firstname = self.firstname if self.firstname else ''
        lastname = self.lastname if self.lastname else ''
        if firstname and lastname:
            return f'{firstname} {lastname}'
        else:
            return ''

    @property
    def qr_code(self):
        """
        生成二维码
        
        基于订单标识符和票券持有者标识符生成二维码。
        
        返回:
            str: Base64编码的二维码图片
        """
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=0,
        )
        identifier = self.identifier
        if not self.identifier:
            identifier = str(self.id)

        # 添加数据到二维码
        qr.add_data(self.order.identifier + "-" + identifier)
        qr.make(fit=True)
        img = qr.make_image()

        # 将图片转换为Base64编码
        buffer = BytesIO()
        img.save(buffer, format="JPEG")
        img_str = str(base64.b64encode(buffer.getvalue()), 'utf-8')
        return img_str

    @property
    def serialize(self):
        """
        序列化对象数据
        
        返回易于序列化的对象数据格式。
        
        返回:
            dict: 序列化的对象数据
        """
        return {
            'id': self.id,
            'firstname': self.firstname,
            'lastname': self.lastname,
            'email': self.email,
            'city': self.city,
            'address': self.address,
            'state': self.state,
            'country': self.country,
            'company': self.company,
            'taxBusinessInfo': self.tax_business_info,
        }

    @property
    def pdf_url_path(self) -> str:
        """
        PDF URL路径属性
        
        返回:
            str: PDF文件的URL路径
        """
        key = UPLOAD_PATHS['pdf']['tickets_all'].format(
            identifier=self.order.identifier, extra_identifier=self.id
        )
        return (
            f'generated/tickets/{key}/{generate_hash(key)}/'
            + self.order.identifier
            + '.pdf'
        )
