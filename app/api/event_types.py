from flask_rest_jsonapi import ResourceDetail, ResourceList, ResourceRelationship

from app.api.bootstrap import api
from app.api.helpers.db import safe_query_kwargs
from app.api.schema.event_types import EventTypeSchema
from app.models import db
from app.models.event import Event
from app.models.event_type import EventType


class EventTypeList(ResourceList):
    """
    列出和创建事件类型
    """

    # 权限装饰器，只有管理员才能执行POST方法
    decorators = (api.has_permission('is_admin', methods="POST"),)
    schema = EventTypeSchema
    data_layer = {'session': db.session, 'model': EventType}


class EventTypeDetail(ResourceDetail):
    """
    根据ID获取事件类型详情
    """

    def before_get_object(self, view_kwargs):
        """
        get方法前的检查方法，用于获取资源ID以获取详情
        :param view_kwargs: 视图关键字参数
        :return:
        """
        # 如果提供了事件标识符，则获取事件并设置事件ID
        if view_kwargs.get('event_identifier'):
            event = safe_query_kwargs(
                Event, view_kwargs, 'event_identifier', 'identifier'
            )
            view_kwargs['event_id'] = event.id

        # 如果提供了事件ID，则获取事件类型ID
        if view_kwargs.get('event_id'):
            event = safe_query_kwargs(Event, view_kwargs, 'event_id')
            if event.event_type_id:
                view_kwargs['id'] = event.event_type_id
            else:
                view_kwargs['id'] = None

    # 权限装饰器，只有管理员才能执行PATCH和DELETE方法
    decorators = (api.has_permission('is_admin', methods="PATCH,DELETE"),)
    schema = EventTypeSchema
    data_layer = {
        'session': db.session,
        'model': EventType,
        'methods': {'before_get_object': before_get_object},
    }


class EventTypeRelationship(ResourceRelationship):
    """
    Event type Relationship
    """

    decorators = (api.has_permission('is_admin', methods="PATCH,DELETE"),)
    schema = EventTypeSchema
    data_layer = {'session': db.session, 'model': EventType}
