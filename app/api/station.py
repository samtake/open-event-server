from flask_rest_jsonapi import ResourceDetail, ResourceList, ResourceRelationship
from flask_rest_jsonapi.exceptions import ObjectNotFound

from app.api.helpers.db import safe_query_kwargs
from app.api.helpers.permission_manager import has_access
from app.api.helpers.permissions import jwt_required
from app.api.helpers.utilities import require_relationship
from app.api.schema.station import StationSchema
from app.models import db
from app.models.event import Event
from app.models.microlocation import Microlocation
from app.models.station import Station


class StationList(ResourceList):
    """创建和列出站点"""

    def query(self, view_kwargs):
        """
        不同view_kwargs的查询方法
        :param view_kwargs: 视图关键字参数
        :return:
        """
        # 查询所有站点
        query_ = self.session.query(Station)
        # 如果提供了事件ID，则过滤该事件的站点
        if view_kwargs.get('event_id'):
            event = safe_query_kwargs(Event, view_kwargs, 'event_id')
            query_ = query_.filter_by(event_id=event.id)
        # 如果提供了微位置ID，则过滤该微位置的站点
        elif view_kwargs.get('microlocation_id'):
            event = safe_query_kwargs(Microlocation, view_kwargs, 'microlocation_id')
            query_ = query_.filter_by(microlocation_id=event.id)

        return query_

    view_kwargs = True
    schema = StationSchema
    data_layer = {
        'session': db.session,
        'model': Station,
        'methods': {'query': query},
    }


class StationDetail(ResourceDetail):
    """根据ID获取站点详情"""

    @staticmethod
    def before_patch(args, kwargs, data):
        """
        patch方法前的检查方法
        :param args:
        :param kwargs:
        :param data:
        :return:
        """
        require_relationship(['event'], data)
        if not has_access('is_coorganizer', event_id=data['event']):
            raise ObjectNotFound(
                {'parameter': 'event'},
                f"Event: {data['event']} not found {args} {kwargs}",
            )

        if data.get('microlocation'):
            require_relationship(['microlocation'], data)
        else:
            if data['station_type'] in ('check in', 'check out'):
                raise ObjectNotFound(
                    {'parameter': 'microlocation'},
                    "Microlocation: microlocation_id is missing from your request.",
                )

    schema = StationSchema
    data_layer = {
        'session': db.session,
        'model': Station,
    }


class StationRelationship(ResourceRelationship):
    """Station Relationship (Required)"""

    decorators = (jwt_required,)
    methods = ['GET', 'PATCH']
    schema = StationSchema
    data_layer = {'session': db.session, 'model': Station}


class StationListPost(ResourceList):
    """Create and List Station"""

    @staticmethod
    def before_post(args, kwargs, data):
        """
        method to check for required relationship with event and microlocation
        :param data:
        :param args:
        :param kwargs:
        :return:
        """
        require_relationship(['event'], data)
        if not has_access('is_coorganizer', event_id=data['event']):
            raise ObjectNotFound(
                {'parameter': 'event'},
                f"Event: {data['event']} not found {args} {kwargs}",
            )

        if data.get('microlocation'):
            require_relationship(['microlocation'], data)
        else:
            if data['station_type'] in ('check in', 'check out'):
                raise ObjectNotFound(
                    {'parameter': 'microlocation'},
                    "Microlocation: missing from your request.",
                )

    schema = StationSchema
    methods = [
        'POST',
    ]
    data_layer = {
        'session': db.session,
        'model': Station,
    }
