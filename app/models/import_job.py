#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
导入任务模型 - Open Event Server 导入任务管理模块

此文件定义了导入任务模型类，用于管理事件数据的导入任务。
导入任务用于将外部数据导入到系统中。

作者: FOSSASIA
"""

from sqlalchemy.sql import func

from app.models import db


class ImportJob(db.Model):
    """
    导入任务模型类
    
    此类代表事件的导入任务，用于将外部数据导入到系统中。
    每个导入任务记录包含任务类型、开始时间、用户ID等信息。
    """
    
    __tablename__ = 'import_jobs'  # 数据库表名
    
    # 基本信息
    id = db.Column(db.Integer, primary_key=True)  # 任务ID
    task = db.Column(db.String, nullable=False)  # 任务类型
    starts_at = db.Column(db.DateTime(timezone=True), default=func.now())  # 开始时间
    
    # 用户信息
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'))  # 用户ID
    user = db.relationship('User', backref='import_jobs')  # 用户关联
    
    # 结果信息
    result = db.Column(db.String)  # 结果
    result_status = db.Column(db.String)  # 结果状态

    def __repr__(self):
        """
        字符串表示
        
        返回:
            str: 导入任务对象的字符串表示
        """
        return '<ImportJob %d by user %s>' % (self.id, str(self.user))