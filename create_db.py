#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库创建脚本 - Open Event Server 数据库初始化工具

此脚本用于创建数据库表结构并初始化超级管理员账户。
支持命令行参数传入管理员凭据，或在交互模式下收集。

作者: FOSSASIA
"""

import argparse
import getpass
import re

from flask_migrate import stamp

from app.instance import current_app
from app.models import db
from populate_db import populate
from tests.all.integration.auth_helper import create_super_admin


def create_default_user(email, password):
    """
    创建默认超级管理员用户
    
    如果没有提供邮箱和密码，将在交互模式下收集。
    
    参数:
        email (str): 管理员邮箱地址
        password (str): 管理员密码
    """
    print("您的登录用户名为 'super_admin'。")
    if not email:
        ask_email = True
        while ask_email:
            email = input("请输入超级管理员邮箱: ")
            if not re.match(r'[^@]+@[^@]+\.[^@]+', email):
                print('\n邮箱地址格式无效\n')
                continue
            ask_email = False
    if not password:
        ask_password = True
        while ask_password:
            password = getpass.getpass("请输入超级管理员密码: ")
            if len(password) < 8:
                print('\n密码长度至少为8个字符')
                continue
            repassword = getpass.getpass("请再次输入密码确认: ")
            if password != repassword:
                print('\n两次输入的密码不匹配')
                continue
            ask_password = False
    create_super_admin(email, password)


if __name__ == "__main__":
    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description="Open Event Server 数据库初始化工具")
    parser.add_argument("email", nargs='?', help="超级管理员邮箱地址", default='')
    parser.add_argument(
        "password", nargs='?', help="超级管理员密码", default=''
    )
    parsed = parser.parse_args()
    
    # 在应用上下文中执行数据库初始化
    with current_app.app_context():
        # 创建PostgreSQL citext扩展（如果不存在）
        db.engine.execute('create extension if not exists citext')
        
        # 创建所有数据库表
        db.create_all()
        
        # 标记数据库迁移状态
        stamp()
        
        # 创建默认超级管理员用户
        create_default_user(parsed.email, parsed.password)
        
        # 填充初始数据
        populate()
