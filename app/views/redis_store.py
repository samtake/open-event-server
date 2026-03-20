#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Redis存储模块 - Open Event Server Redis客户端

此模块提供Redis客户端实例，用于缓存和会话存储。

作者: FOSSASIA
"""

from flask_redis import FlaskRedis

# 创建Redis存储实例
redis_store = FlaskRedis()
