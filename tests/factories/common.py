#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用工厂 - Open Event Server 测试数据生成器

此文件定义了测试中常用的通用数据生成器。

作者: FOSSASIA
"""

import datetime

import factory

from app.api.helpers.utilities import image_link, static_page

# 使用驼峰命名法命名变量

# 基本数据类型
string_ = 'example'  # 示例字符串
email_ = factory.Sequence(lambda n: f'user{n}@example.com')  # 示例邮箱（序列生成）
integer_ = 25  # 示例整数
url_ = static_page  # 示例URL
imageUrl_ = image_link  # 示例图片URL

# 日期时间
date_ = datetime.datetime(2016, 12, 13)  # 示例日期
dateFuture_ = datetime.datetime(2099, 12, 13)  # 未来日期
dateEndFuture_ = datetime.datetime(2099, 12, 14)  # 未来结束日期
dateEnd_ = datetime.datetime(2030, 12, 14)  # 结束日期

# 地理和货币
country_ = 'US'  # 示例国家
currency_ = 'USD'  # 示例货币

# 数字类型
int_ = '1'  # 字符串形式的整数
float_ = '1.23456789'  # 示例浮点数

# 系统和配置
timezone_ = 'UTC'  # 示例时区
environment_ = 'testing'  # 示例环境
secret_ = 'ABCDefghIJKLmnop'  # 示例密钥

# 费用和评价
fee_ = 1.23  # 示例费用
average_rating_ = 3  # 示例平均评分
rating_count_ = 1  # 示例评分数量

# 标识符
slug_ = factory.Sequence(lambda n: f'example_slug{n}')  # 示例slug（序列生成）

# 集合类型
array_ = []  # 示例数组
boolean_ = False  # 示例布尔值


def socialUrl_(name):
    """
    生成社交媒体URL
    
    参数:
        name: 社交媒体平台名称
        
    返回:
        str: 社交媒体URL
    """
    return f'https://{name}.com/{name}'
