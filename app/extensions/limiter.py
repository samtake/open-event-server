#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
限流扩展模块 - Open Event Server 请求限流配置

此模块配置Flask-Limiter扩展，用于API请求频率限制。
基于客户端IP地址进行限流。

作者: FOSSASIA
"""

from flask_limiter import Limiter
from flask_limiter.util import get_ipaddr

# 创建限流器实例，使用客户端IP地址作为限流键
limiter = Limiter(key_func=get_ipaddr)


def init_app(app):
    """
    初始化限流器
    
    参数:
        app: Flask应用实例
    """
    limiter.init_app(app)
