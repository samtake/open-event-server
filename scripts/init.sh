#!/bin/bash
# -*- coding: utf-8 -*-
"""
初始化脚本 - Open Event Server 数据库初始化

此脚本用于初始化数据库并创建管理员账户。

作者: FOSSASIA
"""

# 设置错误时退出
set -e

# 创建数据库和管理员账户
# $ADMIN_EMAIL: 管理员邮箱（环境变量）
# $ADMIN_PASSWORD: 管理员密码（环境变量）
python3 create_db.py $ADMIN_EMAIL $ADMIN_PASSWORD

# 标记数据库迁移版本为最新
python3 manage.py db stamp head
