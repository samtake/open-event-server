#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API引导模块 - Open Event Server API版本和权限管理

此模块负责设置API版本控制和权限管理。

作者: FOSSASIA
"""

from flask import Blueprint
from flask import current_app as app
from flask_rest_jsonapi import Api

from app.api.helpers.permission_manager import permission_manager

# 创建API版本1蓝图
# 所有API端点都将以/v1为前缀
api_v1 = Blueprint('v1', __name__, url_prefix='/v1')

# 创建API实例并绑定到应用
# 使用Flask-REST-JSONAPI扩展创建API实例
api = Api(app, api_v1)

# 设置权限管理器
# 配置API的权限验证机制
api.permission_manager(permission_manager)
