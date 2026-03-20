from flask_rest_jsonapi import ResourceDetail

from app.api.bootstrap import api
from app.api.helpers.db import safe_query_kwargs
from app.api.schema.event_statistics import EventStatisticsGeneralSchema
from app.models import db
from app.models.event import Event


class EventStatisticsGeneralDetail(ResourceDetail):
    """
    根据ID获取事件统计详情
    """

    def before_get_object(self, view_kwargs):
        """
        get方法前的检查方法，用于获取资源ID以获取详情
        :param view_kwargs: 视图关键字参数
        :return:
        """
        # 如果提供了标识符，则获取事件并设置ID
        if view_kwargs.get('identifier'):
            event = safe_query_kwargs(Event, view_kwargs, 'identifier', 'identifier')
            view_kwargs['id'] = event.id

    # 允许的方法
    methods = ['GET']
    # 权限装饰器，只有共同组织者才能访问
    decorators = (
        api.has_permission(
            'is_coorganizer', fetch="id", fetch_as="event_id", model=Event
        ),
    )
    schema = EventStatisticsGeneralSchema
    data_layer = {
        'session': db.session,
        'model': Event,
        'methods': {'before_get_object': before_get_object},
    }
