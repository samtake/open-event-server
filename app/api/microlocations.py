from flask_rest_jsonapi import ResourceDetail, ResourceList, ResourceRelationship

from app.api.bootstrap import api
from app.api.helpers.db import safe_query_kwargs
from app.api.helpers.errors import ForbiddenError
from app.api.helpers.permission_manager import has_access
from app.api.helpers.query import event_query
from app.api.helpers.utilities import require_relationship
from app.api.schema.microlocations import MicrolocationSchema
from app.models import db
from app.models.microlocation import Microlocation
from app.models.session import Session


class MicrolocationListPost(ResourceList):
    """
    微位置列表和创建类
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
    schema = MicrolocationSchema
    data_layer = {'session': db.session, 'model': Microlocation}


class MicrolocationList(ResourceList):
    """
    微位置列表类
    """

    def query(self, view_kwargs):
        """
        资源列表的查询方法
        :param view_kwargs: 视图关键字参数
        :return:
        """
        query_ = self.session.query(Microlocation)
        query_ = event_query(query_, view_kwargs)
        if view_kwargs.get('session_id'):
            session = safe_query_kwargs(Session, view_kwargs, 'session_id')
            query_ = query_.join(Session).filter(Session.id == session.id)
        elif view_kwargs.get('video_stream_id'):
            query_ = query_.filter_by(video_stream_id=view_kwargs['video_stream_id'])
        return query_

    view_kwargs = True
    methods = ['GET']
    schema = MicrolocationSchema
    data_layer = {
        'session': db.session,
        'model': Microlocation,
        'methods': {'query': query},
    }


class MicrolocationDetail(ResourceDetail):
    """
    Microlocation detail by id
    """

    def before_get_object(self, view_kwargs):
        """
        before get method to get the resource id for fetching details
        :param view_kwargs:
        :return:
        """
        if view_kwargs.get('session_id') is not None:
            session = safe_query_kwargs(Session, view_kwargs, 'session_id')
            if session.microlocation_id is not None:
                view_kwargs['id'] = session.microlocation_id
            else:
                view_kwargs['id'] = None

    decorators = (
        api.has_permission(
            'is_coorganizer',
            methods="PATCH,DELETE",
            fetch="event_id",
            model=Microlocation,
        ),
    )
    schema = MicrolocationSchema
    data_layer = {
        'session': db.session,
        'model': Microlocation,
        'methods': {'before_get_object': before_get_object},
    }


class MicrolocationRelationshipRequired(ResourceRelationship):
    """
    Microlocation Relationship for required entities
    """

    decorators = (
        api.has_permission(
            'is_coorganizer',
            methods="PATCH",
            fetch="event_id",
            model=Microlocation,
        ),
    )
    methods = ['GET', 'PATCH']
    schema = MicrolocationSchema
    data_layer = {'session': db.session, 'model': Microlocation}


class MicrolocationRelationshipOptional(ResourceRelationship):
    """
    Microlocation Relationship
    """

    decorators = (
        api.has_permission(
            'is_coorganizer',
            methods="PATCH,DELETE",
            fetch="event_id",
            model=Microlocation,
        ),
    )
    schema = MicrolocationSchema
    data_layer = {'session': db.session, 'model': Microlocation}
