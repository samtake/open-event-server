#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库助手模块 - Open Event Server 数据库操作工具

此模块提供通用的数据库操作助手函数，包括：
- 数据库保存和查询
- 安全查询
- 记录计数
- 标识符生成

作者: FOSSASIA
"""

import binascii
import logging
import os
import uuid

from flask import request
from flask_rest_jsonapi.exceptions import ObjectNotFound
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm.exc import NoResultFound

from app.models import db

# 仅包含不特定于任何模型的数据库助手函数


def save_to_db(item, msg="已保存到数据库", print_error=True):
    """
    便捷函数，用于正确保存到数据库
    
    参数:
        item: 要保存到数据库的对象
        msg: 要记录的日志消息
        print_error: 是否打印错误信息
        
    返回:
        bool: 保存是否成功
    """
    try:
        logging.info(msg)
        db.session.add(item)
        logging.info('已添加到会话')
        db.session.commit()
        return True
    except Exception:
        logging.exception('数据库异常！')
        db.session.rollback()
        return False


def safe_query_by_id(model, id):
    """
    根据ID安全查询
    
    参数:
        model: 要查询的模型
        id: 记录ID
        
    返回:
        查询结果
    """
    return safe_query_by(model, id)


def safe_query_by(model, value, param='id'):
    """
    根据指定参数安全查询
    
    参数:
        model: 要查询的模型
        value: 参数值
        param: 参数名称，默认为'id'
        
    返回:
        查询结果
    """
    return safe_query_without_soft_deleted_entries(model, param, value, param)


def safe_query_kwargs(model, kwargs, parameter_name, column_name='id'):
    """
    使用关键字参数进行安全查询
    
    参数:
        model: 要查询的数据库模型
        kwargs: 包含参数名称值的对象，例如 kwargs['event_id'] 其中 parameter_name='event_id'
        parameter_name: 要在json-api错误消息中打印的参数名称，例如'event_id'
        column_name: 列名称，默认为'id'
        
    返回:
        查询结果
    """
    return safe_query(
        model,
        column_name,
        kwargs[parameter_name],
        parameter_name,
    )


def safe_query_without_soft_deleted_entries(
    model, column_name, value, parameter_name, filter_deleted=True
):
    """
    包装查询，在过滤软删除条目后正确引发异常
    
    参数:
        model: 要查询的数据库模型
        column_name: 要查询给定值的列名称
        value: 要针对给定列名称查询的值，例如 view_kwargs['event_id']
        parameter_name: 要在json-api错误消息中打印的参数名称，例如'event_id'
        filter_deleted: 如果设置为true，则过滤已删除的记录
        
    返回:
        查询结果
        
    异常:
        ObjectNotFound: 当记录未找到时抛出
    """
    try:
        record = model.query.filter(getattr(model, column_name) == value)
        if filter_deleted and hasattr(model, 'deleted_at'):
            record = record.filter_by(deleted_at=None)
        record = record.one()
    except NoResultFound:
        raise ObjectNotFound(
            {'parameter': f'{parameter_name}'},
            f"{model.__name__}: {value} 未找到",
        )
    else:
        return record


def safe_query(model, column_name, value, parameter_name):
    """
    包装查询以正确引发异常
    
    参数:
        model: 要查询的数据库模型
        column_name: 要查询给定值的列名称
        value: 要针对给定列名称查询的值，例如 view_kwargs['event_id']
        parameter_name: 要在json-api错误消息中打印的参数名称，例如'event_id'
        
    返回:
        查询结果
    """
    return safe_query_without_soft_deleted_entries(
        model,
        column_name,
        value,
        parameter_name,
        # TODO(Areeb): 检查只有管理员可以传递此参数
        request.args.get('get_trashed') != 'true',
    )


def get_or_create(model, defaults=None, **kwargs):
    """
    此函数在模型中查询记录，如果未找到则创建一个。
    
    参数:
        model: 要查询的数据库模型
        **kwargs: 要过滤的 sqlalchemy.orm.query.Query.filter_by 方法的参数
        
    返回:
        tuple: (实例, 是否创建)
    """
    fetch = lambda: db.session.query(model).filter_by(**kwargs).first()
    instance = fetch()
    if instance:
        return instance, False
    kwargs.update(defaults or {})
    instance = model(**kwargs)
    try:
        db.session.add(instance)
        db.session.commit()
        return instance, True
    except IntegrityError:
        db.session.rollback()
        instance = fetch()
        if not instance:
            raise
        return instance, False


def get_count(query):
    """
    计算数据库表/模型中有多少条记录
    
    参数:
        query: SQLAlchemy查询对象
        
    返回:
        int: 记录数量
    """
    # 创建计数查询语句
    count_q = query.statement.with_only_columns([func.count()]).order_by(None)
    # 执行查询并获取结果
    count = query.session.execute(count_q).scalar()
    return count


def get_new_slug(model, name):
    """
    辅助函数，如果需要则创建新的slug，否则返回原始值。
    
    参数:
        model: 指定数据库中的模型
        name: 用于生成slug的标识符
        
    返回:
        str: 生成的slug
    """
    # 生成基础slug：转换为小写，移除特殊字符，用连字符连接
    slug = (
        name.lower()
        .replace("& ", "")
        .replace(",", "")
        .replace("/", "-")
        .replace(" ", "-")
    )
    # 检查slug是否已存在
    count = get_count(model.query.filter_by(slug=slug))
    if count == 0:
        # 如果slug唯一，直接返回
        return slug
    # 如果slug已存在，添加UUID后缀确保唯一性
    return f'{slug}-{uuid.uuid4().hex}'


def get_new_identifier(model=None, length=None):
    """
    生成新的标识符
    
    参数:
        model: 模型（可选），用于检查标识符唯一性
        length: 标识符长度（可选），默认为UUID长度
        
    返回:
        str: 新的标识符
    """
    if not length:
        # 生成标准UUID
        identifier = str(uuid.uuid4())
    else:
        # 生成指定长度的随机标识符
        identifier = str(binascii.b2a_hex(os.urandom(int(length / 2))), 'utf-8')
    
    # 如果提供了模型，检查标识符是否唯一
    count = (
        0 if model is None else get_count(model.query.filter_by(identifier=identifier))
    )
    
    # 确保标识符不是纯数字且唯一
    if not identifier.isdigit() and count == 0:
        return identifier
    
    # 递归生成新的标识符直到满足条件
    return get_new_identifier(model)


def save_bulk_to_db(items, msg="已保存到数据库"):
    """
    便捷函数，用于批量保存到数据库
    
    参数:
        items: 要保存到数据库的对象列表
        msg: 要记录的日志消息
        
    返回:
        bool: 保存是否成功
    """
    try:
        logging.info(msg)
        # 使用批量保存提高效率
        db.session.bulk_save_objects(items)
        logging.info('已添加到会话')
        db.session.commit()
        return True
    except SQLAlchemyError:
        logging.exception('数据库异常！')
        db.session.rollback()
        return False
