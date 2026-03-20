from flask_rest_jsonapi import ResourceDetail, ResourceList, ResourceRelationship

from app.api.bootstrap import api
from app.api.helpers.errors import ForbiddenError
from app.api.helpers.query import event_query
from app.api.schema.users_events_roles import UsersEventsRolesSchema
from app.models import db
from app.models.role_invite import RoleInvite
from app.models.users_events_role import UsersEventsRoles


class UsersEventsRolesList(ResourceList):
    """
    列出和创建用户事件角色
    """

    def query(self, view_kwargs):
        """查询方法"""
        query_ = self.session.query(UsersEventsRoles)
        # 查询事件下的用户事件角色
        query_ = event_query(query_, view_kwargs)

        return query_

    view_kwargs = True
    # 权限装饰器，只有共同组织者才能访问
    decorators = (
        api.has_permission('is_coorganizer', fetch='event_id', model=UsersEventsRoles),
    )
    # 允许的方法
    methods = ['GET']
    schema = UsersEventsRolesSchema
    data_layer = {
        'session': db.session,
        'model': UsersEventsRoles,
        'methods': {'query': query},
    }


class UsersEventsRolesDetail(ResourceDetail):
    """
    根据ID获取用户事件角色详情
    """

    def before_delete_object(self, users_events_roles, view_kwargs):
        """删除对象前的检查方法"""
        role = users_events_roles.role
        if role:
            # 不能删除事件所有者
            if role.name == "owner":
                raise ForbiddenError(
                    {'source': 'Role'},
                    '不能删除事件的所有者。',
                )
            RoleInvite.query.filter_by(
                event_id=users_events_roles.event_id,
                email=users_events_roles.user.email,
                role_id=role.id,
            ).delete(synchronize_session=False)

    methods = ['GET', 'PATCH', 'DELETE']
    decorators = (
        api.has_permission('is_coorganizer', fetch='event_id', model=UsersEventsRoles),
    )
    schema = UsersEventsRolesSchema
    data_layer = {
        'session': db.session,
        'model': UsersEventsRoles,
        'methods': {'before_delete_object': before_delete_object},
    }


class UsersEventsRolesRelationship(ResourceRelationship):
    """
    users_events_roles Relationship
    """

    methods = ['GET', 'PATCH']
    schema = UsersEventsRolesSchema
    data_layer = {'session': db.session, 'model': UsersEventsRoles}
