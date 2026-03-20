from flask_rest_jsonapi import ResourceDetail, ResourceList, ResourceRelationship
from flask_rest_jsonapi.exceptions import ObjectNotFound

from app.api.bootstrap import api
from app.api.helpers.db import safe_query_kwargs
from app.api.helpers.permission_manager import has_access
from app.api.helpers.query import event_query
from app.api.helpers.utilities import require_relationship
from app.api.schema.faqs import FaqSchema
from app.models import db
from app.models.faq import Faq
from app.models.faq_type import FaqType


class FaqListPost(ResourceList):
    """
    创建和列出常见问题
    """

    def before_post(self, args, kwargs, data):
        """
        post方法前的检查方法，用于检查与事件的必需关系
        :param args: 参数
        :param kwargs: 关键字参数
        :param data: 数据
        :return:
        """
        # 检查是否提供了必需的关系（事件）
        require_relationship(['event'], data)
        # 检查用户是否有共同组织者权限
        if not has_access('is_coorganizer', event_id=data['event']):
            raise ObjectNotFound(
                {'parameter': 'event_id'}, "找不到事件: {}".format(data['event'])
            )

    schema = FaqSchema
    # 允许的方法
    methods = [
        'POST',
    ]
    data_layer = {'session': db.session, 'model': Faq}


class FaqList(ResourceList):
    """
    显示常见问题列表
    """

    def query(self, view_kwargs):
        """
        不同view_kwargs的查询方法
        :param view_kwargs: 视图关键字参数
        :return:
        """
        query_ = self.session.query(Faq)
        query_ = event_query(query_, view_kwargs)
        if view_kwargs.get('faq_type_id') is not None:
            faq_type = safe_query_kwargs(FaqType, view_kwargs, 'faq_type_id')
            query_ = query_.join(FaqType).filter(FaqType.id == faq_type.id)
        return query_

    view_kwargs = True
    methods = [
        'GET',
    ]
    schema = FaqSchema
    data_layer = {'session': db.session, 'model': Faq, 'methods': {'query': query}}


class FaqDetail(ResourceDetail):
    """
    FAQ Resource
    """

    decorators = (
        api.has_permission(
            'is_coorganizer',
            fetch='event_id',
            model=Faq,
            methods="PATCH,DELETE",
        ),
    )
    schema = FaqSchema
    data_layer = {'session': db.session, 'model': Faq}


class FaqRelationshipRequired(ResourceRelationship):
    """
    FAQ Relationship (Required)
    """

    decorators = (
        api.has_permission(
            'is_coorganizer',
            fetch='event_id',
            model=Faq,
            methods="PATCH",
        ),
    )
    methods = ['GET', 'PATCH']
    schema = FaqSchema
    data_layer = {'session': db.session, 'model': Faq}


class FaqRelationshipOptional(ResourceRelationship):
    """
    FAQ Relationship (Required)
    """

    decorators = (
        api.has_permission(
            'is_coorganizer',
            fetch='event_id',
            model=Faq,
            methods="PATCH",
        ),
    )
    schema = FaqSchema
    data_layer = {'session': db.session, 'model': Faq}
