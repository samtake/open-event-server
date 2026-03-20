from flask_rest_jsonapi import ResourceDetail, ResourceList, ResourceRelationship

from app.api.bootstrap import api
from app.api.helpers.db import safe_query_kwargs
from app.api.schema.custom_system_roles import CustomSystemRoleSchema
from app.models import db
from app.models.custom_system_role import CustomSysRole
from app.models.panel_permission import PanelPermission


class CustomSystemRoleList(ResourceList):
    """
    列出和创建自定义系统角色
    """

    def query(self, view_kwargs):
        """
        面板权限列表的查询方法
        :param view_kwargs: 视图关键字参数
        :return:
        """
        # 查询所有自定义系统角色
        query_ = self.session.query(CustomSysRole)
        # 如果提供了面板ID，则过滤该面板的角色
        if view_kwargs.get('panel_id'):
            panel = safe_query_kwargs(PanelPermission, view_kwargs, 'panel_id')
            query_ = CustomSysRole.query.filter(
                CustomSysRole.panel_permissions.any(id=panel.id)
            )

        return query_

    # 权限装饰器，只有管理员才能执行POST方法
    decorators = (api.has_permission('is_admin', methods="POST"),)
    schema = CustomSystemRoleSchema
    data_layer = {
        'session': db.session,
        'model': CustomSysRole,
        'methods': {'query': query},
    }


class CustomSystemRoleDetail(ResourceDetail):
    """
    根据ID获取自定义系统角色详情
    """

    def before_get_object(self, view_kwargs):
        """
        获取用户对象前的检查方法
        :param view_kwargs: 视图关键字参数
        :return:
        """
        if view_kwargs.get('role_id') is not None:
            panel_perm = safe_query_kwargs(PanelPermission, view_kwargs, 'role_id')
            if panel_perm.role_id is not None:
                view_kwargs['id'] = panel_perm.role_id
            else:
                view_kwargs['id'] = None

    decorators = (api.has_permission('is_admin', methods="PATCH,DELETE"),)
    schema = CustomSystemRoleSchema
    data_layer = {
        'session': db.session,
        'model': CustomSysRole,
        'methods': {'before_get_object': before_get_object},
    }


class CustomSystemRoleRelationship(ResourceRelationship):
    """
    Custom System Role Relationship
    """

    decorators = (api.has_permission('is_admin', methods="PATCH,DELETE"),)
    schema = CustomSystemRoleSchema
    data_layer = {'session': db.session, 'model': CustomSysRole}
