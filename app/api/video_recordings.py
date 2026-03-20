from datetime import datetime

from flask_rest_jsonapi import ResourceDetail, ResourceList
from flask_rest_jsonapi.resource import ResourceRelationship

from app.api.helpers.db import get_or_create, safe_query_kwargs
from app.api.helpers.errors import ForbiddenError, UnprocessableEntityError
from app.api.helpers.permission_manager import has_access
from app.api.helpers.permissions import jwt_required
from app.api.schema.video_recordings import VideoRecordingSchema
from app.api.video_channels.bbb import BigBlueButton
from app.models import db
from app.models.video_recording import VideoRecording
from app.models.video_stream import VideoStream


class VideoRecordingList(ResourceList):
    def before_get(self, args, kwargs):
        """get方法前的检查方法"""
        if kwargs.get('video_stream_id'):
            # 获取视频流
            stream = safe_query_kwargs(VideoStream, kwargs, 'video_stream_id', 'id')

            # 如果是BBB通道
            if stream.channel and stream.channel.provider == 'bbb':
                # 检查是否有组织者权限
                if not has_access('is_organizer', event_id=stream.event_id):
                    raise ForbiddenError(
                        {'pointer': 'event_id'},
                        '需要是事件组织者才能访问视频录制。',
                    )

                # 如果流有额外信息
                if stream.extra is not None:
                    # 设置参数
                    params = dict(
                        meetingID=stream.extra['response']['meetingID'],
                    )
                    channel = stream.channel
                    bbb = BigBlueButton(channel.api_url, channel.api_key)
                    result = bbb.request('getRecordings', params)

                    # 如果有录制
                    if result.data['response']['recordings']:
                        recordings = []
                        if (
                            type(result.data['response']['recordings']['recording'])
                            is list
                        ):
                            recordings = result.data['response']['recordings'][
                                'recording'
                            ]
                        else:
                            recordings.append(
                                result.data['response']['recordings']['recording']
                            )
                        for recording in recordings:
                            get_or_create(
                                VideoRecording,
                                bbb_record_id=recording['recordID'],
                                participants=recording['participants'],
                                url=recording['playback']['format']['url'],
                                start_time=datetime.fromtimestamp(
                                    int(int(recording['startTime']) / 1000)
                                ),
                                end_time=datetime.fromtimestamp(
                                    int(int(recording['endTime']) / 1000)
                                ),
                                video_stream=stream,
                            )

    def query(self, view_kwargs):
        """查询方法"""
        query_ = VideoRecording.query
        # 如果提供了视频流ID，则过滤该视频流的录制
        if view_kwargs.get('video_stream_id'):
            stream = safe_query_kwargs(VideoStream, view_kwargs, 'video_stream_id')
            query_ = VideoRecording.query.filter(
                VideoRecording.video_stream_id == stream.id
            )
        else:
            # 检查用户是否有管理员权限
            if not has_access('is_admin'):
                raise ForbiddenError(
                    {'pointer': 'user'},
                    '需要是管理员才能访问视频录制。',
                )

        return query_

    # 允许的方法
    methods = ['GET']
    view_kwargs = True
    # 需要JWT认证
    decorators = (jwt_required,)
    schema = VideoRecordingSchema
    data_layer = {
        'session': db.session,
        'model': VideoRecording,
        'methods': {
            'query': query,
            'before_get': before_get,
        },
    }


class VideoRecordingDetail(ResourceDetail):
    """
    视频录制详情
    """

    def before_get_object(self, view_kwargs):
        """获取对象前的检查方法"""
        # 如果提供了视频流ID，则设置ID
        if view_kwargs.get('video_stream_id'):
            video_stream = safe_query_kwargs(
                VideoStream,
                view_kwargs,
                'video_stream_id',
            )
            view_kwargs['id'] = video_stream.id

    def after_get_object(self, video_recording, view_kwargs):
        """获取对象后的检查方法"""
        # 检查用户是否有组织者权限
        if not has_access('is_organizer', event_id=video_recording.video_stream.event_id):
            raise ForbiddenError(
                {'pointer': 'event_id'},
                '需要是事件组织者才能访问视频录制。',
            )

    def before_delete_object(self, video_recording, kwargs):
        """
        删除录制详情对象前的检查方法
        :param video_recording: 视频录制对象
        :param kwargs: 关键字参数
        :return:
        """
        # 检查用户是否有管理员权限
        if not has_access('is_admin'):
            raise ForbiddenError(
                {'source': 'User'}, '您没有权限访问此内容。'
            )
        # 获取视频流
        stream = video_recording.video_stream
        # 设置参数
        params = dict(
            recordID=video_recording.bbb_record_id,
        )
        channel = stream.channel
        bbb = BigBlueButton(channel.api_url, channel.api_key)
        # 请求删除录制
        result = bbb.request('deleteRecordings', params)

        # 如果删除失败，抛出错误
        if not result.success:
            raise UnprocessableEntityError(
                {'source': 'recording_id'}, '删除录制时出错'
            )

    # 允许的方法
    methods = ['GET', 'DELETE']
    schema = VideoRecordingSchema
    # 需要JWT认证
    decorators = (jwt_required,)
    data_layer = {
        'session': db.session,
        'model': VideoRecording,
        'methods': {
            'before_get_object': before_get_object,
            'after_get_object': after_get_object,
            'before_delete_object': before_delete_object,
        },
    }


class VideoRecordingRelationship(ResourceRelationship):
    """
    视频录制关系
    """
    
    schema = VideoRecordingSchema
    # 允许的方法
    methods = ['GET']
    data_layer = {'session': db.session, 'model': VideoRecording}
