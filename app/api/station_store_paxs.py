from flask_rest_jsonapi import ResourceDetail, ResourceList, ResourceRelationship
from flask_rest_jsonapi.exceptions import ObjectNotFound

from app.api.helpers.permission_manager import has_access
from app.api.helpers.permissions import jwt_required
from app.api.helpers.utilities import require_relationship
from app.api.schema.station_store_pax import StationStorePaxSchema
from app.models import db
from app.models.session import Session
from app.models.station import Station
from app.models.station_store_pax import StationStorePax


class StationStorePaxList(ResourceList):
    """创建和列出站点存储人数"""

    def query(self, view_kwargs):
        """
        不同view_kwargs的查询方法
        :param view_kwargs: 视图关键字参数
        :return:
        """
        # 查询所有站点存储人数
        query_ = self.session.query(StationStorePax)
        # 如果提供了站点ID，则过滤该站点的数据
        if view_kwargs.get('station_id'):
            query_ = query_.join(Station).filter_by(id=view_kwargs.get('station_id'))
        # 如果提供了会话ID，则过滤该会话的数据
        if view_kwargs.get('session_id'):
            query_ = query_.join(Session).filter_by(id=view_kwargs.get('session_id'))

        return query_

    view_kwargs = True
    # 需要JWT认证
    decorators = (jwt_required,)
    # 允许的方法
    methods = [
        'GET',
    ]
    schema = StationStorePaxSchema
    data_layer = {
        'session': db.session,
        'model': StationStorePax,
        'methods': {'query': query},
    }


class StationStorePaxDetail(ResourceDetail):
    """根据ID获取站点存储人数详情"""

    @staticmethod
    def before_patch(_args, _kwargs, data):
        """
        patch方法前的检查方法
        :param _args:
        :param kwargs:
        :param data:
        :return:
        """
        if data['station']:
            require_relationship(['station'], data)
            if not has_access('is_coorganizer', station=data['station']):
                raise ObjectNotFound(
                    {'parameter': 'station'},
                    f"Station: {data['station']} not found",
                )

        if data['session']:
            require_relationship(['session'], data)
            if not has_access('is_coorganizer', session=data['session']):
                raise ObjectNotFound(
                    {'parameter': 'session'},
                    f"Session: {data['session']} not found",
                )

    schema = StationStorePaxSchema
    data_layer = {
        'session': db.session,
        'model': StationStorePax,
    }


class StationStorePaxRelationship(ResourceRelationship):
    """StationStorePax Relationship (Required)"""

    decorators = (jwt_required,)
    methods = ['GET', 'PATCH']
    schema = StationStorePaxSchema
    data_layer = {'session': db.session, 'model': StationStorePax}


class StationStorePaxListPost(ResourceList):
    """Create and List StationStorePax"""

    @staticmethod
    def before_post(_args, _kwargs, data):
        """
        method to check for required relationship with event and microlocation
        :param data:
        :return:
        """
        require_relationship(['station'], data)
        if not has_access('is_coorganizer', station=data['station']):
            raise ObjectNotFound(
                {'parameter': 'station'},
                f"Station: {data['station']} not found",
            )

        require_relationship(['session'], data)
        if not has_access('is_coorganizer', session=data['session']):
            raise ObjectNotFound(
                {'parameter': 'session'},
                f"Session: {data['session']} not found",
            )

    schema = StationStorePaxSchema
    methods = [
        'POST',
    ]
    data_layer = {'session': db.session, 'model': StationStorePax}
