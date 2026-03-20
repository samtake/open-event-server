from flask_jwt_extended import current_user
from flask_rest_jsonapi import ResourceDetail, ResourceList, ResourceRelationship

from app.api.helpers.db import safe_query_kwargs
from app.api.helpers.errors import ForbiddenError
from app.api.helpers.mail import send_email_to_moderator
from app.api.helpers.permission_manager import has_access
from app.api.helpers.permissions import jwt_required
from app.api.helpers.utilities import require_relationship
from app.api.schema.video_stream_moderators import VideoStreamModeratorSchema
from app.models import db
from app.models.user import User
from app.models.video_stream import VideoStream
from app.models.video_stream_moderator import VideoStreamModerator


class VideoStreamModeratorList(ResourceList):
    """
    视频流主持人列表
    """

    def before_post(self, args, kwargs, data):
        """post方法前的检查方法"""
        # 检查是否提供了必需的关系（视频流）
        require_relationship(['video_stream'], data)
        # 获取视频流
        stream = safe_query_kwargs(VideoStream, data, 'video_stream')
        # 检查用户是否有共同组织者权限
        if not has_access('is_coorganizer', event_id=stream.event_id):
            raise ForbiddenError({'pointer': 'user_id'}, '需要共同组织者权限')

    def after_create_object(self, video_stream_moderator, data, view_kwargs):
        """创建对象后的方法"""
        # 发送邮件给主持人
        send_email_to_moderator(video_stream_moderator)

    def query(self, view_kwargs):
        """查询方法"""
        query_ = self.session.query(VideoStreamModerator)
        # 如果提供了用户ID
        if user_id := view_kwargs.get('user_id'):
            # 检查是否是当前用户
            if current_user.id != int(user_id):
                raise ForbiddenError(
                    {'pointer': 'user_id'}, "不能访问其他用户的数据"
                )
            # 获取用户并过滤
            user = safe_query_kwargs(User, view_kwargs, 'user_id')
            query_ = query_.filter_by(email=user.email)
        # 如果提供了视频流ID
        elif view_kwargs.get('video_stream_id'):
            stream = safe_query_kwargs(VideoStream, view_kwargs, 'video_stream_id')
            # 检查用户是否有共同组织者权限
            if not has_access('is_coorganizer', event_id=stream.event_id):
                raise ForbiddenError(
                    {'pointer': 'user_id'}, '需要共同组织者权限'
                )
            query_ = query_.filter_by(video_stream_id=view_kwargs['video_stream_id'])
        else:
            raise ForbiddenError({'pointer': 'query'}, '不能查询所有主持人')
        return query_

    view_kwargs = True
    # 需要JWT认证
    decorators = (jwt_required,)
    # 允许的方法
    methods = ['GET', 'POST']
    schema = VideoStreamModeratorSchema
    data_layer = {
        'session': db.session,
        'model': VideoStreamModerator,
        'methods': {'query': query, 'after_create_object': after_create_object},
    }


class VideoStreamModeratorDetail(ResourceDetail):
    """
    video_stream_moderators detail by id
    """

    def after_get_object(self, obj, kwargs):
        if not has_access('is_coorganizer', event_id=obj.video_stream.event_id):
            raise ForbiddenError({'pointer': 'user_id'}, 'Co-Organizer access required')

    view_kwargs = True
    decorators = (jwt_required,)
    methods = ['GET', 'PATCH', 'DELETE']
    schema = VideoStreamModeratorSchema
    data_layer = {
        'session': db.session,
        'model': VideoStreamModerator,
        'methods': {'after_get_object': after_get_object},
    }


class VideoStreamModeratorRelationship(ResourceRelationship):
    """
    video_stream_moderators Relationship
    """

    methods = ['GET', 'PATCH']
    schema = VideoStreamModeratorSchema
    data_layer = {'session': db.session, 'model': VideoStreamModerator}
