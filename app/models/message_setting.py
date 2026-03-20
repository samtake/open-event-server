#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
消息设置模型 - Open Event Server 消息设置管理模块

此文件定义了消息设置模型类，用于管理系统中的消息和邮件设置。
包含各种系统操作对应的消息配置，如邮件通知、用户注册、订单状态变更等。

作者: FOSSASIA
"""

from sqlalchemy.ext.hybrid import hybrid_property

from app.api.helpers.db import get_or_create
from app.api.helpers.system_mails import MAILS, MailType
from app.models import db
from app.models.helpers.timestamp import Timestamp


class MessageSettings(db.Model, Timestamp):
    """
    消息设置模型类
    
    此类代表系统中的消息和邮件设置，用于控制各种消息的发送行为。
    继承自SQLAlchemy的Model和Timestamp，提供基本的数据库操作和时间戳功能。
    
    属性:
        id: 设置的唯一标识符
        action: 操作类型，对应系统中的某个具体动作
        enabled: 是否启用该消息设置
        created_at: 创建时间（继承自Timestamp）
        modified_at: 修改时间（继承自Timestamp）
    """
    
    __tablename__ = 'message_settings'  # 数据库表名
    
    # 基本信息 - 数据库字段定义
    id = db.Column(db.Integer, primary_key=True)  # 设置ID，主键
    action = db.Column(db.String, nullable=False)  # 操作类型，如'USER_REGISTER', 'TICKET_PURCHASE'等
    enabled = db.Column(db.Boolean, default=True, nullable=False, server_default='True')  # 是否启用该消息设置，默认为True

    def __repr__(self):
        """
        字符串表示
        
        返回:
            str: 消息设置对象的字符串表示，格式为 '<Message Setting {action} >'
        """
        return '<Message Setting %r >' % self.action

    @staticmethod
    def is_enabled(action: str) -> bool:
        """
        静态方法：检查某个操作是否启用
        
        使用 get_or_create 方法获取或创建指定操作的消息设置，
        如果设置不存在则使用默认值 enabled=True 创建新记录。
        
        参数:
            action (str): 操作类型，如 'USER_REGISTER', 'TICKET_PURCHASE' 等
            
        返回:
            bool: 该操作的消息设置是否启用，True表示启用，False表示禁用
        """
        # 使用 get_or_create 确保设置存在，如果不存在则创建（默认启用）
        settings, _ = get_or_create(
            MessageSettings, action=action, defaults=dict(enabled=True)
        )

        return settings.enabled

    @classmethod
    def _email_message(cls, action, attr=None):
        """
        类方法：获取邮件消息的相关信息
        
        根据操作类型从系统邮件配置中获取相应的邮件信息，
        支持获取邮件模板、接收者、主题等不同属性。
        
        参数:
            action: 操作类型，如 'USER_REGISTER', 'TICKET_PURCHASE' 等
            attr: 属性名称，可选值包括 'message'（邮件内容）、'recipient'（接收者）、'subject'（主题）
            
        返回:
            str: 邮件消息内容或相关属性值，如果未找到则返回 '动态邮件'
        """
        message = {}
        # 检查操作类型是否在预定义的邮件类型中
        if action in MailType.entries():
            message = MAILS.get(action)
        else:
            # 如果不在预定义类型中，尝试从MAILS对象中获取
            message = MAILS.__dict__[action]
        
        # 默认回退消息
        fallback_message = '动态邮件'
        
        # 如果找不到配置，返回默认消息
        if not message:
            return fallback_message
            
        # 如果请求的是消息内容且配置了模板，则读取模板文件
        if attr == 'message' and (template := message.get('template')):
            try:
                # 尝试读取模板文件
                return open('app/templates/' + template).read()
            except FileNotFoundError:
                # 如果模板文件不存在，返回默认消息
                return fallback_message
                
        # 返回指定属性的值，如果不存在则返回默认消息
        message = str(message.get(attr) or fallback_message)
        return message

    @hybrid_property
    def email_message(self):
        """
        混合属性：获取邮件消息内容
        
        这是一个SQLAlchemy混合属性，既可以在Python层面使用，也可以在查询中使用。
        
        返回:
            str: 与当前操作对应的邮件消息内容
        """
        message = self._email_message(self.action, attr='message')
        return message

    @hybrid_property
    def recipient(self):
        """
        混合属性：获取邮件接收者
        
        这是一个SQLAlchemy混合属性，用于获取当前操作对应的邮件接收者信息。
        
        返回:
            str: 与当前操作对应的邮件接收者
        """
        message = self._email_message(self.action, attr='recipient')
        return message

    @hybrid_property
    def email_subject(self):
        """
        混合属性：获取邮件主题
        
        这是一个SQLAlchemy混合属性，用于获取当前操作对应的邮件主题。
        
        返回:
            str: 与当前操作对应的邮件主题
        """
        message = self._email_message(self.action, attr='subject')
        return message