#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
会话模型 - Open Event Server 会话管理模块

此文件定义了会话模型类，用于表示会议中的各个演讲或讨论环节。

作者: FOSSASIA
"""

import datetime

import pytz
from flask_jwt_extended import current_user
from sqlalchemy import event, func
from sqlalchemy.sql import func as sql_func
from sqlalchemy_utils import aggregated

from app.models import db
from app.models.base import SoftDeletionModel
from app.models.feedback import Feedback
from app.models.helpers.versioning import clean_html, clean_up_string
from app.models.user_favourite_session import UserFavouriteSession

# 演讲者和会话的多对多关联表
speakers_sessions = db.Table(
    'speakers_sessions',
    db.Column('speaker_id', db.Integer, db.ForeignKey('speaker.id', ondelete='CASCADE')),
    db.Column('session_id', db.Integer, db.ForeignKey('sessions.id', ondelete='CASCADE')),
    db.PrimaryKeyConstraint('speaker_id', 'session_id'),
)


class Session(SoftDeletionModel):
    """
    会话模型类
    
    此类代表会议中的演讲或讨论环节，包含标题、描述、时间、地点等信息。
    """

    class State:
        """会话状态枚举"""
        PENDING = 'pending'     # 待处理
        ACCEPTED = 'accepted'     # 已接受
        CONFIRMED = 'confirmed'   # 已确认
        REJECTED = 'rejected'     # 已拒绝

    __tablename__ = 'sessions'  # 数据库表名
    __table_args__ = (
        db.Index('session_event_idx', 'event_id'),  # 事件ID索引
        db.Index('session_state_idx', 'state'),     # 状态索引
    )
    
    # 基本信息
    id = db.Column(db.Integer, primary_key=True)  # 会话ID
    title = db.Column(db.String, nullable=False)  # 标题
    subtitle = db.Column(db.String)  # 副标题
    website = db.Column(db.String)   # 网站
    twitter = db.Column(db.String)   # Twitter
    facebook = db.Column(db.String)  # Facebook
    github = db.Column(db.String)    # GitHub
    linkedin = db.Column(db.String)  # LinkedIn
    instagram = db.Column(db.String)  # Instagram
    gitlab = db.Column(db.String)    # GitLab
    mastodon = db.Column(db.String)  # Mastodon
    short_abstract = db.Column(db.Text, default='')  # 简短摘要
    long_abstract = db.Column(db.Text, default='')   # 详细摘要
    comments = db.Column(db.Text)  # 评论
    language = db.Column(db.String)  # 语言
    level = db.Column(db.String)     # 级别
    
    # 时间信息
    starts_at = db.Column(db.DateTime(timezone=True))  # 开始时间
    ends_at = db.Column(db.DateTime(timezone=True))    # 结束时间
    
    # 关联关系
    track_id = db.Column(db.Integer, db.ForeignKey('tracks.id', ondelete='CASCADE'))  # 轨道ID
    microlocation_id = db.Column(
        db.Integer, db.ForeignKey('microlocations.id', ondelete='CASCADE')
    )  # 微地点ID
    session_type_id = db.Column(
        db.Integer, db.ForeignKey('session_types.id', ondelete='CASCADE')
    )  # 会话类型ID
    speakers = db.relationship(
        'Speaker',
        secondary=speakers_sessions,
        backref=db.backref('sessions', lazy='dynamic'),
    )  # 演讲者关联

    feedbacks = db.relationship('Feedback', backref="session")  # 反馈关联
    slides_url = db.Column(db.String)  # 幻灯片URL
    slides = db.Column(db.JSON)        # 幻灯片数据
    video_url = db.Column(db.String)   # 视频URL
    audio_url = db.Column(db.String)   # 音频URL
    signup_url = db.Column(db.String)  # 报名URL

    event_id = db.Column(db.Integer, db.ForeignKey('events.id', ondelete='CASCADE'))  # 事件ID
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'))  # 创建者ID
    creator = db.relationship('User')  # 创建者关联
    state = db.Column(db.String, default="pending")  # 状态
    created_at = db.Column(db.DateTime(timezone=True), default=sql_func.now())  # 创建时间
    submitted_at = db.Column(db.DateTime(timezone=True))  # 提交时间
    submission_modifier = db.Column(db.String)  # 提交修改者
    is_mail_sent = db.Column(db.Boolean, default=False)  # 是否已发送邮件
    last_modified_at = db.Column(db.DateTime(timezone=True), default=func.now())  # 最后修改时间
    send_email = db.Column(db.Boolean, nullable=True)  # 是否发送邮件
    is_locked = db.Column(db.Boolean, default=False, nullable=False)  # 是否锁定
    complex_field_values = db.Column(db.JSON)  # 复杂字段值

    @staticmethod
    def get_service_name():
        """
        获取服务名称
        
        返回:
            str: 服务名称
        """
        return 'session'

    @property
    def is_accepted(self):
        """
        检查会话是否已接受
        
        返回:
            bool: 是否已接受
        """
        return self.state == "accepted"

    @property
    def organizer_site_link(self):
        """
        获取组织者站点链接
        
        返回:
            str: 组织者站点链接
        """
        return self.event.organizer_site_link + f"/session/{self.id}"

    @aggregated(
        'feedbacks', db.Column(db.Float, default=0, server_default='0', nullable=False)
    )
    def average_rating(self):
        return func.coalesce(func.avg(Feedback.rating), 0)

    @aggregated(
        'feedbacks', db.Column(db.Integer, default=0, server_default='0', nullable=False)
    )
    def rating_count(self):
        return func.count('1')

    @aggregated(
        'favourites', db.Column(db.Integer, default=0, server_default='0', nullable=False)
    )
    def favourite_count(self):
        return func.count('1')

    @property
    def favourite(self):
        if not current_user:
            return None
        return UserFavouriteSession.query.filter_by(
            user=current_user, session=self
        ).first()

    @property
    def site_link(self):
        return self.event.site_link + f"/session/{self.id}"

    @property
    def site_cfs_link(self):
        return self.event.site_link + "/cfs"

    def __repr__(self):
        return '<Session %r>' % self.title

    def __setattr__(self, name, value):
        if name == 'short_abstract' or name == 'long_abstract' or name == 'comments':
            super().__setattr__(name, clean_html(clean_up_string(value), allow_link=True))
        else:
            super().__setattr__(name, value)


@event.listens_for(Session, 'before_update')
def receive_after_update(mapper, connection, target):
    target.last_modified_at = datetime.datetime.now(pytz.utc)
