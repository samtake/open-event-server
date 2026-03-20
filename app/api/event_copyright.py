from flask_rest_jsonapi import ResourceDetail, ResourceList, ResourceRelationship
from sqlalchemy.orm.exc import NoResultFound

from app.api.bootstrap import api
from app.api.helpers.db import safe_query, safe_query_kwargs
from app.api.helpers.errors import ForbiddenError, UnprocessableEntityError
from app.api.helpers.permission_manager import has_access
from app.api.helpers.utilities import require_relationship
from app.api.schema.event_copyright import EventCopyrightSchema
from app.models import db
from app.models.event import Event
from app.models.event_copyright import EventCopyright


class EventCopyrightListPost(ResourceList):
    """
    事件版权列表POST类，用于创建事件版权
    仅允许POST方法
    """

    def before_post(self, args, kwargs, data):
        """
        post方法前的检查方法，用于验证必需的关系和适当的权限
        :param args: 参数
        :param kwargs: 关键字参数
        :param data: 数据
        :return:
        """
        # 检查是否提供了必需的关系（事件）
        require_relationship(['event'], data)
        # 检查用户是否有共同组织者权限
        if not has_access('is_coorganizer', event_id=data['event']):
            raise ForbiddenError({'source': ''}, '需要共同组织者权限。')

    def before_create_object(self, data, view_kwargs):
        """
        创建对象前的检查方法，用于检查该事件是否已存在版权
        :param data: 数据
        :param view_kwargs: 视图关键字参数
        :return:
        """
        try:
            # 检查是否已存在该事件的版权记录
            self.session.query(EventCopyright).filter_by(
                event_id=data['event'], deleted_at=None
            ).one()
        except NoResultFound:
            # 如果不存在，则继续执行
            pass
        else:
            # 如果已存在，则抛出错误
            raise UnprocessableEntityError(
                {'parameter': 'event_identifier'},
                "已为提供的事件ID存在事件版权",
            )

    # 允许的方法
    methods = [
        'POST',
    ]
    # 视图参数
    view_kwargs = True
    schema = EventCopyrightSchema
    data_layer = {
        'session': db.session,
        'model': EventCopyright,
        'methods': {'before_create_object': before_create_object},
    }


class EventCopyrightDetail(ResourceDetail):
    """
    事件版权详情类
    """

    def before_get_object(self, view_kwargs):
        """
        获取对象前的检查方法，用于获取版权ID以获取详情
        :param view_kwargs: 视图关键字参数
        :return:
        """
        event = None
        # 根据event_id获取事件
        if view_kwargs.get('event_id'):
            event = safe_query_kwargs(Event, view_kwargs, 'event_id')
        # 根据event_identifier获取事件
        elif view_kwargs.get('event_identifier'):
            event = safe_query_kwargs(
                Event, view_kwargs, 'event_identifier', 'identifier'
            )

        # 如果找到了事件，则获取对应的版权
        if event:
            event_copyright = safe_query(EventCopyright, 'event_id', event.id, 'event_id')
            view_kwargs['id'] = event_copyright.id

    # 权限装饰器，只有共同组织者才能进行PATCH和DELETE操作
    decorators = (
        api.has_permission(
            'is_coorganizer',
            fetch="event_id",
            model=EventCopyright,
            methods="PATCH,DELETE",
        ),
    )
    schema = EventCopyrightSchema
    data_layer = {
        'session': db.session,
        'model': EventCopyright,
        'methods': {'before_get_object': before_get_object},
    }


class EventCopyrightRelationshipRequired(ResourceRelationship):
    """
    事件版权关系类
    """

    # 权限装饰器，只有共同组织者才能进行PATCH操作
    decorators = (
        api.has_permission(
            'is_coorganizer',
            fetch="event_id",
            model=EventCopyright,
            methods="PATCH",
        ),
    )
    # 允许的方法和视图
    methods = ['GET', 'PATCH']
    schema = EventCopyrightSchema
    data_layer = {'session': db.session, 'model': EventCopyright}
