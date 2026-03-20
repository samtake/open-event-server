#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
权限装饰器模块 - Open Event Server API权限控制装饰器

此模块提供各种权限控制装饰器，用于保护API端点。

作者: FOSSASIA
"""

from datetime import datetime
from functools import wraps

from flask import request
from flask_jwt_extended import current_user, verify_jwt_in_request

from app.api.helpers.db import save_to_db
from app.api.helpers.errors import ForbiddenError
from app.models import db
from app.models.event import Event


def second_order_decorator(inner_dec):
    """
    二阶装饰器。用于装饰装饰器的装饰器。
    https://stackoverflow.com/questions/5952641/decorating-decorators-try-to-get-my-head-around-understanding-it
    
    参数:
        inner_dec: 内部装饰器
        
    返回:
        装饰器函数
    """

    def ddmain(outer_dec):
        def decwrapper(f):
            wrapped = inner_dec(outer_dec(f))

            def fwrapper(*args, **kwargs):
                return wrapped(*args, **kwargs)

            fwrapper.__name__ = f.__name__

            return fwrapper

        return decwrapper

    return ddmain


def jwt_required(fn, realm=None):
    """
    从原始jwt_required修改而来，以符合`flask-rest-jsonapi`装饰器约定
    视图装饰器，要求请求中存在有效的JWT令牌
    
    参数:
        fn: 要装饰的函数
        realm: 可选的领域参数
    """

    @wraps(fn)
    def decorator(*args, **kwargs):
        # 验证JWT令牌
        verify_jwt_in_request()
        # 更新用户最后访问时间
        current_user.last_accessed_at = datetime.now()
        save_to_db(current_user)
        return fn(*args, **kwargs)

    return decorator


@second_order_decorator(jwt_required)
def is_super_admin(f):
    """
    仅限超级管理员的装饰器函数。
    如果资源也可由普通管理员访问，请不要使用此函数，而应使用is_admin装饰器。
    
    参数:
        f: 要装饰的函数
        
    返回:
        装饰后的函数
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = current_user
        if not user.is_super_admin:
            raise ForbiddenError({'source': ''}, '需要超级管理员权限')
        return f(*args, **kwargs)

    return decorated_function


@second_order_decorator(jwt_required)
def is_admin(f):
    """
    管理员和超级管理员装饰器函数。
    
    参数:
        f: 要装饰的函数
        
    返回:
        装饰后的函数
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = current_user
        if not user.is_admin and not user.is_super_admin:
            raise ForbiddenError({'source': ''}, '需要管理员权限')
        return f(*args, **kwargs)

    return decorated_function


@second_order_decorator(jwt_required)
def is_user_itself(f):
    """
    允许管理员和超级管理员访问任何资源，无论ID如何。
    否则用户只能访问他/她自己的资源。
    
    参数:
        f: 要装饰的函数
        
    返回:
        装饰后的函数
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = current_user
        if not user.is_admin and not user.is_super_admin and user.id != kwargs['id']:
            raise ForbiddenError({'source': ''}, 'Access Forbidden')
        return f(*args, **kwargs)

    return decorated_function


@second_order_decorator(jwt_required)
def is_owner(f):
    """
    Allows only Owner to access the event resources.
    :param f:
    :return:
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = current_user

        if user.is_staff:
            return f(*args, **kwargs)
        if 'event_id' in kwargs and user.is_owner(kwargs['event_id']):
            return f(*args, **kwargs)
        raise ForbiddenError({'source': ''}, 'Owner access is required')

    return decorated_function


@second_order_decorator(jwt_required)
def is_organizer(f):
    """
    Allows only Organizer to access the event resources.
    :param f:
    :return:
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = current_user

        if user.is_staff:
            return f(*args, **kwargs)
        if 'event_id' in kwargs and user.is_organizer(kwargs['event_id']):
            return f(*args, **kwargs)
        raise ForbiddenError({'source': ''}, 'Organizer access is required')

    return decorated_function


def to_event_id(func):
    """
    Change event_identifier to event_id in kwargs
    :param f:
    :return:
    """

    @wraps(func)
    def decorated_function(*args, **kwargs):

        if 'event_identifier' in kwargs:
            if not kwargs['event_identifier'].isdigit():
                event = (
                    db.session.query(Event)
                    .filter_by(identifier=kwargs['event_identifier'])
                    .first()
                )
                kwargs['event_id'] = event.id
            else:
                kwargs['event_id'] = kwargs['event_identifier']
            kwargs.pop('event_identifier', None)
        return func(*args, **kwargs)

    return decorated_function


@second_order_decorator(jwt_required)
def is_coorganizer(f):
    """
    Allows Organizer and Co-organizer to access the event resources.
    :param f:
    :return:
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = current_user

        if user.is_staff or (
            'event_id' in kwargs and user.has_event_access(kwargs['event_id'])
        ):
            return f(*args, **kwargs)
        raise ForbiddenError({'source': ''}, 'Co-organizer access is required.')

    return decorated_function


@second_order_decorator(jwt_required)
def is_registrar(f):
    """
    Allows Organizer, Co-organizer and registrar to access the event resources.
    :param f:
    :return:
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = current_user

        if user.is_staff:
            return f(*args, **kwargs)
        if 'event_id' in kwargs and (
            user.is_registrar(kwargs['event_id'])
            or user.has_event_access(kwargs['event_id'])
        ):
            return f(*args, **kwargs)
        raise ForbiddenError({'source': ''}, 'Registrar Access is Required.')

    return decorated_function


@second_order_decorator(jwt_required)
def is_track_organizer(f):
    """
    Allows Organizer, Co-organizer and Track Organizer to access the resource(s).
    :param f:
    :return:
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = current_user

        if user.is_staff:
            return f(*args, **kwargs)
        if 'event_id' in kwargs and (
            user.is_track_organizer(kwargs['event_id'])
            or user.has_event_access(kwargs['event_id'])
        ):
            return f(*args, **kwargs)
        raise ForbiddenError({'source': ''}, 'Track Organizer access is Required.')

    return decorated_function


@second_order_decorator(jwt_required)
def is_moderator(f):
    """
    Allows Organizer, Co-organizer and Moderator to access the resource(s).
    :param f:
    :return:
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = current_user

        if user.is_staff:
            return f(*args, **kwargs)
        if 'event_id' in kwargs and (
            user.is_moderator(kwargs['event_id'])
            or user.has_event_access(kwargs['event_id'])
        ):
            return f(*args, **kwargs)
        raise ForbiddenError({'source': ''}, 'Moderator Access is Required.')

    return decorated_function


@second_order_decorator(jwt_required)
def accessible_events(f):
    """
    Filter the accessible events to the current authorized user
    If the user is not admin then only events created by user is
    accessible.
    :param f:
    :return:
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = current_user
        if 'POST' in request.method:
            kwargs['user_id'] = user.id
        else:
            if not user.is_staff:
                kwargs['user_id'] = user.id

        return f(*args, **kwargs)

    return decorated_function
