#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用工具模块 - Open Event Server 通用工具函数

此模块提供通用的工具函数，主要用于Marshmallow序列化器的默认值处理。

作者: FOSSASIA
"""

from marshmallow import pre_load

from app.api.helpers.utilities import dasherize


def patch_defaults(schema, in_data):
    """
    为None字段添加默认值
    
    参数:
        schema: Marshmallow模式对象
        in_data: 包含字段的JSON数据
        
    返回:
        dict: 添加了默认值的JSON数据
    """
    for name, field in schema.fields.items():
        # 将字段名转换为短横线命名格式
        dasherized_name = dasherize(name)
        attribute = in_data.get(dasherized_name)
        # 如果字段值为None，使用字段的默认值
        if attribute is None:
            in_data[dasherized_name] = field.default
    return in_data


@pre_load
def make_object(schema, in_data):
    """
    返回添加默认值后的JSON数据
    
    参数:
        schema: Marshmallow模式对象
        in_data: 包含字段的JSON数据
        
    返回:
        dict: 由patch_defaults函数返回的JSON数据
    """
    return patch_defaults(schema, in_data)


def use_defaults():
    """
    装饰器，用于为具有默认值字段的模型类添加make_object方法
    
    将此装饰器添加到具有默认值字段的模型类上，
    会自动添加上面定义的make_object方法到类中。
    
    返回:
        function: 包装函数
    """

    def wrapper(k, *args, **kwargs):
        # 为类添加make_object方法
        setattr(k, "make_object", eval("make_object", *args, **kwargs))
        return k

    return wrapper
