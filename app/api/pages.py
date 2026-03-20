from flask_rest_jsonapi import ResourceDetail, ResourceList

from app.api.bootstrap import api
from app.api.schema.pages import PageSchema
from app.models import db
from app.models.page import Page


class PageList(ResourceList):
    """
    列出和创建页面
    """

    # 权限装饰器，只有管理员才能执行POST方法
    decorators = (api.has_permission('is_admin', methods="POST"),)
    schema = PageSchema
    data_layer = {'session': db.session, 'model': Page}


class PageDetail(ResourceDetail):
    """
    根据ID获取页面详情
    """

    schema = PageSchema
    # 权限装饰器，只有管理员才能执行PATCH和DELETE方法
    decorators = (api.has_permission('is_admin', methods="PATCH,DELETE"),)
    data_layer = {'session': db.session, 'model': Page}
