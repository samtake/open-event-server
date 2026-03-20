#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户工厂 - Open Event Server 测试数据生成

此文件定义了用户模型的测试工厂，用于生成测试数据。

作者: FOSSASIA
"""

from app.models.user import User
from tests.factories import common
from tests.factories.base import BaseFactory


class UserFactory(BaseFactory):
    """
    用户工厂类
    
    用于生成用户测试数据。
    """
    
    class Meta:
        """工厂元数据"""
        model = User

    # 用户基本信息
    email = common.email_  # 邮箱
    password = 'password'  # 密码
    avatar_url = common.imageUrl_  # 头像URL
    is_super_admin = False  # 是否为超级管理员
    is_admin = True  # 是否为管理员
    is_verified = True  # 是否已验证
    first_name = 'John'  # 名字
    last_name = 'Doe'  # 姓氏
    details = common.string_  # 详细信息
    contact = common.string_  # 联系方式
    
    # 社交媒体链接
    facebook_url = common.socialUrl_('facebook')  # Facebook链接
    twitter_url = common.socialUrl_('twitter')  # Twitter链接
    instagram_url = common.socialUrl_('instagram')  # Instagram链接
    google_plus_url = common.socialUrl_('plus.google')  # Google+链接
    
    # 图片URL
    thumbnail_image_url = common.imageUrl_  # 缩略图URL
    small_image_url = common.imageUrl_  # 小图URL
    icon_image_url = common.imageUrl_  # 图标URL
