import urllib.error

from flask_rest_jsonapi import ResourceDetail, ResourceList, ResourceRelationship

from app.api.bootstrap import api
from app.api.helpers.db import safe_query_kwargs
from app.api.helpers.errors import UnprocessableEntityError
from app.api.helpers.files import create_system_image
from app.api.schema.event_topics import EventTopicSchema
from app.models import db
from app.models.event import Event
from app.models.event_sub_topic import EventSubTopic
from app.models.event_topic import EventTopic


class EventTopicList(ResourceList):
    """
    列出和创建事件主题
    """

    def after_create_object(self, event_topic, data, view_kwargs):
        """
        创建后方法，用于保存用户角色并将用户添加为已接受角色（组织者）
        :param event_topic: 事件主题
        :param data: 数据
        :param view_kwargs: 视图关键字参数
        :return:
        """
        # 如果提供了系统图片URL，则创建系统图片
        if data.get('system_image_url'):
            try:
                uploaded_image = create_system_image(
                    data['system_image_url'], unique_identifier=event_topic.id
                )
            except (urllib.error.HTTPError, urllib.error.URLError):
                raise UnprocessableEntityError(
                    {'source': 'attributes/system-image-url'}, '图片URL无效'
                )
            except OSError:
                raise UnprocessableEntityError(
                    {'source': 'attributes/system-image-url'}, 'URL处图片不存在'
                )
        else:
            # 否则创建默认系统图片
            try:
                uploaded_image = create_system_image(unique_identifier=event_topic.id)
            except OSError:
                raise UnprocessableEntityError(
                    {'source': ''}, '服务器上缺少默认图片'
                )

        self.session.query(EventTopic).filter_by(id=event_topic.id).update(uploaded_image)
        self.session.commit()

    decorators = (api.has_permission('is_admin', methods="POST"),)
    schema = EventTopicSchema
    data_layer = {
        'session': db.session,
        'model': EventTopic,
        'methods': {'after_create_object': after_create_object},
    }


class EventTopicDetail(ResourceDetail):
    """
    Event topic detail by id
    """

    def before_get_object(self, view_kwargs):
        """
        before get method to get the resource id for fetching details
        :param view_kwargs:
        :return:
        """
        if view_kwargs.get('event_identifier'):
            event = safe_query_kwargs(
                Event, view_kwargs, 'event_identifier', 'identifier'
            )
            view_kwargs['event_id'] = event.id

        if view_kwargs.get('event_id'):
            event = safe_query_kwargs(Event, view_kwargs, 'event_id')
            if event.event_topic_id:
                view_kwargs['id'] = event.event_topic_id
            else:
                view_kwargs['id'] = None

        if view_kwargs.get('event_sub_topic_id'):
            event_sub_topic = safe_query_kwargs(
                EventSubTopic,
                view_kwargs,
                'event_sub_topic_id',
            )
            if event_sub_topic.event_topic_id:
                view_kwargs['id'] = event_sub_topic.event_topic_id
            else:
                view_kwargs['id'] = None

    def before_update_object(self, event_topic, data, view_kwargs):
        """
        method to save image urls before updating event object
        :param event_topic:
        :param data:
        :param view_kwargs:
        :return:
        """
        # 如果提供了系统图片URL，则创建系统图片
        if data.get('system_image_url'):
            try:
                uploaded_image = create_system_image(
                    data['system_image_url'], unique_identifier=event_topic.id
                )
            except (urllib.error.HTTPError, urllib.error.URLError):
                raise UnprocessableEntityError(
                    {'source': 'attributes/system-image-url'}, '图片URL无效'
                )
            except OSError:
                raise UnprocessableEntityError(
                    {'source': 'attributes/system-image-url'}, 'URL处图片不存在'
                )
        else:
            # 否则创建默认系统图片
            try:
                uploaded_image = create_system_image(unique_identifier=event_topic.id)
            except OSError:
                raise UnprocessableEntityError(
                    {'source': ''}, '服务器上缺少默认图片'
                )

            data['system_image_url'] = uploaded_image['system_image_url']

    decorators = (api.has_permission('is_admin', methods="PATCH,DELETE"),)
    schema = EventTopicSchema
    data_layer = {
        'session': db.session,
        'model': EventTopic,
        'methods': {
            'before_update_object': before_update_object,
            'before_get_object': before_get_object,
        },
    }


class EventTopicRelationship(ResourceRelationship):
    """
    Event topic Relationship
    """

    decorators = (api.has_permission('is_admin', methods="PATCH,DELETE"),)
    schema = EventTopicSchema
    data_layer = {'session': db.session, 'model': EventTopic}
