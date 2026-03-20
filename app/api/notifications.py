from flask_rest_jsonapi import ResourceDetail, ResourceList, ResourceRelationship

from app.api.bootstrap import api
from app.api.helpers.db import safe_query_kwargs
from app.api.schema.notifications import NotificationSchema
from app.models import db
from app.models.notification import Notification
from app.models.user import User


class NotificationListAdmin(ResourceList):
    """
    列出所有通知
    """

    # 权限装饰器，只有管理员才能访问
    decorators = (api.has_permission('is_admin'),)
    # 允许的方法
    methods = ['GET']
    schema = NotificationSchema
    data_layer = {'session': db.session, 'model': Notification}


class NotificationList(ResourceList):
    """
    列出所有通知
    """

    def query(self, view_kwargs):
        """
        通知列表的查询方法
        :param view_kwargs: 视图关键字参数
        :return:
        """
        # 查询所有通知
        query_ = self.session.query(Notification)
        # 如果提供了用户ID，则过滤该用户的通知
        if view_kwargs.get('user_id'):
            user = safe_query_kwargs(User, view_kwargs, 'user_id')
            query_ = query_.join(User).filter(User.id == user.id)
        return query_

    def before_create_object(self, data, view_kwargs):
        """
        post前创建对象的方法
        :param data: 数据
        :param view_kwargs: 视图关键字参数
        :return:
        """
        # 如果提供了用户ID，则设置通知的用户ID
        if view_kwargs.get('user_id') is not None:
            user = safe_query_kwargs(User, view_kwargs, 'user_id')
            data['user_id'] = user.id

    view_kwargs = True
    decorators = (
        api.has_permission('is_user_itself', fetch="user_id", model=Notification),
    )
    methods = ['GET']
    schema = NotificationSchema
    data_layer = {
        'session': db.session,
        'model': Notification,
        'methods': {'query': query, 'before_create_object': before_create_object},
    }


class NotificationDetail(ResourceDetail):
    """
    Notification detail by ID
    """

    decorators = (
        api.has_permission(
            'is_user_itself', methods="PATCH,DELETE", fetch="user_id", model=Notification
        ),
    )
    schema = NotificationSchema
    data_layer = {
        'session': db.session,
        'model': Notification,
    }


class NotificationRelationship(ResourceRelationship):
    """
    Notification Relationship
    """

    decorators = (
        api.has_permission('is_user_itself', fetch="user_id", model=Notification),
    )
    schema = NotificationSchema
    methods = ['GET', 'PATCH']
    data_layer = {'session': db.session, 'model': Notification}
