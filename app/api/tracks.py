from flask_rest_jsonapi import ResourceDetail, ResourceList, ResourceRelationship

from app.api.bootstrap import api
from app.api.helpers.db import safe_query_kwargs
from app.api.helpers.errors import ForbiddenError
from app.api.helpers.permission_manager import has_access
from app.api.helpers.query import event_query
from app.api.helpers.utilities import require_relationship
from app.api.schema.tracks import TrackSchema
from app.models import db
from app.models.session import Session
from app.models.track import Track


class TrackListPost(ResourceList):
    """
    轨道列表和创建类
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
        # 检查用户是否有轨道组织者权限
        if not has_access('is_track_organizer', event_id=data['event']):
            raise ForbiddenError({'source': ''}, '需要轨道组织者权限。')

    schema = TrackSchema
    data_layer = {'session': db.session, 'model': Track}


class TrackList(ResourceList):
    """
    轨道列表类
    """

    def query(self, view_kwargs):
        """
        资源列表的查询方法
        :param view_kwargs: 视图关键字参数
        :return:
        """
        # 查询所有轨道
        query_ = self.session.query(Track)
        # 根据事件查询条件过滤
        query_ = event_query(query_, view_kwargs)
        return query_

    view_kwargs = True
    methods = ['GET']
    schema = TrackSchema
    data_layer = {'session': db.session, 'model': Track, 'methods': {'query': query}}


class TrackDetail(ResourceDetail):
    """
    Track detail by id
    """

    def before_get_object(self, view_kwargs):
        """
        before get method to get the resource id for fetching details
        :param view_kwargs:
        :return:
        """
        if view_kwargs.get('session_id'):
            session = safe_query_kwargs(Session, view_kwargs, 'session_id')
            if session.event_id:
                view_kwargs['id'] = session.track_id
            else:
                view_kwargs['id'] = None

    decorators = (
        api.has_permission(
            'is_track_organizer',
            fetch='event_id',
            model=Track,
            methods="PATCH,DELETE",
        ),
    )
    schema = TrackSchema
    data_layer = {
        'session': db.session,
        'model': Track,
        'methods': {'before_get_object': before_get_object},
    }


class TrackRelationshipRequired(ResourceRelationship):
    """
    Track Relationship
    """

    decorators = (
        api.has_permission(
            'is_track_organizer',
            fetch='event_id',
            model=Track,
            methods="PATCH",
        ),
    )
    methods = ['GET', 'PATCH']
    schema = TrackSchema
    data_layer = {'session': db.session, 'model': Track}


class TrackRelationshipOptional(ResourceRelationship):
    """
    Track Relationship
    """

    decorators = (
        api.has_permission(
            'is_track_organizer',
            fetch='event_id',
            model=Track,
            methods="PATCH,DELETE",
        ),
    )
    schema = TrackSchema
    data_layer = {'session': db.session, 'model': Track}
