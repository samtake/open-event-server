#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
应用工厂模块 - Open Event Server 应用实例工厂

此模块提供应用实例创建工厂函数，遵循Flask应用工厂模式。

作者: FOSSASIA
"""


def create_app():
    """
    创建Flask应用实例
    
    返回:
        Flask应用实例
    """
    from .instance import app

    return app
