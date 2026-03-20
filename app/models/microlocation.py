#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微地点模型 - Open Event Server 微地点管理模块

此文件定义了微地点模型类，用于表示会议中的具体地点（如会议室、大厅等）。

作者: FOSSASIA
"""

import re

from app.models import db
from app.models.base import SoftDeletionModel


class Microlocation(SoftDeletionModel):
    """
    微地点模型类
    
    此类代表会议中的具体地点，如会议室、大厅等，包含位置信息和相关设置。
    """
    
    __tablename__ = 'microlocations'  # 数据库表名
    
    # 字段定义
    id = db.Column(db.Integer, primary_key=True)  # 微地点ID
    name = db.Column(db.String, nullable=False)  # 名称
    latitude = db.Column(db.Float)  # 纬度
    longitude = db.Column(db.Float)  # 经度
    floor = db.Column(db.Integer)  # 楼层
    hidden_in_scheduler = db.Column(db.Boolean, default=False, nullable=False)  # 是否在调度器中隐藏
    position = db.Column(db.Integer, default=0, nullable=False)  # 排序位置
    room = db.Column(db.String)  # 房间号
    is_chat_enabled = db.Column(db.Boolean, default=False, nullable=True)  # 是否启用聊天
    is_global_event_room = db.Column(db.Boolean, default=False, nullable=True)  # 是否为全局事件房间
    chat_room_id = db.Column(db.String, nullable=True)  # 聊天室ID
    
    # 关联关系
    session = db.relationship('Session', backref="microlocation")  # 会话关联
    event_id = db.Column(db.Integer, db.ForeignKey('events.id', ondelete='CASCADE'))  # 事件ID
    video_stream_id = db.Column(
        db.Integer, db.ForeignKey('video_streams.id', ondelete='CASCADE')
    )  # 视频流ID

    @staticmethod
    def get_service_name():
        """
        获取服务名称
        
        返回:
            str: 服务名称
        """
        return 'microlocation'

    def __repr__(self):
        """
        字符串表示
        
        返回:
            str: 微地点对象的字符串表示
        """
        return '<Microlocation %r>' % self.name

    @property
    def safe_video_stream(self):
        """
        安全视频流属性
        
        在应用访问控制后条件性地返回视频流。
        
        返回:
            VideoStream or None: 视频流对象或None
        """
        stream = self.video_stream
        if stream and stream.user_can_access:
            return stream
        return None

    @safe_video_stream.setter
    def safe_video_stream(self, value):
        """
        安全视频流设置器
        
        参数:
            value: 视频流值
        """
        self.video_stream = value

    @property
    def chat_room_name(self):
        """
        聊天室名称属性
        
        返回:
            str: 基于微地点名称生成的聊天室名称
        """
        return re.sub('[^0-9a-zA-Z!]', '-', self.name) + '-' + str(self.id)
