from flask_rest_jsonapi import ResourceDetail, ResourceList, ResourceRelationship

from app.api.bootstrap import api
from app.api.helpers.query import event_query
from app.api.helpers.utilities import require_relationship
from app.api.schema.social_links import SocialLinkSchema
from app.models import db
from app.models.social_link import SocialLink


class SocialLinkListPost(ResourceList):
    """
    事件的社交链接列表和创建类
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

    # 允许的方法
    methods = ['POST']
    schema = SocialLinkSchema
    data_layer = {'session': db.session, 'model': SocialLink}


class SocialLinkList(ResourceList):
    """
    事件的社交链接列表类
    """

    def query(self, view_kwargs):
        """
        社交链接的查询方法
        :param view_kwargs: 视图关键字参数
        :return:
        """
        # 查询所有社交链接
        query_ = self.session.query(SocialLink)
        # 根据事件查询条件过滤
        query_ = event_query(query_, view_kwargs)
        return query_

    view_kwargs = True
    # 允许的方法
    methods = ['GET']
    schema = SocialLinkSchema
    data_layer = {'session': db.session, 'model': SocialLink, 'methods': {'query': query}}


class SocialLinkDetail(ResourceDetail):
    """
    Social Link detail by id
    """

    decorators = (
        api.has_permission(
            'is_coorganizer',
            methods="PATCH,DELETE",
            fetch="event_id",
            model=SocialLink,
        ),
    )
    schema = SocialLinkSchema
    data_layer = {'session': db.session, 'model': SocialLink}


class SocialLinkRelationship(ResourceRelationship):
    """
    Social Link Relationship
    """

    decorators = (
        api.has_permission(
            'is_coorganizer',
            methods="PATCH,DELETE",
            fetch="event_id",
            model=SocialLink,
        ),
    )
    methods = ['GET', 'PATCH']
    schema = SocialLinkSchema
    data_layer = {'session': db.session, 'model': SocialLink}
