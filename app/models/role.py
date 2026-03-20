#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
角色模型 - Open Event Server 角色管理模块

此文件定义了角色模型类，用于表示系统中的各种角色。

作者: FOSSASIA
"""

from app.models import db


class Role(db.Model):
    """
    角色模型类
    
    此类代表系统中的角色，包括事件所有者、组织者等。
    """
    
    __tablename__ = 'roles'  # 数据库表名

    # 角色常量定义
    OWNER = 'owner'              # 所有者
    ORGANIZER = 'organizer'      # 组织者
    COORGANIZER = 'coorganizer'  # 共同组织者

    # 字段定义
    id = db.Column(db.Integer, primary_key=True)  # 角色ID
    name = db.Column(db.String, nullable=False, unique=True)  # 角色名称
    title_name = db.Column(db.String)  # 角色显示名称

    def __repr__(self):
        """
        字符串表示
        
        返回:
            str: 角色对象的字符串表示
        """
        return '<Role %r>' % self.name
