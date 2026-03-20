from flask_rest_jsonapi import ResourceDetail, ResourceList

from app.api.bootstrap import api
from app.api.schema.mails import MailSchema
from app.models import db
from app.models.mail import Mail


class MailList(ResourceList):
    """
    列出和创建邮件
    """

    # 权限装饰器，只有管理员才能访问
    decorators = (api.has_permission('is_admin'),)
    # 允许的方法
    methods = ['GET']
    schema = MailSchema
    data_layer = {'session': db.session, 'model': Mail}


class MailDetail(ResourceDetail):
    """
    根据ID获取邮件详情
    """

    # 允许的方法
    methods = ['GET']
    schema = MailSchema
    # 权限装饰器，只有管理员才能访问
    decorators = (api.has_permission('is_admin'),)
    data_layer = {'session': db.session, 'model': Mail}
