#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证助手模块 - Open Event Server 数据验证功能

此模块提供复杂字段的验证功能。

作者: FOSSASIA
"""

from app.api.helpers.errors import UnprocessableEntityError
from app.settings import get_settings


def validate_complex_fields_json(self, data, original_data):
    """
    验证复杂字段JSON数据的有效性
    
    确保复杂字段值符合要求的格式和数量限制。
    
    参数:
        self: 验证器实例
        data: 要验证的数据
        original_data: 原始数据
        
    异常:
        UnprocessableEntityError: 当数据格式无效或超出限制时抛出
    """
    if data.get('complex_field_values'):
        # 检查值类型是否有效
        if any(
            ((not isinstance(i, (str, bool, int, float))) and i is not None)
            for i in data['complex_field_values'].values()
        ):
            raise UnprocessableEntityError(
                {'pointer': '/data/attributes/complex_field_values'},
                "只允许扁平化的JSON格式 {key: value}，其中value可以是字符串、"
                "整数、浮点数、布尔值或null",
            )

        # 检查复杂字段数量是否超出限制
        if (
            len(data['complex_field_values'])
            > get_settings()['max_complex_custom_fields']
        ):
            raise UnprocessableEntityError(
                {'pointer': '/data/attributes/complex_field_values'},
                "当前最多支持 {} 个复杂自定义表单字段".format(
                    get_settings()['max_complex_custom_fields']
                ),
            )
