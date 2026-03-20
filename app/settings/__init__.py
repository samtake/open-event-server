#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
设置模块 - Open Event Server 系统设置管理

此模块提供系统设置的获取和更新功能。
管理系统级别的配置，如应用名称、环境、支付设置等。

作者: FOSSASIA
"""

import stripe
from flask import current_app
from sqlalchemy import desc

from app.models.setting import Environment, Setting


def get_settings(from_db=False):
    """
    获取最新的系统设置
    
    该函数首先从缓存中获取设置，如果缓存不存在或需要强制刷新，
    则从数据库中获取最新的设置。
    
    参数:
        from_db (bool): 是否强制从数据库获取，忽略缓存
        
    返回:
        dict: 系统设置字典，包含所有系统配置项
    """
    # 如果缓存中有设置且不强制从数据库获取，则返回缓存设置
    if not from_db and 'custom_settings' in current_app.config:
        return current_app.config['custom_settings']

    # 获取当前应用环境（默认为生产环境）
    app_environment = current_app.config.get('ENV', 'production')
    
    # 根据当前应用环境查询对应的设置记录
    s = Setting.query.filter(Setting.app_environment == app_environment).first()

    if s is None:
        # 如果设置不存在，则创建默认设置
        set_settings(app_name='Open Event', app_environment=app_environment)
    else:
        # 将设置对象转换为字典并缓存到应用配置中
        current_app.config['custom_settings'] = make_dict(s)
        # 如果设置中没有应用环境，重新设置
        if not current_app.config['custom_settings'].get('app_environment'):
            set_settings(app_name='Open Event', app_environment=app_environment)
    return current_app.config['custom_settings']


def refresh_settings():
    """
    刷新系统设置
    
    强制从数据库获取最新的设置，从而刷新缓存中的设置。
    这在设置被外部修改后调用，确保应用使用最新的设置。
    """
    get_settings(from_db=True)


def get_setts():
    """
    获取最新的设置对象
    
    返回数据库中ID最大的设置对象（即最新的设置）。
    
    返回:
        Setting: 最新的设置对象
    """
    return Setting.query.order_by(desc(Setting.id)).first()


def set_settings(**kwargs):
    """
    更新系统设置
    
    更新系统级别的配置，包括应用名称、环境、支付设置等。
    更新后会自动刷新Stripe API密钥和Flask应用配置。
    
    参数:
        **kwargs: 设置参数，支持所有Setting模型的字段
    """
    # 获取最新的设置对象
    setting = Setting.query.order_by(desc(Setting.id)).first()
    if not setting:
        # 如果设置不存在，则创建新设置
        setting = Setting(**kwargs)
    else:
        # 更新现有设置的字段值
        for key, value in list(kwargs.items()):
            setattr(setting, key, value)
    
    from app.api.helpers.db import save_to_db
    # 保存设置到数据库
    save_to_db(setting, '设置已保存')
    
    # 更新Stripe API密钥
    stripe.api_key = setting.stripe_secret_key

    # 根据设置的环境更新Flask应用配置
    # 只有当当前配置与设置环境不匹配时才更新
    if (
        setting.app_environment == Environment.DEVELOPMENT
        and not current_app.config['DEVELOPMENT']
    ):
        current_app.config.from_object('config.DevelopmentConfig')

    if (
        setting.app_environment == Environment.STAGING
        and not current_app.config['STAGING']
    ):
        current_app.config.from_object('config.StagingConfig')

    if (
        setting.app_environment == Environment.PRODUCTION
        and not current_app.config['PRODUCTION']
    ):
        current_app.config.from_object('config.ProductionConfig')

    if (
        setting.app_environment == Environment.TESTING
        and not current_app.config['TESTING']
    ):
        current_app.config.from_object('config.TestingConfig')

    # 更新应用配置中的自定义设置缓存
    current_app.config['custom_settings'] = make_dict(setting)


def make_dict(s):
    """
    将设置对象转换为字典
    
    将SQLAlchemy模型对象转换为Python字典，排除主键和唯一键字段。
    
    参数:
        s (Setting): 设置对象
        
    返回:
        dict: 设置字典，包含所有非主键和非唯一键的字段
    """
    arguments = {}
    # 遍历模型的所有列
    for name, column in list(s.__mapper__.columns.items()):
        # 排除主键和唯一键字段
        if not (column.primary_key or column.unique):
            arguments[name] = getattr(s, name)
    return arguments
