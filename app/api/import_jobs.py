from flask_jwt_extended import current_user
from flask_rest_jsonapi import ResourceDetail, ResourceList

from app.api.helpers.permissions import jwt_required
from app.api.schema.import_jobs import ImportJobSchema
from app.models import db
from app.models.import_job import ImportJob


class ImportJobList(ResourceList):
    """
    列出导入作业
    """

    def query(self, kwargs):
        """查询方法"""
        query_ = self.session.query(ImportJob)
        # 过滤当前用户的导入作业
        query_ = query_.filter_by(user_id=current_user.id)
        return query_

    # 需要JWT认证
    decorators = (jwt_required,)
    schema = ImportJobSchema
    data_layer = {
        'session': db.session,
        'model': ImportJob,
        'methods': {
            'query': query,
        },
    }


class ImportJobDetail(ResourceDetail):
    """
    根据ID获取导入作业详情
    """

    # 需要JWT认证
    decorators = (jwt_required,)
    schema = ImportJobSchema
    data_layer = {'session': db.session, 'model': ImportJob}
