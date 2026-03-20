#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
轨道模型 - Open Event Server 轨道管理模块

此文件定义了轨道模型类，用于表示会议中的主题轨道。

作者: FOSSASIA
"""

from app.models import db
from app.models.base import SoftDeletionModel


class Track(SoftDeletionModel):
    """
    轨道模型类
    
    此类代表会议中的主题轨道，用于对会话进行分类。
    """
    
    __tablename__ = 'tracks'  # 数据库表名
    
    # 字段定义
    id = db.Column(db.Integer, primary_key=True)  # 轨道ID
    name = db.Column(db.String, nullable=False)  # 轨道名称
    description = db.Column(db.Text)  # 轨道描述
    color = db.Column(db.String, nullable=False)  # 轨道颜色
    sessions = db.relationship('Session', backref='track')  # 会话关联
    event_id = db.Column(db.Integer, db.ForeignKey('events.id', ondelete='CASCADE'))  # 事件ID
    position = db.Column(db.Integer, default=0, nullable=False)  # 排序位置

    @staticmethod
    def get_service_name():
        """
        获取服务名称
        
        返回:
            str: 服务名称
        """
        return 'track'

    def __repr__(self):
        """
        字符串表示
        
        返回:
            str: 轨道对象的字符串表示
        """
        return '<Track %r>' % self.name

    @property
    def font_color(self):
        """
        获取字体颜色
        
        根据轨道背景颜色自动计算合适的字体颜色（黑色或白色）。
        
        返回:
            str: 字体颜色（#000000或#ffffff）
        """
        if self.color.startswith('#'):
            h = self.color.lstrip('#')
            a = (
                1
                - (
                    0.299 * int(h[0:2], 16)
                    + 0.587 * int(h[2:4], 16)
                    + 0.114 * int(h[4:6], 16)
                )
                / 255
            )
        elif self.color.startswith('rgba'):
            h = self.color.lstrip('rgba').replace('(', '', 1).replace(')', '', 1)
            h = h.split(',')
            a = (
                1
                - (0.299 * int(h[0], 16) + 0.587 * int(h[1], 16) + 0.114 * int(h[2], 16))
                / 255
            )
        # 根据亮度选择字体颜色
        return '#000000' if (a < 0.5) else '#ffffff'
