#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
认证助手模块 - Open Event Server 用户认证和权限管理

此模块提供用户认证、权限管理和令牌黑名单功能。
包括Flask-Login集成、管理员认证和JWT令牌管理。

作者: FOSSASIA
"""

import datetime

import flask_login as login
import pytz
from flask_login import current_user

from app.models import db
from app.models.user import User
from app.models.user_token_blacklist import UserTokenBlackListTime


class AuthManager:
    """
    认证管理器类
    
    提供用户认证和权限管理的核心功能。
    """
    
    def __init__(self):
        """初始化认证管理器"""
        pass

    @staticmethod
    def init_login(app):
        """
        初始化Flask-Login认证系统
        
        参数:
            app: Flask应用实例
        """
        from flask import redirect, request, url_for

        login_manager = login.LoginManager()
        login_manager.init_app(app)

        # 创建用户加载函数
        @login_manager.user_loader
        def load_user(user_id):
            """根据用户ID加载用户对象"""
            return db.session.query(User).get(user_id)

        @login_manager.unauthorized_handler
        def unauthorized():
            """处理未授权访问"""
            return redirect(url_for('admin.login_view', next=request.url))

    @staticmethod
    def is_verified_user():
        """
        检查当前用户是否已验证
        
        返回:
            bool: 用户是否已验证
        """
        return current_user.is_verified

    @staticmethod
    def is_accessible():
        """
        检查当前用户是否已认证
        
        返回:
            bool: 用户是否已认证
        """
        return current_user.is_authenticated

    @staticmethod
    def check_auth_admin(username, password):
        """
        检查管理员认证凭据
        
        此函数用于检查管理员权限和认证。
        
        参数:
            username (str): 用户名（邮箱）
            password (str): 密码
            
        返回:
            bool: 认证是否成功
        """
        if username and password:
            user = User.query.filter_by(_email=username).first()
            if user and user.is_correct_password(password) and user.is_admin:
                return True
        return False


def blacklist_token(user):
    """
    将用户令牌加入黑名单
    
    当用户登出或需要强制登出时，将其令牌加入黑名单。
    
    参数:
        user: 用户对象
    """
    blacklist_time = UserTokenBlackListTime.query.filter_by(user_id=user.id).first()
    if blacklist_time:
        blacklist_time.blacklisted_at = datetime.datetime.now(pytz.utc)
    else:
        blacklist_time = UserTokenBlackListTime(user_id=user.id)

    db.session.add(blacklist_time)
    db.session.commit()


def is_token_blacklisted(token):
    """
    检查令牌是否在黑名单中
    
    参数:
        token (dict): JWT令牌数据
        
    返回:
        bool: 令牌是否在黑名单中
    """
    blacklist_time = UserTokenBlackListTime.query.filter_by(
        user_id=token['identity']
    ).first()
    if not blacklist_time:
        return False
    return token['iat'] < blacklist_time.blacklisted_at.timestamp()
