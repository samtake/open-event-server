"""
此API用于存储Celery任务的结果
并用于轮询等目的
"""
from celery.result import AsyncResult
from flask import Blueprint, current_app, jsonify

from app.api.helpers.utilities import TASK_RESULTS

celery_routes = Blueprint('tasks', __name__, url_prefix='/v1')


@celery_routes.route('/tasks/<string:task_id>')
def celery_task(task_id):
    """
    获取基于API的任务的Celery任务状态
    """
    # 如果是always eager模式，获取结果。不要调用AsyncResult
    # AsyncResult会从redis中查找
    if current_app.config.get('CELERY_ALWAYS_EAGER'):
        state = TASK_RESULTS[task_id]['state']
        info = TASK_RESULTS[task_id]['result']
    else:
        from app.api.helpers.tasks import celery

        result = AsyncResult(id=task_id, app=celery)
        state = result.state
        info = result.info
    # 检查状态
    if state == 'SUCCESS':
        if type(info) is dict:
            # 检查是否是错误
            if '__error' in info:
                return jsonify(state='FAILURE', result=info['result'])
            # 正常返回
        return jsonify(state=state, result=info)
    return jsonify(state=state)
