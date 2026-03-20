from flask_rest_jsonapi import ResourceDetail, ResourceList

from app.api.bootstrap import api
from app.api.schema.services import ServiceSchema
from app.models import db
from app.models.service import Service


class ServiceList(ResourceList):
    """
    列出所有服务，如微位置、会话、演讲者、轨道、赞助商
    """

    # 权限装饰器，只有管理员才能访问
    decorators = (api.has_permission('is_admin', methods="GET"),)
    # 允许的方法
    methods = ['GET']
    schema = ServiceSchema
    data_layer = {'session': db.session, 'model': Service}


class ServiceDetail(ResourceDetail):
    """
    根据ID获取服务详情
    """

    # 权限装饰器，只有管理员才能执行PATCH方法
    decorators = (api.has_permission('is_admin', methods="PATCH"),)
    schema = ServiceSchema
    # 允许的方法
    methods = ['GET', 'PATCH']
    data_layer = {'session': db.session, 'model': Service}
