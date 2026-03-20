from flask_rest_jsonapi import ResourceDetail, ResourceList, ResourceRelationship

from app.api.bootstrap import api
from app.api.helpers.db import safe_query_kwargs
from app.api.helpers.errors import ForbiddenError
from app.api.helpers.permission_manager import has_access
from app.api.helpers.query import event_query
from app.api.helpers.utilities import require_relationship
from app.api.schema.ticket_tags import TicketTagSchema
from app.models import db
from app.models.ticket import Ticket, TicketTag, ticket_tags_table


class TicketTagListPost(ResourceList):
    """
    门票标签列表和创建类
    """

    def before_post(self, args, kwargs, data):
        """
        post方法前的检查方法，用于验证必需的关系
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

    schema = TicketTagSchema
    # 允许的方法
    methods = [
        'POST',
    ]
    data_layer = {'session': db.session, 'model': TicketTag}


class TicketTagList(ResourceList):
    """
    根据事件ID或门票ID列出门票标签
    """

    def query(self, view_kwargs):
        """
        根据不同参数查询门票标签的方法
        :param view_kwargs: 视图关键字参数
        :return:
        """
        query_ = self.session.query(TicketTag)
        if view_kwargs.get('ticket_id'):
            ticket = safe_query_kwargs(Ticket, view_kwargs, 'ticket_id')
            query_ = query_.join(ticket_tags_table).filter_by(ticket_id=ticket.id)
        query_ = event_query(query_, view_kwargs)
        return query_

    view_kwargs = True
    schema = TicketTagSchema
    methods = [
        'GET',
    ]
    data_layer = {'session': db.session, 'model': TicketTag, 'methods': {'query': query}}


class TicketTagDetail(ResourceDetail):
    """
    TicketTag detail by id
    """

    decorators = (
        api.has_permission(
            'is_coorganizer',
            methods="PATCH,DELETE",
            fetch="event_id",
            model=TicketTag,
        ),
    )
    schema = TicketTagSchema
    data_layer = {'session': db.session, 'model': TicketTag}


class TicketTagRelationshipRequired(ResourceRelationship):
    """
    TicketTag Relationship
    """

    decorators = (
        api.has_permission(
            'is_coorganizer',
            methods="PATCH,DELETE",
            fetch="event_id",
            model=TicketTag,
        ),
    )
    schema = TicketTagSchema
    methods = ['GET', 'PATCH']
    schema = TicketTagSchema
    data_layer = {'session': db.session, 'model': TicketTag}


class TicketTagRelationshipOptional(ResourceRelationship):
    """
    TicketTag Relationship
    """

    decorators = (
        api.has_permission(
            'is_coorganizer',
            methods="PATCH,DELETE",
            fetch="event_id",
            model=TicketTag,
        ),
    )
    schema = TicketTagSchema
    schema = TicketTagSchema
    data_layer = {'session': db.session, 'model': TicketTag}
