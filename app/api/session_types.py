from flask_rest_jsonapi import ResourceDetail, ResourceList, ResourceRelationship

from app.api.bootstrap import api
from app.api.helpers.db import safe_query_kwargs
from app.api.helpers.errors import ForbiddenError
from app.api.helpers.permission_manager import has_access
from app.api.helpers.query import event_query
from app.api.helpers.utilities import require_relationship
from app.api.schema.session_types import SessionTypeSchema
from app.models import db
from app.models.session import Session
from app.models.session_type import SessionType


class SessionTypeListPost(ResourceList):
    """
    会话类型列表和创建类
    """

    def before_post(self, args, kwargs, data):
        """
        post方法前的检查方法，用于验证必需的关系和适当权限
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

    # 允许的方法
    methods = [
        'POST',
    ]
    schema = SessionTypeSchema
    data_layer = {'session': db.session, 'model': SessionType}


class SessionTypeList(ResourceList):
    """
    会话类型列表类
    """

    def query(self, view_kwargs):
        """
        会话类型列表的查询方法
        :param view_kwargs: 视图关键字参数
        :return:
        """
        query_ = self.session.query(SessionType)
        query_ = event_query(query_, view_kwargs)
        return query_

    view_kwargs = True
    methods = [
        'GET',
    ]
    schema = SessionTypeSchema
    data_layer = {
        'session': db.session,
        'model': SessionType,
        'methods': {
            'query': query,
        },
    }


class SessionTypeDetail(ResourceDetail):
    """
    Detail about a single session type by id
    """

    def before_get_object(self, view_kwargs):
        """
        before get method for session type detail
        :param data:
        :param view_kwargs:
        :return:
        """
        if view_kwargs.get('session_id'):
            session = safe_query_kwargs(Session, view_kwargs, 'session_id')
            if session.session_type_id:
                view_kwargs['id'] = session.session_type_id
            else:
                view_kwargs['id'] = None

    decorators = (
        api.has_permission(
            'is_coorganizer',
            methods="PATCH,DELETE",
            fetch="event_id",
            model=SessionType,
        ),
    )
    schema = SessionTypeSchema
    data_layer = {
        'session': db.session,
        'model': SessionType,
        'methods': {'before_get_object': before_get_object},
    }


class SessionTypeRelationshipRequired(ResourceRelationship):
    """
    SessionType Relationship
    """

    methods = ['GET', 'PATCH']
    decorators = (
        api.has_permission(
            'is_coorganizer',
            methods="PATCH",
            fetch="event_id",
            model=SessionType,
        ),
    )
    schema = SessionTypeSchema
    data_layer = {'session': db.session, 'model': SessionType}


class SessionTypeRelationshipOptional(ResourceRelationship):
    """
    SessionType Relationship
    """

    decorators = (
        api.has_permission(
            'is_coorganizer',
            methods="PATCH,DELETE",
            fetch="event_id",
            model=SessionType,
        ),
    )
    schema = SessionTypeSchema
    data_layer = {'session': db.session, 'model': SessionType}
