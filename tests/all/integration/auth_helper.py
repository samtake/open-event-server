#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
认证助手 - Open Event Server 测试认证辅助函数

此文件提供测试中的用户创建和认证辅助函数。

作者: FOSSASIA
"""

from app.api.helpers.db import save_to_db
from app.models.user import User


def create_user(email, password, is_verified=True):
    """
    注册用户但不登录
    
    参数:
        email (str): 用户邮箱
        password (str): 用户密码
        is_verified (bool): 是否已验证
        
    返回:
        User: 创建的用户对象
    """
    user = User(email=email, password=password, is_verified=is_verified)
    save_to_db(user, "用户已创建")
    return user


def create_super_admin(email, password):
    """
    创建超级管理员
    
    参数:
        email (str): 管理员邮箱
        password (str): 管理员密码
        
    返回:
        User: 创建的超级管理员对象
    """
    user = create_user(email, password, is_verified=True)
    user.is_super_admin = True
    user.is_admin = True
    save_to_db(user, "用户已更新")
    return user
