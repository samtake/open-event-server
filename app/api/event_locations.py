from flask import request, url_for
from flask_rest_jsonapi import ResourceList
from flask_rest_jsonapi.pagination import add_pagination_links
from flask_rest_jsonapi.querystring import QueryStringManager as QSManager
from sqlalchemy import desc, func

from app.api.bootstrap import api
from app.api.schema.event_locations import EventLocationSchema
from app.models import db
from app.models.event import Event
from app.models.event_location import EventLocation


class EventLocationList(ResourceList):
    """
    列出事件位置
    """

    def get(self, *args, **kwargs):
        """获取事件位置列表"""
        qs = QSManager(request.args, self.schema)
        # 查询最受欢迎的位置（按事件数量排序）
        popular_locations = (
            db.session.query(
                Event.searchable_location_name, func.count(Event.id).label('counts')
            )
            .group_by(Event.searchable_location_name)
            .order_by(desc('counts'))
            .limit(6)
        )
        locations = []
        # 处理查询结果
        for location, _ in popular_locations:
            if location is not None:
                new_location = EventLocation(name=location)
                new_location.id = len(locations)
                locations.append(new_location)
        schema = EventLocationSchema()
        result = schema.dump(locations, many=True).data
        view_kwargs = (
            request.view_args if getattr(self, 'view_kwargs', None) is True else {}
        )
        # 添加分页链接
        add_pagination_links(
            result, len(locations), qs, url_for(self.view, **view_kwargs)
        )
        result.update({'meta': {'count': len(locations)}})
        return result

    # 权限装饰器，只有管理员才能执行POST方法
    decorators = (api.has_permission('is_admin', methods="POST"),)
    schema = EventLocationSchema
    data_layer = {'session': db.session, 'model': EventLocation}
