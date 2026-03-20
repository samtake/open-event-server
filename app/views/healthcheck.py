#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
健康检查模块 - Open Event Server 系统健康状态监控

此模块提供系统组件的健康检查功能，包括：
- Celery和Redis状态检查
- 数据库连接检查
- 数据库迁移状态检查

作者: FOSSASIA
"""

from errno import errorcode

from redis.exceptions import ConnectionError
from sentry_sdk import capture_exception, capture_message

from app.models import db


def health_check_celery():
    """
    检查Celery和Redis代理的健康状态
    
    返回:
        tuple: (是否健康, 状态消息)
    """
    from app.api.helpers.tasks import celery

    try:
        # 检查Celery工作节点状态
        d = celery.control.inspect().stats()
        if not d:
            capture_message('未找到正在运行的Celery工作节点。')
            return False, '未找到正在运行的Celery工作节点。'
    except ConnectionError as e:
        capture_exception(e)
        return False, '无法连接到Redis服务器'
    except OSError as e:
        msg = "连接到后端时出错: " + str(e)
        if len(e.args) > 0 and errorcode.get(e.args[0]) == 'ECONNREFUSED':
            msg += ' 请检查Redis服务器是否正在运行。'
        capture_exception(e)
        return False, msg
    except ImportError as e:
        capture_exception(e)
        return False, str(e)
    except Exception:
        capture_exception()
        return False, 'Celery状态异常'
    return True, 'Celery状态正常'


def health_check_db():
    """
    检查数据库的健康状态
    
    返回:
        tuple: (是否健康, 状态消息)
    """
    try:
        # 执行简单查询测试数据库连接
        db.session.execute('SELECT 1')
        return True, '数据库连接正常'
    except:
        capture_exception()
        return False, '连接数据库时出错'


def check_migrations():
    """
    通过在每个模型上执行选择查询来检查数据库是否与迁移保持同步
    
    返回:
        str: 检查结果消息
    """
    # 获取数据库中的所有模型，所有模型都应该有明确的__tablename__
    classes, models, table_names = [], [], []
    # noinspection PyProtectedMember
    for class_ in list(db.Model._decl_class_registry.values()):
        try:
            table_names.append(class_.__tablename__)
            classes.append(class_)
        except:
            pass
    for table in list(db.metadata.tables.items()):
        if table[0] in table_names:
            models.append(classes[table_names.index(table[0])])

    # 检查每个模型是否可以正常查询
    for model in models:
        try:
            db.session.query(model).first()
        except:
            capture_exception()
            return f'失败,{model} 模型与迁移不同步'
    return '成功,数据库与迁移保持同步'


def health_check_migrations():
    """
    检查数据库迁移状态
    
    返回:
        tuple: (是否健康, 状态消息)
    """
    result = check_migrations().split(',')
    if result[0] == '成功':
        return True, result[1]
    # 异常将在check_migrations函数中被捕获，因此这里不需要Sentry捕获异常
    return False, result[1]
