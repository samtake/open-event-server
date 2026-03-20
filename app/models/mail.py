#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
邮件模型 - Open Event Server 邮件管理模块

此文件定义了邮件模型类，用于记录系统发送的邮件。

作者: FOSSASIA
"""

from sqlalchemy.sql import func

from app.models import db


class Mail(db.Model):
    """
    邮件模型类
    
    此类代表系统发送的邮件记录，包含收件人、时间、主题等信息。
    """
    
    __tablename__ = 'mails'  # 数据库表名
    
    # 基本信息
    id = db.Column(db.Integer, primary_key=True)  # 邮件ID
    recipient = db.Column(db.String)  # 收件人
    time = db.Column(db.DateTime(timezone=True), default=func.now())  # 发送时间
    action = db.Column(db.String)  # 操作
    subject = db.Column(db.String)  # 主题
    message = db.Column(db.String)  # 消息内容

    def __repr__(self):
        """
        字符串表示
        
        返回:
            str: 邮件对象的字符串表示
        """
        return f'<Mail {self.id!r} to {self.recipient!r}>'