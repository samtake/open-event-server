from flask_rest_jsonapi import ResourceDetail, ResourceList, ResourceRelationship

from app.api.bootstrap import api
from app.api.helpers.db import safe_query_kwargs
from app.api.schema.panel_permissions import PanelPermissionSchema
from app.models import db
from app.models.custom_system_role import CustomSysRole
from app.models.panel_permission import PanelPermission


class PanelPermissionList(ResourceList):
    """
    列出面板权限
    """

    def query(self, view_kwargs):
        """
        面板权限列表的查询方法
        :param view_kwargs: 视图关键字参数
        :return:
        """
        # 查询所有面板权限
        query_ = self.session.query(PanelPermission)
        # 如果提供了自定义系统角色ID，则过滤该角色的权限
        if view_kwargs.get('custom_system_role_id'):
            role = safe_query_kwargs(
                CustomSysRole,
                view_kwargs,
                'custom_system_role_id',
            )
            query_ = PanelPermission.query.filter(
                PanelPermission.custom_system_roles.any(id=role.id)
            )

        return query_

    # 权限装饰器，只有管理员才能访问
    decorators = (api.has_permission('is_admin', methods="GET,POST"),)
    schema = PanelPermissionSchema
    data_layer = {
        'session': db.session,
        'model': PanelPermission,
        'methods': {'query': query},
    }


class PanelPermissionDetail(ResourceDetail):
    """
    根据ID获取面板权限详情
    """

    schema = PanelPermissionSchema
    # 权限装饰器，只有管理员才能访问
    decorators = (api.has_permission('is_admin', methods="GET,PATCH,DELETE"),)
    data_layer = {'session': db.session, 'model': PanelPermission}


class PanelPermissionRelationship(ResourceRelationship):
    """
    Panel Permission Relationship
    """

    decorators = (api.has_permission('is_admin', methods="PATCH,DELETE"),)
    methods = ['GET', 'PATCH']
    schema = PanelPermissionSchema
    data_layer = {'session': db.session, 'model': PanelPermission}
