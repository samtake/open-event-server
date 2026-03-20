#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
赞助商模型 - Open Event Server 赞助商管理模块

此文件定义了赞助商模型类，用于表示活动的赞助商。

作者: FOSSASIA
"""

from app.models import db
from app.models.base import SoftDeletionModel
from app.models.helpers.versioning import clean_html, clean_up_string


class Sponsor(SoftDeletionModel):
    """
    赞助商模型类
    
    此类代表活动的赞助商，包含赞助商信息和相关设置。
    """
    
    __tablename__ = 'sponsors'  # 数据库表名

    # 字段定义
    id = db.Column(db.Integer, primary_key=True)  # 赞助商ID
    name = db.Column(db.String, nullable=False)  # 赞助商名称
    description = db.Column(db.String)  # 赞助商描述
    url = db.Column(db.String)  # 赞助商网站
    level = db.Column(db.Integer)  # 赞助级别
    logo_url = db.Column(db.String)  # 徽标URL
    event_id = db.Column(db.Integer, db.ForeignKey('events.id', ondelete='CASCADE'))  # 事件ID
    type = db.Column(db.String)  # 赞助商类型

    @staticmethod
    def get_service_name():
        """
        获取服务名称
        
        返回:
            str: 服务名称
        """
        return 'sponsor'

    def __repr__(self):
        """
        字符串表示
        
        返回:
            str: 赞助商对象的字符串表示
        """
        return '<Sponsor %r>' % self.name

    def __setattr__(self, name, value):
        """
        设置属性时的自定义处理
        
        对描述字段进行HTML清理。
        
        参数:
            name: 属性名称
            value: 属性值
        """
        if name == 'description':
            super().__setattr__(name, clean_html(clean_up_string(value)))
        else:
            super().__setattr__(name, value)
