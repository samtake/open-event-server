#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
错误处理模块 - Open Event Server API错误响应

此模块定义了符合JSON:API规范的错误响应类。

作者: FOSSASIA
"""

import json
from typing import Union

from flask import make_response
from flask_rest_jsonapi import JsonApiException
from flask_rest_jsonapi.errors import jsonapi_errors


class ErrorResponse(JsonApiException):
    """
    错误响应父类，用于处理符合json-api规范的错误。
    受`flask-rest-jsonapi`本身的JsonApiException类启发
    """

    headers = {'Content-Type': 'application/vnd.api+json'}

    def __init__(self, source: Union[dict, str], detail=None, title=None, status=None):
        """
        初始化jsonapi错误响应对象

        参数:
            source: 错误来源
            detail: 错误详情
            title: 错误标题
            status: HTTP状态码
        """

        if isinstance(source, str) and detail is None:
            # 我们被传递了一个参数，因此source未知
            # 所以我们将source表示为detail
            super().__init__(None, source)
        else:
            super().__init__(source, detail, title, status)

    def respond(self):
        """
        返回符合jsonapi规范的响应对象
        
        返回:
            Response: Flask响应对象
        """
        dict_ = self.to_dict()
        return make_response(
            json.dumps(jsonapi_errors([dict_])), self.status, self.headers
        )


class ForbiddenError(ErrorResponse):
    """
    403错误的默认类
    """

    title = '访问被禁止'
    status = 403


class NotFoundError(ErrorResponse):
    """
    404错误的默认类
    """

    title = '未找到'
    status = 404


class ServerError(ErrorResponse):
    """
    500错误的默认类
    """
    status = 500
    title = '内部服务器错误'


class UnprocessableEntityError(ErrorResponse):
    """
    422错误的默认类
    """

    status = 422
    title = '无法处理的实体'


class BadRequestError(ErrorResponse):
    """
    400错误的默认类
    """

    status = 400
    title = '错误请求'


class ConflictError(ErrorResponse):
    """
    409错误的默认类
    """

    title = "冲突"
    status = 409


class MethodNotAllowed(ErrorResponse):
    """
    抛出HTTP 405异常的默认类
    """

    title = "方法不被允许"
    status = 405
