from flask_rest_jsonapi import ResourceDetail, ResourceList

from app.api.bootstrap import api
from app.api.helpers.db import safe_query_kwargs
from app.api.helpers.permission_manager import has_access, is_logged_in
from app.api.schema.video_channel import VideoChannelSchema, VideoChannelSchemaPublic
from app.models import db
from app.models.video_channel import VideoChannel
from app.models.video_stream import VideoStream


class VideoChannelListPost(ResourceList):
    """
    创建视频通道
    """

    # 允许的方法
    methods = ['POST']
    # 权限装饰器，只有管理员才能执行POST方法
    decorators = (api.has_permission('is_admin', methods="POST"),)
    schema = VideoChannelSchema
    data_layer = {
        'session': db.session,
        'model': VideoChannel,
    }


class VideoChannelList(ResourceList):
    """
    列出视频通道
    """

    def before_get(self, args, kwargs):
        """get方法前的检查方法"""
        # 如果用户已登录且有管理员权限，则使用完整模式
        if is_logged_in() and has_access('is_admin'):
            self.schema = VideoChannelSchema
        else:
            # 否则使用公共模式
            self.schema = VideoChannelSchemaPublic

    # 允许的方法
    methods = ['GET']
    schema = VideoChannelSchemaPublic
    data_layer = {
        'session': db.session,
        'model': VideoChannel,
    }


class VideoChannelDetail(ResourceDetail):
    """
    视频通道详情
    """

    def before_get(self, args, kwargs):
        """get方法前的检查方法"""
        # 如果用户已登录且有管理员权限，则使用完整模式
        if is_logged_in() and has_access('is_admin'):
            self.schema = VideoChannelSchema
        else:
            # 否则使用公共模式
            self.schema = VideoChannelSchemaPublic

        # 如果提供了视频流ID，则获取通道ID
        if kwargs.get('video_stream_id'):
            stream = safe_query_kwargs(VideoStream, kwargs, 'video_stream_id')
            kwargs['id'] = stream.channel_id

    schema = VideoChannelSchema
    decorators = (
        api.has_permission(
            'is_admin',
            methods="PATCH,DELETE",
        ),
    )
    data_layer = {
        'session': db.session,
        'model': VideoChannel,
    }
