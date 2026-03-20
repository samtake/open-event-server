#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JWT助手模块 - Open Event Server JWT认证工具

此模块提供JWT认证相关的辅助函数，包括用户认证、用户加载和身份获取。

作者: FOSSASIA
"""

from flask import _app_ctx_stack as ctx_stack  # pytype: disable=import-error
from flask_jwt_extended.config import config
from flask_jwt_extended.exceptions import JWTExtendedException, UserLoadError
from flask_jwt_extended.view_decorators import _decode_jwt_from_request, _load_user
from jwt.exceptions import PyJWTError

from app.models.user import User


def jwt_authenticate(email, password):
    """
    用户认证辅助函数
    
    验证用户凭据是否正确，支持常规密码和Facebook登录哈希。
    
    参数:
        email (str): 用户邮箱
        password (str): 用户密码或Facebook登录哈希
        
    返回:
        User: 认证成功的用户对象，失败则返回None
    """
    # 查询用户（排除已删除用户）
    user = User.query.filter_by(email=email.strip(), deleted_at=None).first()
    if user is None:
        return None
    
    # 验证密码或Facebook登录哈希
    auth_ok = user.facebook_login_hash == password or user.is_correct_password(password)
    if auth_ok:
        return user
    return None


def jwt_user_loader(identity):
    """
    JWT用户加载器
    
    根据用户ID加载用户对象，用于JWT认证。
    
    参数:
        identity: 用户ID
        
    返回:
        User: 用户对象
    """
    return User.query.filter_by(id=identity, deleted_at=None).first()


def get_identity():
    """
    获取当前用户身份
    
    仅在需要过期令牌的身份信息时使用，否则使用flask_jwt的current_identity。
    
    返回:
        User: 当前用户对象
    """
    token = None
    try:
        # 尝试从请求中解码JWT令牌
        token, _ = _decode_jwt_from_request('access')
    except (JWTExtendedException, PyJWTError):
        # 如果解码失败，尝试获取过期的JWT
        token = getattr(ctx_stack.top, 'expired_jwt', None)

    if token:
        try:
            # 加载用户
            _load_user(token[config.identity_claim_key])
            return getattr(ctx_stack.top, 'jwt_user', None)
        except UserLoadError:
            pass
