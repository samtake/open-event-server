from flask_rest_jsonapi import ResourceDetail, ResourceList

from app.api.bootstrap import api
from app.api.schema.notification_settings import NotificationSettingSchema
from app.models import db
from app.models.notification_setting import NotificationSettings


class NotificationSettingsList(ResourceList):
    """
    通知设置列表
    """

    # 权限装饰器，只有管理员才能访问
    decorators = (api.has_permission('is_admin', methods="GET"),)
    # 允许的方法
    methods = ['GET']
    schema = NotificationSettingSchema
    data_layer = {'session': db.session, 'model': NotificationSettings}


class NotificationSettingsDetail(ResourceDetail):
    """
    通知设置详情
    """

    schema = NotificationSettingSchema
    # 权限装饰器，只有管理员才能执行PATCH方法
    decorators = (api.has_permission('is_admin', methods="PATCH"),)
    # 允许的方法
    methods = ['GET', 'PATCH']
    data_layer = {'session': db.session, 'model': NotificationSettings}
