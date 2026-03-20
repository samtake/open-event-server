#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实用工具模块 - Open Event Server 通用工具函数

此模块提供通用的工具函数，不依赖于事件系统的特定模块。

作者: FOSSASIA
"""

# 请将所有对任何数据类型执行通用格式化的函数放在这里，
# 不要使用与事件系统相关的任何模块，即特定于DB模型的函数，
# 例如仅用于role_invites的函数
import random
import re
import string
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Dict

import bleach
import requests
from flask import current_app
from itsdangerous import Serializer

from app.api.helpers.errors import UnprocessableEntityError


def make_dict(list_of_object, key):
    """
    将对象列表转换为字典。
    
    这将返回一个包含唯一键的字典，
    映射到包含该键的对象。
    
    参数:
        list_of_object: 对象列表
        key: 用于映射的键名
        
    返回:
        dict: 映射字典
    """
    mapped_dict = {}
    for obj in list_of_object:
        mapped_dict[getattr(obj, key)] = obj
    return mapped_dict


def dasherize(text):
    """
    将下划线转换为短横线
    
    参数:
        text (str): 输入文本
        
    返回:
        str: 转换后的文本
    """
    return text.replace('_', '-')


def to_snake_case(text):
    """
    转换为蛇形命名法
    
    参数:
        text (str): 输入文本
        
    返回:
        str: 转换后的文本
    """
    text = text.replace('-', '_')
    return re.sub('([A-Z]+)', r'_\1', text).lower()


def dict_to_snake_case(input_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    将字典的键转换为蛇形命名法
    
    参数:
        input_dict: 输入字典
        
    返回:
        dict: 转换后的字典
    """
    if not input_dict:
        return input_dict

    output = {}
    for key, val in input_dict.items():
        output[to_snake_case(key)] = val

    return output


def require_relationship(resource_list, data):
    """
    要求必须存在的关系
    
    参数:
        resource_list: 必需的资源列表
        data: 数据字典
        
    异常:
        UnprocessableEntityError: 当必需的关系不存在时抛出
    """
    for resource in resource_list:
        if resource not in data:
            raise UnprocessableEntityError(
                {'pointer': f'/data/relationships/{resource}'},
                f"需要与 {resource} 资源的有效关系",
            )


def require_exclusive_relationship(resource_list, data, optional=False):
    """
    只应存在传递的关系中的一个
    
    参数:
        resource_list: 资源列表
        data: 数据字典
        optional: 是否可选
        
    异常:
        UnprocessableEntityError: 当关系要求不满足时抛出
    """
    present = False
    multiple = False
    for resource in resource_list:
        if resource in data:
            if present:
                multiple = True
            present = True

    if multiple or not (optional or present):
        raise UnprocessableEntityError(
            {'pointer': f'/data/relationships'},
            f"需要与以下资源之一的有效关系: {resource_list}",
        )


def remove_html_tags(raw_html):
    """
    移除HTML标签
    
    参数:
        raw_html (str): 包含HTML的文本
        
    返回:
        str: 移除HTML标签后的文本
    """
    return re.sub('<.*?>', '', raw_html)


def string_empty(value):
    """
    检查字符串是否为空
    
    参数:
        value: 要检查的值
        
    返回:
        bool: 是否为空字符串
    """
    return isinstance(value, str) and not value.strip()


def strip_tags(html):
    """
    移除HTML标签
    
    参数:
        html (str): HTML文本
        
    返回:
        str: 移除标签后的文本
    """
    if html is None:
        return None
    return bleach.clean(html, tags=[], attributes={}, styles=[], strip=True)


def get_serializer(secret_key=None):
    """
    获取序列化器
    
    参数:
        secret_key: 密钥，如果未提供则使用应用密钥
        
    返回:
        Serializer: 序列化器实例
    """
    if not secret_key:
        secret_key = current_app.config['SECRET_KEY']
    return Serializer(secret_key)


def str_generator(size=6, chars=string.ascii_uppercase + string.digits):
    """
    生成随机字符串
    
    参数:
        size (int): 字符串长度
        chars (str): 可用字符
        
    返回:
        str: 随机字符串
    """
    return ''.join(random.choice(chars) for _ in range(size))


# 来自 http://stackoverflow.com/a/3425124
def monthdelta(date, delta):
    """
    计算月份增量
    
    参数:
        date: 日期
        delta: 月份增量
        
    返回:
        datetime: 计算后的日期
    """
    m, y = (date.month + delta) % 12, date.year + (date.month + delta - 1) // 12
    if not m:
        m = 12
    d = min(
        date.day,
        [
            31,
            29 if y % 4 == 0 and not y % 400 == 0 else 28,
            31,
            30,
            31,
            30,
            31,
            31,
            30,
            31,
            30,
            31,
        ][m - 1],
    )
    return date.replace(day=d, month=m, year=y)


def represents_int(value):
    """
    检查值是否表示整数
    
    参数:
        value: 要检查的值
        
    返回:
        bool: 是否表示整数
    """
    try:
        int(value)
        return True
    except:
        return False


def is_downloadable(url):
    """
    URL是否包含可下载资源
    
    参数:
        url (str): URL地址
        
    返回:
        bool: 是否可下载
    """
    h = requests.head(url, allow_redirects=True)
    header = h.headers
    content_type = header.get('content-type')
    # content_length = header.get('content-length', 1e10)
    if content_type and 'text' in content_type.lower():
        return False
    if content_type and 'html' in content_type.lower():
        return False
    return True


def get_filename_from_cd(cd):
    """
    从content-disposition获取文件名和扩展名
    
    参数:
        cd (str): Content-Disposition头部
        
    返回:
        tuple: (文件名, 扩展名)
    """
    if not cd:
        return '', ''
    fname = re.findall('filename=(.+)', cd)
    if len(fname) == 0:
        return '', ''
    fn = fname[0].rsplit('.', 1)
    return fn[0], '' if len(fn) == 1 else ('.' + fn[1])


def write_file(file, data):
    """
    简单写入文件
    
    参数:
        file: 文件路径
        data: 要写入的数据
    """
    fp = open(file, 'w')
    fp.write(str(data, 'utf-8'))
    fp.close()


def update_state(task_handle, state, result=None):
    """
    更新Celery任务状态
    
    参数:
        task_handle: 任务句柄
        state: 任务状态
        result: 任务结果
    """
    if result is None:
        result = {}
    if not current_app.config.get('CELERY_ALWAYS_EAGER'):
        task_handle.update_state(state=state, meta=result)


def round_money(money):
    """
    四舍五入货币金额
    
    参数:
        money: 金额
        
    返回:
        Decimal: 四舍五入后的金额
    """
    return Decimal(money).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


# 静态页面和图像链接
static_page = 'https://eventyay.com/'
image_link = 'https://www.gstatic.com/webp/gallery/1.jpg'

# 存储测试结果
# 状态和info
TASK_RESULTS = {}


class EmptyObject:
    """
    空对象类
    """
    pass


def group_by(items, key):
    """
    按键分组
    
    参数:
        items: 项目列表
        key: 分组键
        
    返回:
        dict: 分组结果
    """
    result = {}
    for item in items:
        result[item[key]] = result.get(item[key], []) + [item]
    return result


def changed(obj, data: Dict, attr: str) -> bool:
    """
    检查对象的属性是否已更改
    
    参数:
        obj: 对象
        data: 数据字典
        attr: 属性名
        
    返回:
        bool: 是否已更改
    """
    return data.get(attr) and (data[attr] != getattr(obj, attr))
