#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
活动日志模型 - Open Event Server 活动日志管理模块

此文件定义了活动日志模型类，用于记录系统中的各种活动。
活动日志用于跟踪用户行为和系统事件，便于审计和问题排查。

作者: FOSSASIA
"""

from sqlalchemy.sql import func

from app.models import db

# 活动类型定义
ACTIVITIES = {
    'create_user': '用户 {user} 已创建',
    'update_user': '用户 {user} 的个人资料已更新',
    'update_user_email': '用户 {user_id} 的邮箱已从 {old} 更改为 {new}',
    'user_login': '用户 {user} 从IP {ip} 使用浏览器 {browser} 在 {platform} 平台登录',
    'user_logout': '用户 {user} 从IP {ip} 使用浏览器 {browser} 在 {platform} 平台登出',
    'update_event': '事件 {event_id} 已更新',
    'create_event': '事件 {event_id} 已创建',
    'delete_event': '事件 {event_id} 已删除',
    'import_event': '事件 {event_id} 已导入',
    'publish_event': '事件 {event_id} {status}',
    'export_event': '事件 {event_id} 已导出',
    'create_role': '为用户 {user} 在事件 {event_id} 中创建角色 {role}',
    'update_role': '用户 {user} 在事件 {event_id} 中的角色已更新为 {role}',
    'delete_role': '用户 {user} 已从事件 {event_id} 中的角色 {role} 中移除',
    'create_session': '在事件 {event_id} 中创建了会话 {session}',
    'update_session': '事件 {event_id} 中的会话 {session} 已更新',
    'delete_session': '事件 {event_id} 中的会话 {session} 已删除',
    'create_track': '在事件 {event_id} 中创建了轨道 {track}',
    'update_track': '事件 {event_id} 中的轨道 {track} 已更新',
    'delete_track': '事件 {event_id} 中的轨道 {track} 已删除',
    'create_speaker': '在事件 {event_id} 中创建了演讲者 {speaker}',
    'delete_speaker': '事件 {event_id} 中的演讲者 {speaker} 已删除',
    'update_speaker': '事件 {event_id} 中的演讲者 {speaker} 已更新',
    'add_speaker_to_session': '演讲者 {speaker} 已添加到事件 {event_id} 的会话 {session}',
    'invite_user': '已向用户 {user_id} 发送事件 {event_id} 的邀请',
    'system_admin': '用户 {user} {status} 系统管理员',
    'mail_event': '邮件已发送至 {email}，操作：{action}，主题：{subject}',
    'notification_event': '通知已发送至 {user}，操作：{action}，标题：{title}',
}


class Activity(db.Model):
    """
    活动日志模型类
    
    此类代表系统中的活动日志记录，用于跟踪用户行为和系统事件。
    每个活动记录包含执行者、时间戳和操作信息。
    """
    
    __tablename__ = 'activities'  # 数据库表名
    
    # 基本信息
    id = db.Column(db.Integer, primary_key=True)  # 活动ID
    actor = db.Column(db.String)  # 执行者（用户邮箱+ID）
    time = db.Column(db.DateTime(timezone=True), default=func.now())  # 活动时间
    action = db.Column(db.String)  # 操作描述

    def __repr__(self):
        """
        字符串表示
        
        返回:
            str: 活动日志对象的字符串表示
        """
        return '<Activity by %s>' % self.actor