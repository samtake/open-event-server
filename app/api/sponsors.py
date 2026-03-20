from flask_rest_jsonapi import ResourceDetail, ResourceList, ResourceRelationship

from app.api.bootstrap import api
from app.api.events import Event
from app.api.helpers.db import get_count
from app.api.helpers.errors import ForbiddenError
from app.api.helpers.permission_manager import has_access
from app.api.helpers.query import event_query
from app.api.helpers.utilities import require_relationship
from app.api.schema.sponsors import SponsorSchema
from app.models import db
from app.models.sponsor import Sponsor


class SponsorListPost(ResourceList):
    """
    赞助商列表和创建类
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
        # 检查事件是否启用了赞助商功能
        if (
            get_count(
                db.session.query(Event).filter_by(
                    id=int(data['event']), is_sponsors_enabled=False
                )
            )
            > 0
        ):
            raise ForbiddenError({'pointer': ''}, "此事件已禁用赞助商功能")

    # 允许的方法
    methods = ['POST']
    schema = SponsorSchema
    data_layer = {'session': db.session, 'model': Sponsor}


class SponsorList(ResourceList):
    """
    赞助商列表类
    """

    def query(self, view_kwargs):
        """
        query method for Sponsor List
        :param view_kwargs:
        :return:
        """
        query_ = self.session.query(Sponsor)
        query_ = event_query(query_, view_kwargs)
        return query_

    view_kwargs = True
    methods = ['GET']
    schema = SponsorSchema
    data_layer = {'session': db.session, 'model': Sponsor, 'methods': {'query': query}}


class SponsorDetail(ResourceDetail):
    """
    Sponsor detail by id
    """

    decorators = (
        api.has_permission(
            'is_coorganizer',
            methods="PATCH,DELETE",
            fetch="event_id",
            model=Sponsor,
        ),
    )
    schema = SponsorSchema
    data_layer = {'session': db.session, 'model': Sponsor}


class SponsorRelationship(ResourceRelationship):
    """
    Sponsor Schema Relation
    """

    decorators = (
        api.has_permission(
            'is_coorganizer',
            methods="PATCH,DELETE",
            fetch="event_id",
            model=Sponsor,
        ),
    )
    methods = ['GET', 'PATCH']
    schema = SponsorSchema
    data_layer = {'session': db.session, 'model': Sponsor}
