from flask_rest_jsonapi import ResourceDetail

from app.api.bootstrap import api
from app.api.schema.image_sizes import SpeakerImageSizeSchema
from app.models import db
from app.models.image_size import ImageSizes


class SpeakerImageSizeDetail(ResourceDetail):
    """
    根据ID获取演讲者图片尺寸详情
    """

    @classmethod
    def before_get(self, args, kwargs):
        """get方法前的检查方法，设置ID为2"""
        kwargs['id'] = 2

    # 权限装饰器，只有管理员才能执行PATCH方法
    decorators = (api.has_permission('is_admin', methods="PATCH", id="2"),)
    # 允许的方法
    methods = ['GET', 'PATCH']
    schema = SpeakerImageSizeSchema
    data_layer = {'session': db.session, 'model': ImageSizes}
